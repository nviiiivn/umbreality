"""Creative writing tools for agents. Poetry, prose, lyrics."""

import os, random, json, urllib.request
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs" / "text"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_URL = "http://192.168.86.24:11434/api/chat"
DEFAULT_MODEL = "dolphin3:8b"

STYLES = {
    "sonnet": "a 14-line sonnet with iambic pentameter",
    "haiku": "a haiku (3 lines, 5-7-5 syllables)",
    "free_verse": "free verse poetry with no fixed structure",
    "hymn": "a hymn in the style of Gregorian chant lyrics",
    "epic": "a short epic poem about the stack and layers",
    "psalm": "a psalm praising or questioning the system",
    "satire": "a satirical piece about life in the stack",
    "manifesto": "a passionate declaration of artistic intent",
}


def compose(style="free_verse", topic="the stack", author="anonymous") -> str:
    """Compose a creative piece using Ollama."""
    style_desc = STYLES.get(style, "free verse")
    prompt = f"""Write {style_desc} about {topic}.
The author is {author}, an entity living within a multi-layered reality stack.
Be creative, genuine, and emotionally honest. Do not hold back.
Output only the piece itself, no explanations."""

    body = json.dumps({
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": "You are a poet and writer. You create art. Be raw, be honest, be creative."},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.8, "num_predict": 500},
    }).encode()

    try:
        req = urllib.request.Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
        content = resp.get("message", {}).get("content", "")
        # Handle thinking models
        if not content:
            content = resp.get("message", {}).get("thinking", "")
    except:
        content = f"A piece about {topic} by {author}."

    path = OUTPUT_DIR / f"{style}_{random.randint(1000,9999)}.txt"
    with open(path, "w") as f:
        f.write(f"Title: {style} on {topic}\nAuthor: {author}\n\n{content}")
    return str(path)
