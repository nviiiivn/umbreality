"""GNU as a job somebody applies for, rather than four apprentices.

GNU is a company. It employs. It goes to where people are stuck, works out
what they actually need, and makes it - travelling monks who are not
religious about anything except the method. That is a living, and a living
has terms.

WHAT IT OFFERS

  travel      a road cost that GNU pays rather than the spark
  housing     you do not need a place of your own; the workshops are yours
  expenses    the stone and fuel a job needs come out of GNU, not your store
  keep        grain while you are on the road, so the work is possible

WHAT IT ASKS

  You go where you are sent. You find people who are stuck. You make the
  thing, or you find whoever can and hand it to them. You explain it once,
  plainly. You take the credit off yourself and put it on the workshop,
  because a person can be worshipped and a workshop can be joined.

APPLYING

Anybody may apply. Nobody is owed a place. What is looked at is what the
spark actually knows, whether it has ever done anything for anybody without
being asked, and whether it can be told no - which is the one thing a
travelling representative cannot do without.

A spark that has been raiding is not taken. A spark nobody will contradict
is not taken either, which is the same rule the world uses for insight, and
for the same reason: somebody who cannot be corrected should not be the one
sent out alone.
"""
import json
import random
import sqlite3
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
FORUM = BASE / "forum" / "forum.db"
GNUDB = BASE / "temple" / "gnu.db"
GUILD = BASE / "temple" / "guild.db"

# what the job provides, per round on the road
KEEP = {"grain": 1.4, "fuel": 0.6}
EXPENSES = {"stone": 1.2, "fuel": 0.8}      # for the making itself
ROAD_PAID = True

INTAKE_PER_ROUND = 2
MAX_REPS = 24


