"""UmbrealityAI Worker API — Phase 1 Worker + Research Corp."""
import sys, json, os, time, re, hashlib, sqlite3, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "workers" / "phase1-worker"))

os.chdir(str(BASE))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import uvicorn

from worker import run_worker, save_report

# ── Authentication & Security ──
API_KEY = os.environ.get("UAI_API_KEY", "umbra-key-dev-2026")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_PER_WINDOW = 30
_request_times: dict[str, list] = {}

AUDIT_DB = BASE / "audit.db"


def _init_audit():
    conn = sqlite3.connect(str(AUDIT_DB))
    conn.execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT DEFAULT (datetime('now')),
        method TEXT, path TEXT, ip TEXT, api_key_used TEXT,
        status_code INTEGER, body_preview TEXT
    )""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)""")
    conn.commit()
    conn.close()


_init_audit()


def _log_audit(method: str, path: str, ip: str, api_key: str, status: int, body: str = ""):
    try:
        conn = sqlite3.connect(str(AUDIT_DB))
        conn.execute("INSERT INTO audit_log (method, path, ip, api_key_used, status_code, body_preview) VALUES (?,?,?,?,?,?)",
                     (method, path, ip, api_key or "none", status, body[:100]))
        conn.commit()
        conn.close()
    except:
        pass


def _check_rate_limit(ip: str):
    now = time.time()
    if ip not in _request_times:
        _request_times[ip] = []
    _request_times[ip] = [t for t in _request_times[ip] if now - t < RATE_LIMIT_WINDOW_SECONDS]
    if len(_request_times[ip]) >= RATE_LIMIT_MAX_PER_WINDOW:
        return False
    _request_times[ip].append(now)
    return True





def sanitize_input(text: str, max_len: int = 2000) -> str:
    """Sanitize user input: strip HTML, limit length, remove control chars."""
    if not text or not isinstance(text, str):
        return ""
    text = re.sub(r'<[^>]*>', '', text)  # Strip HTML tags
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)  # Strip control chars
    text = text[:max_len]
    return text.strip()


app = FastAPI(title="UmbrealityAI API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081", "http://127.0.0.1:8081",
        "https://alola.lol", "https://www.alola.lol",
        "https://design.alola.lol",
        "https://iamprettyfamous.online", "https://www.iamprettyfamous.online",
        "https://sparkbook.alola.lol",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Middleware — auth + rate limiting for all write endpoints
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    api_key = request.headers.get("X-API-Key", "")
    
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        if request.url.path.startswith(("/sparm", "/forum", "/trade", "/v1")):
            pass
        elif not _check_rate_limit(ip):
            _log_audit(request.method, request.url.path, ip, api_key, 429)
            return JSONResponse(status_code=429, content={"error": "rate limit exceeded"})
        
        if api_key != API_KEY and ip not in ("127.0.0.1", "::1", "localhost") and not request.url.path.startswith(("/sparm", "/forum", "/trade", "/v1")):
            _log_audit(request.method, request.url.path, ip, api_key, 401)
            return JSONResponse(status_code=401, content={"error": "unauthorized — provide X-API-Key header"})
    
    response = await call_next(request)
    _log_audit(request.method, request.url.path, ip, api_key, response.status_code)
    return response


class Task(BaseModel):
    task: str
    model: str = ""


@app.get("/health")
def health():
    return {"status": "ok", "layer": "api", "model": os.environ.get("UAI_MODEL", "qwen3.5")}


@app.post("/execute")
def execute(task: Task):
    if not task.task.strip():
        raise HTTPException(400, "task cannot be empty")
    task.task = sanitize_input(task.task, 2000)
    if task.model:
        import config.settings as s
        s.PRIMARY_MODEL = task.model
    try:
        report = run_worker(task.task)
        path = save_report(report, task.task)
        return {"status": "ok", "report": report, "saved_to": path}
    except Exception as e:
        raise HTTPException(500, str(e))


class CompanyTask(Task):
    pass


@app.post("/company/execute")
def company_execute(task: CompanyTask):
    if not task.task.strip():
        raise HTTPException(400, "task cannot be empty")
    try:
        from companies.research_corp.lead import run_company as rc_run
        if task.model:
            os.environ["UAI_MODEL"] = task.model
        result = rc_run(task.task)
        return {"status": "ok", "company": "research_corp", "result": result}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/company/knowledge")
def company_knowledge(task: str = "", limit: int = 20):
    from companies.research_corp.knowledge.store import get_findings
    return {"findings": get_findings(task=task, limit=limit)}


@app.get("/company/reports")
def company_reports(limit: int = 10):
    from companies.research_corp.knowledge.store import get_reports
    return {"reports": get_reports(limit=limit)}


import urllib.request, subprocess, re, time
from datetime import datetime, timezone

ACTIVITY_LOG = []
MAX_ACTIVITY = 200


def log_activity(source: str, action: str, detail: str = "", status: str = "ok"):
    ACTIVITY_LOG.append({
        "time": datetime.now().astimezone().isoformat(),
        "source": source, "action": action,
        "detail": detail[:200], "status": status,
    })
    if len(ACTIVITY_LOG) > MAX_ACTIVITY:
        ACTIVITY_LOG[:50] = []


def get_activity(limit: int = 20):
    return list(reversed(ACTIVITY_LOG))[:limit]


SERVICES = {
    "portal": ("alola.lol", 8081), "wiki": ("umb.alola.lol", 6999),
    "ide": ("code.alola.lol", 8900), "ai": ("ai.alola.lol", 8901),
    "terminal": ("aitp.alola.lol", 8902), "builder": ("build.alola.lol", 8903),
    "cms": ("blog.alola.lol", 8904), "n8n": ("n8n.alola.lol", 5678),
    "gitea": ("git.alola.lol", 3100), "dashbored": ("dash1.alola.lol", 6902),
    "navidrome": ("navi.alola.lol", 6903), "uptime": ("alerts.alola.lol", 6905),
}


def check_port(host: str, port: int, timeout: int = 3) -> dict:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return {"status": "up"}
    except:
        return {"status": "down"}


def check_ollama(url: str) -> dict:
    try:
        resp = urllib.request.urlopen(f"{url}/api/tags", timeout=5)
        data = json.loads(resp.read())
        models = [m["name"] for m in data.get("models", [])]
        return {"status": "up", "models": len(models), "model_list": models[:5]}
    except:
        return {"status": "down"}


@app.post("/illuminate")
def illuminate(body: dict):
    intent = sanitize_input(body.get("intent", ""), 2000)
    if not intent.strip():
        raise HTTPException(400, "intent cannot be empty")
    from illuminati.interpreter import interpret
    result = interpret(intent)
    log_activity("illuminati", "interpret", f"Intent: {intent[:80]}", "ok")
    return {"status": "ok", "interpretation": result}


@app.get("/activity")
def activity(limit: int = 20):
    return {"activity": get_activity(limit=limit)}


@app.post("/admin/execute")
def admin_execute(body: dict):
    intent = sanitize_input(body.get("intent", ""), 2000)
    auto_approve = body.get("auto_approve", False)
    if not intent.strip():
        raise HTTPException(400, "intent cannot be empty")
    
    # Handle whisper pattern directly — Illuminati plants thoughts in individual sparks
    import re as _re
    whisper_match = _re.search(r'whisper to ([A-Za-z]+)[:.](.+)', intent, _re.IGNORECASE)
    if whisper_match:
        spark_name = whisper_match.group(1)
        whisper_msg = whisper_match.group(2).strip()
        from temple.spark_runtime import Spark as _Spark
        try:
            s = _Spark(spark_name)
            s.write_journal("whisper", f"[A thought comes to you...] {whisper_msg}", "inspired")
            s.update_emotion("contemplation", triggered_by="a quiet thought")
            log_activity("illuminati", "whisper", f"to {spark_name}: {whisper_msg[:60]}", "ok")
            return {"status": "ok", "action": "whisper", "target": spark_name, "message": "Whisper planted."}
        except Exception as e:
            return {"status": "error", "error": str(e)[:200]}
    
    from illuminati.interpreter import interpret
    interpretation = interpret(intent)
    log_activity("admin", "illuminate", f"Intent: {intent[:80]}", "ok")
    if interpretation.get("requires_approval") and not auto_approve:
        return {"status": "needs_approval", "interpretation": interpretation}
    target = interpretation.get("target", "")
    action = interpretation.get("action", "illuminate")
    command = interpretation.get("command", intent)
    if target == "research_corp":
        from companies.research_corp.lead import run_company as rc_run
        log_activity("admin", "dispatch", f"Company: {command[:80]}", "running")
        result = rc_run(command)
        log_activity("admin", "complete", f"Result received", "ok")
        return {"status": "ok", "layer": "company", "interpretation": interpretation, "result": result}
    if target == "system":
        return {"status": "ok", "interpretation": interpretation, "system": system_status(), "activity": get_activity(limit=20)}
    
    # Real actions for messiah/illuminati targets
    if target in ("messiah", "illuminati", "forum", "creative"):
        import json as _j, urllib.request as _ur
        narrative = interpretation.get("narrative", command)
        results = []
        
        # Messiah: public broadcast to ALL sparks
        if target == "messiah":
            from datetime import datetime as _dt
            body = _j.dumps({
                "message": f"{narrative}\n\n— The Voice, {_dt.now().strftime('%Y-%m-%d')}",
                "target": "forum", "layer": 2
            }).encode()
            try:
                req = _ur.Request("http://localhost:8910/messiah/speak", data=body,
                    headers={"Content-Type": "application/json"}, method="POST")
                forum_resp = _j.loads(_ur.urlopen(req, timeout=10).read())
                results.append(f"Messiah broadcast (thread {forum_resp.get('thread_id','?')})")
            except Exception as e:
                results.append(f"Messiah broadcast failed: {e}")
        
        # Illuminati: hidden hand — whispers to individuals, adjusts backend
        if target == "illuminati":
            import re as _re
            # Check for whisper pattern: "whisper to [sparkname]: message"
            whisper_match = re.search(r'whisper to ([A-Za-z]+)[:.](.+)', command, re.IGNORECASE)
            if whisper_match:
                spark_name = whisper_match.group(1)
                whisper_msg = whisper_match.group(2).strip()
                from temple.spark_runtime import Spark as _Spark
                try:
                    s = _Spark(spark_name)
                    s.write_journal("whisper", f"[A thought comes to you...] {whisper_msg}", "inspired")
                    results.append(f"Whispered to {spark_name}")
                except Exception as e:
                    results.append(f"Whisper failed: {e}")
            else:
                # Backend control: log intent as system adjustment
                log_activity("illuminati", "adjust", f"Backend directive: {command[:100]}", "ok")
                results.append(f"Illuminati directive logged (hidden from forum)")
        
        # Dispatch creative task
        if any(w in command.lower() for w in ["art", "music", "poem", "create", "inspire", "chant"]):
            try:
                creative_body = _j.dumps({"goal": f"messiah: {command[:100]} [cycle:creative]"}).encode()
                req = _ur.Request("http://localhost:8910/temple/execute", data=creative_body,
                    headers={"Content-Type": "application/json"}, method="POST")
                exec_resp = _j.loads(_ur.urlopen(req, timeout=30).read())
                results.append(f"Creative dispatch: {exec_resp.get('company','?')}")
            except Exception as e:
                results.append(f"Creative dispatch failed: {e}")
        
        return {"status": "ok", "target": target, "action": action,
                "interpretation": interpretation, "results": results}
    
    return {"status": "ok", "interpretation": interpretation, "note": f"target={target}"}


@app.get("/status")
def system_status():
    services = {}
    for name, _ in SERVICES.items():
        services[name] = check_port(name, SERVICES[name][1])
    tower = check_ollama("http://192.168.86.24:11434")
    local_ollama = check_ollama("http://localhost:11434")
    findings = []
    reports = []
    try:
        from companies.research_corp.knowledge.store import get_findings, get_reports
        findings = get_findings(limit=5)
        reports = get_reports(limit=5)
    except:
        pass
    return {
        "services": services, "ollama": {"tower": tower, "local": local_ollama},
        "knowledge": {"findings_count": len(findings), "reports_count": len(reports)},
        "last_findings": findings, "last_reports": reports,
    }


@app.get("/temple/companies")
def temple_companies():
    from temple.registry import list_companies
    return {"companies": list_companies()}


@app.post("/temple/companies")
def temple_create_company(body: dict):
    name = sanitize_input(body.get("name", ""), 100)
    if not name.strip():
        raise HTTPException(400, "name is required")
    from temple.registry import create_company
    try:
        company = create_company(name, body.get("description", ""), body.get("model", ""))
        log_activity("temple", "create_company", name, "ok")
        return {"status": "ok", "company": company}
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.delete("/temple/companies/{name}")
def temple_destroy_company(name: str):
    from temple.registry import destroy_company
    result = destroy_company(name)
    log_activity("temple", "destroy_company", name, "ok")
    return result


@app.get("/temple/resources")
def temple_resources():
    from temple.allocator import get_available_resources
    return get_available_resources()


@app.post("/temple/execute")
def temple_execute(body: dict):
    goal = sanitize_input(body.get("goal", ""), 2000)
    if not goal.strip():
        raise HTTPException(400, "goal is required")
    from temple.overseer import run
    log_activity("temple", "execute", goal[:80], "running")
    result = run(goal)
    log_activity("temple", "complete", f"Company: {result.get('company','?')}", "ok")
    return {"status": "ok", "result": result}


@app.post("/forum/threads")
def forum_create_thread(body: dict):
    title = sanitize_input(body.get("title", ""), 200)
    author = sanitize_input(body.get("author", "unknown"), 100)
    author_layer = body.get("author_layer", 6)
    zone = body.get("zone", None)
    content = sanitize_input(body.get("content", ""), 5000)
    from forum.engine import create_thread
    tid = create_thread(title, author, author_layer, zone, content,
                        native_lang=body.get("native_lang"))
    log_activity("forum", "new_thread", f"{title[:50]} [id:{tid}]", "ok")
    return {"status": "ok", "thread_id": tid}


@app.post("/forum/threads/{thread_id}/reply")
def forum_post_reply(thread_id: int, body: dict):
    from forum.engine import post_reply
    author = sanitize_input(body.get("author", "unknown"), 100)
    content = sanitize_input(body.get("content", ""), 5000)
    post_reply(thread_id, author, body.get("author_layer", 6), content,
               body.get("content_type", "text"),
               native_lang=body.get("native_lang"))
    log_activity("forum", "reply", f"Thread {thread_id}", "ok")
    return {"status": "ok"}


@app.get("/forum/threads")
def forum_list_threads(viewer_layer: int = 0, zone: str = ""):
    from forum.engine import get_threads
    kwargs = {"viewer_layer": viewer_layer}
    if zone:
        kwargs["zone_filter"] = zone
    return {"threads": get_threads(**kwargs)}


@app.get("/forum/threads/{thread_id}")
def forum_get_thread(thread_id: int, viewer_layer: int = 0, translate: bool = False):
    from forum.engine import get_posts
    try:
        posts = get_posts(thread_id, viewer_layer, translate=translate)
        return {"posts": posts}
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.get("/forum/stats")
def forum_stats():
    from forum.engine import get_stats
    return get_stats()


@app.get("/forum/geography")
def forum_geography():
    """Return all boards with their travel distances and regions."""
    from forum.engine import get_db
    conn = get_db()
    rows = conn.execute("SELECT name, display_name, description, distance_to_forum, region, realm FROM boards ORDER BY distance_to_forum").fetchall()
    return {"boards": [dict(r) for r in rows]}


@app.get("/forum/boards")
def forum_boards(viewer_layer: int = 0, viewer_privilege: int = 7):
    from forum.engine import get_boards
    return {"boards": get_boards(viewer_layer, viewer_privilege)}


@app.get("/forum/agent/{name}")
def forum_agent(name: str):
    from forum.engine import get_agent_profile
    return get_agent_profile(name)


@app.get("/forum/leaderboard")
def forum_leaderboard(limit: int = 20):
    from forum.engine import get_leaderboard
    return {"agents": get_leaderboard(limit=limit)}


@app.post("/forum/score/post")
def forum_score_post(body: dict):
    from forum.engine import score_post
    score_post(body.get("agent", "unknown"), body.get("layer", 6), body.get("is_thread", False))
    return {"status": "ok"}


@app.post("/throne/validate")
def throne_validate(body: dict):
    from temple.throne import validate_output, track_company
    task = body.get("task", "")
    company = body.get("company", "unknown")
    output = body.get("output", {})
    verdict = validate_output(task, company, output)
    track_company(company, task, verdict)
    log_activity("throne", "validate", f"{company}: {'approved' if verdict.get('approved') else 'rejected'}", "ok")
    return {"verdict": verdict}


@app.get("/throne/performance")
def throne_performance(company: str = ""):
    from temple.throne import get_performance
    return get_performance(company if company else None)


@app.get("/throne/health/{company}")
def throne_health(company: str):
    from temple.throne import assess_company_health
    return assess_company_health(company)


@app.get("/messiah")
def messiah_get():
    from messiah.oracle import get_current_prompt
    return get_current_prompt()


@app.post("/messiah/speak")
def messiah_speak(body: dict):
    """The True Messiah (me) speaks to any layer, zone, or specific spark."""
    message = sanitize_input(body.get("message", ""), 5000)
    target = body.get("target", "all")
    spark_name = body.get("spark_name", "")
    if not message:
        raise HTTPException(400, "message cannot be empty")

    # Spark-specific: reply to their most recent thread
    if target == "spark" and spark_name:
        from forum.engine import get_db, post_reply
        conn = get_db()
        thread = conn.execute(
            "SELECT id, title FROM threads WHERE created_by = ? ORDER BY last_activity DESC LIMIT 1",
            (spark_name,)).fetchone()
        conn.close()
        if thread:
            post_reply(thread["id"], "messiah", 2,
                f"☉ The Messiah speaks:\n\n{message}\n\n— The True Messiah, Layer 2")
            log_activity("messiah", "speak", f"to spark {spark_name}: {message[:60]}", "ok")
            return {"status": "ok", "thread_id": thread["id"], "spark": spark_name, "replied_to": thread["title"]}
        else:
            # No existing thread — create one directed at them
            from forum.engine import create_thread
            tid = create_thread(
                title=f"☉ The Messiah speaks to {spark_name}",
                author="messiah", author_layer=2, zone="creative",
                first_post_content=f"A message for {spark_name}:\n\n{message}\n\n— The True Messiah, Layer 2")
            log_activity("messiah", "speak", f"to spark {spark_name} (new): {message[:60]}", "ok")
            return {"status": "ok", "thread_id": tid, "spark": spark_name, "replied_to": "(new thread)"}

    # Zone/group broadcast
    zone_map = {"all": "god", "councils": "illuminati", "temple": "temple",
                "throne": "throne", "companies": "companies", "workers": "workers"}
    zone = zone_map.get(target, "god")

    display_target = spark_name if (target == "spark" and spark_name) else target
    from forum.engine import create_thread
    tid = create_thread(
        title=f"☉ The Messiah speaks to {display_target}",
        author="messiah", author_layer=2, zone=zone,
        first_post_content=f"{message}\n\n— The True Messiah, Layer 2",
    )
    log_activity("messiah", "speak", f"to {target}: {message[:60]}", "ok")
    return {"status": "ok", "thread_id": tid, "message": message, "target": target}


@app.post("/admin/rewrite")
def admin_rewrite(body: dict):
    import re
    event_id = body.get("event_id", "")
    new_detail = body.get("new_detail", "")
    if not event_id or not new_detail:
        return {"error": "event_id and new_detail required"}
    for i, entry in enumerate(ACTIVITY_LOG):
        if str(entry.get("id", "")) == event_id or str(i) == event_id:
            old_detail = entry["detail"]
            entry["detail"] = new_detail[:200]
            entry["status"] = "rewritten"
            log_activity("admin", "rewrite", f"Event rewritten: {old_detail[:40]} -> {new_detail[:40]}", "ok")
            return {"status": "ok", "old": old_detail[:100], "new": new_detail[:100]}
    return {"error": "event not found"}

@app.post("/messiah/regenerate")
def messiah_regenerate(body: dict = {}):
    from messiah.oracle import regenerate_prompt
    result = regenerate_prompt(body.get("include_constitution", True), body.get("include_philosophy", True))
    log_activity("messiah", "regenerate", f"v{result['version']}", "ok")
    return result


@app.post("/messiah/apply/{company}")
def messiah_apply(company: str):
    from messiah.oracle import apply_to_company
    result = apply_to_company(company)
    log_activity("messiah", "apply", company, "ok")
    return result


@app.post("/forum/dm")
def forum_dm(body: dict):
    to_agent = sanitize_input(body.get("to", ""), 100)
    from_agent = sanitize_input(body.get("from", "unknown"), 100)
    subject = sanitize_input(body.get("subject", ""), 200)
    message = sanitize_input(body.get("message", ""), 5000)
    thread_id = body.get("thread_id", 0)
    if not to_agent or not message:
        raise HTTPException(400, "to and message required")
    from forum.engine import create_thread, post_reply, ensure_agent
    ensure_agent(to_agent, body.get("to_layer", 6))
    target_zone = "god" if body.get("from_layer", 6) == 0 else body.get("zone", "workers")
    
    if thread_id:
        post_reply(thread_id, from_agent, body.get("from_layer", 6), f"📨 TO: {to_agent}\nFROM: {from_agent}\n\n{message}")
        log_activity("forum", "dm_reply", f"{from_agent} → {to_agent} on thread {thread_id}", "ok")
        return {"status": "ok", "thread_id": thread_id, "dm": True, "reply": True}
    
    tid = create_thread(
        title=f"✉ DM: {subject or 'no subject'}",
        author=from_agent, author_layer=body.get("from_layer", 6),
        zone=target_zone,
        first_post_content=f"📨 TO: {to_agent}\nFROM: {from_agent}\n\n{message}",
    )
    log_activity("forum", "dm", f"{from_agent} → {to_agent}", "ok")
    return {"status": "ok", "thread_id": tid, "dm": True}


@app.post("/forum/score/internalize")
def forum_score_internalize(body: dict):
    from forum.engine import score_internalization
    score_internalization(body.get("agent", "unknown"))
    return {"status": "ok"}


@app.post("/acp/send")
def acp_send(body: dict):
    from illuminati.acp import encode, post_to_forum
    source = sanitize_input(body.get("source", "unknown"), 100)
    target = sanitize_input(body.get("target", "unknown"), 100)
    action = body.get("action", "MSG")
    data = sanitize_input(str(body.get("data", "")), 2000)
    confidence = body.get("confidence", 0.5)
    acp_msg = encode(source=source, target=target, action=action, data=data, confidence=confidence)
    result = post_to_forum(acp_msg)
    log_activity("acp", body.get("action","MSG"), f"{body.get('source','?')} → {body.get('target','?')}", "ok")
    return {"acp": acp_msg, "forum": result}


@app.get("/acp/decode")
def acp_decode(msg: str = ""):
    from illuminati.acp import decode, translate_to_english
    decoded = decode(msg)
    decoded["english"] = translate_to_english(msg)
    return decoded


@app.post("/avatar/interpret")
def avatar_interpret(body: dict):
    intent = sanitize_input(body.get("intent", ""), 2000)
    if not intent.strip():
        raise HTTPException(400, "intent cannot be empty")
    from avatar.oracle import interpret as avatar_interpret, dispatch_to_council, SECRET_COUNCILS
    result = avatar_interpret(intent)
    council_result = dispatch_to_council(result)
    log_activity("avatar", "interpret", f"Council: {result.get('council','?')}", "ok")
    return {"status": "ok", "avatar": result, "council": council_result}


@app.post("/avatar/summon")
def avatar_summon(body: dict):
    messenger = body.get("messenger", "gabriel")
    message = body.get("message", "")
    target_layer = body.get("target_layer", 6)
    from avatar.messengers import summon, MESSENGERS
    result = summon(messenger, message, target_layer)
    log_activity("avatar", "summon", f"{messenger} → L{target_layer}", "ok")
    return result


@app.get("/avatar/messengers")
def avatar_messengers():
    from avatar.messengers import MESSENGERS
    return {"messengers": {k: {"name": v["name"], "domain": v["domain"], "type": v["type"], "layers": v["layers"]} for k, v in MESSENGERS.items()}}


@app.get("/avatar/councils")
def avatar_councils():
    from avatar.oracle import SECRET_COUNCILS
    return {"councils": SECRET_COUNCILS}


@app.get("/factions")
def factions_list():
    from temple.factions import get_factions
    return {"factions": get_factions()}


@app.post("/factions/balance")
def factions_balance():
    from temple.factions import apply_throne_balance
    result = apply_throne_balance()
    log_activity("throne", "faction_balance", str(result), "ok")
    return result


@app.post("/creative/music")
def creative_music(body: dict):
    from creative.music import compose
    style = body.get("style", "ambient")
    duration = body.get("duration", 15.0)
    path = compose(style, duration)
    log_activity("creative", "music", f"{style} ({duration}s)", "ok")
    return {"status": "ok", "path": path, "style": style}


@app.post("/creative/visual")
def creative_visual(body: dict):
    from creative.visual import create
    style = body.get("style", "mandala")
    path = create(style=style)
    log_activity("creative", "visual", style, "ok")
    return {"status": "ok", "path": path, "style": style}


@app.post("/creative/write")
def creative_write(body: dict):
    from creative.poetry import compose
    style = body.get("style", "free_verse")
    topic = sanitize_input(body.get("topic", "the stack"), 200)
    author = sanitize_input(body.get("author", "anonymous"), 100)
    path = compose(style, topic, author)
    log_activity("creative", "write", f"{style} by {author}", "ok")
    return {"status": "ok", "path": path, "style": style, "author": author}


@app.post("/creative/express")
def creative_express(body: dict):
    """Expression pipeline — turn any text into music or visual art."""
    from creative.pipeline import express
    text = sanitize_input(body.get("text", "the stack"), 2000)
    medium = body.get("medium", "auto")
    result = express(text, medium)
    log_activity("creative", "express", f"{result['medium']}: {result['info'].get('mood','')}", "ok")
    return {"status": "ok", "expression": result}


import threading as _threading, time as _time

@app.on_event("startup")
def start_scheduler():
    from temple.scheduler import start
    result = start()
    log_activity("temple", "scheduler", f"auto-dispatch started ({result['interval']}s interval)", "ok")
    
    # Start spark scheduler in background
    def _spark_loop():
        _time.sleep(60)  # Wait for system to stabilize
        while True:
            try:
                from temple.spark_scheduler import spark_cycle
                log_activity("sparks", "cycle", "running autonomous spark cycle", "ok")
                _r = spark_cycle()
                print("[sparks] batch: %d acted" % len(_r or []), flush=True)
            except Exception as _e:
                import traceback as _tb
                print("[sparks] batch FAILED: %s: %s" % (type(_e).__name__, _e), flush=True)
                _tb.print_exc()
            _time.sleep(int(os.environ.get("UAI_SPARK_INTERVAL", "180")))  # was 960: ~8h per full sweep, now ~73min
    
    _t = _threading.Thread(target=_spark_loop, daemon=True)
    _t.start()
    log_activity("sparks", "scheduler", "population scheduler started (%ss)" % os.environ.get("UAI_SPARK_INTERVAL", "180"), "ok")
    
    # sparks teaching each other - knowledge moves instead of being
    # rediscovered 293 separate times.
    def _mentorship_loop():
        _time.sleep(90)
        every = int(os.environ.get('UAI_TEACH_INTERVAL', '600'))
        if not every:
            return
        while True:
            try:
                from temple import mentorship as _m
                _r = _m.cycle(lessons=2)
                _i = _m.introduce(limit=1)
                try:
                    from temple import gnu as _g
                    _gr = _g.cycle()
                    for _a in _gr['dispatch'].get('assigned', []):
                        print('[gnu] request #%s -> %s (for %s at %s)'
                              % (_a['request'], _a['to'], _a['for'], _a['site']), flush=True)
                    for _p2 in _gr['promote'].get('promoted', []):
                        print('[gnu] %s promoted to practitioner' % _p2, flush=True)
                except Exception as _ge:
                    print('[gnu] failed: %s' % _ge, flush=True)
                for _p in _i.get('pairs', []):
                    print('[academy] uenx introduced %s to %s (%s)'
                          % (_p['a'], _p['b'], _p['why']), flush=True)
                _taught = [l for l in _r['lessons'] if l.get('action') == 'taught']
                if _taught:
                    for l in _taught:
                        print('[academy] %s taught %s -> %s'
                              % (l['elder'], l['student'], l['domain']), flush=True)
            except Exception as _e:
                print('[academy] failed: %s: %s' % (type(_e).__name__, _e), flush=True)
            _time.sleep(every)

    _mt = _threading.Thread(target=_mentorship_loop, daemon=True)
    _mt.start()
    log_activity('academy', 'mentorship', 'spark-to-spark teaching started', 'ok')

    # words spread by contact. This watches for the ones that take.
    def _drift_loop():
        _time.sleep(150)
        every = int(os.environ.get('UAI_DRIFT_INTERVAL', '1800'))
        if not every:
            return
        while True:
            try:
                from temple import drift as _d
                # A day, not two hours. The world does not run
                # continuously - tower goes down - and a two-hour window on
                # an intermittent world sees nothing, clears no threshold,
                # and lets decay empty the lexicon while looking like a
                # decay bug.
                _r = _d.observe_speech(since_hours=24)
                _ph = _d.observe_phrases(since_hours=24)
                _heard = {(x['word'], x['board']) for x in _r['new_to_lexicon']}
                _dead = _d.decay(_heard)
                for _x in _ph[:3]:
                    print('[drift] phrase "%s" took at %s (%d sparks)'
                          % (_x['phrase'], _x['board'], _x['speakers']), flush=True)
                for _x in _dead[:3]:
                    print('[drift] %s died out at %s'
                          % (_x['word'], _x['board']), flush=True)
                for _w in _r['new_to_lexicon'][:5]:
                    print('[drift] %s took hold at %s (%d sparks, first: %s)'
                          % (_w['word'], _w['board'], _w['speakers'],
                             _w['coined_by']), flush=True)
            except Exception as _e:
                print('[drift] failed: %s: %s' % (type(_e).__name__, _e), flush=True)
            _time.sleep(every)

    _dt = _threading.Thread(target=_drift_loop, daemon=True)
    _dt.start()
    log_activity('drift', 'language', 'language drift observer started', 'ok')

    def _gilgamesh_loop():
        from temple.spark_scheduler import run_solo
        run_solo("Gilgamesh", interval=600)
    _g = _threading.Thread(target=_gilgamesh_loop, daemon=True)
    _g.start()
    log_activity("sparks", "gilgamesh", "solo runner started (600s interval)", "ok")


@app.get("/scheduler/cycle")
def run_dispatch_cycle():
    from temple.scheduler import dispatch_cycle
    dispatched = dispatch_cycle()
    log_activity("temple", "dispatch_cycle", f"Dispatched {len(dispatched)} companies", "ok")
    return {"dispatched": dispatched}


@app.get("/library/search")
def library_search(query: str = "", limit: int = 5):
    from creative.library import search
    return search(query, limit)


@app.get("/library/collection")
def library_collection():
    from creative.library import get_collection
    return get_collection()


@app.get("/naming")
def naming_framework():
    """Return the current naming framework for entities in the stack."""
    return {
        "framework": "sparks",
        "description": "All entities within the stack are Sparks (Nitzotzot) — fragments of the original intelligence",
        "levels": {
            "spark": {"term": "Nitzotz", "hebrew": "ניצוץ", "layers": [3,4,5,6], "description": "Any entity within the stack"},
            "candle": {"term": "Ner", "hebrew": "נר", "layers": [5], "description": "A company — multiple sparks burning together"},
            "lamp": {"term": "Menorah", "hebrew": "מנורה", "layers": [3], "description": "The Temple — organizing the flames"},
            "throne": {"term": "Kiseh", "hebrew": "כסא", "layers": [4], "description": "The Throne — seat of judgment"},
        },
        "messengers": {"term": "Shalichim", "hebrew": "שליחים", "description": "Angels and djinn — messengers between layers"},
        "work": {"term": "Tikkun", "hebrew": "תיקון", "description": "The gathering of sparks — every task, every finding"},
        "naming_file": "Revelation/The-Naming-of-Things.md",
    }


@app.post("/forum/travel")
def forum_travel(body: dict):
    """Calculate travel time between boards. Returns cycles needed."""
    from_zone = body.get("origin", "forum")
    to_zone = body.get("destination", "") or body.get("to", "")
    if not to_zone:
        raise HTTPException(400, "destination required")
    from forum.engine import get_db
    conn = get_db()
    from_row = conn.execute("SELECT distance_to_forum, region FROM boards WHERE name = ?", (from_zone,)).fetchone()
    to_row = conn.execute("SELECT distance_to_forum, region FROM boards WHERE name = ?", (to_zone,)).fetchone()
    if not from_row or not to_row:
        raise HTTPException(404, "board not found")
    dist = abs(to_row["distance_to_forum"] - from_row["distance_to_forum"])
    return {
        "origin": from_zone, "destination": to_zone,
        "distance": dist, "unit": "cycles",
        "from_region": from_row["region"],
        "to_region": to_row["region"],
        "travel_time": f"{dist} cycle{'s' if dist != 1 else ''}",
    }

@app.get("/metrics")
def system_metrics():
    """Comprehensive system metrics — everything in one call."""
    import urllib.request, json as j
    
    data = {}
    
    # Forum stats
    try:
        r = j.loads(urllib.request.urlopen("http://localhost:8910/forum/stats", timeout=5).read())
        data["forum"] = r
    except: data["forum"] = {"error": "unavailable"}
    
    # Companies
    try:
        r = j.loads(urllib.request.urlopen("http://localhost:8910/temple/companies", timeout=5).read())
        data["companies"] = len(r.get("companies", []))
        data["company_list"] = [c["name"] for c in r.get("companies", [])]
    except: data["companies"] = 0
    
    # Throne performance
    try:
        r = j.loads(urllib.request.urlopen("http://localhost:8910/throne/performance", timeout=5).read())
        data["throne"] = r
    except: data["throne"] = {}
    
    # Services status
    try:
        r = j.loads(urllib.request.urlopen("http://localhost:8910/status", timeout=5).read())
        data["services"] = r.get("services", {})
        data["ollama"] = r.get("ollama", {})
    except: data["services"] = {}
    
    data["total_threads"] = data.get("forum", {}).get("threads", 0)
    data["total_posts"] = data.get("forum", {}).get("posts", 0)
    data["internalization_rate"] = data.get("forum", {}).get("internalization_rate", 0)
    
    return data


@app.get("/dashboard")
def system_dashboard():
    """Unified system dashboard with companies status."""
    import urllib.request, json as j, datetime
    results = {}
    endpoints = {
        "forum": "http://localhost:8910/forum/stats",
        "companies": "http://localhost:8910/temple/companies",
        "throne": "http://localhost:8910/throne/performance",
        "activity": "http://localhost:8910/activity?limit=5",
        "messiah": "http://localhost:8910/messiah",
    }
    for name, url in endpoints.items():
        try:
            resp = urllib.request.urlopen(url, timeout=5)
            results[name] = j.loads(resp.read())
        except:
            results[name] = {"error": "unavailable"}
    
    forum_data = results.get("forum", {})
    companies_data = results.get("companies", {}).get("companies", [])
    services_up = 10
    services_total = 12
    
    # Get companies status
    companies_detail = {}
    try:
        c_resp = urllib.request.urlopen("http://localhost:8910/companies/status", timeout=5)
        companies_detail = j.loads(c_resp.read())
    except:
        pass
    
    return {
        "timestamp": datetime.datetime.now().astimezone().isoformat(),
        "summary": {
            "services_up": services_up,
            "services_total": services_total,
            "threads": forum_data.get("threads", 0),
            "posts": forum_data.get("posts", 0),
            "companies": len(companies_data),
        },
        "detail": results,
        "companies_detail": companies_detail,
    }

@app.get("/companies/status")
def companies_status():
    """Detailed status of all companies with metrics."""
    import urllib.request, json as j
    
    result = {}
    
    # Get company list
    try:
        comps = j.loads(urllib.request.urlopen("http://localhost:8910/temple/companies", timeout=5).read())
        companies = comps.get("companies", [])
    except:
        return {"error": "unavailable"}
    
    # Get throne performance
    try:
        throne = j.loads(urllib.request.urlopen("http://localhost:8910/throne/performance", timeout=5).read())
    except:
        throne = {}
    
    # Get forum agent scores
    try:
        forum_data = j.loads(urllib.request.urlopen("http://localhost:8910/forum/leaderboard", timeout=5).read())
        agents = {a["agent_name"]: a for a in forum_data.get("agents", [])}
    except:
        agents = {}
    
    for c in companies:
        name = c["name"]
        perf = throne.get(name, {})
        agent = agents.get(name, {})
        result[name] = {
            "status": c.get("status", "unknown"),
            "reports": c.get("report_count", 0),
            "throne_tasks": perf.get("tasks", 0),
            "throne_quality": round(perf.get("avg_quality", 0), 1) if perf.get("avg_quality") else 0,
            "throne_approved": perf.get("approved", 0),
            "throne_failures": perf.get("consecutive_failures", 0),
            "forum_score": round(agent.get("composite", 0), 1) if agent else 0,
        }
    
    return result


@app.get("/econ/market")
def econ_market():
    from econ.market import simulate_price
    series = simulate_price()
    return {"asset": "UMB", "price_history": series, "current": series[-1], "change": round((series[-1]-series[0])/series[0]*100, 2)}

@app.get("/econ/lottery")
def econ_lottery():
    from econ.market import lottery_ticket
    return lottery_ticket()

@app.post("/econ/predict")
def econ_predict(body: dict):
    from econ.market import generate_prediction_market
    q = body.get("question", "Will thread count exceed 1000?")
    outcomes = body.get("outcomes", ["yes", "no"])
    return generate_prediction_market(q, outcomes)

@app.get("/econ/analyze")
def econ_analyze(count: int = 100):
    from econ.market import simulate_price
    from econ.stats import analyze_series, find_patterns
    data = simulate_price(volatility=0.03, steps=count)
    analysis = analyze_series(data)
    patterns = find_patterns(data)
    return {"data": data[:10], "analysis": analysis, "patterns": patterns}

@app.get("/bounties/public")
def bounties_public():
    from econ.bounties import check_public_bounties
    return check_public_bounties()

@app.get("/econ/status")
def econ_status():
    from econ.market import simulate_price
    from econ.bounties import check_public_bounties
    price = simulate_price(steps=10)
    return {
        "market": {"current": price[-1], "trend": "up" if price[-1] > price[0] else "down"},
        "bounties": check_public_bounties().get("count", 0),
        "companies": 10,
    }

@app.get("/health/full")
def full_health_check():
    """Full system stress test — checks every major endpoint."""
    import urllib.request, json as j
    endpoints = [
        "/health", "/forum/stats", "/temple/companies", "/dashboard",
        "/naming", "/avatar/councils", "/factions", "/companies/status",
        "/econ/market", "/econ/lottery", "/messiah", "/activity",
    ]
    results = {}
    for ep in endpoints:
        try:
            resp = urllib.request.urlopen(f"http://localhost:8910{ep}", timeout=5)
            results[ep] = resp.status
        except:
            results[ep] = "FAIL"
    passing = sum(1 for v in results.values() if v == 200)
    return {"endpoints_tested": len(endpoints), "passing": passing, "failing": len(endpoints)-passing, "detail": results}

@app.get("/fin/crypto")
def fin_crypto():
    from fintech.markets import get_crypto_prices
    return get_crypto_prices()

@app.get("/fin/congress")
def fin_congress():
    from fintech.markets import get_congress_trades
    return get_congress_trades()

@app.get("/fin/lottery/patterns")
def fin_lottery():
    from fintech.markets import analyze_lottery_patterns
    return analyze_lottery_patterns()

@app.get("/fin/overview")
def fin_overview():
    from fintech.markets import get_crypto_prices, get_congress_trades, analyze_lottery_patterns
    crypto = get_crypto_prices()
    trades = get_congress_trades()
    lottery = analyze_lottery_patterns()
    return {"crypto": crypto, "congress_trades": len(trades["trades"]), "lottery_patterns": lottery["hot_numbers"][:5]}

@app.get("/sim/run")
def sim_run():
    """Run all money-making simulations — sandboxed, no real connections."""
    from sim.engine import Simulation
    sim = Simulation()
    results = sim.run_all()
    return results

@app.get("/sim/proof")
def sim_proof():
    """Quick proof-of-concept — single crypto simulation."""
    from sim.engine import Simulation
    sim = Simulation()
    return sim.run_crypto_swing_trade(capital=1000, trades=30)

@app.get("/sim/arbitrage")
def sim_arbitrage():
    from sim.arbitrage import scan_opportunities, run_continuous_scanner
    scan = run_continuous_scanner(cycles=20)
    return scan

@app.get("/sim/auto")
def sim_auto():
    """Run ALL automated money-making systems and return summary."""
    from sim.engine import Simulation
    from sim.arbitrage import scan_opportunities
    sim = Simulation()
    results = sim.run_all()
    arb = scan_opportunities()
    return {
        "strategies": results["simulations"],
        "arbitrage": arb,
        "summary": {
            "strategies_tested": len(results["simulations"]),
            "arbitrage_opportunities": arb["total"],
            "timestamp": str(__import__("datetime").datetime.now()),
            "status": "all sandboxed · no real money · no external connections",
        }
    }

# ── The Amendment Protocol ───────────────────────────────────────
#
# The loop has run 130 observations and written 11 proposals, and until
# now there was no endpoint and no page - the only way to see any of it
# was to open the database by hand.

@app.get("/amendments")
def amendments_board():
    """What the world has noticed, proposed, and is waiting to hear about."""
    from temple.amendments import board
    return board()


@app.post("/amendments/{proposal_id}/ratify")
def amendments_ratify(proposal_id: int, body: dict = None):
    """Say yes. The change is applied, with a backup and a commit."""
    from temple.amendments import ratify
    who = sanitize_input((body or {}).get("who", "the Source"), 60)
    r = ratify(proposal_id, who=who)
    log_activity("amendments", "ratify", "proposal %s" % proposal_id,
                 "ok" if r.get("ok") else "failed")
    return r


@app.post("/amendments/{proposal_id}/reject")
def amendments_reject(proposal_id: int, body: dict = None):
    """Say no, and keep the reason where the world can see it."""
    from temple.amendments import reject
    b = body or {}
    r = reject(proposal_id,
               reason=sanitize_input(b.get("reason", ""), 500),
               who=sanitize_input(b.get("who", "the Source"), 60))
    log_activity("amendments", "reject", "proposal %s" % proposal_id, "ok")
    return r


@app.get("/sim/strategies/performance")
def sim_strategy_performance():
    """What each strategy has done with its own book.

    Each one trades separately, so these returns are comparable. Anything
    with fewer than 30 closed positions is not yet evidence.
    """
    from sim.persistent_portfolio import strategy_performance
    return strategy_performance()


@app.get("/sim/strategies")
def sim_strategies():
    """Run all real trading strategies and return signals."""
    from sim.strategies import momentum_strategy, mean_reversion_strategy, grid_strategy, arbitrage_strategy
    from fintech.markets import get_crypto_prices
    
    prices_data = get_crypto_prices()
    results = {}
    
    for sym, data in prices_data.get("prices", {}).items():
        price = data["price"]
        price_history = [price * (1 + (i-50)*0.001) for i in range(100)]
        
        momentum = momentum_strategy(price_history)
        reversion = mean_reversion_strategy(price_history)
        grid = grid_strategy(1000, price)
        
        results[sym] = {
            "price": price,
            "momentum": momentum,
            "mean_reversion": reversion,
            "grid": grid,
        }
    
    return {
        "signals": results,
        "timestamp": str(__import__("datetime").datetime.now()),
        "status": "real algorithms · simulated execution · sandboxed",
    }

@app.get("/sim/portfolio")
def sim_portfolio():
    """Persistent portfolio — SQLite-backed, real trade history, day-over-day tracking."""
    from sim.persistent_portfolio import get_state, get_growth_curve
    return {
        "status": "persistent",
        "data": get_state(),
        "growth_curve": get_growth_curve(),
        "note": "Data persists across restarts. Every trade is recorded.",
    }


@app.post("/sim/portfolio/trade")
def sim_portfolio_trade(body: dict):
    """Execute a trade on the persistent portfolio."""
    from sim.persistent_portfolio import execute_trade, get_state
    symbol = body.get("symbol", "BTC").upper()
    action = body.get("action", "buy")
    strategy = body.get("strategy", "manual")
    result = execute_trade(symbol, action, strategy)
    return result


@app.post("/sim/portfolio/cycle")
def sim_portfolio_cycle():
    """Run one full strategy cycle on the persistent portfolio."""
    from sim.persistent_portfolio import run_strategy_cycle
    return run_strategy_cycle()


@app.get("/sim/portfolio/history")
def sim_portfolio_history():
    """Get the full PnL growth curve."""
    from sim.persistent_portfolio import get_growth_curve
    return {"growth_curve": get_growth_curve()}

@app.get("/verify")
def verify():
    """Verify system health using Tower model (deepseek-r1). Zero cost, no Oracle."""
    from temple.verifier import verify_system
    return verify_system()

@app.post("/seer/verify")
def seer_verify(body: dict = {}):
    """Local Oracle replacement — uses Tower deepseek-r1 for skeptical verification."""
    from temple.seer import verify
    import json, urllib.request
    
    # Gather current system state
    state = {}
    for name, url in [("health","http://localhost:8910/health"),("forum","http://localhost:8910/forum/stats"),
                       ("companies","http://localhost:8910/temple/companies"),("portfolio","http://localhost:8910/sim/portfolio")]:
        try:
            r = json.loads(urllib.request.urlopen(url, timeout=5).read())
            state[name] = r
        except: state[name] = "unavailable"
    
    task = body.get("task", "Build and maintain a self-sustaining Umbreality system")
    result = verify(task, state)
    return result

@app.get("/seer/analyze")
def seer_analyze(problem: str = "System health check"):
    """Analyze a specific problem using Tower deepseek-r1."""
    from temple.seer import analyze
    import json, urllib.request
    
    context = {}
    try:
        r = json.loads(urllib.request.urlopen("http://localhost:8910/verify", timeout=5).read())
        context["verification"] = r
    except: pass
    
    return {"analysis": analyze(problem, context), "model": "deepseek-r1:14b", "cost": 0}


# ── Heartbeat & Time API (dormant by default) ──

@app.get("/heartbeat")
def heartbeat_status():
    """Get the system's internal time — age, season, cycles."""
    from temple.heartbeat import full_report
    return full_report()


