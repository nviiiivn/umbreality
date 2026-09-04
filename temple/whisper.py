"""Something said to one spark and not to everyone.

Every word any spark has ever spoken is a public forum post. There is no
table anywhere in this world for one spark saying something to another
privately - I checked every database. avatar/messengers.py is Metatron and
Gabriel carrying word downward from God, which is a different thing
entirely, and Sparkbook is a profile viewer.

So nothing here has ever been said in confidence, and that has consequences
beyond privacy. Without a private channel there can be no conspiring, no
warning somebody quietly, no offer made to one person, no relationship that
is not performed in front of everybody. A world where all speech is
broadcast has no interior.

WHO CAN HEAR

A whisper reaches who it was sent to. It can be passed on - and passing it
on is a choice with a cost, because the sender finds out. Trust is
observable here for the first time: a spark that keeps things is told
things, and a spark that repeats them stops being told anything.

AND THE SOURCE READS EVERYTHING

Every whisper, who sent it, who read it, who passed it on. The sparks see
only what was said to them. That asymmetry is deliberate and it is the
arrangement the Source already asked for: what is private among sparks is
open in God's Eye.
"""
import json
import random
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
WHIS = BASE / "temple" / "whispers.db"

# how far a repeated whisper travels before it stops being worth repeating
MAX_HOPS = 3