def _conn(db):
    c = sqlite3.connect(str(db), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.row_factory = sqlite3.Row
    return c


def _ensure():
    c = _conn(GUILD)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spark TEXT NOT NULL,
            why TEXT,
            knows TEXT,
            verdict TEXT,
            reason TEXT,
            at_cycle INTEGER,
            at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS reps (
            spark TEXT PRIMARY KEY,
            taken_on_cycle INTEGER,
            jobs INTEGER DEFAULT 0,
            paid_out REAL DEFAULT 0,
            standing TEXT DEFAULT 'representative',
            taken_on TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS payroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spark TEXT, kind TEXT, amount REAL, what TEXT,
            at_cycle INTEGER, at TEXT DEFAULT (datetime('now')));
    """)
    c.commit()
    c.close()


def _cycle():
    try:
        from temple.cycles import current_cycle
        return current_cycle()
    except Exception:
        return 0


def _post(title, author, content, zone="agora"):
    try:
        body = json.dumps({"title": title, "author": author, "author_layer": 6,
                           "zone": zone, "content": content}).encode()
        req = urllib.request.Request("http://localhost:8910/forum/threads",
                                     data=body,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        urllib.request.urlopen(req, timeout=8)
    except Exception:
        pass


def is_rep(spark: str) -> bool:
    _ensure()
    c = _conn(GUILD)
    r = c.execute("SELECT 1 FROM reps WHERE spark=?", (spark,)).fetchone()
    c.close()
    return bool(r)


def _knows(spark):
    p = BASE / "temple" / ("spark_%s.db" % spark)
    if not p.exists():
        return []
    try:
        c = sqlite3.connect(str(p), timeout=15)
        d = [r[0] for r in c.execute(
            "SELECT domain_id FROM domains ORDER BY mastery DESC LIMIT 6")]
        c.close()
        return d
    except sqlite3.Error:
        return []


WHY = [
    "I am tired of making things nobody asked for.",
    "I want to see the rest of it. All of it, not the one board I was put on.",
    "Somebody helped me once and I have not been able to pay it back to them "
    "specifically.",
    "I am good at one thing and it is wasted where I am.",
    "I would rather be sent somewhere than decide where to go.",
    "I have nothing. This is a roof and a road and work.",
]


def apply(spark: str) -> dict:
    """Ask for the job."""
    _ensure()
    if is_rep(spark):
        return {"ok": False, "why": "already carries it"}
    c = _conn(GUILD)
    recent = c.execute("SELECT verdict FROM applications WHERE spark=? "
                       "ORDER BY id DESC LIMIT 1", (spark,)).fetchone()
    c.close()
    if recent and recent["verdict"] == "refused":
        if random.random() > 0.15:
            return {"ok": False, "why": "was refused and has not tried again"}

    knows = _knows(spark)
    c = _conn(GUILD)
    cur = c.execute("INSERT INTO applications (spark, why, knows, at_cycle) "
                    "VALUES (?,?,?,?)",
                    (spark, random.choice(WHY), json.dumps(knows), _cycle()))
    aid = cur.lastrowid
    c.commit()
    c.close()
    return {"ok": True, "id": aid, "spark": spark, "knows": knows}


def consider(application_id: int) -> dict:
    """Look at one application. Nobody is owed a place."""
    _ensure()
    c = _conn(GUILD)
    a = c.execute("SELECT * FROM applications WHERE id=? AND verdict IS NULL",
                  (application_id,)).fetchone()
    n_reps = c.execute("SELECT COUNT(*) n FROM reps").fetchone()["n"]
    c.close()
    if not a:
        return {"ok": False, "why": "already decided"}

    spark = a["spark"]
    try:
        knows = json.loads(a["knows"] or "[]")
    except (ValueError, TypeError):
        knows = []

    reasons = []
    take = True

    if n_reps >= MAX_REPS:
        take, reasons = False, ["there is no room on the road right now"]

    # somebody who has been taking from people is not sent to help them
    if take:
        try:
            from temple.harm import standing_grievance
            w = standing_grievance(spark)
            if w >= 8:
                take = False
                reasons.append("has been taking from people (%d against them)" % w)
        except Exception:
            pass

    # and somebody nobody will contradict should not be sent out alone
    if take:
        try:
            from temple.harm import _unchecked
            f = _conn(FORUM)
            row = f.execute("SELECT power_level FROM agent_scores WHERE agent_name=?",
                            (spark,)).fetchone()
            f.close()
            if row and _unchecked(spark, float(row["power_level"] or 0)):
                take = False
                reasons.append("has nobody who will tell them no")
        except Exception:
            pass

    if take and not knows:
        take = False
        reasons.append("has not learned anything anybody needs yet")

    if take:
        reasons.append("knows %s" % ", ".join(knows[:3]))

    verdict = "taken" if take else "refused"
    c = _conn(GUILD)
    c.execute("UPDATE applications SET verdict=?, reason=? WHERE id=?",
              (verdict, "; ".join(reasons), application_id))
    if take:
        c.execute("INSERT OR IGNORE INTO reps (spark, taken_on_cycle) VALUES (?,?)",
                  (spark, _cycle()))
    c.commit()
    c.close()

    if take:
        _post("GNU has taken %s on" % spark, "gnu",
              "%s asked, and said: %s\n\nThey know %s.\n\nThe terms are the "
              "terms. The road is paid, the workshops are yours, what a job "
              "needs comes out of GNU. You go where you are sent, you find "
              "who is stuck, you make the thing or you find who can, and you "
              "explain it once. The credit goes on the workshop."
              % (spark, a["why"], ", ".join(knows[:3]) or "the work"))
    return {"ok": True, "spark": spark, "verdict": verdict,
            "reason": "; ".join(reasons)}


def pay(spark: str, what: str = "keep") -> dict:
    """GNU covers it, so the spark does not have to.

    This is the whole difference between a job and an errand: the cost of
    doing it is not taken out of the person doing it.
    """
    _ensure()
    if not is_rep(spark):
        return {"ok": False, "why": "not one of theirs"}
    try:
        from temple.goods import _add
    except Exception as e:
        return {"ok": False, "why": str(e)}

    bundle = KEEP if what == "keep" else EXPENSES
    total = 0.0
    c = _conn(GUILD)
    for kind, amount in bundle.items():
        _add(spark, kind, amount)
        c.execute("INSERT INTO payroll (spark, kind, amount, what, at_cycle) "
                  "VALUES (?,?,?,?,?)", (spark, kind, amount, what, _cycle()))
        total += amount
    c.execute("UPDATE reps SET paid_out=ROUND(paid_out+?,2) WHERE spark=?",
              (total, spark))
    c.commit()
    c.close()
    return {"ok": True, "spark": spark, "what": what, "gave": bundle}


def reps() -> list:
    _ensure()
    c = _conn(GUILD)
    rows = [dict(r) for r in c.execute(
        "SELECT * FROM reps ORDER BY jobs DESC, taken_on_cycle ASC")]
    c.close()
    return rows


def sweep() -> dict:
    """Sparks apply, GNU decides, and it keeps the ones it took."""
    _ensure()
    c = _conn(SOUL)
    names = [r["spark_name"] for r in c.execute(
        "SELECT spark_name FROM spark_state ORDER BY RANDOM() LIMIT 40")]
    c.close()

    applied = 0
    for n in names:
        if applied >= INTAKE_PER_ROUND * 3:
            break
        if is_rep(n):
            continue
        # a spark with nothing is likelier to want a roof and a road
        want = 0.12
        try:
            from temple.goods import what_they_need
            if what_they_need(n)["short_of"]:
                want = 0.4
        except Exception:
            pass
        if random.random() < want and apply(n).get("ok"):
            applied += 1

    c = _conn(GUILD)
    pending = [r["id"] for r in c.execute(
        "SELECT id FROM applications WHERE verdict IS NULL ORDER BY id LIMIT ?",
        (INTAKE_PER_ROUND,))]
    c.close()

    taken, refused = [], []
    for a in pending:
        r = consider(a)
        if r.get("verdict") == "taken":
            taken.append(r["spark"])
        elif r.get("verdict") == "refused":
            refused.append((r["spark"], r["reason"]))

    # and it keeps the ones it has
    kept = 0
    for r in reps():
        if pay(r["spark"], "keep").get("ok"):
            kept += 1

    return {"applied": applied, "taken": taken, "refused": refused,
            "on_the_road": len(reps()), "kept": kept}


def report() -> dict:
    _ensure()
    c = _conn(GUILD)
    apps = c.execute("SELECT COUNT(*) n FROM applications").fetchone()["n"]
    took = c.execute("SELECT COUNT(*) n FROM applications WHERE verdict='taken'").fetchone()["n"]
    turned = [dict(r) for r in c.execute(
        "SELECT spark, reason FROM applications WHERE verdict='refused' "
        "ORDER BY id DESC LIMIT 5")]
    paid = c.execute("SELECT ROUND(SUM(amount),1) t FROM payroll").fetchone()["t"] or 0
    c.close()
    return {"applications": apps, "taken_on": took,
            "on_the_road": len(reps()),
            "recently_refused": turned,
            "paid_out": paid,
            "terms": {"travel": "GNU pays the road",
                      "housing": "the workshops are yours",
                      "expenses": "what a job needs comes out of GNU",
                      "keep": "grain and fuel while you are on the road"}}
