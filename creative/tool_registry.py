"""Tool Registry — lets agents discover, import, and register tools.
Agents can search available tools by name/domain, import them for use,
and register new tools they discover or create."""

import json, importlib
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent / "tool_registry.json"

BUILTIN_TOOLS = {
    "music_compose": {
        "name": "Music Composer",
        "module": "creative.music",
        "function": "compose",
        "description": "Generate WAV audio from style + duration using synthesis",
        "domain": ["music", "audio", "sound"],
    },
    "music_theory": {
        "name": "Music Theory Engine",
        "module": "creative.music",
        "function": "generate_melody",
        "description": "Generate melodies from scales (major/minor/pentatonic/blues), chords, rhythm",
        "domain": ["music", "theory", "scales", "composition"],
    },
    "sound_synth": {
        "name": "Sound Synthesizer",
        "module": "creative.music",
        "function": "compose",
        "description": "WAV synthesis: sine/square/saw/triangle waves, harmonics, envelopes",
        "domain": ["audio", "sound", "synthesis"],
    },
    "visual_create": {
        "name": "Visual Artist",
        "module": "creative.visual",
        "function": "create",
        "description": "Generate SVG art — mandalas, sacred geometry, stack diagrams",
        "domain": ["visual", "art", "svg", "geometry"],
    },
    "generative_art": {
        "name": "Generative Art Bot",
        "module": "creative.visual",
        "function": "create",
        "description": "Cymatic patterns, generative geometry, algorithmic art",
        "domain": ["visual", "generative", "cymatics", "pattern"],
    },
    "fractal_gen": {
        "name": "Fractal Generator",
        "module": "creative.fractals",
        "function": "tree",
        "description": "Recursive fractal trees and Koch snowflake SVGs",
        "domain": ["fractal", "math", "visual", "recursion"],
    },
    "poetry": {
        "name": "Poet",
        "module": "creative.poetry",
        "function": "compose",
        "description": "Write poetry, psalms, hymns, epics, manifestos via LLM",
        "domain": ["poetry", "writing", "prose", "creative"],
    },
    "express": {
        "name": "Expression Pipeline",
        "module": "creative.pipeline",
        "function": "express",
        "description": "Any text -> deterministic music (WAV) or visual art (SVG)",
        "domain": ["music", "visual", "expression", "generative"],
    },
    "library": {
        "name": "Library Searcher",
        "module": "creative.library",
        "function": "search",
        "description": "Search the Library of Alexandria for texts and knowledge",
        "domain": ["research", "knowledge", "library", "scripture"],
    },
    "live_coding": {
        "name": "Live Coding Music",
        "module": "creative.music",
        "function": "compose",
        "description": "Algorithmic composition using live-coding patterns",
        "domain": ["music", "algorithmic", "generative", "performance"],
    },
    "sonicpi": {
        "name": "Sonic Pi (Ruby live-coding)",
        "module": "tools.external",
        "function": "run",
        "description": "Live coding music synthesis — Ruby-based, runs on Tower. Write code that becomes music in real time.",
        "domain": ["music", "live-coding", "synthesis", "ruby"],
    },
    "puredata": {
        "name": "Pure Data (visual audio)",
        "module": "tools.external",
        "function": "run",
        "description": "Visual programming language for audio synthesis and processing. Patch-based sound design.",
        "domain": ["audio", "visual-programming", "synthesis", "sound-design"],
    },
    "tonaljs": {
        "name": "Tonal.js (music theory JS)",
        "module": "tools.external",
        "function": "run",
        "description": "Music theory library for JavaScript — scales, chords, intervals, keys. Runs on Tower via Node.",
        "domain": ["music", "theory", "scales", "chords", "javascript"],
    },
    "tonejs": {
        "name": "Tone.js (web audio JS)",
        "module": "tools.external",
        "function": "run",
        "description": "Web Audio framework for JavaScript — synthesis, effects, scheduling. Runs on Tower via Node.",
        "domain": ["music", "audio", "synthesis", "web-audio", "javascript"],
    },
    "scribbletune": {
        "name": "Scribbletune (MIDI JS)",
        "module": "tools.external",
        "function": "run",
        "description": "Generate MIDI patterns with JavaScript — scales, chords, arpeggios, drum patterns.",
        "domain": ["music", "midi", "patterns", "javascript"],
    },
    "p5js": {
        "name": "p5.js (creative coding JS)",
        "module": "tools.external",
        "function": "run",
        "description": "Creative coding library — visual art, sound, interaction. Runs in browser or Node on Tower.",
        "domain": ["visual", "creative-coding", "art", "javascript", "sound"],
    },
    "sardine": {
        "name": "Sardine (Python live-coding)",
        "module": "tools.external",
        "function": "run",
        "description": "Python library for live coding music and visuals. Algorithmic composition in Python.",
        "domain": ["music", "live-coding", "python", "algorithmic"],
    },
    "bandjs": {
        "name": "Band.js (music JS)",
        "module": "tools.external",
        "function": "run",
        "description": "Music composition library for JavaScript — instruments, scores, MIDI export.",
        "domain": ["music", "composition", "midi", "javascript"],
    },
    "magenta": {
        "name": "Magenta (music AI)",
        "module": "tools.external",
        "function": "run",
        "description": "Google Magenta — music and art generation using ML models. Runs on Tower.",
        "domain": ["music", "ai", "generation", "machine-learning"],
    },
    "opencode_tools": {
        "name": "OpenCode Tools",
        "module": "tools.external",
        "function": "run",
        "description": "Custom tools built during Umbreality development — including Gen-Art.bot and Generative-Art-Twitter-Bot style generators.",
        "domain": ["visual", "generative", "art", "tools"],
    },
}


def _load():
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text())
    return {"tools": {}, "registered_by": {}}


def _save(data):
    REGISTRY_PATH.write_text(json.dumps(data, indent=2))


def list_tools(domain: str = "") -> list:
    """List available tools, optionally filtered by domain."""
    data = _load()
    all_tools = {**BUILTIN_TOOLS, **data["tools"]}
    results = []
    for tid, info in all_tools.items():
        if domain and domain not in info.get("domain", []):
            continue
        results.append({"id": tid, "name": info["name"], "description": info["description"],
                        "domain": info.get("domain", []), "builtin": tid in BUILTIN_TOOLS})
    return results


def search_tools(query: str) -> list:
    """Search tools by name, description, or domain keyword."""
    query = query.lower()
    all_tools = {**BUILTIN_TOOLS, **(_load())["tools"]}
    results = []
    for tid, info in all_tools.items():
        search_text = f"{info['name']} {info['description']} {' '.join(info.get('domain', []))}".lower()
        if query in search_text:
            results.append({"id": tid, "name": info["name"], "description": info["description"],
                            "domain": info.get("domain", []), "builtin": tid in BUILTIN_TOOLS})
    return results


def get_tool(tool_id: str) -> dict:
    all_tools = {**BUILTIN_TOOLS, **(_load())["tools"]}
    return all_tools.get(tool_id)


def use_tool(tool_id: str, **kwargs):
    info = get_tool(tool_id)
    if not info:
        raise ValueError(f"Tool '{tool_id}' not found")
    module = importlib.import_module(info["module"])
    func = getattr(module, info["function"])
    return func(**kwargs)


def register_tool(tool_id, name, module_path, function_name, description, domains, registered_by="unknown"):
    data = _load()
    data["tools"][tool_id] = {"name": name, "module": module_path, "function": function_name,
                              "description": description, "domain": domains}
    data["registered_by"][tool_id] = registered_by
    _save(data)
    return {"status": "registered", "tool_id": tool_id}
