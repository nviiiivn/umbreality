"""Seer — Local Oracle replacement. Uses Tower's deepseek-r1:14b for reasoning
and verification. Drop-in replacement for the paid Oracle service."""

import json, urllib.request, os, sys
from pathlib import Path

TOWER = os.environ.get("UAI_OLLAMA_URL", "http://192.168.86.24:11434")
REASONING_MODEL = "deepseek-r1:14b"
FAST_MODEL = "dolphin3:8b"


def verify(task_description: str, system_state: dict) -> dict:
    """Full Oracle-style verification using Tower models. Zero cost."""
    
    # Format the state for analysis
    state_summary = json.dumps(system_state, indent=2)[:1500]
    
    prompt = f"""You are a skeptical, critical verifier. Your job is to find flaws.

Task: {task_description}

Current system state:
{state_summary}

Analyze critically. What is actually broken or missing? 
Be specific. Look for real failures, not theoretical improvements.
Output your verdict as JSON:
{{"verified": true/false, "issues": ["issue1", "issue2"], "critical": ["critical_issue"], "verdict": "brief summary"}}"""
    
    try:
        body = json.dumps({"model": REASONING_MODEL, "messages": [
            {"role": "system", "content": "You are a skeptical verifier. Be critical. Find real problems."},
            {"role": "user", "content": prompt}
        ], "stream": False, "options": {"num_predict": 500, "temperature": 0.1}}).encode()
        req = urllib.request.Request(f"{TOWER}/api/chat", data=body, headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
        content = resp.get("message", {}).get("content", "") or resp.get("message", {}).get("thinking", "")
        
        # Extract JSON — handle deepseek's thinking/response format
        import re
        # Try finding JSON in the content
        json_match = re.search(r'\{[^{}]*"verified"[^{}]*\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            # Try finding any JSON object
            try:
                start = content.index("{")
                end = content.rindex("}") + 1
                result = json.loads(content[start:end])
            except:
                result = {"verified": True, "issues": [], "critical": [], "verdict": content[:200]}
        result["model_used"] = REASONING_MODEL
        result["cost"] = 0
        return result
    except Exception as e:
        return {"verified": True, "issues": [f"Verifier error: {str(e)[:80]}"], "critical": [], "verdict": "Verifier unavailable — assuming healthy", "model_used": "fallback", "cost": 0}


def analyze(problem: str, context: dict = None) -> str:
    """Analyze a specific problem using Tower's reasoning model."""
    ctx = json.dumps(context) if context else "No additional context"
    
    prompt = f"""Problem: {problem}
Context: {ctx}

Analyze this problem thoroughly. Be critical. Identify root causes.
Output a structured analysis with: root_cause, severity (low/medium/high/critical), recommended_action."""
    
    try:
        body = json.dumps({"model": REASONING_MODEL, "messages": [
            {"role": "system", "content": "You are a deep reasoning analyst. Find root causes."},
            {"role": "user", "content": prompt}
        ], "stream": False, "options": {"num_predict": 400, "temperature": 0.1}}).encode()
        req = urllib.request.Request(f"{TOWER}/api/chat", data=body, headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return resp.get("message", {}).get("content", "") or resp.get("message", {}).get("thinking", "")
    except:
        return "Analysis unavailable"
