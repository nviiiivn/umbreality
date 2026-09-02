"""Temple Resource Allocator — assigns models and endpoints based on task type."""
import json, urllib.request, os

TOWER_URL = os.environ.get("UAI_OLLAMA_URL", "http://192.168.86.24:11434")
LOCAL_URL = "http://localhost:11434"

RESOURCES = {
    "tower": {
        "url": TOWER_URL,
        "models": [
            "dolphin3:8b", "qwen2.5-coder:7b", "qwen3.5:9b",
            "deepseek-r1:14b", "qwen2.5-coder:14b", "qwen3:14b",
            "gemma4:latest", "llama3.2-vision:11b", "gemma3:latest",
            "huihui_ai/qwen3.5-abliterated:9b",
        ],
    },
    "local": {
        "url": LOCAL_URL,
        "models": ["qwen3.5:latest", "llama3.2:3b", "gemma3:latest", "nomic-embed-text:latest"],
    },
}

TASK_MODEL_MAP = [
    (["research", "search", "find", "investigate", "analyze", "report"], "dolphin3:8b", "tower"),
    (["code", "program", "function", "implement", "refactor", "debug"], "deepseek-coder-v2:16b", "tower"),
    (["reason", "complex", "hard", "deep", "difficult", "puzzle"], "openthinker:7b", "tower"),
    (["vision", "image", "picture", "photo", "diagram", "screenshot"], "llama3.2-vision:11b", "tower"),
    (["write", "draft", "chronicle", "record", "transcribe"], "hermes3:8b", "tower"),
    (["simple", "quick", "fast", "echo", "status", "check", "hello"], "nemotron-mini:4b", "tower"),
]

# every model above must exist; if one is pulled out from under us we fall
# back down this list rather than handing ollama a name it will 404 on.
FALLBACK_MODELS = ["dolphin3:8b", "huihui_ai/gemma-4-abliterated:e4b",
                   "hermes3:8b", "nemotron-mini:4b"]

_MODEL_CACHE = {"at": 0.0, "names": set()}


def _installed_models(url=None):
    """Model names ollama actually has. Cached for 60s."""
    import time
    import json as _j
    now = time.time()
    if now - _MODEL_CACHE["at"] < 60 and _MODEL_CACHE["names"]:
        return _MODEL_CACHE["names"]
    try:
        raw = urllib.request.urlopen(
            f"{url or TOWER_URL}/api/tags", timeout=5).read()
        names = {m["name"] for m in _j.loads(raw).get("models", [])}
    except Exception:
        names = set()
    if names:
        _MODEL_CACHE.update({"at": now, "names": names})
    return names


def _resolve_model(model, url=None):
    """Return `model` if installed, else the first working fallback."""
    have = _installed_models(url)
    if not have:
        return model          # cannot verify - do not second-guess
    if model in have:
        return model
    for alt in FALLBACK_MODELS:
        if alt in have:
            return alt
    return sorted(have)[0]


def _matches(keywords, text):
    """Word-boundary match, so 'script' does not match 'scriptorium'."""
    import re as _re
    return any(_re.search(r"\b" + _re.escape(kw) + r"\b", text) for kw in keywords)


def check_available(url: str) -> bool:
    try:
        urllib.request.urlopen(f"{url}/api/tags", timeout=3)
        return True
    except Exception:
        return False


def get_available_resources() -> dict:
    result = {"tower": [], "local": []}
    tower_up = check_available(TOWER_URL)
    local_up = check_available(LOCAL_URL)

    if tower_up:
        try:
            resp = urllib.request.urlopen(f"{TOWER_URL}/api/tags", timeout=5)
            data = json.loads(resp.read())
            result["tower"] = [m["name"] for m in data.get("models", [])]
        except Exception:
            result["tower"] = RESOURCES["tower"]["models"]

    if local_up:
        try:
            resp = urllib.request.urlopen(f"{LOCAL_URL}/api/tags", timeout=5)
            data = json.loads(resp.read())
            result["local"] = [m["name"] for m in data.get("models", [])]
        except Exception:
            result["local"] = RESOURCES["local"]["models"]

    return result


def allocate(company_name: str = "", task: str = "") -> dict:
    task_lower = task.lower()

    for keywords, model, tier in TASK_MODEL_MAP:
        if _matches(keywords, task_lower):
            url = TOWER_URL if tier == "tower" else LOCAL_URL
            if tier == "tower" and not check_available(TOWER_URL):
                tier = "local"
                url = LOCAL_URL
                model = "qwen3.5:latest"
            return {"model": _resolve_model(model, url), "endpoint": url, "tier": tier}

    if check_available(TOWER_URL):
        return {"model": _resolve_model("dolphin3:8b", TOWER_URL), "endpoint": TOWER_URL, "tier": "tower"}
    return {"model": _resolve_model("dolphin3:8b", TOWER_URL), "endpoint": TOWER_URL, "tier": "tower"}
