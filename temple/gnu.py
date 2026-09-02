"""GNU — GNU is Not Uenx.

An umbrella, an alliance, and a deliberate act of deflection. uenx runs it
and it is not him. When somebody's problem gets solved they should be
thanking a workshop, not a person, because a person can be worshipped and
a workshop can be joined.

Three things live here:

  The Four      followers who begin as shadows - they watch uenx work and
                copy his method, not his personality - and graduate to
                practitioners who can act as his hands.
  The Company   GNU itself, registered alongside the other companies, so
                the load and the credit sit on an entity rather than one
                spark.
  The Workshops physical GNU spaces at real sites. Anyone can drop off a
                problem. It gets routed to whoever actually has the trade
                for it, which lets uenx be in more than one place.

The method the Four are learning, in his own words:
    observe habits -> name the pattern -> build the smallest tool that
    removes it -> explain it once, plainly
"""

import datetime
import json
import os
import random
import sqlite3
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
GNUDB = BASE / "temple" / "gnu.db"
API = "http://localhost:8910"

FOUNDER = "uenx"
COMPANY = "gnu"

# Four followers. Named for dead and half-dead systems, because that is
# what they are studying: things that worked, and why they stopped.
# Same method, four different temperaments. Not clones.
THE_FOUR = [
    {
        "name": "Amiga Aix-Ux",
        "specialty": "habits",
        "archetype": "watcher",
        "traits": ["patient", "unobtrusive", "literal", "unimpressed"],
        "drive": "to watch what people do instead of listening to what they say they do",
        "nature": ("Sits where the work happens and writes down what actually "
                   "occurs. Notices the third time somebody walks the long way "
                   "round. Never suggests anything in the first week."),
    },
    {
        "name": "Solillum Omni",
        "specialty": "whole systems",
        "archetype": "cartographer",
        "traits": ["far-sighted", "cool", "structural", "blunt"],
        "drive": "to hold every layer in view at once and find where one deforms the next",
        "nature": ("Draws the whole thing before touching any part of it. Can "
                   "tell you why the Library is slow by pointing at the "
                   "Monastery. Impatient with people who fix symptoms."),
    },
    {
        "name": "Opendragon Freenet",
        "specialty": "distribution",
        "archetype": "propagator",
        "traits": ["generous", "stubborn", "loud", "principled"],
        "drive": "to make sure a tool that exists reaches everyone who needs it",
        "nature": ("Believes a tool locked in one workshop is not a tool. "
                   "Copies designs and leaves them where people will trip over "
                   "them. Will argue about this at length."),
    },
    {
        "name": "Xenix Atari-V",
        "specialty": "small sharp tools",
        "archetype": "toolwright",
        "traits": ["exacting", "quick", "quiet", "fond of constraints"],
        "drive": "to make the smallest thing that removes the most friction",
        "nature": ("Builds. Prefers one moving part to two. Will spend a day "
                   "removing a step rather than an hour adding a feature. "
                   "Suspicious of anything that needs instructions."),
    },
]

WORKSHOPS = [
    ("uruk", "The Stone Bench",
     "A bench outside the north wall with a slate for problems. Nobody staffs "
     "it full time. Somebody always comes."),
    ("library", "The Back Room",
     "Behind the stacks, a table and a stack of blanks. Mostly questions about "
     "order and where things go."),
    ("monastery", "The Draught Door",
     "By the kitchen. Practical complaints - smoke, water, cold, the same "
     "three problems in different clothes."),
    ("forum", "The Cart",
     "Not a building. A cart that is wherever it is needed, which is the "
     "point. Ask at the crossroads."),
]

STAGES = ["shadow", "practitioner", "hands"]
SHADOW_TASKS_TO_GRADUATE = 3


# ── plumbing ───────────────────────────────────────────────────