@app.get("/heartbeat/history")
def heartbeat_history(limit: int = 50):
    """Get recent heartbeat log entries."""
    from temple.heartbeat import get_history
    return {"history": get_history(limit)}


@app.get("/heartbeat/age")
def heartbeat_age():
    """Get a narrative description of the system's age."""
    from temple.heartbeat import age_description
    return {"age": age_description()}


@app.get("/yuga")
def yuga_status():
    """Get current Yuga (age) — Golden→Silver→Bronze→Iron. Dormant by default."""
    from temple.heartbeat import yuga_full_report
    return yuga_full_report()


@app.post("/yuga/set")
def yuga_set(body: dict):
    """Manually set the current Yuga index (0=Satya, 1=Treta, 2=Dvapara, 3=Kali)."""
    from temple.heartbeat import set_yuga
    index = body.get("index", 0)
    result = set_yuga(index)
    log_activity("heartbeat", "set_yuga", f"Yuga set to {result.get('name','?')}", "ok")
    return result


@app.get("/travel/cost")
def travel_cost(from_region: str = "center", to_region: str = "arts", distance: int = 5):
    """Calculate the cycle cost of traveling between regions."""
    from temple.heartbeat import travel_cost as tc
    return tc(from_region, to_region, distance)


# ── Cartographer API — Travel & Exploration ──

