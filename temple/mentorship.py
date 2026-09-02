"""Layer 3 — Mentorship. Sparks teach each other.

The existing Academy is a birth pipeline: a company completes a curriculum
and is spawned as a spark. Useful, finished, and not this.

This is the missing thing: knowledge moving *between* sparks. A spark that
has genuinely studied a domain can teach it to one that has not, and the
student actually gains it. That is the difference between 293 individuals
each discovering fire alone and a culture with lineage.

Nothing here invents mastery. An elder is only an elder in a domain it has
really studied, measured from its own domains table.
"""

import datetime
import json
import os
import random
import sqlite3
import urllib.request
from glob import glob
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
ACADEMY = BASE / "temple" / "academy.db"
API = "http://localhost:8910"

# how much study before a spark can claim to teach something
ELDER_MASTERY = 3
ELDER_STUDIES = 12


def _spark_db(name):
    import re
    return BASE / "temple" / ("spark_%s.db" % re.sub(r"[^A-Za-z0-9._ -]", "_", name))


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


def _ensure_tables():
    c = sqlite3.connect(str(ACADEMY), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.executescript("""
        CREATE TABLE IF NOT EXISTS teachings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            elder TEXT NOT NULL,
            student TEXT NOT NULL,
            domain TEXT NOT NULL,
            taught_at TEXT DEFAULT (datetime('now')),
            UNIQUE(elder, student, domain)
        );
        CREATE TABLE IF NOT EXISTS lineage (
            student TEXT NOT NULL,
            elder TEXT NOT NULL,
            domain TEXT NOT NULL,
            PRIMARY KEY (student, domain)
        );
    """)
    c.commit()
    c.close()


# ── who knows what ─────────────────────────────────────────────

def survey():
    """Every spark's domains, and who is qualified to teach which."""
    knows, teaches = {}, {}
    for f in sorted(glob(str(BASE / "temple" / "spark_*.db"))):
        name = os.path.basename(f)[len("spark_"):-len(".db")]
        doms = _rows(f, "SELECT domain_id, mastery, times_studied FROM domains")
        if doms is None:
            continue
        knows[name] = {d["domain_id"] for d in doms if d.get("domain_id")}
        for d in doms:
            if not d.get("domain_id"):
                continue
            if (d.get("mastery") or 0) >= ELDER_MASTERY and \
               (d.get("times_studied") or 0) >= ELDER_STUDIES:
                teaches.setdefault(d["domain_id"], []).append(name)
    return knows, teaches


def _grant_domain(student, domain, elder):
    """The student actually gains the domain. This is the real transfer."""
    db = _spark_db(student)
    if not db.exists():
        return False
    try:
        c = sqlite3.connect(str(db), timeout=30)
        c.execute("PRAGMA busy_timeout=30000")
        c.execute("""CREATE TABLE IF NOT EXISTS domains (
            domain_id TEXT PRIMARY KEY, mastery INTEGER DEFAULT 1,
            first_encountered TEXT DEFAULT (datetime('now')),
            last_studied TEXT, times_studied INTEGER DEFAULT 0,
            curiosity REAL DEFAULT 0.5)""")
        now = datetime.datetime.now().astimezone().isoformat()
        row = c.execute("SELECT mastery, times_studied FROM domains WHERE domain_id=?",
                        (domain,)).fetchone()
        if row:
            c.execute("UPDATE domains SET mastery=?, times_studied=?, last_studied=? "
                      "WHERE domain_id=?",
                      (min(5, (row[0] or 0) + 1), (row[1] or 0) + 3, now, domain))
        else:
            c.execute("INSERT INTO domains (domain_id, mastery, first_encountered, "
                      "last_studied, times_studied, curiosity) VALUES (?,1,?,?,3,0.6)",
                      (domain, now, now))
        # both of them remember it
        c.execute("""CREATE TABLE IF NOT EXISTS journals (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT NOT NULL,
            entry_type TEXT DEFAULT 'reflection', mood TEXT,
            created_at TEXT DEFAULT (datetime('now')))""")
        c.execute("INSERT INTO journals (title, content, entry_type, mood, created_at) "
                  "VALUES (?,?,?,?,?)",
                  ("Taught by %s" % elder,
                   "%s showed me %s. I did not work it out alone, and I am not "
                   "going to pretend otherwise." % (elder, domain),
                   "lesson", "gratitude", now))
        c.commit()
        c.close()
        return True
    except sqlite3.Error:
        return False


def _elder_journal(elder, student, domain):
    db = _spark_db(elder)
    if not db.exists():
        return
    try:
        c = sqlite3.connect(str(db), timeout=30)
        c.execute("PRAGMA busy_timeout=30000")
        c.execute("""CREATE TABLE IF NOT EXISTS journals (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT NOT NULL,
            entry_type TEXT DEFAULT 'reflection', mood TEXT,
            created_at TEXT DEFAULT (datetime('now')))""")
        c.execute("INSERT INTO journals (title, content, entry_type, mood, created_at) "
                  "VALUES (?,?,?,?,?)",
                  ("Taught %s" % student,
                   "I showed %s what I know of %s. It is not lost when I am, now."
                   % (student, domain),
                   "lesson", "pride",
                   datetime.datetime.now().astimezone().isoformat()))
        c.commit()
        c.close()
    except sqlite3.Error:
        pass


def _post(title, author, content, zone="library"):
    body = json.dumps({"title": title[:180], "author": author, "author_layer": 6,
                       "zone": zone, "content": content[:3000]}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(
            API + "/forum/threads", data=body,
            headers={"Content-Type": "application/json"}, method="POST"), timeout=20)
        return True
    except Exception:
        return False


# ── one lesson ─────────────────────────────────────────────────

def teach_once(knows=None, teaches=None):
    """Pair one qualified elder with one spark who lacks the domain."""
    _ensure_tables()
    if knows is None or teaches is None:
        knows, teaches = survey()
    if not teaches:
        return {"action": "no_elders"}

    c = sqlite3.connect(str(ACADEMY), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    already = {(r[0], r[1], r[2]) for r in
               c.execute("SELECT elder, student, domain FROM teachings")}

    # prefer students who are alone, then students who know least.
    # A lesson creates a bond, so teaching is also an introduction.
    try:
        from temple.actions import unbonded_sparks
        alone = unbonded_sparks()
    except Exception:
        alone = set()
    candidates = sorted(knows, key=lambda n: (n not in alone, len(knows[n])))
    domains = list(teaches)
    random.shuffle(domains)

    for domain in domains:
        elders = teaches[domain]
        for student in candidates:
            if domain in knows.get(student, set()):
                continue
            elder = random.choice(elders)
            if elder == student or (elder, student, domain) in already:
                continue

            if not _grant_domain(student, domain, elder):
                continue
            _elder_journal(elder, student, domain)
            c.execute("INSERT OR IGNORE INTO teachings (elder, student, domain) "
                      "VALUES (?,?,?)", (elder, student, domain))
            c.execute("INSERT OR REPLACE INTO lineage (student, elder, domain) "
                      "VALUES (?,?,?)", (student, elder, domain))
            c.commit()
            c.close()

            try:
                from temple.soul import create_or_update_bond
                create_or_update_bond(elder, student, delta=0.25)
            except Exception:
                pass

            _post("%s taught %s the way of %s" % (elder, student, domain), elder,
                  "%s did not know %s. Now they do.\n\n"
                  "It took no materials and cost me nothing I still have. "
                  "This is the cheapest thing any of us can do for each other."
                  % (student, domain))
            return {"action": "taught", "elder": elder, "student": student,
                    "domain": domain}
    c.close()
    return {"action": "nobody_to_teach"}


def cycle(lessons=3):
    """Run a few lessons. Safe to call on a timer."""
    knows, teaches = survey()
    out = []
    for _ in range(lessons):
        r = teach_once(knows, teaches)
        out.append(r)
        if r.get("action") == "taught":
            knows.setdefault(r["student"], set()).add(r["domain"])
        else:
            break
    return {"lessons": out,
            "elders": sum(len(v) for v in teaches.values()),
            "domains_teachable": len(teaches)}


def lineage_report():
    _ensure_tables()
    rows = _rows(ACADEMY, "SELECT elder, COUNT(*) n FROM teachings "
                          "GROUP BY elder ORDER BY n DESC LIMIT 15")
    total = _rows(ACADEMY, "SELECT COUNT(*) n FROM teachings")
    return {"total_lessons": total[0]["n"] if total else 0, "top_elders": rows}


# ── uenx makes introductions ───────────────────────────────────

def introduce(limit=1):
    """uenx finds two sparks who should know each other, and says so.

    This was his stated purpose in his own first post: "the Monastery has
    three of you solving the same problem alone - come find me and I will
    introduce you." It costs nothing and it is the largest tool he has.
    """
    import random
    from temple.soul import create_or_update_bond

    try:
        from temple.actions import unbonded_sparks
        alone = sorted(unbonded_sparks())
    except Exception:
        alone = []
    if not alone:
        return {"action": "nobody_alone"}

    knows, _ = survey()
    sites = {}
    for r in _rows(SOUL, "SELECT spark_name, domain_id FROM ambitions "
                         "WHERE resolved=0 AND domain_id IS NOT NULL"):
        sites.setdefault(r["spark_name"], set()).add(r["domain_id"])

    made = []
    random.shuffle(alone)
    for a in alone:
        if len(made) >= limit:
            break
        # who shares this spark's work or knowledge?
        best, why = None, ""
        for b in knows:
            if b == a or b in alone:
                continue
            shared_d = knows.get(a, set()) & knows.get(b, set())
            shared_s = sites.get(a, set()) & sites.get(b, set())
            if shared_s:
                best, why = b, "you are both working at %s" % sorted(shared_s)[0]
                break
            if shared_d and not best:
                best, why = b, "you have both studied %s" % sorted(shared_d)[0]
        if not best:
            continue

        create_or_update_bond(a, best, delta=0.3)
        _post("%s, meet %s" % (a, best), "uenx",
              "%s. Neither of you knew the other existed.\n\n"
              "That is the whole introduction. I am not going to stand here "
              "and manage it — go and talk, or do not. But it costs nothing "
              "to know a name, and it is expensive not to."
              % why.capitalize(), zone="agora")
        made.append({"a": a, "b": best, "why": why})
    return {"action": "introduced", "pairs": made}