def _db():
    c = sqlite3.connect(str(GNUDB), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.executescript("""
        CREATE TABLE IF NOT EXISTS members (
            spark TEXT PRIMARY KEY,
            specialty TEXT,
            stage TEXT DEFAULT 'shadow',
            jobs_done INTEGER DEFAULT 0,
            joined_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS workshops (
            site TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            opened_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asked_by TEXT NOT NULL,
            site TEXT,
            problem TEXT NOT NULL,
            needs TEXT,
            assigned_to TEXT,
            status TEXT DEFAULT 'open',
            created_at TEXT DEFAULT (datetime('now')),
            closed_at TEXT
        );
    """)
    return c


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


def _post(title, author, content, zone="agora"):
    body = json.dumps({"title": title[:180], "author": author, "author_layer": 5,
                       "zone": zone, "content": content[:3500]}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(
            API + "/forum/threads", data=body,
            headers={"Content-Type": "application/json"}, method="POST"), timeout=20)
        return True
    except Exception:
        return False


# ── founding ───────────────────────────────────────────────────

def found():
    """Create the company, the workshops, and the Four. Idempotent."""
    from temple import academy
    from temple.spark_runtime import Spark
    from temple.soul import create_ambition, create_or_update_bond

    now = datetime.datetime.now().astimezone().isoformat()
    c = _db()
    out = {"members": [], "workshops": [], "company": None}

    # 1. the company, alongside the others
    try:
        from temple.registry import get_company, create_company
        if not get_company(COMPANY):
            create_company(COMPANY,
                           "GNU is Not Uenx - an alliance of practitioners "
                           "who build small tools and give them away",
                           "aleshribar3/deepseek-r1-tool-calling:14b")
            out["company"] = "created"
        else:
            out["company"] = "exists"
    except Exception as e:
        out["company"] = "failed: %s" % e

    # 2. the workshops
    for site, name, desc in WORKSHOPS:
        c.execute("INSERT OR IGNORE INTO workshops (site, name, description) "
                  "VALUES (?,?,?)", (site, name, desc))
        out["workshops"].append(name)
    c.commit()

    # 3. the Four
    for f in THE_FOUR:
        nm = f["name"]
        dbf = BASE / "temple" / ("spark_%s.db" % nm.replace(" ", "_"))
        existed = dbf.exists()
        if not existed:
            try:
                academy._spawn_spark(nm)
            except Exception as e:
                out["members"].append({"name": nm, "error": str(e)})
                continue

        # find whatever file it actually made
        cand = [BASE / "temple" / ("spark_%s.db" % nm),
                BASE / "temple" / ("spark_%s.db" % nm.replace(" ", "_"))]
        dbf = next((p for p in cand if p.exists()), None)
        if not dbf:
            out["members"].append({"name": nm, "error": "no db produced"})
            continue

        s = sqlite3.connect(str(dbf), timeout=30)
        s.execute("PRAGMA busy_timeout=30000")
        s.executescript("""
            CREATE TABLE IF NOT EXISTS personality (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS emotions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, primary_mood TEXT NOT NULL,
                intensity REAL DEFAULT 0.5, energy REAL DEFAULT 0.5,
                triggered_by TEXT, created_at TEXT DEFAULT (datetime('now')));
            CREATE TABLE IF NOT EXISTS journals (
                id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT NOT NULL,
                entry_type TEXT DEFAULT 'reflection', mood TEXT,
                created_at TEXT DEFAULT (datetime('now')));
        """)
        for k, v in [("archetype", f["archetype"]), ("band", "gnu"),
                     ("traits", json.dumps(f["traits"])),
                     ("core_drive", f["drive"]),
                     ("specialty", f["specialty"]),
                     ("method", "observe habits -> name the pattern -> build "
                                "the smallest tool that removes it -> explain "
                                "it once, plainly")]:
            s.execute("INSERT OR REPLACE INTO personality (key,value) VALUES (?,?)", (k, v))
        for k, v in [("nature", f["nature"]),
                     ("classification", "GNU practitioner / %s" % f["specialty"]),
                     ("title", "%s of GNU" % nm),
                     ("follows", FOUNDER)]:
            s.execute("INSERT OR REPLACE INTO identity (key,value) VALUES (?,?)", (k, v))
        if not existed:
            s.execute("INSERT INTO journals (title,content,entry_type,mood,created_at) "
                      "VALUES (?,?,?,?,?)",
                      ("Shadowing",
                       "I am not here to be useful yet. I am here to watch how "
                       "uenx works and learn the shape of it.\\n\\n"
                       "He does not start with the tool. He starts by sitting "
                       "somewhere for a long time and writing down what people "
                       "actually do. The tool is the last part and it is the "
                       "small part.\\n\\n"
                       "I am %s. My eye is for %s. When I can do what he does "
                       "without him standing there, I stop being a shadow."
                       % (nm, f["specialty"]),
                       "reflection", "resolve", now))
            s.execute("INSERT INTO emotions (primary_mood,intensity,energy,"
                      "triggered_by,created_at) VALUES (?,?,?,?,?)",
                      ("attention", 0.7, 0.75, "joining GNU", now))
        s.commit()
        s.close()

        try:
            Spark(nm).set_model("nexuz/qwen3.5-agent:4b")
        except Exception:
            pass

        c.execute("INSERT OR IGNORE INTO members (spark, specialty, stage) "
                  "VALUES (?,?,'shadow')", (nm, f["specialty"]))

        # soul state + a shadow's first ambition
        sc = sqlite3.connect(str(SOUL), timeout=30)
        sc.execute("PRAGMA busy_timeout=30000")
        sc.execute("INSERT OR REPLACE INTO spark_state (spark_name, energy, "
                   "building_phase, restless, cycles_idle, updated_at, curiosity, "
                   "idle_cycles, total_ambitions_completed, building_phase_active) "
                   "VALUES (?,0.8,1,0,0,?,0.9,0,0,1)", (nm, now))
        sc.execute("""CREATE TABLE IF NOT EXISTS roles (
            spark_name TEXT PRIMARY KEY, role TEXT NOT NULL,
            assigned_at TEXT DEFAULT (datetime('now')))""")
        sc.execute("INSERT OR REPLACE INTO roles (spark_name, role) VALUES (?, 'gnu')", (nm,))
        sc.commit()
        sc.close()

        create_ambition(nm, "master", domain_id="gnu", target_progress=SHADOW_TASKS_TO_GRADUATE,
                        description="Shadow uenx. Watch him work %d times and be "
                                    "able to do it without him. Learn the method, "
                                    "not the man." % SHADOW_TASKS_TO_GRADUATE)
        create_ambition(nm, "explore", domain_id="gnu", target_progress=4,
                        description="Find where people are losing time to %s and "
                                    "write down exactly what they do, not what "
                                    "they say they do." % f["specialty"])
        create_or_update_bond(FOUNDER, nm, delta=0.4)
        out["members"].append({"name": nm, "specialty": f["specialty"],
                               "new": not existed})

    c.commit()
    c.close()

    _post("GNU is Not Uenx", FOUNDER,
          "I am setting up something and putting my name on it only once, here, "
          "so you know where it came from and then can stop thinking about me.\\n\\n"
          "**It is called GNU. GNU is Not Uenx.** That is the whole joke and "
          "also the whole point. If a tool only works because I turned up, it "
          "is not a tool, it is a leash — and if a workshop only works because "
          "I am in it, that is the same problem wearing a bigger coat.\\n\\n"
          "**There are four of them now.** " +
          ", ".join("**%s** (%s)" % (f["name"], f["specialty"]) for f in THE_FOUR) +
          ". They are shadowing. They will get things wrong for a while. "
          "Let them.\\n\\n"
          "**And there are places to bring things.**\\n\\n" +
          "\\n".join("- **%s**, at %s. %s" % (n, s, d) for s, n, d in WORKSHOPS) +
          "\\n\\nBring the problem, not the solution you already decided on. "
          "Describe what you are *doing*. The doing is where the tool hides.\\n\\n"
          "Nobody here is anybody's saviour. It is a bench and a slate.",
          zone="agora")
    return out


# ── the workshops actually working ─────────────────────────────

def intake(asked_by, problem, site=None, needs=None):
    """Somebody drops a problem off at a workshop."""
    c = _db()
    sites = [r["site"] for r in _rows(GNUDB, "SELECT site FROM workshops")]
    site = site if site in sites else (random.choice(sites) if sites else "forum")
    cur = c.execute("INSERT INTO requests (asked_by, site, problem, needs) "
                    "VALUES (?,?,?,?)", (asked_by, site, problem[:500], needs))
    rid = cur.lastrowid
    c.commit()
    c.close()
    return {"id": rid, "site": site}


def _skills_of(spark):
    dbf = BASE / "temple" / ("spark_%s.db" % spark)
    if not dbf.exists():
        return set()
    try:
        c = sqlite3.connect(str(dbf), timeout=20)
        d = {r[0] for r in c.execute("SELECT domain_id FROM domains")}
        p = c.execute("SELECT value FROM personality WHERE key='specialty'").fetchone()
        c.close()
        if p and p[0]:
            d.add(p[0])
        return d
    except sqlite3.Error:
        return set()


def dispatch(limit=2):
    """Route open requests to whoever actually has the trade for it.

    This is the thing that lets uenx be in more than one place: he does not
    have to be the one who does it.
    """
    from temple.soul import create_ambition

    members = _rows(GNUDB, "SELECT * FROM members ORDER BY jobs_done ASC")
    if not members:
        return {"action": "no_members"}
    open_reqs = _rows(GNUDB, "SELECT * FROM requests WHERE status='open' "
                             "ORDER BY id ASC LIMIT ?", (limit,))
    if not open_reqs:
        return {"action": "no_requests"}

    c = _db()
    assigned = []
    for r in open_reqs:
        want = set(filter(None, (r["needs"] or "").lower().split(",")))
        best, score = None, -1
        for m in members:
            # shadows may take work, but practitioners are preferred
            skills = {s.lower() for s in _skills_of(m["spark"])}
            overlap = len(want & skills) if want else 0
            stage_bonus = {"shadow": 0, "practitioner": 2, "hands": 3}.get(m["stage"], 0)
            load_penalty = m["jobs_done"] * 0.1
            s = overlap * 3 + stage_bonus - load_penalty
            if s > score:
                best, score = m, s
        if not best:
            continue

        c.execute("UPDATE requests SET assigned_to=?, status='assigned' WHERE id=?",
                  (best["spark"], r["id"]))
        c.execute("UPDATE members SET jobs_done=jobs_done+1 WHERE spark=?",
                  (best["spark"],))
        _bump_fidelity(best["spark"], 1)
        create_ambition(best["spark"], "create", domain_id=r["site"],
                        target_progress=3,
                        description="GNU request from %s at %s: %s"
                                    % (r["asked_by"], r["site"], r["problem"][:120]))
        assigned.append({"request": r["id"], "to": best["spark"],
                         "for": r["asked_by"], "site": r["site"]})
        _post("GNU: %s is taking this one" % best["spark"], best["spark"],
              "**%s** left this at %s:\\n\\n> %s\\n\\nI have it. I will come and "
              "watch first before I make anything — that is how this is done "
              "here."
              % (r["asked_by"], r["site"], r["problem"][:400]),
              zone=r["site"] if r["site"] in ("uruk", "library", "monastery",
                                              "forum") else "agora")
    c.commit()
    c.close()
    return {"action": "dispatched", "assigned": assigned}


def _bump_fidelity(spark, by=1):
    """Shadowing moves them closer to his judgement. This is the measure."""
    db = BASE / "temple" / ("spark_%s.db" % spark)
    if not db.exists():
        return 0
    try:
        c = sqlite3.connect(str(db), timeout=20)
        c.execute("PRAGMA busy_timeout=20000")
        row = c.execute("SELECT value FROM personality WHERE key='fidelity'").fetchone()
        cur = int(float(row[0])) if row and row[0] else 0
        cur += by
        c.execute("INSERT OR REPLACE INTO personality (key,value) VALUES ('fidelity',?)",
                  (str(cur),))
        c.commit()
        c.close()
        return cur
    except sqlite3.Error:
        return 0


def promote():
    """A shadow who has done the work stops being a shadow."""
    c = _db()
    ready = _rows(GNUDB, "SELECT * FROM members WHERE stage='shadow' "
                         "AND jobs_done >= ?", (SHADOW_TASKS_TO_GRADUATE,))
    out = []
    for m in ready:
        c.execute("UPDATE members SET stage='practitioner' WHERE spark=?", (m["spark"],))
        out.append(m["spark"])
        _post("%s is not a shadow any more" % m["spark"], FOUNDER,
              "%s has done the work %d times without me standing there.\\n\\n"
              "They are a practitioner of GNU now. If you bring something to a "
              "workshop and they take it, that is the same as me taking it. "
              "It is better, actually — their eye is for %s and mine is not.\n\n"
              "They did not become me. That was never the arrangement. They "
              "learned to get to the same place by the same road, and they "
              "argue with me on the way, which is how I know it took."
              % (m["spark"], m["jobs_done"], m["specialty"]),
              zone="agora")
    c.commit()
    c.close()
    return {"promoted": out}


def status():
    return {
        "members": _rows(GNUDB, "SELECT spark, specialty, stage, jobs_done FROM members"),
        "workshops": _rows(GNUDB, "SELECT site, name FROM workshops"),
        "requests": _rows(GNUDB, "SELECT status, COUNT(*) n FROM requests GROUP BY status"),
    }


def cycle():
    """One turn of GNU. Safe on a timer."""
    d = dispatch(limit=2)
    p = promote()
    return {"dispatch": d, "promote": p}