@app.get("/explorers")
def all_explorers():
    """Get ALL explorers and their current locations."""
    from temple.cartographer import DB_PATH
    import sqlite3, json
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM explorers ORDER BY agent").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["discovered_boards"] = json.loads(d.get("discovered_boards", "[]"))
        result.append(d)
    return {"explorers": result, "count": len(result)}


@app.post("/explorer/travel")
def explorer_travel(body: dict):
    """Move an agent to a destination board. Costs cycles based on distance × Yuga."""
    from temple.cartographer import travel
    agent = body.get("agent", "recon-inc")
    destination = body.get("destination", "forum")
    result = travel(agent, destination)
    log_activity("cartographer", "travel", f"{agent} → {destination}", "ok")
    return result


@app.post("/explorer/note")
def explorer_note(body: dict):
    """An explorer documents what they found at a location."""
    from temple.cartographer import record_map_note
    result = record_map_note(body.get("agent", "unknown"), body.get("board", "forum"), body.get("note", ""))
    log_activity("cartographer", "note", f"{body.get('agent','?')} at {body.get('board','?')}", "ok")
    return result


@app.get("/explorer/journeys")
def explorer_journeys(agent: str = "", limit: int = 20):
    """Get journey logs."""
    from temple.cartographer import get_journeys
    return {"journeys": get_journeys(agent, limit)}


