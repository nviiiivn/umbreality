"""Generic company lead — works for any registered company.
Auto-dispatches to workers, stores findings, reports results."""

import json, sys, os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE))

COMPANY_NAME = Path(__file__).resolve().parent.name


def get_company_info():
    from temple.registry import get_company
    return get_company(COMPANY_NAME) or {"name": COMPANY_NAME, "model": "dolphin3:8b"}


def run_company(task: str) -> dict:
    info = get_company_info()
    model = info.get("model", "dolphin3:8b")

    from companies.research_corp.workers.base import call_ollama
    from companies.research_corp.knowledge.store import store_finding, create_report

    messages = [
        {"role": "system", "content": f"You are {COMPANY_NAME}, a company in the Umbreality system. "
         f"Your model is {model}. Execute the given task and report results as JSON."},
        {"role": "user", "content": f"Task: {task}\n\nExecute this and report findings."},
    ]

    response = call_ollama(messages, model=model, temperature=0.3, max_tokens=1000, timeout=120)

    # Store findings
    fid = store_finding(
        task=task, worker=f"{COMPANY_NAME}-lead",
        content=response[:1000], source=f"company:{COMPANY_NAME}", confidence=0.7,
    )

    rid = create_report(task=task, lead_summary=response[:500], worker_count=1)

    return {
        "company": COMPANY_NAME,
        "model_used": model,
        "task": task,
        "findings_count": 1,
        "report_id": rid,
        "summary": response[:300],
    }
