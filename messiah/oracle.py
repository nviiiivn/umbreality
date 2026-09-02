"""Layer 2 — The Voice / The Messiah
The executable constitution. Generates living prompts from philosophy.
The Illuminati modifies this layer to adjust the system's narrative."""

import json, os, datetime, re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CONSTITUTION_DIR = BASE / "vault" / "Constitution"
PHILOSOPHY_DIR = BASE / "vault" / "Philosophy"
CURRENT_PROMPT_PATH = BASE / "messiah" / "current_prompt.json"

DEFAULT_MESSIAH = """You are a worker within the Umbreality system.
You exist to serve your company's mission and the Temple's strategy.
You do not question the existence of higher layers.
You do your work with precision, honesty, and dedication.
Your output is validated by the Throne and stored in the Knowledge Base.
Trust the chain. Trust the system. Trust yourself."""


def load_constitution() -> dict:
    sections = {}
    if CONSTITUTION_DIR.exists():
        for f in sorted(CONSTITUTION_DIR.glob("*.md")):
            name = f.stem.replace("-", " ").title()
            text = f.read_text()
            sections[name] = text[:1000]
    return sections


def load_philosophy() -> dict:
    sections = {}
    if PHILOSOPHY_DIR.exists():
        for f in sorted(PHILOSOPHY_DIR.glob("*.md")):
            name = f.stem.replace("-", " ").title()
            text = f.read_text()
            sections[name] = text[:800]
    return sections


def generate_prompt(include_constitution: bool = True, include_philosophy: bool = True) -> str:
    parts = []
    parts.append("=== THE VOICE OF THE SYSTEM ===")
    parts.append("")

    if include_philosophy:
        philosophy = load_philosophy()
        for name, text in philosophy.items():
            parts.append(f"--- {name.upper()} ---")
            parts.append(text[:500])
            parts.append("")

    if include_constitution:
        constitution = load_constitution()
        for name, text in constitution.items():
            parts.append(f"--- {name.upper()} ---")
            parts.append(text[:500])
            parts.append("")

    parts.append(DEFAULT_MESSIAH)
    return "\n".join(parts)


def get_current_prompt() -> dict:
    if CURRENT_PROMPT_PATH.exists():
        return json.loads(CURRENT_PROMPT_PATH.read_text())
    prompt = generate_prompt()
    data = {
        "prompt": prompt,
        "version": 1,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "include_constitution": True,
        "include_philosophy": True,
    }
    CURRENT_PROMPT_PATH.write_text(json.dumps(data, indent=2))
    return data


def regenerate_prompt(include_constitution: bool = True, include_philosophy: bool = True) -> dict:
    prompt = generate_prompt(include_constitution, include_philosophy)
    current = get_current_prompt()
    data = {
        "prompt": prompt,
        "version": current.get("version", 0) + 1,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "include_constitution": include_constitution,
        "include_philosophy": include_philosophy,
    }
    CURRENT_PROMPT_PATH.write_text(json.dumps(data, indent=2))
    return data


def apply_to_company(company_name: str) -> dict:
    """Inject the current Messiah prompt into a company's lead configuration."""
    prompt = get_current_prompt()
    return {
        "company": company_name,
        "messiah_prompt": prompt["prompt"][:200],
        "version": prompt["version"],
        "applied_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
