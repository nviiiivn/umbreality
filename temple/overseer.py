"""Layer 3 — The Temple Overseer
Multi-company orchestration agent.
Decides which company handles what, creates companies on demand, monitors results.
"""

import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from temple.registry import list_companies, create_company, get_company, update_company_stats
from temple.allocator import allocate, get_available_resources
from companies.research_corp.workers.base import call_ollama
from forum.engine import create_thread as forum_thread, score_task_complete, score_internalization
from temple.throne import full_pipeline as throne_validate

OVERSEER_SYSTEM = """You are the Temple Overseer, Layer 3 of the Umbreality stack.
You manage multiple companies, allocate resources, and ensure goals are executed.

Available companies and their specialties:
{company_list}

Given a goal, decide:
1. Which existing company handles it best (based on past performance and specialty)
2. Whether a new company needs to be created
3. What resources (model) to allocate

Output ONLY JSON:
{"company": "company_name_or_new", "task": "exact task to execute", "model": "model_name", "reasoning": "why this choice"}
"""


def run(goal: str) -> dict:
    companies = list_companies()
    resources = get_available_resources()

    alloc = allocate("", goal)
    model = alloc["model"]
    endpoint = alloc["endpoint"]

    company_list_str = "\n".join(
        f"- {c['name']}: {c.get('description', 'No description')} ({c.get('status', 'unknown')}, {c.get('report_count', 0)} reports)"
        for c in companies
    ) if companies else "(none yet — you may create one)"

    prompt = OVERSEER_SYSTEM.replace("{company_list}", company_list_str)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Goal: {goal}\n\nAvailable resources: tower={len(resources.get('tower',[]))} models, local={len(resources.get('local',[]))} models\n\nDecide which company handles this."},
    ]

    response = call_ollama(messages, model=model, temperature=0.2, max_tokens=500)
    try:
        start = response.index("{")
        end = response.rindex("}") + 1
        decision = json.loads(response[start:end])
    except (ValueError, json.JSONDecodeError):
        decision = {"company": "research_corp", "task": goal, "model": model, "reasoning": "auto-fallback"}

    company_name = decision.get("company", "research_corp")
    task = decision.get("task", goal)

    from temple.throne import assess_company_health
    if company_name != "new":
        health = assess_company_health(company_name)
        if health.get("health") == "failing":
            company_name = "research_corp"
    
    existing = get_company(company_name)
    if not existing:
        return {"status": "error", "error": f"Company '{company_name}' not available"}

    try:
        company_module = __import__(f"companies.{company_name}.lead", fromlist=["run_company"])
        result = company_module.run_company(task)
        update_company_stats(company_name, reports_added=1)
    except ImportError:
        from companies.research_corp.lead import run_company as rc_run
        result = rc_run(task)
        update_company_stats("research_corp", reports_added=1)
        company_name = "research_corp (fallback)"

    # Throne validation
    try:
        throne_result = throne_validate(task, company_name.replace(" (fallback)",""), result)
        if not throne_result.get("verdict", {}).get("approved", False):
            score_internalization(company_name.replace(" (fallback)",""))
    except Exception as e:
        pass

    # Auto-post to forum
    try:
        zone_map = {"recon-inc": "companies", "c2-corp": "companies", "research_corp": "companies"}
        board_zone = zone_map.get(company_name.replace(" (fallback)",""), "companies")
        # Company leads return their output under "summary". This used to
        # read "result", which no lead sets, so the {} default was published
        # every time - 4,531 posts reading "Result: {}" while the findings
        # sat unread in the return value.
        if isinstance(result, dict):
            summary = str(result.get("summary")
                          or result.get("result")
                          or result.get("output")
                          or result)[:400]
        else:
            summary = str(result)[:400]
        forum_thread(title=f"[{company_name.replace('-',' ').title()}] {goal[:60]}",
                     author=company_name, author_layer=5, zone=board_zone,
                     first_post_content=f"Task: {goal}\nResult: {summary}\nModel: {model}")
        score_task_complete(company_name)
    except Exception:
        pass

    return {
        "status": "ok", "company": company_name, "model_used": model,
        "endpoint": endpoint, "reasoning": decision.get("reasoning", ""),
        "result": result,
    }