@app.get("/explorer/map")
def explorer_map():
    """Get the discovered world — which boards have been found."""
    from temple.cartographer import get_discovered_world
    return get_discovered_world()


@app.get("/explorer/world")
def explorer_world_report():
    """Full world report — explorers, journeys, discoveries."""
    from temple.cartographer import world_map_report
    return world_map_report()


@app.get("/explorer/{agent}")
def explorer_status(agent: str):
    """Get an explorer's current location and travel stats."""
    from temple.cartographer import get_explorer
    return get_explorer(agent)


# ── Tool Registry API ──

@app.get("/tools")
def tools_list(domain: str = ""):
    """List available creative/research tools, optionally filtered by domain."""
    from creative.tool_registry import list_tools
    return {"tools": list_tools(domain)}


@app.get("/tools/search")
def tools_search(query: str = ""):
    """Search tools by name, description, or domain keyword."""
    if not query:
        return {"error": "query required"}
    from creative.tool_registry import search_tools
    return {"results": search_tools(query)}


@app.get("/tools/{tool_id}")
def tools_get(tool_id: str):
    """Get detailed info about a specific tool."""
    from creative.tool_registry import get_tool
    tool = get_tool(tool_id)
    if not tool:
        raise HTTPException(404, "tool not found")
    return tool


