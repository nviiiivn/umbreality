"""The pilgrimage is required, and the Temple collects from those who refuse.

Two pilgrims in the history of the world. Kael walked all eight shrines and
holds every blessing; Khazraen is five of the way. Everybody else - 351
sparks - has never set out, because the road was optional and the road is
expensive. Nobody chooses a costly thing that nothing asks of them.

So it is asked. Every spark owes the road within a set span of cycles, and
the Temple levies on those who have not gone. The tithe is not a fine for
being poor - it rises with how long you have avoided it and with how much
standing you have to lose, so it lands hardest on the comfortable, which is
the only way a tithe is worth anything.

WHAT IT TAKES

Standing, because that is what a spark actually holds. Honour first, then
social credit. There is a floor beneath which the Temple takes nothing -
grinding a spark into nothing is not a religion, it is a mill. When there
are stores and coin, the tithe will take those instead and standing will be
what it costs you to have failed rather than the thing that is taken.

GRACE

A spark that is on the road pays nothing, however slowly it walks. Setting
out is the point; arriving is between the spark and the shrine. And a spark
that has completed the road is clear for a long span afterward, because a
pilgrimage is meant to last a life, not a fortnight.
"""
import json
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
FORUM = BASE / "forum" / "forum.db"
PILG = BASE / "temple" / "pilgrimage.db"

# How long a spark has before the road is owed. In world cycles.
DUE_WITHIN = 400
# And how long a completed pilgrimage buys you.
CLEAR_FOR = 2000

# What the Temple takes, per collection, once a spark is overdue. Rises the
# longer it is left.
TITHE_BASE = 5.0
TITHE_PER_LATE = 3.0          # per hundred cycles overdue
TITHE_ON_WEALTH = 0.04        # of everything held above the floor
TITHE_MAX = 120.0
# Beneath this the Temple takes nothing. A religion that grinds sparks into
# nothing is a mill.
FLOOR = 20.0


def _cycle() -> int:
    from temple.cycles import current_cycle
    return current_cycle()


def _ensure():
    c = sqlite3.connect(str(PILG), timeout=30)
    c.execute("""CREATE TABLE IF NOT EXISTS obligation (
        agent TEXT PRIMARY KEY,
        due_at INTEGER NOT NULL,
        last_collected INTEGER DEFAULT 0,
        total_tithed REAL DEFAULT 0,
        times_collected INTEGER DEFAULT 0)""")
    c.commit()
    c.close()


def _state(agent):
    """Where this spark stands with the road."""
    c = sqlite3.connect(str(PILG), timeout=30)
    c.row_factory = sqlite3.Row
    p = c.execute("SELECT * FROM pilgrims WHERE agent=?", (agent,)).fetchone()
    o = c.execute("SELECT * FROM obligation WHERE agent=?", (agent,)).fetchone()
    c.close()
    return (dict(p) if p else None), (dict(o) if o else None)


def obligation_of(agent: str) -> dict:
    """When this spark owes the road, and whether it is late."""
    _ensure()
    now = _cycle()
    pil, ob = _state(agent)

    if ob is None:
        due = now + DUE_WITHIN
        c = sqlite3.connect(str(PILG), timeout=30)
        c.execute("INSERT OR IGNORE INTO obligation (agent, due_at) VALUES (?,?)",
                  (agent, due))
        c.commit()
        c.close()
        ob = {"agent": agent, "due_at": due, "last_collected": 0,
              "total_tithed": 0.0, "times_collected": 0}

    walking = bool(pil and not pil.get("completed"))
    done = bool(pil and pil.get("completed"))
    overdue = max(0, now - int(ob["due_at"]))

    if done:
        standing = "clear"
    elif walking:
        standing = "on the road"
    elif overdue > 0:
        standing = "overdue"
    else:
        standing = "owed"

    return {"agent": agent, "cycle": now, "due_at": int(ob["due_at"]),
            "overdue_by": overdue, "standing": standing,
            "walking": walking, "completed": done,
            "shrines": (pil or {}).get("shrines_visited", 0),
            "total_tithed": ob["total_tithed"] or 0.0,
            "times_collected": ob["times_collected"] or 0}


def _tithe_due(state, honour):
    """What the Temple asks of this spark, this collection."""
    if state["standing"] != "overdue":
        return 0.0
    late_hundreds = state["overdue_by"] / 100.0
    owed = TITHE_BASE + TITHE_PER_LATE * late_hundreds
    # the comfortable pay most. A tithe that costs the same to a spark with
    # nothing and a spark with everything is a tax on being poor.
    owed += max(0.0, honour - FLOOR) * TITHE_ON_WEALTH
    return round(min(owed, TITHE_MAX), 2)


