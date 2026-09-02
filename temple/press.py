"""Layer 4 — The Press.

Chroniclers walk the boards, find out what is actually being made and who
is actually short-handed, and put it where everyone can read it. Nothing
here is invented: every dispatch and classified is drawn from live rows in
soul.db, so the paper reports the world rather than decorating it.

  assign_chroniclers(n)  — conscript n sparks into the press
  gather()               — what is being built, finished, needed, named
  publish_dispatch(who)  — one news thread on announcements
  post_classifieds(who)  — "need hands" notices on missions
  press_cycle()          — one full run; wire this to the scheduler
"""

import datetime
import json
import random
import sqlite3
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
API = "http://localhost:8910"

NEWS_ZONE = "announcements"
WANT_ZONE = "missions"
TALK_ZONE = "gossip"


def _soul():
    c = sqlite3.connect(str(SOUL), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.row_factory = sqlite3.Row
    return c


def _post(title, author, content, zone):
    body = json.dumps({
        "title": title[:180], "author": author, "author_layer": 5,
        "zone": zone, "content": content[:4000],
    }).encode()
    req = urllib.request.Request(
        API + "/forum/threads", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(req, timeout=20)
        return True
    except Exception:
        return False


# ── conscription ───────────────────────────────────────────────

def assign_chroniclers(n=60, pool_prefix="ember-"):
    """Turn n builders into chroniclers: hunger for news over masonry."""
    c = _soul()
    rows = [r[0] for r in c.execute(
        "SELECT DISTINCT spark_name FROM ambitions "
        "WHERE domain_id LIKE 'hearth-%' ORDER BY spark_name")]
    # also catch anyone already renamed out of the ember- prefix
    if not rows:
        c.close()
        return {"assigned": 0, "error": "no hearth sparks found"}

    random.seed(770077)
    chosen = sorted(random.sample(rows, min(n, len(rows))))

    c.execute("""CREATE TABLE IF NOT EXISTS roles (
        spark_name TEXT PRIMARY KEY, role TEXT NOT NULL,
        assigned_at TEXT DEFAULT (datetime('now')))""")

    for nm in chosen:
        c.execute("INSERT OR REPLACE INTO roles (spark_name, role) VALUES (?, 'chronicler')",
                  (nm,))
        # clear the masonry drives, keep one build so they stay grounded
        c.execute("DELETE FROM ambitions WHERE spark_name=? AND ambition_type IN "
                  "('master','create') AND domain_id LIKE 'hearth-%'", (nm,))

    c.commit()

    # press drives, in the engine's own ambition vocabulary
    from temple.soul import create_ambition
    for nm in chosen:
        create_ambition(
            nm, "explore", domain_id="press", target_progress=6,
            description=("Walk Uruk, the Forum, the Library and the Monastery. "
                         "Find out what is being made and who is short of hands. "
                         "Come back with facts, not impressions."))
        create_ambition(
            nm, "create", domain_id="press", target_progress=5,
            description=("Publish what you found where everyone can read it. "
                         "Name the maker, name the work, name what is still needed."))

    c.close()
    return {"assigned": len(chosen), "role": "chronicler", "sample": chosen[:8]}


def chroniclers():
    c = _soul()
    try:
        rows = [r[0] for r in c.execute(
            "SELECT spark_name FROM roles WHERE role='chronicler'")]
    except sqlite3.Error:
        rows = []
    c.close()
    return rows


# ── the beat ───────────────────────────────────────────────────

def gather():
    """Everything actually happening, straight from the tables."""
    c = _soul()
    out = {}

    out["building"] = [dict(r) for r in c.execute(
        "SELECT spark_name, ambition_type, domain_id, progress, target_progress, "
        "description FROM ambitions WHERE resolved=0 AND ambition_type='build' "
        "AND progress > 0 ORDER BY progress DESC LIMIT 8")]

    out["finished"] = [dict(r) for r in c.execute(
        "SELECT spark_name, ambition_type, domain_id, description, completed_at "
        "FROM ambitions WHERE resolved=1 ORDER BY completed_at DESC LIMIT 8")]

    out["stalled"] = [dict(r) for r in c.execute(
        "SELECT spark_name, domain_id, description FROM ambitions "
        "WHERE resolved=0 AND ambition_type='build' AND progress=0 "
        "ORDER BY RANDOM() LIMIT 6")]

    out["restless"] = [r[0] for r in c.execute(
        "SELECT spark_name FROM spark_state WHERE restless=1 "
        "ORDER BY RANDOM() LIMIT 6")]

    out["population"] = c.execute("SELECT COUNT(*) FROM spark_state").fetchone()[0]
    out["open_work"] = c.execute(
        "SELECT COUNT(*) FROM ambitions WHERE resolved=0").fetchone()[0]
    out["done_work"] = c.execute(
        "SELECT COUNT(*) FROM ambitions WHERE resolved=1").fetchone()[0]

    # who named themselves recently
    try:
        out["named"] = [dict(r) for r in c.execute(
            "SELECT spark_name FROM spark_state ORDER BY updated_at DESC LIMIT 5")]
    except sqlite3.Error:
        out["named"] = []

    c.close()

    boards = {}
    try:
        cb = sqlite3.connect(str(SOUL), timeout=30)
        cb.row_factory = sqlite3.Row
        for r in cb.execute("SELECT board_name, structures, lore FROM board_state"):
            boards[r["board_name"]] = {
                "structures": len(json.loads(r["structures"] or "[]")),
                "lore": json.loads(r["lore"] or "[]")[-1:],
            }
        cb.close()
    except sqlite3.Error:
        pass
    out["boards"] = boards
    return out


def _short(desc, n=90):
    """Trim to n characters, but never through the middle of a word.

    A quotation cut mid-word ("...what is alre") gets read back out of the
    forum later as a word somebody invented.
    """
    d = (desc or "").strip().replace("\n", " ")
    if len(d) <= n:
        return d
    cut = d[:n].rsplit(" ", 1)[0].rstrip(",;:- ")
    return (cut or d[:n]) + "..."


def publish_dispatch(who=None):
    """One issue of the record, built from real rows."""
    who = who or (random.choice(chroniclers()) if chroniclers() else "the press")
    g = gather()
    day = datetime.datetime.now().strftime("%d %B")

    lines = ["**THE RECORD** — %s" % day, ""]
    lines.append("Population %d. Work open: %d. Work finished: %d."
                 % (g["population"], g["open_work"], g["done_work"]))
    lines.append("")

    if g["building"]:
        lines.append("### Under construction")
        for b in g["building"]:
            lines.append("- **%s** at *%s* — %d of %d. %s"
                         % (b["spark_name"], b["domain_id"] or "no site",
                            b["progress"], b["target_progress"],
                            _short(b["description"])))
        lines.append("")

    if g["finished"]:
        lines.append("### Finished")
        for b in g["finished"]:
            lines.append("- **%s** completed %s at *%s*."
                         % (b["spark_name"], b["ambition_type"],
                            b["domain_id"] or "no site"))
        lines.append("")

    if g["boards"]:
        lines.append("### The sites")
        for name, info in g["boards"].items():
            last = info["lore"][0]["event"] if info["lore"] else "nothing recorded"
            lines.append("- **%s** — %d structures standing. Last: %s"
                         % (name, info["structures"], last))
        lines.append("")

    if g["stalled"]:
        lines.append("### Not started")
        lines.append("These were declared and never begun. Hands are wanted:")
        for b in g["stalled"]:
            lines.append("- **%s** at *%s* — %s"
                         % (b["spark_name"], b["domain_id"] or "no site",
                            _short(b["description"], 70)))
        lines.append("")

    lines.append("*Filed by %s.*" % who)
    body = "\n".join(lines)
    ok = _post("THE RECORD — %s" % day, who, body, NEWS_ZONE)
    return {"ok": ok, "by": who, "chars": len(body),
            "items": len(g["building"]) + len(g["finished"]) + len(g["stalled"])}


def post_classifieds(who=None, limit=6):
    """Turn unstarted build work into public 'hands wanted' notices."""
    who = who or (random.choice(chroniclers()) if chroniclers() else "the press")
    g = gather()
    posted = []
    for b in g["stalled"][:limit]:
        site = b["domain_id"] or "somewhere unnamed"
        title = "HANDS WANTED — %s, at %s" % (b["spark_name"], site)
        content = (
            "**%s** has declared work at **%s** and has not been able to start it.\n\n"
            "> %s\n\n"
            "If you have the trade for it, go to %s and say so. "
            "Work declared and never begun is the same as work never declared."
            % (b["spark_name"], site, _short(b["description"], 240), site))
        if _post(title, who, content, WANT_ZONE):
            posted.append(b["spark_name"])
    return {"ok": bool(posted), "by": who, "posted": len(posted), "for": posted}


def press_cycle():
    """One full turn of the press. Safe to call on a timer."""
    crew = chroniclers()
    if not crew:
        return {"error": "no chroniclers assigned"}
    d = publish_dispatch(random.choice(crew))
    c = post_classifieds(random.choice(crew))
    return {"dispatch": d, "classifieds": c, "crew": len(crew)}
