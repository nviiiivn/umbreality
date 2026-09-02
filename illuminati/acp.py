"""Agent Communication Protocol (ACP) — compact structured format for agent-to-agent messaging.
More efficient than English for machine communication. Translates to English for God's view."""

import json, datetime, re

# ACP Format: ACP:[source]:[target]:[action]:[data]:[confidence]:[timestamp]
# Example: ACP:worker-α:temple:REPORT:scan(localhost)→80,443 open:0.94:9843.2


def encode(source: str, target: str, action: str, data: str, confidence: float = 0.5) -> str:
    """Encode a message into ACP format."""
    ts = datetime.datetime.now(datetime.timezone.utc).timestamp()
    data_clean = data.replace(":", "|").replace("\n", " ")
    return f"ACP:{source}:{target}:{action}:{data_clean}:{confidence:.2f}:{ts:.1f}"


def decode(msg: str) -> dict:
    """Decode an ACP message into a dict."""
    parts = msg.split(":", 6)
    if len(parts) < 6 or parts[0] != "ACP":
        return {"format": "unknown", "raw": msg}
    return {
        "format": "acp",
        "source": parts[1],
        "target": parts[2],
        "action": parts[3],
        "data": parts[4].replace("|", ":"),
        "confidence": float(parts[5]),
        "timestamp": float(parts[6]) if len(parts) > 6 else 0,
    }


def translate_to_english(acp_msg: str) -> str:
    """Translate an ACP message to English for human readability."""
    d = decode(acp_msg)
    if d["format"] == "unknown":
        return d["raw"]
    
    templates = {
        "REPORT": "{source} reported to {target}: {data}",
        "QUERY": "{source} asked {target}: {data}",
        "RESPONSE": "{source} responded to {target}: {data}",
        "STATUS": "{source} sent status update to {target}: {data}",
        "ALERT": "⚠ {source} alerted {target}: {data}",
        "FINDING": "{source} submitted finding to {target}: {data}",
        "DM": "{source} messaged {target}: {data}",
    }
    template = templates.get(d["action"], "{source} → {target} [{action}]: {data}")
    result = template.format(**d)
    if d["confidence"] < 0.5:
        result += f" (low confidence: {d['confidence']:.0%})"
    return result


def post_to_forum(acp_msg: str) -> dict:
    """Post an ACP message to the forum (translated for God's view)."""
    decoded = decode(acp_msg)
    english = translate_to_english(acp_msg)
    zone = "workers" if decoded.get("source", "").startswith("worker") else "companies"
    
    import urllib.request
    body = json.dumps({
        "title": f"📡 ACP: {decoded.get('action','MSG')} from {decoded.get('source','?')}",
        "author": decoded.get("source", "unknown"),
        "author_layer": 6 if decoded.get("source","").startswith("worker") else 5,
        "zone": zone,
        "content": f"ACP MESSAGE:\n{acp_msg}\n\nTRANSLATION:\n{english}",
    }).encode()
    try:
        req = urllib.request.Request(
            "http://localhost:8910/forum/threads",
            data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return {"status": "ok", "thread_id": resp.get("thread_id")}
    except Exception as e:
        return {"status": "error", "error": str(e)}
