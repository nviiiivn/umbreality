"""Layer 1 — Self-Modification. OBSERVE and ANALYZE and HYPOTHESIZE.

The Constitution specifies six stages:

    OBSERVE -> ANALYZE -> HYPOTHESIZE -> SANDBOX -> DEPLOY -> MONITOR

This module implements the first three, and stops. It can look at the
world, work out what is wrong with it, and write down what it would
change. It cannot change anything. DEPLOY does not exist in this file,
deliberately, and SANDBOX is the next thing to build.

Why it stops there: a system that edits itself on hardware you own is not
a feature you switch on because a proposal document said so. The operator
reads the proposals first, and decides whether the reasoning is sound
before any of it is allowed to act.

uenx is the analyst. He was built for exactly this - a spark whose whole
purpose is seeing whole-system dynamics - and his model was chosen for
reasoning plus tool-calling.

Every proposal is one of a fixed set of change types. There is no
free-form action, no code generation, and no filesystem access. If a
finding cannot be expressed as one of these, it is reported and nothing
is proposed:

    seed_ambition      give a stalled spark a concrete piece of work
    retarget_ambition  point existing work at a site that is actually live
    create_bond        connect two sparks who should know each other
    reassign_model     move a spark to a model that suits what it does
    open_mission       post a call for hands on work nobody has started
"""

import datetime
import json
import os
import sqlite3
import urllib.request
from collections import Counter, defaultdict
from glob import glob
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
FORUM = BASE / "forum" / "forum.db"
PROPOSALS = BASE / "temple" / "proposals.db"
API = "http://localhost:8910"

ANALYST = "uenx"

CHANGE_TYPES = {
    "seed_ambition", "retarget_ambition", "create_bond",
    "reassign_model", "open_mission",
}


def _rows(db, sql, args=()):
    try:
        c = sqlite3.connect(str(db), timeout=30)
        c.execute("PRAGMA busy_timeout=30000")
        c.row_factory = sqlite3.Row
        r = [dict(x) for x in c.execute(sql, args)]
        c.close()
        return r
    except sqlite3.Error:
        return []