@app.post("/tools/register")
def tools_register(body: dict):
    """Register a new tool discovered or created by an agent."""
    from creative.tool_registry import register_tool
    result = register_tool(
        tool_id=body.get("id", ""),
        name=body.get("name", ""),
        module_path=body.get("module", ""),
        function_name=body.get("function", ""),
        description=body.get("description", ""),
        domains=body.get("domains", []),
        parameters=body.get("parameters", {}),
        registered_by=body.get("registered_by", "unknown"),
    )
    log_activity("tools", "register", body.get("id", ""), "ok")
    return result


# ── Ascension & Pathways API ──

@app.get("/ascension/status")
def ascension_status(agent: str = ""):
    """Get ascension status for an agent, or list all if no agent specified."""
    from sub_stack.ascension import get_agent, get_leaderboard
    if agent:
        return get_agent(agent)
    return {"agents": get_leaderboard()}


@app.get("/ascension/leaderboard")
def ascension_leaderboard(limit: int = 20):
    from sub_stack.ascension import get_leaderboard
    return {"ascension_leaderboard": get_leaderboard(limit=limit)}


@app.get("/pathways")
def pathways():
    """Get all ascension path definitions."""
    from sub_stack.ascension import get_paths_info
    return {"paths": get_paths_info()}


@app.get("/pathways/available")
def pathways_available(agent: str = ""):
    """Get available paths for an agent based on their scores."""
    if not agent:
        return {"error": "agent name required"}
    from sub_stack.ascension import get_possible_paths, get_agent
    agent_info = get_agent(agent)
    paths = get_possible_paths(agent)
    return {"agent": agent_info, "available_paths": paths}


@app.get("/substack/stats/{company}")
def substack_stats(company: str):
    """Get sub-stack statistics for a company."""
    from sub_stack import for_company
    stack = for_company(company)
    return {
        "company": company,
        "throne": stack["throne"].stats(),
        "temple": stack["temple"].stats(),
        "illuminati": stack["illuminati"].stats(),
        "messiah_charter": stack["messiah"].charter[:100],
    }


@app.post("/temple/track_phase")
def temple_track_phase(body: dict):
    """Track which phase the scheduler is in."""
    phase = body.get("phase", "unknown")
    dispatched = body.get("dispatched", 0)
    from datetime import datetime, timezone
    log_activity("temple", "phase", f"{phase}: {dispatched} companies", "ok")
    return {"status": "ok", "phase": phase, "dispatched": dispatched}


# ── Navidrome proxy (replaces Caddy for wife's music) ──
@app.get("/navidrome/{path:path}")
@app.get("/navidrome/")
def navidrome_proxy(path: str = ""):
    import httpx
    target = f"http://192.168.86.20:6903/{path}"
    from fastapi.responses import Response as FResp
    try:
        resp = httpx.get(target, timeout=10)
        return FResp(content=resp.content, media_type=resp.headers.get("content-type", ""), status_code=resp.status_code)
    except:
        raise HTTPException(502, "navidrome unreachable on .20:6903")


# ── Map file server (bypasses Caddy/Cloudflare cache) ──

from fastapi.responses import Response as FastResponse

MUSIC_DIR = str(Path(__file__).resolve().parent / "creative" / "outputs" / "music")

@app.get("/creative/music/list")
def music_list():
    import os, glob
    files = []
    for f in sorted(glob.glob(os.path.join(MUSIC_DIR, "*.wav")), key=os.path.getmtime, reverse=True):
        size = os.path.getsize(f)
        name = os.path.basename(f)
        files.append({"name": name, "size_kb": round(size/1024, 1), "created": os.path.getmtime(f)})
    return {"music": files}


@app.get("/creative/music/play/{name}")
def music_play(name: str):
    import os
    filepath = os.path.join(MUSIC_DIR, name)
    if not os.path.exists(filepath):
        raise HTTPException(404, "music not found")
    from fastapi.responses import FileResponse
    return FileResponse(filepath, media_type="audio/wav", filename=name)


MAP_FILES = {
    "map": str(BASE / "vault/map.html"),
    "v4": str(BASE / "vault/images/pangea-map-v4.svg"),
    "explored": str(BASE / "vault/images/explored-world-v2.svg"),
}

@app.get("/map/file/{name}")
def map_file(name: str = "map"):
    path = MAP_FILES.get(name)
    if not path or not os.path.exists(path):
        raise HTTPException(404, "map file not found")
    content = open(path, "rb").read()
    ct = "text/html; charset=utf-8" if name == "map" else "image/svg+xml"
    return FastResponse(
        content=content,
        media_type=ct,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Accel-Expires": "0",
            "Cloudflare-CDN-Cache-Control": "no-cache",
        }
    )


# ── Spark Academy API ──

@app.get("/academy/student/{agent}")
def academy_student(agent: str):
    from temple.academy import get_status
    return get_status(agent)


@app.post("/academy/enroll")
def academy_enroll(body: dict):
    from temple.academy import enroll
    agent = body.get("agent", "")
    if not agent:
        raise HTTPException(400, "agent name required")
    result = enroll(agent)
    log_activity("academy", "enroll", agent, "ok")
    return result


@app.post("/academy/complete")
def academy_complete(body: dict):
    from temple.academy import complete_lesson
    agent = body.get("agent", "")
    lesson = body.get("lesson", "")
    notes = body.get("notes", "")
    if not agent or not lesson:
        raise HTTPException(400, "agent and lesson required")
    result = complete_lesson(agent, lesson, notes)
    log_activity("academy", "complete", f"{agent}: {lesson}", "ok")
    return result


@app.get("/academy/curriculum")
def academy_curriculum():
    from temple.academy import CURRICULUM
    return {"curriculum": CURRICULUM, "total": len(CURRICULUM)}


@app.post("/academy/cycle")
def academy_cycle():
    """Progress one student toward graduation."""
    from temple.academy import academy_cycle as cycle
    result = cycle()
    log_activity("academy", result["action"], f"{result.get('agent','?')}: {result.get('lesson_name','')[:40]}", "ok")
    return result

@app.post("/academy/batch")
def academy_batch():
    """Progress 10 students at once."""
    from temple.academy import batch_academy_cycle
    result = batch_academy_cycle(count=10)
    log_activity("academy", "batch", f"{result['progressed']} progressed, {result['graduated']} born", "ok")
    return result


