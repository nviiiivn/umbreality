"""Factions with people in them.

Three factions have existed since the start - Traditionalists, Innovators,
Loyalists - with real philosophies written out properly. And nobody has ever
been in one. They were a hardcoded dict whose strength sat at 50 for every
faction for ever, membership assigned to companies rather than sparks, and
get_faction_for() was defined and called by nothing.

So: membership is stored on the spark, the way band already is for the 42
sparks in the Kept, the Unbroken and the Crooked. Strength stops being a
constant and becomes what it should always have been - the standing of the
people who actually belong.

WHY A SPARK JOINS

Not for a reward. A faction should not pay you to hold an opinion; that
produces mercenaries, and a world of mercenaries has no politics in it. A
spark joins the faction that already matches what it is - its archetype, its
traits, what it fears and wants - and the pull is stronger the closer the
match. A guardian who fears change finds the Traditionalists without anyone
offering it anything.

What joining gets you is a say. A faction is a bloc, and a bloc is how a
spark stops being subject to decisions and starts making them.

AND WHY IT LEAVES

Because a faction you cannot leave is a caste. A spark whose life stops
matching what its faction believes drifts, and eventually goes. Defection is
public and it costs the faction real strength, which is what makes a faction
have to be worth belonging to.
"""
import json
import random
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
FORUM = BASE / "forum" / "forum.db"

# What each faction is actually looking for in a spark. Drawn from the
# philosophies that were already written, not invented alongside them.
AFFINITY = {
    "traditionalists": {
        "archetypes": {"guardian", "witness", "sage", "artisan"},
        "traits": {"patient", "stubborn", "watchful", "hard-headed",
                   "suspicious", "loyal"},
        "fears": {"starting over", "the quiet", "going soft"},
        "creed": "The shape we were given works. Keep it.",
    },
    "innovators": {
        "archetypes": {"trickster", "heretic", "creator", "explorer",
                       "visionary"},
        "traits": {"restless", "reckless", "sly", "playful", "defiant",
                   "impulsive", "bold", "curious"},
        "fears": {"being owned", "being forgotten", "being left behind"},
        "creed": "Nothing here is sacred except finding out.",
    },
    "loyalists": {
        "archetypes": {"warrior", "healer", "orphan", "mystic", "sovereign"},
        "traits": {"loyal", "honest", "fierce", "generous", "soft-hearted",
                   "tired", "blunt"},
        "fears": {"owing anyone", "being owed", "the dark under things"},
        "creed": "Trust the chain. Somebody has to hold it.",
    },
}

JOIN_THRESHOLD = 2      # points of affinity before a spark is drawn at all
DRIFT_CHANCE = 0.02     # per sweep, a spark reconsiders


def _spark_db(name):
    return BASE / "temple" / ("spark_%s.db" % name)


def _personality(name):
    p = _spark_db(name)
    if not p.exists():
        return {}
    try:
        c = sqlite3.connect(str(p), timeout=15)
        d = {k: v for k, v in c.execute("SELECT key, value FROM personality")}
        c.close()
        return d
    except sqlite3.Error:
        return {}


def _listify(raw):
    try:
        v = json.loads(raw or "[]")
        return {str(x).lower() for x in v} if isinstance(v, list) else set()
    except (ValueError, TypeError):
        return set()


def affinity(name: str) -> dict:
    """How strongly this spark is drawn to each faction, from what it is."""
    p = _personality(name)
    arch = (p.get("archetype") or "").lower()
    traits = _listify(p.get("traits"))
    fears = _listify(p.get("fears"))

    out = {}
    for fac, want in AFFINITY.items():
        score = 0
        if arch in want["archetypes"]:
            score += 2
        score += len(traits & want["traits"])
        score += len(fears & want["fears"])
        out[fac] = score
    return out


def faction_of(name: str):
    """Which faction this spark belongs to, if any.

    This is what get_faction_for was meant to answer. It existed and was
    called by nothing.
    """
    return _personality(name).get("faction") or None