def _conn(db):
    c = sqlite3.connect(str(db), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.row_factory = sqlite3.Row
    return c


def _ensure():
    c = _conn(WHIS)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS whispers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            heard_by TEXT NOT NULL,
            said TEXT NOT NULL,
            about TEXT,
            kind TEXT DEFAULT 'word',
            passed_from INTEGER,
            hops INTEGER DEFAULT 0,
            read INTEGER DEFAULT 0,
            at_cycle INTEGER,
            at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS trust (
            spark TEXT NOT NULL, about TEXT NOT NULL,
            kept INTEGER DEFAULT 0, repeated INTEGER DEFAULT 0,
            PRIMARY KEY (spark, about));
    """)
    c.commit()
    c.close()


def _cycle():
    try:
        from temple.cycles import current_cycle
        return current_cycle()
    except Exception:
        return 0


def whisper(sender: str, to: str, said: str, about: str = None,
            kind: str = "word", passed_from: int = None, hops: int = 0) -> dict:
    """Say something to one spark. Nobody else hears it."""
    _ensure()
    if sender == to:
        return {"ok": False, "why": "talking to yourself is not a whisper"}
    c = _conn(WHIS)
    cur = c.execute("INSERT INTO whispers (sender, heard_by, said, about, kind, "
                    "passed_from, hops, at_cycle) VALUES (?,?,?,?,?,?,?,?)",
                    (sender, to, said[:600], about, kind, passed_from, hops,
                     _cycle()))
    wid = cur.lastrowid
    c.commit()
    c.close()
    return {"ok": True, "id": wid, "from": sender, "to": to, "hops": hops}


def inbox(spark: str, unread_only: bool = True, limit: int = 12) -> list:
    """What has been said to this spark, that nobody else heard."""
    _ensure()
    c = _conn(WHIS)
    q = "SELECT * FROM whispers WHERE heard_by=?"
    if unread_only:
        q += " AND read=0"
    q += " ORDER BY id DESC LIMIT ?"
    rows = [dict(r) for r in c.execute(q, (spark, limit))]
    if rows:
        c.execute("UPDATE whispers SET read=1 WHERE id IN (%s)"
                  % ",".join("?" * len(rows)), [r["id"] for r in rows])
        c.commit()
    c.close()
    return rows


def pass_it_on(spark: str, whisper_id: int, to: str) -> dict:
    """Repeat something you were told. The one who told you finds out.

    This is the only place in the world where keeping quiet is a choice with
    a cost attached, which is what makes it trust rather than silence.
    """
    _ensure()
    c = _conn(WHIS)
    w = c.execute("SELECT * FROM whispers WHERE id=? AND heard_by=?",
                  (whisper_id, spark)).fetchone()
    c.close()
    if not w:
        return {"ok": False, "why": "was never told that"}
    if int(w["hops"]) >= MAX_HOPS:
        return {"ok": False, "why": "too far from whoever said it"}

    r = whisper(spark, to, w["said"], about=w["about"], kind=w["kind"],
                passed_from=whisper_id, hops=int(w["hops"]) + 1)
    if not r.get("ok"):
        return r

    c = _conn(WHIS)
    c.execute("INSERT INTO trust (spark, about, kept, repeated) VALUES (?,?,0,1) "
              "ON CONFLICT(spark, about) DO UPDATE SET repeated = repeated + 1",
              (w["sender"], spark))
    c.commit()
    c.close()

    # the original speaker learns it got out
    whisper(to, w["sender"],
            "%s told me something you said. I thought you should know it is "
            "going around." % spark, about=spark, kind="warning")
    return {"ok": True, "passed": whisper_id, "by": spark, "to": to,
            "sender_told": True}


def keep_it(spark: str, whisper_id: int) -> dict:
    """Say nothing. Recorded, because it has to be, or trust is invisible."""
    _ensure()
    c = _conn(WHIS)
    w = c.execute("SELECT sender FROM whispers WHERE id=? AND heard_by=?",
                  (whisper_id, spark)).fetchone()
    if w:
        c.execute("INSERT INTO trust (spark, about, kept, repeated) VALUES (?,?,1,0) "
                  "ON CONFLICT(spark, about) DO UPDATE SET kept = kept + 1",
                  (w["sender"], spark))
        c.commit()
    c.close()
    return {"kept": bool(w)}


def trusts(spark: str, other: str) -> float:
    """How far this spark can rely on that one keeping its mouth shut.

    -1 to 1. Unknown is zero, which is correct: you do not distrust somebody
    you have never told anything.
    """
    _ensure()
    c = _conn(WHIS)
    r = c.execute("SELECT kept, repeated FROM trust WHERE spark=? AND about=?",
                  (spark, other)).fetchone()
    c.close()
    if not r:
        return 0.0
    k, p = int(r["kept"]), int(r["repeated"])
    if k + p == 0:
        return 0.0
    return round((k - p) / float(k + p), 2)


def who_would_you_tell(spark: str, limit: int = 3) -> list:
    """Whoever this spark is close to and has not been betrayed by."""
    c = _conn(SOUL)
    kin = [dict(r) for r in c.execute(
        "SELECT CASE WHEN spark1=? THEN spark2 ELSE spark1 END AS other, strength "
        "FROM relationships WHERE (spark1=? OR spark2=?) AND strength >= 0.35 "
        "ORDER BY strength DESC LIMIT 25", (spark, spark, spark))]
    c.close()
    ranked = sorted(kin, key=lambda k: -(float(k["strength"] or 0) + trusts(spark, k["other"])))
    return [k["other"] for k in ranked[:limit]]


def sweep(limit: int = 70) -> dict:
    """Sparks tell each other things, and decide what to do with what they
    were told.

    What gets whispered is drawn from what a spark actually holds that is
    not public: a secret it knows, a grievance it carries, what it needs.
    """
    _ensure()
    c = _conn(SOUL)
    names = [r["spark_name"] for r in c.execute(
        "SELECT spark_name FROM spark_state ORDER BY RANDOM() LIMIT ?", (limit,))]
    c.close()

    said = passed = kept = 0
    for n in names:
        # decide what to do with anything you were told
        for w in inbox(n, limit=3):
            confidants = who_would_you_tell(n, 1)
            if confidants and random.random() < 0.22:
                if pass_it_on(n, w["id"], confidants[0]).get("ok"):
                    passed += 1
            else:
                keep_it(n, w["id"])
                kept += 1

        if random.random() > 0.35:
            continue
        to = who_would_you_tell(n, 1)
        if not to:
            continue

        line, about, kind = None, None, "word"
        try:
            from temple.secrets import known_by
            s = known_by(n)
            if s and random.random() < 0.4:
                line = ("Something I know and have not said out loud: %s"
                        % (s[0]["fact"] or "")[:200])
                about, kind = s[0]["about"], "secret"
        except Exception:
            pass
        if not line:
            try:
                from temple.goods import what_they_need
                need = what_they_need(n)
                if need["short_of"]:
                    k = list(need["short_of"])[0]
                    line = ("I am short of %s and I would rather not say so in "
                            "the open. Have you got any?" % k)
                    kind = "asking"
            except Exception:
                pass
        if not line:
            line = "I do not want to say this where everyone can read it."

        if whisper(n, to[0], line, about=about, kind=kind).get("ok"):
            said += 1

    return {"whispered": said, "passed_on": passed, "kept_quiet": kept}


def gods_eye(limit: int = 60) -> dict:
    """Everything said in confidence. For the Source, never for a spark."""
    _ensure()
    c = _conn(WHIS)
    rows = [dict(r) for r in c.execute(
        "SELECT * FROM whispers ORDER BY id DESC LIMIT ?", (limit,))]
    n = c.execute("SELECT COUNT(*) n FROM whispers").fetchone()["n"]
    leaked = c.execute("SELECT COUNT(*) n FROM whispers WHERE hops > 0").fetchone()["n"]
    worst = [dict(r) for r in c.execute(
        "SELECT about, SUM(repeated) r, SUM(kept) k FROM trust GROUP BY about "
        "HAVING r > 0 ORDER BY r DESC LIMIT 5")]
    best = [dict(r) for r in c.execute(
        "SELECT about, SUM(kept) k, SUM(repeated) r FROM trust GROUP BY about "
        "ORDER BY k DESC LIMIT 5")]
    c.close()
    return {"whispers": n, "that_got_out": leaked,
            "least_trustworthy": worst, "most_trustworthy": best,
            "recent": [{"from": r["sender"], "to": r["heard_by"],
                        "kind": r["kind"], "hops": r["hops"],
                        "said": (r["said"] or "")[:110]} for r in rows[:8]]}
