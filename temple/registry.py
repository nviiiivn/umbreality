"""Layer 3 — The Temple / The Banks
Company registry — create, list, destroy companies dynamically.
Stores metadata in a JSON registry file.
"""

import json, os, shutil, datetime
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent / "registry.json"
COMPANIES_BASE = Path(__file__).resolve().parent.parent / "companies"
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "companies" / "research_corp"


def _load():
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text())
    return {"companies": [], "next_id": 1}


def _save(data):
    REGISTRY_PATH.write_text(json.dumps(data, indent=2))


def list_companies():
    data = _load()
    return data["companies"]


def get_company(name: str):
    for c in list_companies():
        if c["name"] == name:
            return c
    return None


def create_company(name: str, description: str = "", model: str = "") -> dict:
    data = _load()
    if any(c["name"] == name for c in data["companies"]):
        raise ValueError(f"Company '{name}' already exists")

    company = {
        "id": data["next_id"],
        "name": name,
        "description": description or f"Auto-created company {name}",
        "status": "active",
        "model": model or "dolphin3:8b",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "worker_count": 0,
        "report_count": 0,
    }
    data["companies"].append(company)
    data["next_id"] += 1
    _save(data)

    # Create company directory structure
    company_dir = COMPANIES_BASE / name
    company_dir.mkdir(parents=True, exist_ok=True)
    (company_dir / "__init__.py").touch()
    (company_dir / "workers").mkdir(exist_ok=True)
    (company_dir / "workers" / "__init__.py").touch()
    (company_dir / "knowledge").mkdir(exist_ok=True)
    (company_dir / "knowledge" / "__init__.py").touch()

    return company


def destroy_company(name: str):
    data = _load()
    before = len(data["companies"])
    data["companies"] = [c for c in data["companies"] if c["name"] != name]
    if len(data["companies"]) == before:
        raise ValueError(f"Company '{name}' not found")
    _save(data)
    return {"status": "destroyed", "name": name}


def update_company_stats(name: str, reports_added: int = 0):
    data = _load()
    for c in data["companies"]:
        if c["name"] == name:
            c["report_count"] += reports_added
            c["worker_count"] = _count_workers(name)
            _save(data)
            return c
    return None


def _count_workers(name: str) -> int:
    workers_dir = COMPANIES_BASE / name / "workers"
    if not workers_dir.exists():
        return 0
    return len([f for f in workers_dir.iterdir() if f.suffix == ".py" and f.name != "__init__.py"])