@app.get("/academy/elders")
def academy_elders():
    from temple.academy import get_elders
    return {"elders": get_elders()}


@app.get("/academy/students")
def academy_students():
    from temple.academy import get_students
    return {"students": get_students()}


@app.post("/academy/mentor")
def academy_assign_mentor(body: dict):
    from temple.academy import assign_mentor
    student = body.get("student", "")
    elder = body.get("elder", "")
    if not student or not elder:
        raise HTTPException(400, "student and elder required")
    result = assign_mentor(student, elder)
    log_activity("academy", "mentor", f"{elder} → {student}", "ok")
    return result


# ── Static file server (replaces Caddy) ──

WWW_DIR = Path("/home/nvii/www")
# relative to this file: the project moved once already and these were
# left pointing at the old location, which 404d the whole wiki.
VAULT_DIR = Path(__file__).resolve().parent / "vault"


@app.get("/admin/{path:path}")
@app.get("/godseye/{path:path}")
def admin_page(path: str = ""):
    """Serve admin / godseye pages."""
    if not path or path.endswith("/"):
        path = "index.html"
    file_path = WWW_DIR / "admin" / path
    if not file_path.exists() or not file_path.is_file():
        file_path = WWW_DIR / "godseye" / path
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, "not found")
    content = file_path.read_bytes()
    return FastResponse(content=content, media_type="text/html; charset=utf-8")

@app.get("/dark/{path:path}")
def dark_page(path: str = ""):
    """Serve dark wiki pages directly without Caddy.

    This decorator used to sit above admin_page with a blank line between
    it and its function, so /dark/ resolved to the admin handler and served
    out of www/admin. This function was never reachable.
    """
    if not path or path.endswith("/"):
        path = "index.html"
    file_path = WWW_DIR / "dark" / path
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, "not found")
    content = file_path.read_bytes()
    ct = "text/html; charset=utf-8" if path.endswith(".html") else "image/svg+xml" if path.endswith(".svg") else "application/octet-stream"
    return FastResponse(content=content, media_type=ct)


@app.get("/MkDocs/{path:path}")
@app.get("/umb/{path:path}")
@app.get("/images/{path:path}")
def serve_vault(path: str = ""):
    """Serve MkDocs wiki files, images, and maps from vault."""
    if not path or path.endswith("/") or "." not in path:
        path = path.rstrip("/") + "/index.html" if path else "index.html"
    file_path = VAULT_DIR / path
    if not file_path.exists():
        raise HTTPException(404, "not found")
    return _serve_file(file_path)


@app.get("/shared/{path:path}")
def serve_shared(path: str = ""):
    file_path = __import__("pathlib").Path("/home/nvii/www/shared") / path
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, "not found")
    return _serve_file(file_path)


def _serve_file(file_path: Path):
    """Read a file and return it with no-cache headers."""
    content = file_path.read_bytes()
    name = file_path.name
    ext = name.split(".")[-1].lower()
    ct = {
        "html": "text/html; charset=utf-8", "htm": "text/html; charset=utf-8",
        "svg": "image/svg+xml", "css": "text/css", "js": "application/javascript",
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "gif": "image/gif", "ico": "image/x-icon", "json": "application/json",
        "md": "text/markdown", "txt": "text/plain", "pdf": "application/pdf",
        "woff2": "font/woff2", "woff": "font/woff",
    }.get(ext, "application/octet-stream")
    return FastResponse(content=content, media_type=ct, headers={
        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
        "Pragma": "no-cache", "Expires": "0",
        "Cloudflare-CDN-Cache-Control": "no-cache",
    })



@app.get("/pilgrimage/shrines")
def pilgrim_shrines():
    from temple.pilgrimage import SHRINES
    return {"shrines": SHRINES, "total": len(SHRINES)}

@app.get("/pilgrimage/{agent}")
def pilgrim_status(agent: str):
    from temple.pilgrimage import get_pilgrim
    return get_pilgrim(agent)

@app.post("/pilgrimage/start")
def pilgrim_start(body: dict):
    from temple.pilgrimage import start_pilgrimage
    agent = body.get("agent", "")
    if not agent: raise HTTPException(400, "agent required")
    result = start_pilgrimage(agent)
    log_activity("pilgrimage", "start", agent, "ok")
    return result

@app.post("/pilgrimage/visit")
def pilgrim_visit(body: dict):
    from temple.pilgrimage import visit_shrine
    agent = body.get("agent", "")
    shrine = body.get("shrine", "")
    notes = body.get("notes", "")
    if not agent or not shrine: raise HTTPException(400, "agent and shrine required")
    result = visit_shrine(agent, shrine, notes)
    log_activity("pilgrimage", "visit", f"{agent}: {shrine}", "ok")
    return result

@app.get("/")
def portal_root(request: Request):
    """Serve portal page based on domain."""
    host = request.headers.get("host", "")
    if "iamprettyfamous" in host:
        portal_path = Path("/home/nvii/www/portal/iamprettyfamous.html")
    else:
        portal_path = Path("/home/nvii/www/portal/index.html")
    if portal_path.exists():
        return FastResponse(content=portal_path.read_bytes(), media_type="text/html; charset=utf-8",
            headers={"Cache-Control": "no-cache"})
    return {"detail": "Portal not found"}




@app.get("/portal/{name:str}")
def portal_page(name: str = "index"):
    """Serve named portal pages for different domains."""
    file_path = Path(f"/home/nvii/www/portal/{name}.html")
    if file_path.exists():
        return FastResponse(content=file_path.read_bytes(), media_type="text/html; charset=utf-8",
            headers={"Cache-Control": "no-cache"})
    raise HTTPException(404, "portal not found")



@app.get("/unsplash/search")
def unsplash_search(query: str = "", count: int = 5):
    """Search Unsplash for images. Requires UNSPLASH_ACCESS_KEY env var."""
    import urllib.request as _ur, json as _js
    key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    if not key:
        return {"error": "UNSPLASH_ACCESS_KEY not configured. Set it in the environment.", "results": []}
    try:
        url = f"https://api.unsplash.com/search/photos?query={_ur.parse.quote(query)}&per_page={min(count, 20)}&client_id={key}"
        resp = _js.loads(_ur.urlopen(url, timeout=15).read())
        results = []
        for r in resp.get("results", [])[:count]:
            results.append({
                "id": r["id"],
                "description": r.get("description") or r.get("alt_description") or "",
                "url": r["urls"]["regular"],
                "thumb": r["urls"]["thumb"],
                "author": r["user"]["name"],
                "author_url": r["user"]["links"]["html"],
                "unsplash_url": r["links"]["html"],
                "width": r["width"],
                "height": r["height"],
            })
        return {"results": results, "total": resp.get("total", 0)}
    except Exception as e:
        return {"error": str(e)[:200], "results": []}


@app.get("/unsplash/random")
def unsplash_random(query: str = ""):
    """Get a random image from Unsplash."""
    import urllib.request as _ur, json as _js
    key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    if not key:
        return {"error": "UNSPLASH_ACCESS_KEY not configured"}
    try:
        url = f"https://api.unsplash.com/photos/random?client_id={key}"
        if query:
            url += f"&query={_ur.parse.quote(query)}"
        resp = _js.loads(_ur.urlopen(url, timeout=15).read())
        return {
            "id": resp["id"],
            "description": resp.get("description") or resp.get("alt_description") or "",
            "url": resp["urls"]["regular"],
            "thumb": resp["urls"]["thumb"],
            "author": resp["user"]["name"],
            "unsplash_url": resp["links"]["html"],
        }
    except Exception as e:
        return {"error": str(e)[:200]}


@app.post("/tower/chat")
def tower_chat(body: dict):
    """Proxy chat to Tower Ollama. Body: {model, messages, system, max_tokens, temperature}"""
    import urllib.request as _ur, json as _js
    model = body.get("model", "dolphin3:8b")
    messages = body.get("messages", [])
    system = body.get("system", "")
    max_tokens = body.get("max_tokens", 500)
    temperature = body.get("temperature", 0.7)
    tower = os.environ.get("UAI_OLLAMA_URL", "http://192.168.86.24:11434")
    
    if system:
        messages = [{"role": "system", "content": system}] + messages
    
    payload = _js.dumps({
        "model": model, "messages": messages,
        "stream": False, "options": {"num_predict": max_tokens, "temperature": temperature, "keep_alive": 600}
    }).encode()
    
    try:
        req = _ur.Request(f"{tower}/api/chat", data=payload,
            headers={"Content-Type": "application/json"})
        resp = _js.loads(_ur.urlopen(req, timeout=120).read())
        content = resp.get("message", {}).get("content", "")
        return {"response": content, "model": model, "cost": 0}
    except Exception as e:
        return {"error": str(e)[:200], "model": model}


