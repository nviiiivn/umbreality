"""
UmbrealityAI — Phase 1: The First Worker
=========================================
Python ReAct loop that calls the tower Ollama model.
One tool: web search. Reports findings in structured format.

Usage:
    python worker.py "Find recent CVEs in Apache HTTP Server 2.4"
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config.settings import (
    TOWER_BASE_URL,
    PRIMARY_MODEL,
    REPORT_DIR,
    MAX_TOOL_CALLS,
    TEMPERATURE,
    TOKEN_LIMIT,
    WORKER_IDENTITY,
)
from tools.web_search import web_search, format_results


# ── Tool Registry ──────────────────────────────────────────────────────────

TOOLS = {
    "web_search": {
        "description": "Search the web for information. Use for finding docs, CVEs, vulnerabilities, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "description": "Number of results (1-10)"},
            },
            "required": ["query"],
        },
        "function": lambda query, num_results=5: web_search(query, num_results),
    },
}

TOOL_DESCRIPTIONS = "\n".join(
    f"- {name}: {info['description']}"
    for name, info in TOOLS.items()
)


# ── Ollama API ─────────────────────────────────────────────────────────────

def call_ollama(messages: list[dict], model: str = PRIMARY_MODEL) -> dict[str, Any]:
    """Call the tower's Ollama chat API."""
    resp = requests.post(
        f"{TOWER_BASE_URL}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": TEMPERATURE,
                "num_predict": TOKEN_LIMIT,
            },
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


# ── System Prompt ──────────────────────────────────────────────────────────

WORKER_SYSTEM_PROMPT = f"""You are {WORKER_IDENTITY['name']}, a security research worker for {WORKER_IDENTITY['company']}.

{WORKER_IDENTITY['mission']}

## Rules
1. You have tools available. Use them when you need information.
2. When you use a tool, output exactly: TOOL: <tool_name>
   ARGS: <JSON arguments>
3. When you have a final answer, output exactly:
   REPORT: <structured JSON with findings>
4. Do not explain your tool usage — just use the tool.
5. Do not ask questions. Execute the task.

## Available Tools
{TOOL_DESCRIPTIONS}

## Output Format
Your output must be parseable line by line. Either:
- TOOL: tool_name\\nARGS: {{"arg": "value"}}
- REPORT: {{"findings": [...], "summary": "..."}}
- THOUGHT: your reasoning (will not be passed to tools)

Always end with a REPORT when the task is complete.
"""


# ── ReAct Loop ─────────────────────────────────────────────────────────────

def extract_tool_call(text: str) -> tuple[str | None, dict | None]:
    """Parse TOOL/ARGS from model output."""
    lines = text.strip().split("\n")
    tool_line = None
    args_line = None
    for line in lines:
        if line.startswith("TOOL:"):
            tool_line = line[len("TOOL:"):].strip()
        elif line.startswith("ARGS:"):
            args_str = line[len("ARGS:"):].strip()
            try:
                args_line = json.loads(args_str)
            except json.JSONDecodeError:
                args_line = None
    if tool_line and tool_line in TOOLS:
        return tool_line, args_line or {}
    return None, None


def extract_report(text: str) -> dict | None:
    """Parse REPORT JSON from model output."""
    for line in text.strip().split("\n"):
        if line.startswith("REPORT:"):
            report_str = line[len("REPORT:"):].strip()
            try:
                return json.loads(report_str)
            except json.JSONDecodeError:
                return None
    return None


def build_prompt(task: str) -> list[dict]:
    """Build the initial message list."""
    return [
        {"role": "system", "content": WORKER_SYSTEM_PROMPT},
        {"role": "user", "content": f"Task: {task}\n\nExecute this task using your tools. Report findings when complete."},
    ]


def run_worker(task: str) -> dict:
    """Main ReAct loop. Returns final report."""
    messages = build_prompt(task)

    for step in range(MAX_TOOL_CALLS):
        print(f"\n[Step {step + 1}/{MAX_TOOL_CALLS}]")
        
        # Call model
        response = call_ollama(messages)
        content = response.get("message", {}).get("content", "")
        
        # Check for report
        report = extract_report(content)
        if report:
            print(f"  REPORT: {json.dumps(report, indent=2)}")
            return report

        # Check for tool call
        tool_name, tool_args = extract_tool_call(content)
        if tool_name:
            print(f"  TOOL: {tool_name}")
            print(f"  ARGS: {tool_args}")
            
            # Execute tool
            tool_fn = TOOLS[tool_name]["function"]
            result = tool_fn(**tool_args)
            
            formatted = format_results(result)
            
            # Add to context
            messages.append({"role": "assistant", "content": content})
            messages.append({
                "role": "tool",
                "content": f"Tool result ({tool_name}):\n{formatted}",
            })
        else:
            # No tool call, no report — must be thinking. Push forward.
            messages.append({"role": "assistant", "content": content})
            messages.append({
                "role": "user",
                "content": "Continue. Use a tool or provide your final REPORT.",
            })

    # Timeout — return what we have
    return {
        "error": "MAX_TOOL_CALLS_REACHED",
        "partial_output": messages[-1]["content"] if messages else "",
    }


def save_report(report: dict, task: str) -> str:
    """Save report to disk."""
    report_dir = Path(__file__).parent / REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = "".join(c if c.isalnum() else "_" for c in task[:30])
    path = report_dir / f"report_{timestamp}_{slug}.json"
    
    report_data = {
        "task": task,
        "timestamp": timestamp,
        "report": report,
    }
    
    path.write_text(json.dumps(report_data, indent=2))
    return str(path)


# ── Entry Point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python worker.py <task description>")
        print("Example: python worker.py 'Find recent CVEs in Apache HTTP Server 2.4'")
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    print(f"\n{'='*60}")
    print(f" UmbrealityAI — Phase 1 Worker")
    print(f" Task: {task}")
    print(f" Time: {datetime.now().isoformat()}")
    print(f" Model: {PRIMARY_MODEL}")
    print(f"{'='*60}\n")

    try:
        report = run_worker(task)
        path = save_report(report, task)
        print(f"\nReport saved to: {path}")
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
