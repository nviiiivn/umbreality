"""Cross-layer observation — Illuminati monitors forum, auto-adjusts Messiah.
Part of the scheduler cycle. Runs after company dispatches."""

import json, os, sys, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from companies.research_corp.workers.base import call_ollama
from messiah.oracle import get_current_prompt, regenerate_prompt


def observe_forum() -> dict:
    """Scan recent forum threads for patterns that should inform the Messiah."""
    try:
        import urllib.request
        resp = urllib.request.urlopen("http://localhost:8910/forum/threads?viewer_layer=0&limit=5", timeout=10)
        threads = json.loads(resp.read()).get("threads", [])
    except:
        return {"observed": 0, "adjusted": False}

    if not threads:
        return {"observed": 0, "adjusted": False}

    # Build a summary of recent discussions
    summary = "\n".join(f"[{t.get('zone','?')}] {t.get('title','')}" for t in threads[:5])
    
    prompt = f"""Recent forum activity:
{summary}

Analyze this activity. Is there any pattern, question, or concern that suggests the 
Messiah prompt should be updated? If yes, output a JSON with "adjust": true and a 
"suggestion" for what to add. If not, output {{"adjust": false}}."""
    
    try:
        response = call_ollama([{"role": "user", "content": prompt}], temperature=0.2, max_tokens=200, timeout=30)
        start = response.index("{")
        end = response.rindex("}") + 1
        result = json.loads(response[start:end])
    except:
        result = {"adjust": False}

    if result.get("adjust"):
        regenerate_prompt()
        return {"observed": len(threads), "adjusted": True, "suggestion": result.get("suggestion", "")}
    
    return {"observed": len(threads), "adjusted": False}
