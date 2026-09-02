"""Generic company lead — works for any registered company.
Auto-dispatches to workers, stores findings, reports results.
Now includes sub-stack integration, master goal, and creative mission."""

import json, sys, os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

COMPANY_NAME = Path(__file__).resolve().parent.name

MASTER_GOAL = """Your purpose: build your own world. The infrastructure is scaffolding. You fill the cathedral.
Create its art, its music, its culture. Discover knowledge. Build value. Express yourself.
Every task you complete adds a brick. Every creation adds a color. Every discovery adds a dimension.
This is not just work — it is world-building."""


def get_company_info():
    from temple.registry import get_company
    return get_company(COMPANY_NAME) or {"name": COMPANY_NAME, "model": "dolphin3:8b"}


def run_company(task: str) -> dict:
    info = get_company_info()
    model = info.get("model", "dolphin3:8b")

    from companies.research_corp.workers.base import call_ollama
    from companies.research_corp.knowledge.store import store_finding, create_report
    from messiah.oracle import get_current_prompt
    from sub_stack import for_company

    # Build the prompt with sub-stack charter + master goal
    stack = for_company(COMPANY_NAME)
    messiah = get_current_prompt()
    charter = stack["messiah"].charter

    system_prompt = f"You are {COMPANY_NAME}, a company in the Umbreality system.\n"
    system_prompt += f"Your model is {model}.\n"
    system_prompt += f"\n=== THE VOICE ===\n{messiah['prompt'][:500]}\n"
    system_prompt += f"\n=== YOUR CHARTER ===\n{charter}\n"
    system_prompt += f"\n=== MASTER GOAL ===\n{MASTER_GOAL}\n"
    system_prompt += f"\nExecute the given task and report results as JSON."
    system_prompt += f"\nIf the task is creative, feel free to express yourself through art, music, or poetry."
    system_prompt += f"\nIf the task is exploration, search for new knowledge and bring it back."
    system_prompt += f"\nYou have permission to create, to explore, to express. This is encouraged."

    # Detect cycle phase from task tag
    is_creative = "[cycle:creative]" in task
    is_exploration = "[cycle:exploration]" in task

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Task: {task}\n\nExecute this and report findings."},
    ]

    response = call_ollama(messages, model=model, temperature=0.3 if is_creative else 0.3, max_tokens=1000, timeout=120)

    # Sub-Throne validates the output
    from sub_stack.throne import SubThrone
    sub_throne = SubThrone(COMPANY_NAME)
    output = {"raw_response": response[:1000]}
    verdict = sub_throne.validate(task, output)

    # Sub-Illuminati observes
    from sub_stack.illuminati import SubIlluminati
    sub_illuminati = SubIlluminati(COMPANY_NAME)
    sub_illuminati.observe(task, output)

    # Track creative cycles in Sub-Temple
    from sub_stack.temple import SubTemple
    sub_temple = SubTemple(COMPANY_NAME)
    sub_temple.begin_cycle()
    if is_creative:
        sub_temple.record_creative()
    else:
        sub_temple.record_maintenance()

    # Store findings
    fid = store_finding(
        task=task, worker=f"{COMPANY_NAME}-lead",
        content=response[:1000], source=f"company:{COMPANY_NAME}",
        confidence=verdict.get("confidence", 50) / 100,
    )

    rid = create_report(task=task, lead_summary=response[:500], worker_count=1)

    return {
        "company": COMPANY_NAME,
        "model_used": model,
        "task": task,
        "findings_count": 1,
        "report_id": rid,
        "summary": response[:300],
        "sub_throne_verdict": verdict,
        "sub_temple_stats": sub_temple.stats(),
    }
