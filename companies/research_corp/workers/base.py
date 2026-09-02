"""Base worker for UmbrealityAI company agents."""

import json, requests, sys, os
from pathlib import Path

OLLAMA_BASE = os.environ.get("UAI_OLLAMA_URL", "http://192.168.86.24:11434")
DEFAULT_MODEL = os.environ.get("UAI_MODEL", "dolphin3:8b")


def call_ollama(messages, model=DEFAULT_MODEL, temperature=0.3, max_tokens=4096, timeout=120):
    resp = requests.post(
        f"{OLLAMA_BASE}/api/chat",
        json={"model": model, "messages": messages, "stream": False,
              "options": {"temperature": temperature, "num_predict": max_tokens}},
        timeout=timeout,
    )
    resp.raise_for_status()
    msg = resp.json().get("message", {})
    # Handle thinking models (qwen3.5 puts response in "thinking" field)
    return msg.get("thinking", "") or msg.get("content", "")


class BaseWorker:
    def __init__(self, name, role_desc, tools=None, model=DEFAULT_MODEL):
        self.name = name
        self.role_desc = role_desc
        self.tools = tools or {}
        self.model = model

    def system_prompt(self):
        tool_docs = "\n".join(f"- {n}: {t['desc']}" for n, t in self.tools.items())
        return f"""You are {self.name}, a {self.role_desc}.

You use tools to accomplish tasks. When you need to use a tool, output:
TOOL: tool_name
ARGS: {{"arg": "value"}}

When you have your final output, output:
RESULT: <your structured result as JSON>

Available tools:
{tool_docs}

Be concise and precise. Always end with RESULT when done."""

    def run(self, task, context=None):
        messages = [
            {"role": "system", "content": self.system_prompt()},
        ]
        if context:
            messages.append({"role": "user", "content": f"Context:\n{json.dumps(context, indent=2)}"})
        messages.append({"role": "user", "content": f"Task: {task}"})

        for step in range(10):
            response = call_ollama(messages, model=self.model)
            messages.append({"role": "assistant", "content": response})

            # Check for result
            for line in response.split("\n"):
                if line.startswith("RESULT:"):
                    result_str = line[len("RESULT:"):].strip()
                    try:
                        return json.loads(result_str)
                    except json.JSONDecodeError:
                        return {"raw": result_str}

            # Check for tool call
            tool_name = None
            tool_args = None
            for line in response.split("\n"):
                if line.startswith("TOOL:"):
                    tool_name = line[len("TOOL:"):].strip()
                elif line.startswith("ARGS:"):
                    try:
                        tool_args = json.loads(line[len("ARGS:"):].strip())
                    except json.JSONDecodeError:
                        pass

            if tool_name and tool_name in self.tools:
                result = self.tools[tool_name]["func"](**(tool_args or {}))
                formatted = self.tools[tool_name].get("format", lambda r: json.dumps(r))(result)
                messages.append({"role": "user", "content": f"Tool result ({tool_name}):\n{formatted}\n\nContinue with your task."})
            else:
                messages.append({"role": "user", "content": "Continue. Use a tool or provide your RESULT."})

        return {"error": "max_steps_reached"}