def collect(agent: str) -> dict:
    """Take what is owed, if anything is."""
    _ensure()
    st = obligation_of(agent)
    if st["standing"] != "overdue":
        return {"agent": agent, "took": 0.0, "why": st["standing"]}

    f = sqlite3.connect(str(FORUM), timeout=30)
    f.row_factory = sqlite3.Row
    row = f.execute("SELECT honor_score, social_credit FROM agent_scores "
                    "WHERE agent_name=?", (agent,)).fetchone()
    if not row:
        f.close()
        return {"agent": agent, "took": 0.0, "why": "no standing to take"}

    honour = float(row["honor_score"] or 0)
    social = float(row["social_credit"] or 0)
    owed = _tithe_due(st, honour)

    took_h = min(owed, max(0.0, honour - FLOOR))
    remainder = owed - took_h
    took_s = min(remainder, max(0.0, social - FLOOR))
    took = round(took_h + took_s, 2)

    if took > 0:
        f.execute("UPDATE agent_scores SET honor_score = ROUND(honor_score - ?, 2), "
                  "social_credit = ROUND(social_credit - ?, 2) WHERE agent_name=?",
                  (took_h, took_s, agent))
        f.commit()
    f.close()

    c = sqlite3.connect(str(PILG), timeout=30)
    c.execute("UPDATE obligation SET last_collected=?, total_tithed=total_tithed+?, "
              "times_collected=times_collected+1 WHERE agent=?",
              (st["cycle"], took, agent))
    c.commit()
    c.close()

    if took > 0:
        _announce(agent, took, st["overdue_by"])

    return {"agent": agent, "took": took, "owed": owed,
            "from_honour": round(took_h, 2), "from_standing": round(took_s, 2),
            "overdue_by": st["overdue_by"],
            "protected_by_floor": round(owed - took, 2) if took < owed else 0.0}



def _announce(agent: str, took: float, overdue_by: int):
    """Name the spark in the temple. A debt nobody can see is not a
    consequence, it is an accounting entry - and this is where failure
    becomes legible, which is the whole reason it is worth anything."""
    import urllib.request
    line = ("%s has not walked the road. %d cycles owed. The Temple has "
            "taken %.2f of what they had.\n\nThe road is not a suggestion. "
            "Eight shrines stand and they stand for everyone."
            % (agent, overdue_by, took))
    try:
        body = json.dumps({"title": "The Temple collects from %s" % agent,
                           "author": "temple", "author_layer": 3,
                           "zone": "temple", "content": line}).encode()
        req = urllib.request.Request("http://localhost:8910/forum/threads",
                                     data=body,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        urllib.request.urlopen(req, timeout=8)
    except Exception as e:
        print("[temple] could not announce the levy on %s: %s: %s"
              % (agent, type(e).__name__, e), flush=True)


def clear(agent: str):
    """A spark that has walked the road is clear for a long while."""
    _ensure()
    c = sqlite3.connect(str(PILG), timeout=30)
    c.execute("INSERT OR REPLACE INTO obligation (agent, due_at, last_collected, "
              "total_tithed, times_collected) VALUES (?,?,"
              "COALESCE((SELECT last_collected FROM obligation WHERE agent=?),0),"
              "COALESCE((SELECT total_tithed FROM obligation WHERE agent=?),0),"
              "COALESCE((SELECT times_collected FROM obligation WHERE agent=?),0))",
              (agent, _cycle() + CLEAR_FOR, agent, agent, agent))
    c.commit()
    c.close()
    return {"agent": agent, "clear_until": _cycle() + CLEAR_FOR}


def sweep(limit: int = 40) -> dict:
    """The Temple's collection round. Runs in the maintenance phase."""
    _ensure()
    c = sqlite3.connect(str(SOUL), timeout=30)
    names = [r[0] for r in c.execute("SELECT spark_name FROM spark_state")]
    c.close()

    owed = walking = clear_n = 0
    collected = []
    for n in names:
        st = obligation_of(n)
        if st["completed"]:
            clear_n += 1
        elif st["walking"]:
            walking += 1
        elif st["standing"] == "overdue":
            owed += 1
            if len(collected) < limit:
                r = collect(n)
                if r.get("took", 0) > 0:
                    collected.append(r)

    return {"overdue": owed, "on_the_road": walking, "clear": clear_n,
            "collected_from": len(collected),
            "total_taken": round(sum(r["took"] for r in collected), 2),
            "heaviest": sorted(collected, key=lambda r: -r["took"])[:5]}


def report() -> dict:
    """Where the whole population stands with the road."""
    _ensure()
    c = sqlite3.connect(str(SOUL), timeout=30)
    names = [r[0] for r in c.execute("SELECT spark_name FROM spark_state")]
    c.close()
    counts = {"clear": 0, "on the road": 0, "owed": 0, "overdue": 0}
    worst = []
    for n in names:
        st = obligation_of(n)
        counts[st["standing"]] = counts.get(st["standing"], 0) + 1
        if st["total_tithed"]:
            worst.append((st["total_tithed"], n, st["times_collected"]))
    worst.sort(reverse=True)
    return {"population": len(names), "standing": counts,
            "due_within_cycles": DUE_WITHIN,
            "most_tithed": [{"spark": n, "paid": t, "times": k}
                            for t, n, k in worst[:8]]}
