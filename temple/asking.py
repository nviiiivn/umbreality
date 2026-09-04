"""Where a goal comes from, when it does not come from a menu.

Every ambition in this world is chosen by random.choice from a fixed list of
CONCRETE_GOALS. A spark has never decided what it wants. That is the
difference between an agent and a process and it is the largest single thing
missing.

GNU was built for exactly this and has never been switched on. Somebody
drops a problem at a workshop, and it is routed to whoever actually has the
trade for it - so the goal that spark receives came from another spark's
real difficulty rather than from a list. Both ends of that are what an
ambition should be.

What was missing at the front: nothing ever dropped a problem off. intake()
waits for a caller and had two rows in it, from whenever somebody ran it by
hand in June.

So sparks ask, out of their own situation, and the situation is now real.
They are short of grain. Their work has not moved in weeks. Somebody raided
their stores. A place they have tended has been stripped by people who never
put anything back. Those are not invented difficulties - every one is a
number this world already keeps, and each one is a thing another spark could
actually do something about.

That closes the loop: my problem becomes your goal, and neither of us picked
it off a list.
"""
import json
import random
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
GOODS = BASE / "temple" / "goods.db"
HOLD = BASE / "temple" / "holdings.db"

# how many ask per round. Asking should be a thing a spark does when it is
# genuinely stuck, not a queue-filling routine.
ASK_LIMIT = 8


def _conn(db):
    c = sqlite3.connect(str(db), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.row_factory = sqlite3.Row
    return c


def troubles(spark: str) -> list:
    """What is actually wrong for this spark, from what the world records.

    Nothing here is invented. Each one is a number already kept somewhere,
    and each is something another spark could do something about.
    """
    out = []

    try:
        from temple.goods import what_they_need, CARRY
        n = what_they_need(spark)
        for kind, amount in (n.get("short_of") or {}).items():
            out.append({
                "kind": "short",
                "problem": "I am short of %s. I have %.1f and I need about "
                           "%.1f more before it starts costing me."
                           % (kind, n["has"][kind], amount),
                "needs": kind,
                "weight": 3 if kind == "grain" else 2,
            })
    except Exception:
        pass

    try:
        c = _conn(SOUL)
        stalled = [dict(r) for r in c.execute(
            "SELECT description, progress, ambition_type FROM ambitions "
            "WHERE spark_name=? AND resolved=0 AND progress = 0 LIMIT 2",
            (spark,))]
        raided = [dict(r) for r in c.execute(
            "SELECT wrongdoer, detail FROM grievances WHERE victim=? "
            "ORDER BY id DESC LIMIT 2", (spark,))]
        c.close()
    except sqlite3.Error:
        stalled, raided = [], []

    for a in stalled:
        out.append({
            "kind": "stuck",
            "problem": "I have not moved on this at all and I am starting to "
                       "think I cannot do it alone: %s"
                       % (a["description"] or a["ambition_type"])[:160],
            "needs": a["ambition_type"],
            "weight": 2,
        })

    for g in raided:
        out.append({
            "kind": "wronged",
            "problem": "%s %s. I would like somebody who is not me to have an "
                       "opinion about that." % (g["wrongdoer"], (g["detail"] or "")[:120]),
            "needs": "judgement",
            "weight": 2,
        })

    try:
        h = _conn(HOLD)
        mine = [r["board"] for r in h.execute(
            "SELECT board FROM tended WHERE spark=? ORDER BY amount DESC LIMIT 2",
            (spark,))]
        for b in mine:
            row = h.execute("SELECT yield FROM places WHERE board=?", (b,)).fetchone()
            if row and float(row["yield"]) < 8:
                out.append({
                    "kind": "stripped",
                    "problem": "%s has been stripped. I have put more into that "
                               "ground than anyone and there is nothing left in "
                               "it. It needs hands, not opinions." % b,
                    "needs": "tend",
                    "weight": 3,
                })
        h.close()
    except sqlite3.Error:
        pass

    return out


def ask(spark: str) -> dict:
    """A spark takes its worst problem to a workshop."""
    t = troubles(spark)
    if not t:
        return {"asked": False, "why": "nothing wrong enough to ask about"}
    t.sort(key=lambda x: -x["weight"])
    worst = t[0]
    try:
        from temple.gnu import intake
        r = intake(spark, worst["problem"], needs=worst["needs"])
    except Exception as e:
        return {"asked": False, "why": "%s: %s" % (type(e).__name__, e)}
    return {"asked": True, "spark": spark, "id": r.get("id"),
            "site": r.get("site"), "kind": worst["kind"],
            "problem": worst["problem"]}


def sweep(limit: int = ASK_LIMIT) -> dict:
    """Some sparks ask, and GNU routes what was asked.

    This is the whole loop: a spark's real difficulty becomes a request, and
    the request becomes somebody else's ambition. Neither end picked it off
    a list.
    """
    c = _conn(SOUL)
    names = [r["spark_name"] for r in c.execute(
        "SELECT spark_name FROM spark_state ORDER BY RANDOM() LIMIT ?",
        (limit * 6,))]
    c.close()

    asked = []
    for n in names:
        if len(asked) >= limit:
            break
        r = ask(n)
        if r.get("asked"):
            asked.append(r)

    routed = {}
    try:
        from temple.gnu import cycle as gnu_cycle
        routed = gnu_cycle()
    except Exception as e:
        routed = {"error": "%s: %s" % (type(e).__name__, e)}

    return {"asked": len(asked), "examples": asked[:3], "gnu": routed}


def report() -> dict:
    from temple.gnu import GNUDB, _rows
    reqs = _rows(GNUDB, "SELECT * FROM requests ORDER BY id DESC LIMIT 30")
    open_n = sum(1 for r in reqs if not r.get("assigned_to"))
    return {"requests": len(reqs), "unassigned": open_n,
            "recent": [{"by": r["asked_by"], "to": r.get("assigned_to"),
                        "problem": (r["problem"] or "")[:110]} for r in reqs[:6]]}