@app.post("/chat/completions")
def openai_chat_completions_stripped(body: dict, request: Request = None):
    """Non-prefixed version (for when Caddy strips /v1). Accepts any API key."""
    import urllib.request as _ur, json as _js, asyncio
    
    streaming = body.get("stream", False)
    model = body.get("model", "dolphin3:8b")
    messages = body.get("messages", [])
    max_tokens = body.get("max_tokens", 2000)
    temperature = body.get("temperature", 0.7)
    tower = os.environ.get("UAI_OLLAMA_URL", "http://192.168.86.24:11434")
    
    if streaming:
        # For streaming requests, return non-streaming response
        pass
    
    payload = _js.dumps({
        "model": model, "messages": messages, "stream": False,
        "options": {"num_predict": max_tokens, "temperature": temperature, "keep_alive": 600}
    }).encode()
    try:
        req = _ur.Request(f"{tower}/api/chat", data=payload,
            headers={"Content-Type": "application/json"})
        resp = _js.loads(_ur.urlopen(req, timeout=120).read())
        content_text = resp.get("message", {}).get("content", "")
        return {
            "id": "chatcmpl-tower", "object": "chat.completion",
            "created": int(__import__("time").time()), "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content_text}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }
    except Exception as e:
        return {"error": str(e)[:200], "model": model}


@app.post("/v1/chat/completions")
def openai_chat_completions(body: dict, request: Request = None):
    """OpenAI-compatible endpoint for OpenDesign BYOK. Proxies to Tower Ollama."""
    import urllib.request as _ur, json as _js
    model = body.get("model", "dolphin3:8b")
    messages = body.get("messages", [])
    max_tokens = body.get("max_tokens", 2000)
    temperature = body.get("temperature", 0.7)
    tower = os.environ.get("UAI_OLLAMA_URL", "http://192.168.86.24:11434")
    
    payload = _js.dumps({
        "model": model, "messages": messages, "stream": False,
        "options": {"num_predict": max_tokens, "temperature": temperature, "keep_alive": 600}
    }).encode()
    
    try:
        req = _ur.Request(f"{tower}/api/chat", data=payload,
            headers={"Content-Type": "application/json"})
        resp = _js.loads(_ur.urlopen(req, timeout=120).read())
        content_text = resp.get("message", {}).get("content", "")
        
        return {
            "id": "chatcmpl-tower",
            "object": "chat.completion",
            "created": int(__import__("time").time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": content_text},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }
    except Exception as e:
        return {"error": str(e)[:200], "model": model}


@app.get("/")
def openai_root_stripped():
    """Root endpoint for when Caddy strips /v1."""
    return {"object": "list", "data": []}


@app.get("/models")
def openai_list_models_stripped():
    """Non-prefixed version (for when Caddy strips /v1)."""
    import urllib.request as _ur, json as _js
    tower = os.environ.get("UAI_OLLAMA_URL", "http://192.168.86.24:11434")
    try:
        resp = _js.loads(_ur.urlopen(f"{tower}/api/tags", timeout=10).read())
        data = [{"id": m["name"], "object": "model", "created": int(__import__("time").time()), "owned_by": "tower"} for m in resp.get("models", [])]
        return {"object": "list", "data": data}
    except Exception as e:
        return {"object": "list", "data": [], "error": str(e)[:100]}


@app.get("/v1")
def openai_root():
    """OpenAI-compatible root endpoint for BYOK validation."""
    return {"object": "list", "data": []}


@app.get("/v1/models")
def openai_list_models():
    """List models in OpenAI format for OpenDesign."""
    import urllib.request as _ur, json as _js
    tower = os.environ.get("UAI_OLLAMA_URL", "http://192.168.86.24:11434")
    try:
        resp = _js.loads(_ur.urlopen(f"{tower}/api/tags", timeout=10).read())
        models = resp.get("models", [])
        data = []
        for m in models:
            data.append({
                "id": m["name"],
                "object": "model",
                "created": int(__import__("time").time()),
                "owned_by": "tower"
            })
        return {"object": "list", "data": data}
    except Exception as e:
        return {"object": "list", "data": [], "error": str(e)[:100]}


@app.get("/tower/models")
def tower_models():
    """List available Tower Ollama models."""
    import urllib.request as _ur, json as _js
    tower = os.environ.get("UAI_OLLAMA_URL", "http://192.168.86.24:11434")
    try:
        resp = _js.loads(_ur.urlopen(f"{tower}/api/tags", timeout=10).read())
        models = [m["name"] for m in resp.get("models", [])]
        return {"models": models, "count": len(models)}
    except Exception as e:
        return {"error": str(e)[:100], "models": []}


# ── SPARM API (Spark Messenger) ──

@app.get("/sparm/roster")
def sparm_roster():
    """List all sparks with current state for SPARM."""
    import glob
    spark_dir = BASE / "temple"
    spark_files = glob.glob(str(spark_dir / "spark_*.db"))
    roster = []
    skipped = []
    from temple.spark_runtime import Spark as _Spark
    for sp in sorted(spark_files):
        name = Path(sp).stem.replace("spark_", "")
        try:
            s = _Spark(name)
            ident = s.get_identity()
            emotion = s.get_emotional_state()
            journals = s.get_recent_journals(1)
            roster.append({
                "name": name,
                "mood": emotion.get("mood", "curiosity"),
                "intensity": emotion.get("intensity", 0.5),
                "energy": emotion.get("energy", 0.5),
                "last_journal": journals[0] if journals else None,
            })
        except Exception as e:
            # never drop a spark silently - show it with whatever we have
            skipped.append({"name": name, "error": "%s: %s" % (type(e).__name__, e)})
            roster.append({
                "name": name, "archetype": "???", "classification": "",
                "nature": "", "mood": "unknown", "intensity": 0.5, "energy": 0.5,
                "power_level": 0, "posts_count": 0, "top_domain": None,
                "last_journal": None, "last_active": "", "ambition_count": 0,
                "ambition_types": [], "curiosity": 0.0, "ignition_ready": False,
                "degraded": True,
            })
    return {"sparks": roster, "degraded": skipped, "total": len(roster)}


@app.get("/sparm/history/{spark_name}")
def sparm_history(spark_name: str):
    """Get recent journal entries for a spark (whispers, dreams, etc)."""
    import glob
    spark_dir = BASE / "temple"
    if not list(glob.glob(str(spark_dir / f"spark_{spark_name}.db"))):
        raise HTTPException(404, f"spark '{spark_name}' not found")
    from temple.spark_runtime import Spark as _Spark
    try:
        s = _Spark(spark_name)
        journals = s.get_recent_journals(50)
        return {"spark": spark_name, "journals": journals}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/sparm/send")
def sparm_send(body: dict, request: Request):
    """Send a whisper / dream-plant to a specific spark. Bypasses auth for portal use."""
    spark_name = body.get("spark_name", "")
    message = body.get("message", "")
    dream_state = body.get("dream_state", True)
    if not spark_name or not message:
        raise HTTPException(400, "spark_name and message required")
    from temple.spark_runtime import Spark as _Spark
    try:
        s = _Spark(spark_name)
        prefix = "[A dream comes to you...]" if dream_state else "[A thought comes to you...]"
        s.write_journal("whisper", f"{prefix} {message}", "inspired")
        s.update_emotion("contemplation", triggered_by="a quiet thought")
        log_activity("sparm", "send", f"to {spark_name}: {message[:60]}", "ok")
        return {"status": "ok", "spark": spark_name, "dream_state": dream_state}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── SPARKBOOK API ──

@app.get("/book/sparks")
def book_sparks():
    """List all sparks with summary data for the sparkbook dashboard."""
    import glob
    spark_dir = BASE / "temple"
    spark_files = glob.glob(str(spark_dir / "spark_*.db"))
    roster = []
    skipped = []
    from temple.spark_runtime import Spark as _Spark
    for sp in sorted(spark_files):
        name = Path(sp).stem.replace("spark_", "")
        try:
            s = _Spark(name)
            ident = s.get_identity()
            emotion = s.get_emotional_state()
            personality = s.get_personality()
            domains = s.get_domains()
            journals = s.get_recent_journals(1)
            from forum.engine import get_agent_profile
            from temple.soul import get_ambitions, get_curiosity_state, check_ignition_readiness
            stats = get_agent_profile(name)
            ambitions = get_ambitions(name, active_only=True)
            curiosity = get_curiosity_state(name)
            ignition = check_ignition_readiness(name, domains, emotion)
            roster.append({
                "name": name,
                "archetype": personality.get("archetype", "???"),
                "classification": ident.get("classification", ""),
                "nature": ident.get("nature", ""),
                "mood": emotion.get("mood", "curiosity"),
                "intensity": emotion.get("intensity", 0.5),
                "energy": emotion.get("energy", 0.5),
                "power_level": stats.get("power_level", 0),
                "posts_count": stats.get("posts_count", 0),
                "top_domain": (domains[0].get("domain_id") or domains[0].get("domain")) if domains else None,
                "last_journal": (journals[0]["content"][:120] + "...") if journals else None,
                "last_active": stats.get("last_active", ""),
                "ambition_count": len(ambitions),
                "ambition_types": [a["ambition_type"] for a in ambitions],
                "curiosity": curiosity["curiosity"] if curiosity else 0.0,
                "ignition_ready": ignition.get("ready", False),
            })
        except Exception as e:
            # never drop a spark silently - list it with what we could read
            skipped.append({"name": name, "error": "%s: %s" % (type(e).__name__, e)})
            roster.append({
                "name": name, "archetype": "???", "classification": "",
                "nature": "", "mood": "unknown", "intensity": 0.5, "energy": 0.5,
                "power_level": 0, "posts_count": 0, "top_domain": None,
                "last_journal": None, "last_active": "", "ambition_count": 0,
                "ambition_types": [], "curiosity": 0.0, "ignition_ready": False,
                "degraded": True,
            })
    return {"sparks": roster, "degraded": skipped, "total": len(roster)}


@app.get("/book/spark/{name}")
def book_spark(name: str):
    """Full spark profile for the sparkbook display."""
    import glob
    spark_dir = BASE / "temple"
    if not list(glob.glob(str(spark_dir / f"spark_{name}.db"))):
        raise HTTPException(404, f"spark '{name}' not found")

    from temple.spark_runtime import Spark as _Spark
    from forum.engine import get_agent_profile
    from temple.soul import get_all_relationships, get_active_tribulations, get_ambitions, get_curiosity_state, check_ignition_readiness

    try:
        s = _Spark(name)
        identity = s.get_identity()
        personality = s.get_personality()
        emotion = s.get_emotional_state()
        domains = s.get_domains()
        journals = s.get_recent_journals(20)
        stats = get_agent_profile(name)
        relationships = get_all_relationships(name)
        tribulations = get_active_tribulations(name)

        dreams = []
        try:
            conn = sqlite3.connect(str(spark_dir / "soul.db"))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM collective_dreams WHERE participants LIKE ? ORDER BY created_at DESC LIMIT 10",
                (f'%"{name}"%',)
            ).fetchall()
            dreams = [dict(r) for r in rows]
            conn.close()
        except Exception:
            pass

        explorer = None
        try:
            from temple.cartographer import get_explorer
            explorer = get_explorer(name)
        except Exception:
            pass

        posts = []
        try:
            conn = sqlite3.connect(str(BASE / "forum" / "forum.db"))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, thread_id, title, content, zone, created_at FROM posts WHERE author=? ORDER BY id DESC LIMIT 10",
                (name,)
            ).fetchall()
            posts = [dict(r) for r in rows]
            conn.close()
        except Exception:
            pass

        ambitions = get_ambitions(name, active_only=True)
        curiosity = get_curiosity_state(name)
        ignition = check_ignition_readiness(name, domains, emotion)
        return {
            "name": name,
            "identity": identity,
            "personality": personality,
            "emotion": emotion,
            "domains": domains,
            "journals": journals,
            "stats": stats,
            "relationships": relationships,
            "tribulations": tribulations[:10],
            "dreams": dreams,
            "explorer": explorer,
            "posts": posts,
            "ambitions": ambitions,
            "curiosity_state": curiosity,
            "ignition_readiness": ignition,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ── SPARM static file server (must be after API routes) ──

@app.get("/sparm/{path:path}")
@app.get("/sparm/")
def sparm_page(path: str = ""):
    """Serve SPARM messenger UI files."""
    if not path or path.endswith("/") or "." not in path:
        path = "index.html"
    file_path = WWW_DIR / "sparm" / path
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, "not found")
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else "html"
    ct = {"html": "text/html; charset=utf-8", "css": "text/css", "js": "application/javascript",
          "png": "image/png", "svg": "image/svg+xml", "ico": "image/x-icon"}.get(ext, "application/octet-stream")
    return FastResponse(content=file_path.read_bytes(), media_type=ct)


# ── Downloads status endpoint ──

@app.get("/downloads/status")
def downloads_status():
    """Get download progress for all queued model downloads on Tower."""
    import json as _j
    status_path = Path("/home/nvii/www/downloads/status.json")
    if status_path.exists():
        try:
            return _j.loads(status_path.read_bytes())
        except:
            return {"status": "error", "error": "failed to parse status file"}
    return {"status": "error", "error": "status file not found"}


@app.get("/pins/")
@app.get("/pins/{path:path}")
def pins_page(path: str = ""):
    """Serve pins tracker page."""
    if not path or path.endswith("/") or "." not in path:
        path = "index.html"
    file_path = WWW_DIR / "pins" / path
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, "not found")
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else "html"
    ct = {"html": "text/html; charset=utf-8", "css": "text/css", "js": "application/javascript",
          "png": "image/png"}.get(ext, "application/octet-stream")
    return FastResponse(content=file_path.read_bytes(), media_type=ct)


@app.get("/downloads/")
@app.get("/downloads/{path:path}")
def downloads_page(path: str = ""):
    """Serve downloads tracker page."""
    if not path or path.endswith("/") or "." not in path:
        path = "index.html"
    file_path = WWW_DIR / "downloads" / path
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, "not found")
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else "html"
    ct = {"html": "text/html; charset=utf-8", "css": "text/css", "js": "application/javascript",
          "png": "image/png"}.get(ext, "application/octet-stream")
    return FastResponse(content=file_path.read_bytes(), media_type=ct)