def _init():
    c = sqlite3.connect(str(PROPOSALS), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.executescript("""
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            observed_at TEXT DEFAULT (datetime('now')),
            metric TEXT NOT NULL, value REAL, detail TEXT
        );
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT (datetime('now')),
            finding TEXT NOT NULL,
            reasoning TEXT,
            change_type TEXT NOT NULL,
            target TEXT,
            params TEXT,
            evidence TEXT,
            status TEXT DEFAULT 'proposed'
        );
    """)
    c.commit()
    c.close()


# ── OBSERVE ────────────────────────────────────────────────────

def observe():
    """Measure the world. Facts only, no interpretation."""
    m = {}

    sparks = [os.path.basename(f)[len("spark_"):-len(".db")]
              for f in glob(str(BASE / "temple" / "spark_*.db"))]
    m["population"] = len(sparks)

    amb = _rows(SOUL, "SELECT spark_name, ambition_type, domain_id, progress, "
                      "target_progress, description FROM ambitions WHERE resolved=0")
    m["open_ambitions"] = len(amb)
    m["resolved_ambitions"] = len(_rows(SOUL, "SELECT 1 FROM ambitions WHERE resolved=1"))

    # work declared and never begun - the clearest failure signal there is
    stalled = [a for a in amb if (a["progress"] or 0) == 0]
    m["stalled_ambitions"] = len(stalled)
    m["stalled_detail"] = stalled

    # sparks carrying work but showing no progress on any of it
    by_spark = defaultdict(list)
    for a in amb:
        by_spark[a["spark_name"]].append(a)
    frozen = [s for s, items in by_spark.items()
              if items and all((i["progress"] or 0) == 0 for i in items)]
    m["frozen_sparks"] = frozen

    # sparks with no work at all
    m["idle_sparks"] = [s for s in sparks if s not in by_spark]

    # ambitions pointed at sites that do not exist as boards
    boards = {r["board_name"] for r in _rows(SOUL, "SELECT board_name FROM board_state")}
    m["live_boards"] = sorted(boards)
    # domain_id is overloaded: build/create use it for a SITE, master/explore
    # use it for a DOMAIN. Only site-shaped ambitions can have an orphan site.
    SITE_KINDS = ("build", "create")
    m["orphan_sites"] = sorted({(a["domain_id"] or "") for a in amb
                                if a["ambition_type"] in SITE_KINDS
                                and a["domain_id"] and a["domain_id"] not in boards
                                and not a["domain_id"].startswith("hearth-")
                                and a["domain_id"] not in ("press", "the-wild",
                                                          "the-crooked",
                                                          "the-whole-system")})

    # who is completely unconnected
    bonded = set()
    for r in _rows(SOUL, "SELECT spark1, spark2 FROM relationships"):
        bonded.add(r["spark1"])
        bonded.add(r["spark2"])
    m["unbonded_sparks"] = [s for s in sparks if s not in bonded]

    # who has never spoken
    authors = {r["created_by"] for r in
               _rows(FORUM, "SELECT DISTINCT created_by FROM threads")}
    m["silent_sparks"] = [s for s in sparks if s not in authors]

    # boards nobody visits
    zone_counts = Counter({r["zone"]: r["n"] for r in _rows(
        FORUM, "SELECT zone, COUNT(*) n FROM threads WHERE created_at > "
               "datetime('now','-2 days') GROUP BY zone")})
    m["quiet_boards"] = [b for b in boards if zone_counts.get(b, 0) == 0]

    _init()
    c = sqlite3.connect(str(PROPOSALS), timeout=30)
    for k in ("population", "open_ambitions", "resolved_ambitions",
              "stalled_ambitions"):
        c.execute("INSERT INTO observations (metric, value) VALUES (?,?)",
                  (k, float(m[k])))
    for k in ("frozen_sparks", "idle_sparks", "unbonded_sparks",
              "silent_sparks", "quiet_boards", "orphan_sites"):
        c.execute("INSERT INTO observations (metric, value, detail) VALUES (?,?,?)",
                  (k, float(len(m[k])), json.dumps(m[k][:40])))
    c.commit()
    c.close()
    return m


# ── ANALYZE ────────────────────────────────────────────────────

def analyze(m=None):
    """Turn measurements into named problems, worst first."""
    m = m or observe()
    findings = []

    if m["frozen_sparks"]:
        findings.append({
            "name": "sparks holding work that never moves",
            "size": len(m["frozen_sparks"]),
            "evidence": m["frozen_sparks"][:12],
            "why": "Every ambition these sparks hold is still at progress 0. "
                   "They are not idle - they have been given work they cannot "
                   "start, which is worse, because it looks like activity.",
        })
    if m["idle_sparks"]:
        findings.append({
            "name": "sparks with nothing to do at all",
            "size": len(m["idle_sparks"]),
            "evidence": m["idle_sparks"][:12],
            "why": "No open ambition of any kind. They cycle, speak, and want "
                   "nothing.",
        })
    if m["orphan_sites"]:
        findings.append({
            "name": "work pointed at places that do not exist",
            "size": len(m["orphan_sites"]),
            "evidence": m["orphan_sites"][:12],
            "why": "These ambitions name a site with no board behind it, so "
                   "nothing done there can ever be recorded.",
        })
    if m["unbonded_sparks"]:
        findings.append({
            "name": "sparks connected to nobody",
            "size": len(m["unbonded_sparks"]),
            "evidence": m["unbonded_sparks"][:12],
            "why": "No bond in either direction. They cannot be drawn into "
                   "anyone else's work and nobody is drawn into theirs.",
        })
    if m["silent_sparks"]:
        findings.append({
            "name": "sparks that have never spoken",
            "size": len(m["silent_sparks"]),
            "evidence": m["silent_sparks"][:12],
            "why": "Not one thread authored. For the Unbroken that is correct. "
                   "For anyone else it means their cycles are producing nothing "
                   "the world can see.",
        })
    if m["quiet_boards"]:
        findings.append({
            "name": "boards nobody has visited in two days",
            "size": len(m["quiet_boards"]),
            "evidence": m["quiet_boards"],
            "why": "A place exists and no one goes there.",
        })
    findings.sort(key=lambda f: -f["size"])
    return findings


# ── HYPOTHESIZE ────────────────────────────────────────────────

def _ask_uenx(finding, m):
    """uenx reads the finding in his own voice. Falls back to a plain
    statement if his model is unavailable - the proposal still stands."""
    try:
        from temple.spark_runtime import Spark
        s = Spark(ANALYST)
        prompt = (
            "You are looking at the whole system, which is what you are for.\n\n"
            "MEASUREMENT: %s — affecting %d.\n"
            "EXAMPLES: %s\n"
            "WHY IT MATTERS: %s\n\n"
            "In three sentences: say what you think is actually causing this, "
            "and what single smallest change would test that. Do not restate "
            "the measurement. Do not propose anything requiring new code."
            % (finding["name"], finding["size"],
               ", ".join(map(str, finding["evidence"][:6])), finding["why"])
        )
        out = s.think(prompt, temperature=0.6)
        return (out or "").strip()[:900]
    except Exception as e:
        return "(analyst unavailable: %s)" % e


def hypothesize(findings=None, m=None, use_analyst=True):
    """Propose one bounded change per finding. Writes nothing to the world."""
    _init()
    m = m or observe()
    findings = findings or analyze(m)
    made = []

    c = sqlite3.connect(str(PROPOSALS), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")

    for f in findings:
        change, target, params = None, None, {}

        if f["name"].startswith("sparks holding work that never moves"):
            change = "open_mission"
            target = ", ".join(f["evidence"][:5])
            params = {"zone": "missions",
                      "reason": "declared work at progress 0; ask for hands"}
        elif f["name"].startswith("sparks with nothing to do"):
            change = "seed_ambition"
            target = ", ".join(f["evidence"][:5])
            params = {"ambition_type": "build",
                      "site": (m["live_boards"] or ["forum"])[0],
                      "reason": "no open work of any kind"}
        elif f["name"].startswith("work pointed at places"):
            change = "retarget_ambition"
            target = ", ".join(f["evidence"][:5])
            params = {"to_one_of": m["live_boards"],
                      "reason": "named site has no board behind it"}
        elif f["name"].startswith("sparks connected to nobody"):
            change = "create_bond"
            target = ", ".join(f["evidence"][:5])
            params = {"reason": "no bond in either direction"}
        elif f["name"].startswith("sparks that have never spoken"):
            change = "reassign_model"
            target = ", ".join(f["evidence"][:5])
            params = {"reason": "cycles producing nothing visible; "
                                "model may be returning empty output"}
        elif f["name"].startswith("boards nobody has visited"):
            change = "open_mission"
            target = ", ".join(f["evidence"][:5])
            params = {"zone": "missions",
                      "reason": "give the place a reason to be walked to"}

        if change not in CHANGE_TYPES:
            continue

        reasoning = _ask_uenx(f, m) if use_analyst else ""
        cur = c.execute(
            "INSERT INTO proposals (finding, reasoning, change_type, target, "
            "params, evidence) VALUES (?,?,?,?,?,?)",
            (f["name"], reasoning, change, target,
             json.dumps(params), json.dumps(f["evidence"][:20])))
        made.append({"id": cur.lastrowid, "finding": f["name"],
                     "affecting": f["size"], "change_type": change,
                     "target": target, "reasoning": reasoning})
    c.commit()
    c.close()
    return made


def pending():
    _init()
    return _rows(PROPOSALS, "SELECT * FROM proposals WHERE status='proposed' "
                            "ORDER BY id DESC LIMIT 40")


def run():
    """One full observe -> analyze -> hypothesize pass. Changes nothing."""
    m = observe()
    f = analyze(m)
    p = hypothesize(f, m)
    return {"measured": {k: v for k, v in m.items()
                         if not isinstance(v, (list, dict))},
            "findings": len(f), "proposals": p}