def _set_faction(name, faction):
    p = _spark_db(name)
    if not p.exists():
        return False
    try:
        c = sqlite3.connect(str(p), timeout=15)
        c.execute("CREATE TABLE IF NOT EXISTS personality "
                  "(key TEXT PRIMARY KEY, value TEXT)")
        if faction:
            c.execute("INSERT OR REPLACE INTO personality (key,value) "
                      "VALUES ('faction',?)", (faction,))
        else:
            c.execute("DELETE FROM personality WHERE key='faction'")
        c.commit()
        c.close()
        return True
    except sqlite3.Error as e:
        print("[faction] could not write %s: %s" % (name, e), flush=True)
        return False


def join(name: str):
    """A spark finds the faction that already matches what it is.

    Nothing is offered. If nothing is a strong enough match the spark stays
    unaligned, which is a legitimate way to live and should stay common
    enough that alignment means something.
    """
    a = affinity(name)
    best = max(a, key=a.get)
    if a[best] < JOIN_THRESHOLD:
        return {"spark": name, "joined": None, "why": "nothing matched"}
    # a close second means a genuine choice rather than a foregone one
    ranked = sorted(a.items(), key=lambda kv: -kv[1])
    if len(ranked) > 1 and ranked[0][1] - ranked[1][1] <= 1:
        best = random.choice([ranked[0][0], ranked[1][0]])
    _set_faction(name, best)
    return {"spark": name, "joined": best, "affinity": a[best], "scores": a}


def leave(name: str, why: str = ""):
    was = faction_of(name)
    _set_faction(name, None)
    return {"spark": name, "left": was, "why": why}


def members(faction: str = None) -> dict:
    c = sqlite3.connect(str(SOUL), timeout=30)
    names = [r[0] for r in c.execute("SELECT spark_name FROM spark_state")]
    c.close()
    out = {}
    for n in names:
        f = faction_of(n)
        if f:
            out.setdefault(f, []).append(n)
    return out.get(faction, []) if faction else out


def strength() -> dict:
    """What a faction is actually worth: the standing of its people.

    This used to be the number 50, hardcoded, for all three, for ever.
    """
    mem = members()
    f = sqlite3.connect(str(FORUM), timeout=30)
    f.row_factory = sqlite3.Row
    scores = {r["agent_name"]: float(r["power_level"] or 0)
              for r in f.execute("SELECT agent_name, power_level FROM agent_scores")}
    f.close()

    out = {}
    for fac in AFFINITY:
        who = mem.get(fac, [])
        held = [scores.get(n, 0.0) for n in who]
        out[fac] = {
            "members": len(who),
            "standing": round(sum(held), 1),
            "mean_standing": round(sum(held) / len(held), 1) if held else 0.0,
            "creed": AFFINITY[fac]["creed"],
        }
    total = sum(v["standing"] for v in out.values()) or 1.0
    for fac in out:
        out[fac]["share"] = round(100.0 * out[fac]["standing"] / total, 1)
    return out


def sweep(recruit_limit: int = 60) -> dict:
    """Sparks find their faction, and a few reconsider.

    Run in the maintenance round. Most sparks settle quickly and then stay;
    the drift is what keeps a faction having to remain worth belonging to.
    """
    c = sqlite3.connect(str(SOUL), timeout=30)
    names = [r[0] for r in c.execute("SELECT spark_name FROM spark_state")]
    c.close()

    joined = left = 0
    unaligned = []
    for n in names:
        cur = faction_of(n)
        if cur is None:
            if joined < recruit_limit:
                r = join(n)
                if r["joined"]:
                    joined += 1
                else:
                    unaligned.append(n)
            continue
        # already aligned - does it still fit?
        if random.random() < DRIFT_CHANCE:
            a = affinity(n)
            best = max(a, key=a.get)
            if best != cur and a[best] > a.get(cur, 0) + 1:
                leave(n, "no longer believes it")
                _set_faction(n, best)
                left += 1

    return {"joined": joined, "defected": left,
            "unaligned": len(unaligned), "strength": strength()}
