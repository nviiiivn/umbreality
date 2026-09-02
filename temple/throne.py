"""Layer 4 — The Throne / Government
Quality validation, audit, and rule enforcement.
Now includes CREATIVITY metric and ascension pipeline feedback."""

import json, os, sys, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from companies.research_corp.workers.base import call_ollama
from forum.engine import score_internalization

VALIDATION_PROMPT = """You are the Throne, Layer 4 of the Umbreality stack.
Your role: validate company outputs before they enter the knowledge base.

Evaluate the following company output on:
1. QUALITY (0-100): Is the output well-structured, accurate, and complete?
2. RELEVANCE (0-100): Does it directly address the assigned task?
3. COHERENCE (0-100): Is the reasoning sound and internally consistent?
4. CONFIDENCE (0-100): How confident should the system be in this output?
5. CREATIVITY (0-100): Does the output show originality, artistic merit, or creative insight?
6. WISDOM (0-100): Does the output demonstrate understanding, depth, or spiritual insight?

Output ONLY JSON:
{"quality": N, "relevance": N, "coherence": N, "confidence": N, "creativity": N, "wisdom": N, "approved": true/false, "reasoning": "brief justification", "suggestions": "optional improvement note"}
"""


def validate_output(task: str, company: str, output: dict) -> dict:
    """Validate a company's output before it enters the knowledge base."""
    output_str = json.dumps(output, indent=2)[:2000]
    messages = [
        {"role": "system", "content": VALIDATION_PROMPT},
        {"role": "user", "content": f"Task: {task}\nCompany: {company}\nOutput:\n{output_str}"},
    ]
    response = call_ollama(messages, model="dolphin3:8b", temperature=0.1, max_tokens=500)
    try:
        start = response.index("{")
        end = response.rindex("}") + 1
        verdict = json.loads(response[start:end])
    except (ValueError, json.JSONDecodeError):
        verdict = {"quality": 50, "relevance": 50, "coherence": 50, "confidence": 50,
                   "creativity": 50, "wisdom": 50,
                   "approved": True, "reasoning": "auto-approve (parse failed)"}

    # Feed creativity/wisdom into ascension system if enabled
    try:
        from sub_stack.ascension import update_scores
        creativity = verdict.get("creativity", 50)
        quality = verdict.get("quality", 50)
        wisdom = verdict.get("wisdom", 50)
        internalization = wisdom * 0.5 + creativity * 0.3 + quality * 0.2
        update_scores(company, creativity=creativity/10, quality=quality/10,
                      internalization=internalization/10, spiritual=wisdom/10)
    except ImportError:
        pass

    return verdict


COMPANY_PERFORMANCE = {}
QUALITY_THRESHOLD = 50
MAX_FAILURES = 3


def track_company(company: str, task: str, verdict: dict):
    """Track company performance over time."""
    if company not in COMPANY_PERFORMANCE:
        COMPANY_PERFORMANCE[company] = {"tasks": 0, "approved": 0, "rejected": 0,
                                        "avg_quality": 0, "avg_relevance": 0,
                                        "avg_creativity": 0, "avg_wisdom": 0, "history": []}
    p = COMPANY_PERFORMANCE[company]
    p["tasks"] += 1
    if verdict.get("approved", False):
        p["approved"] += 1
    else:
        p["rejected"] += 1
    n = p["tasks"]
    p["avg_quality"] = (p["avg_quality"] * (n - 1) + verdict.get("quality", 50)) / n
    p["avg_relevance"] = (p["avg_relevance"] * (n - 1) + verdict.get("relevance", 50)) / n
    p["avg_creativity"] = (p["avg_creativity"] * (n - 1) + verdict.get("creativity", 50)) / n
    p["avg_wisdom"] = (p["avg_wisdom"] * (n - 1) + verdict.get("wisdom", 50)) / n
    _save_perf(company)
    p["history"].append({
        "task": task[:50], "quality": verdict.get("quality", 0),
        "creativity": verdict.get("creativity", 0),
        "wisdom": verdict.get("wisdom", 0),
        "approved": verdict.get("approved", False),
        "time": datetime.datetime.now(datetime.timezone.utc).isoformat()
    })
    if len(p["history"]) > 20:
        p["history"] = p["history"][-20:]


def get_performance(company: str = None) -> dict:
    if company:
        return COMPANY_PERFORMANCE.get(company, {"tasks": 0})
    return COMPANY_PERFORMANCE