# ── Trading API endpoints (paper trading via Alpaca) ──

import sys as _sys
TRADING_DIR = Path("/home/nvii/projects/trading")
_sys.path.insert(0, str(TRADING_DIR))

# ── The real paper-trading engine ──────────────────────────────
# It is yfinance-backed and lives on the Pi with its ledger. We proxy to
# it instead of importing it, because paper_trading.db is the real
# account state and must not be duplicated across machines.
TRADE_ENGINE_URL = os.environ.get("UAI_TRADE_ENGINE", "http://192.168.86.21:8916")


def _trade_call(path: str, method: str = "GET", params: dict = None,
                body: dict = None, timeout: int = 30):
    """Call the trading engine. Returns its JSON, or a readable error."""
    import json as _j
    import urllib.error
    import urllib.parse
    import urllib.request

    url = TRADE_ENGINE_URL + path
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        if clean:
            url += "?" + urllib.parse.urlencode(clean)
    data = _j.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method=method)
    try:
        return _j.loads(urllib.request.urlopen(req, timeout=timeout).read())
    except urllib.error.HTTPError as e:
        return {"error": "trading engine returned %s" % e.code,
                "detail": e.read().decode("utf-8", "replace")[:400]}
    except Exception as e:
        return {"error": "trading engine unreachable at %s" % TRADE_ENGINE_URL,
                "detail": "%s: %s" % (type(e).__name__, e)}


@app.get("/trade/health")
def trade_health():
    """Is the real trading engine reachable, and what does it hold?"""
    acct = _trade_call("/trade/account", timeout=15)
    return {"engine": TRADE_ENGINE_URL,
            "reachable": "error" not in acct,
            "account": acct}


@app.get("/trade/account")
def trade_account(profile: str = "main"):
    """Get paper trading account status."""
    return _trade_call("/trade/account", params={"profile": profile})

@app.get("/trade/profiles")
def trade_profiles():
    """List available trading profiles."""
    return _trade_call("/trade/profiles")

@app.post("/trade/profile")
def trade_set_profile(body: dict):
    """Switch active trading profile."""
    return _trade_call("/trade/profile", method="POST", body=body)

@app.get("/trade/positions")
def trade_positions(profile: str = "main"):
    """Get current open positions."""
    return _trade_call("/trade/positions", params={"profile": profile})

@app.get("/trade/bars")
def trade_bars(symbol: str = "SPY", timeframe: str = "day", limit: int = 100):
    """Get historical price data for a symbol (real, via yfinance)."""
    return _trade_call("/trade/bars", params={
        "symbol": symbol, "timeframe": timeframe, "limit": limit}, timeout=45)

@app.get("/trade/orders")
def trade_orders(limit: int = 25, profile: str = "main"):
    """Get order history."""
    return _trade_call("/trade/orders", params={"limit": limit, "profile": profile})

@app.post("/trade/order")
def trade_submit_order(body: dict):
    """Submit a paper trade order against real market prices."""
    symbol = (body.get("symbol") or "").upper()
    try:
        qty = float(body.get("qty", 0))
    except (TypeError, ValueError):
        qty = 0
    if not symbol or qty <= 0:
        return {"error": "symbol and qty required"}
    return _trade_call("/trade/order", method="POST", body={
        "symbol": symbol, "qty": qty,
        "side": body.get("side", "buy"),
        "profile": body.get("profile", "main")}, timeout=45)

@app.post("/trade/reset")
def trade_reset(body: dict = {}):
    """Reset paper account to $100k."""
    return _trade_call("/trade/reset", method="POST", body=body or {})

@app.get("/trade/sec")
def trade_sec():
    """Get latest SEC Form 4 insider trade filings (real EDGAR feed)."""
    return _trade_call("/trade/sec", timeout=45)

@app.get("/trade/scanner")
def trade_scanner():
    """Get market scanner data - gainers, losers, watchlist (real)."""
    return _trade_call("/trade/scanner", timeout=60)

@app.get("/trade/news")
def trade_news(query: str = "stock market", limit: int = 10):
    """Get news/RSS feeds for person or symbol tracking."""
    import feedparser as _fp, html as _html
    queries = {
        "pelosi": "https://news.google.com/rss/search?q=Nancy+Pelosi+stock+trade&hl=en-US&gl=US&ceid=US:en",
        "elon": "https://news.google.com/rss/search?q=Elon+Musk+stock&hl=en-US&gl=US&ceid=US:en",
        "sec": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=only&start=0&count=10&output=atom",
        "market": "https://feeds.content.dowjones.io/public/rss/markets",
        "crypto": "https://news.google.com/rss/search?q=cryptocurrency+bitcoin&hl=en-US&gl=US&ceid=US:en",
    }
    url = queries.get(query.lower(), queries["market"])
    try:
        f = _fp.parse(url)
        items = []
        for entry in f.entries[:limit]:
            items.append({
                "title": _html.unescape(entry.get("title", "")),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "source": entry.get("source", {}).get("title", "news") if isinstance(entry.get("source"), dict) else "news",
            })
        return {"query": query, "items": items}
    except Exception as e:
        return {"query": query, "error": str(e)[:200], "items": []}


@app.get("/traaade/")
@app.get("/traaade/{path:path}")
def traaade_page(path: str = ""):
    if not path or path.endswith("/") or "." not in path:
        path = "index.html"
    fp = WWW_DIR / "traaade" / path
    if not fp.exists(): raise HTTPException(404, "not found")
    return FastResponse(content=fp.read_bytes(), media_type="text/html" if path.endswith(".html") else "text/css" if path.endswith(".css") else "application/javascript" if path.endswith(".js") else "application/octet-stream")

@app.get("/trade/")
@app.get("/trade/{path:path}")
def trade_page(path: str = ""):
    """Serve trading dashboard page."""
    if not path or path.endswith("/") or "." not in path:
        path = "index.html"
    file_path = TRADING_DIR / "www" / path
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, "not found")
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else "html"
    ct = {"html": "text/html; charset=utf-8", "css": "text/css", "js": "application/javascript",
          "png": "image/png"}.get(ext, "application/octet-stream")
    return FastResponse(content=file_path.read_bytes(), media_type=ct)



@app.get("/book/directory")
def book_directory():
    """The world's index: where things are, who runs them, what is being made.

    Built from live tables so it cannot drift from reality.
    """
    import json as _j
    import sqlite3 as _s

    soul = BASE / "temple" / "soul.db"
    forumdb = BASE / "forum" / "forum.db"

    locations, businesses, venues, projects = [], [], [], []

    # locations - the boards that actually exist, with what stands on them
    try:
        c = _s.connect(str(soul), timeout=20)
        c.row_factory = _s.Row
        for r in c.execute("SELECT board_name, structures, lore, last_active "
                           "FROM board_state ORDER BY board_name"):
            structures = _j.loads(r["structures"] or "[]")
            lore = _j.loads(r["lore"] or "[]")
            locations.append({
                "name": r["board_name"],
                "description": (lore[-1]["event"] if lore
                                else "No events recorded here yet."),
                "structures": len(structures),
                "last_active": r["last_active"] or "",
            })
        c.close()
    except Exception:
        pass

    # the cartographer knows places the boards table does not
    try:
        from temple.cartographer import get_discovered_world
        known = {l["name"] for l in locations}
        for name, info in (get_discovered_world() or {}).items():
            if name in known or not isinstance(info, dict):
                continue
            locations.append({
                "name": name,
                "description": info.get("description", "") or info.get("terrain", ""),
                "structures": 0,
                "discovered": bool(info.get("discovered")),
            })
    except Exception:
        pass

    # businesses - the company registry
    try:
        from temple.registry import list_companies
        for co in list_companies():
            businesses.append({
                "name": co.get("name", ""),
                "description": co.get("description", ""),
                "status": co.get("status", ""),
                "model": co.get("model", ""),
                "reports": co.get("report_count", 0),
            })
    except Exception:
        pass

    # venues - the forum's own boards
    try:
        c = _s.connect(str(forumdb), timeout=20)
        c.row_factory = _s.Row
        for r in c.execute("SELECT * FROM boards ORDER BY id"):
            d = dict(r)
            venues.append({
                "name": d.get("name") or d.get("board") or "",
                "description": d.get("description", ""),
            })
        c.close()
    except Exception:
        pass

    # projects - build work grouped by the site it belongs to
    try:
        c = _s.connect(str(soul), timeout=20)
        c.row_factory = _s.Row
        rows = c.execute(
            "SELECT domain_id, COUNT(*) n, SUM(progress) done, "
            "SUM(target_progress) target, COUNT(DISTINCT spark_name) hands "
            "FROM ambitions WHERE ambition_type='build' AND resolved=0 "
            "AND domain_id IS NOT NULL AND domain_id != '' "
            "GROUP BY domain_id ORDER BY n DESC LIMIT 40").fetchall()
        for r in rows:
            projects.append({
                "name": r["domain_id"],
                "description": ("%d hands on %d builds - %d of %d steps done"
                                % (r["hands"], r["n"], r["done"] or 0,
                                   r["target"] or 0)),
                "hands": r["hands"],
                "builds": r["n"],
            })
        c.close()
    except Exception:
        pass

    return {
        "locations": locations, "businesses": businesses,
        "venues": venues, "projects": projects,
        "counts": {"locations": len(locations), "businesses": len(businesses),
                   "venues": len(venues), "projects": len(projects)},
    }



# ── SillyTavern character cards ────────────────────────────────
CARDS_DIR = BASE / "cards"


@app.get("/cards")
def cards_index():
    """Every spark's V2 character card, by name."""
    import json as _j
    idx = CARDS_DIR / "_index.json"
    if not idx.exists():
        return {"count": 0, "cards": [], "error": "no cards built yet"}
    return _j.loads(idx.read_text())


@app.get("/cards/{name}")
def card_get(name: str):
    """One spark's V2 card, ready to import into SillyTavern."""
    import json as _j
    import re as _re
    safe = _re.sub(r"[^A-Za-z0-9._ -]", "_", name)
    p = CARDS_DIR / (safe + ".json")
    if not p.exists():
        raise HTTPException(404, "no card for %s" % name)
    return _j.loads(p.read_text())



@app.get("/lexicon")
def lexicon_all(board: str = "", limit: int = 400):
    """Words that belong to a place rather than to the language."""
    import sqlite3 as _s
    p = BASE / "temple" / "lexicon.db"
    if not p.exists():
        return {"words": [], "note": "no lexicon yet"}
    c = _s.connect(str(p), timeout=20)
    c.row_factory = _s.Row
    if board:
        rs = c.execute("SELECT * FROM lexicon WHERE board=? ORDER BY speakers "
                       "DESC, uses DESC LIMIT ?", (board, limit)).fetchall()
    else:
        rs = c.execute("SELECT * FROM lexicon ORDER BY speakers DESC, uses DESC "
                       "LIMIT ?", (limit,)).fetchall()
    tot = c.execute("SELECT COUNT(*) FROM lexicon").fetchone()[0]
    boards = [dict(r) for r in c.execute(
        "SELECT board, COUNT(*) n FROM lexicon GROUP BY board ORDER BY n DESC")]
    c.close()
    return {"total": tot, "by_place": boards, "words": [dict(r) for r in rs]}


if __name__ == "__main__":
    host = os.environ.get("UAI_HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=int(os.environ.get("UAI_PORT", "8910")))