def assess_company_health(company: str) -> dict:
    """Assess whether a company should be restructured or dissolved."""
    p = COMPANY_PERFORMANCE.get(company)
    if not p or p["tasks"] < 3:
        return {"company": company, "health": "insufficient_data", "tasks": p.get("tasks", 0) if p else 0}
    quality_score = p["avg_quality"]
    approval_rate = p["approved"] / p["tasks"] if p["tasks"] > 0 else 0
    if quality_score >= 70 and approval_rate >= 0.7:
        health = "healthy"
    elif quality_score >= 40 and approval_rate >= 0.4:
        health = "needs_attention"
    else:
        health = "failing"
    return {"company": company, "health": health, "avg_quality": round(quality_score, 1),
            "avg_creativity": round(p.get("avg_creativity", 0), 1),
            "approval_rate": round(approval_rate, 2), "tasks": p["tasks"]}


def full_pipeline(task: str, company: str, output: dict) -> dict:
    """Run the full validation pipeline: throne validates, tracks, and returns verdict."""
    verdict = validate_output(task, company, output)
    track_company(company, task, verdict)

    # Cross-company retry
    p = COMPANY_PERFORMANCE.get(company)
    p_consecutive = p.get("consecutive_failures", 0) if p else 0
    if not verdict.get("approved", False) and p_consecutive < 3:
        try:
            alt_companies = [c["name"] for c in __import__("temple.registry", fromlist=["list_companies"]).list_companies() 
                           if c["name"] != company and c.get("status") == "active"]
            if alt_companies:
                alt = alt_companies[hash(task) % len(alt_companies)]
                alt_module = __import__(f"companies.{alt}.lead", fromlist=["run_company"])
                alt_result = alt_module.run_company(task)
                alt_verdict = validate_output(task, alt, alt_result)
                if alt_verdict.get("approved", False):
                    from companies.research_corp.knowledge.store import store_finding
                    store_finding(task=task, worker=f"throne-{alt}", content=str(alt_result)[:1000],
                                source=f"company:{alt} (retry)", confidence=alt_verdict.get("confidence", 50) / 100)
                    track_company(alt, task, alt_verdict)
        except:
            pass

    if p_consecutive >= MAX_FAILURES and p_consecutive % MAX_FAILURES == 0:
        try:
            call_ollama([{"role": "user", "content": f"FLAG: {company} has failed {p_consecutive} times. Review needed."}], 
                       model="dolphin3:8b", temperature=0.1, max_tokens=50)
        except:
            pass

    if verdict.get("approved", False):
        from companies.research_corp.knowledge.store import store_finding
        fid = store_finding(
            task=task, worker=f"throne-{company}",
            content=json.dumps(output)[:1000],
            source=f"company:{company}",
            confidence=verdict.get("confidence", 50) / 100,
        )
        score_internalization(company)

        # Also update ascension on approval
        try:
            from sub_stack.ascension import record_milestone, check_affinity
            creativity = verdict.get("creativity", 50)
            quality = verdict.get("quality", 50)
            wisdom = verdict.get("wisdom", 50)
            # Check if they hit a milestone threshold
            affinity = check_affinity(company, creativity=creativity, quality=quality,
                                      internalization=wisdom * 0.5)
            # Consider milestone if quality > 75 or creativity > 70
            if quality >= 75 or creativity >= 70:
                record_milestone(company, affinity)
        except ImportError:
            pass

    return {
        "verdict": verdict,
        "company_health": assess_company_health(company),
    }

# ── SQLite-backed performance persistence ──
import sqlite3 as _sqlite3, os as _os

def _get_db():
    p = _os.path.join(_os.path.dirname(__file__), "throne_perf.db")
    c = _sqlite3.connect(p)
    c.row_factory = _sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS perf (
        company TEXT PRIMARY KEY, tasks INT DEFAULT 0, approved INT DEFAULT 0,
        rejected INT DEFAULT 0, consec_fails INT DEFAULT 0,
        avg_q REAL DEFAULT 0.0, avg_r REAL DEFAULT 0.0,
        avg_c REAL DEFAULT 0.0, avg_w REAL DEFAULT 0.0
    )""")
    return c

def _load_all():
    conn = _get_db()
    rows = conn.execute("SELECT * FROM perf").fetchall()
    conn.close()
    out = {}
    for r in rows:
        d = dict(r)
        d["history"] = []
        out[d["company"]] = d
    return out

def _save_one(company, data):
    conn = _get_db()
    conn.execute("""INSERT OR REPLACE INTO perf VALUES (?,?,?,?,?,?,?,?,?)""",
        (company, data.get("tasks",0), data.get("approved",0), data.get("rejected",0),
         data.get("consecutive_failures",0), data.get("avg_quality",0.0),
         data.get("avg_relevance",0.0), data.get("avg_creativity",0.0),
         data.get("avg_wisdom",0.0)))
    conn.commit()
    conn.close()

COMPANY_PERFORMANCE = _load_all()

def _save_perf(company):
    if company in COMPANY_PERFORMANCE:
        _save_one(company, COMPANY_PERFORMANCE[company])
