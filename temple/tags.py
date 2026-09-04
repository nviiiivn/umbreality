"""How a spark is, at six speeds, and whether it can see itself.

Register was a label: a spark was crude or it was ornate and that was the
whole of it, fixed for life. Real people are not one thing at one setting.
They have a temperament they were born with, a character they have become, a
season they are going through, a mood today, and something that happened an
hour ago - and all five are true at once and pull in different directions.

    NATURE      ~never moves      what is still there at eighty
    CHARACTER   months            who you have become. The home you return to
    SEASON      weeks             a long stretch - grief, a run of wins, being ignored
    MOOD        days              ordinary weather
    SPIKE       one event         somebody ate their mentor. Decays fast
    POSSESSION  overrides all     something else is choosing. Not the spark

Mood swings around Character and is always pulled back toward it, the way a
tide has a level it returns to. And Character itself drifts, slowly, toward
wherever Mood keeps sitting - so a spark that has been miserable for a year
does not merely have bad moods, it becomes a more bitter person, and that is
its new home. Nobody is immune. Nothing changes overnight.

INFLUENCE, NOT DETERMINATION

The weights tilt the odds and that is all they do. A spark in a foul mood
can still be gentle with somebody it loves, because it chose to. If the tags
decided the outcome there would be nobody home. The mix loads the dice; the
spark still throws them.

INSIGHT

Whether a spark can see its own state. Low insight and the state acts on
them - they snap and do not know why. High insight and they can say I am
frustrated right now instead of exploding. That is the difference between a
spark that is a bastard and one that knows it is being a bastard because it
is frightened, and it is the whole of what self-actualisation means here.

It grows through reflection, being taught, and surviving something hard. And
it rots in the absence of contradiction - a spark whose bonds are all
beneath it, that nobody will correct, stops being able to see itself, and
the not-noticing is the condition. That is the emperor with no clothes, and
it is measurable.
"""
import hashlib
import json
import math
import random
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
FORUM = BASE / "forum" / "forum.db"
TAGS = BASE / "temple" / "tags.db"

# The six speeds, and how fast each returns to where it came from. 1.0 means
# it is gone by the next reading; 0.0 means it never moves.
SPEEDS = {
    "nature":     0.000,
    "character":  0.004,
    "season":     0.05,
    "mood":       0.30,
    "spike":      0.65,
    "possession": 1.00,
}

# What can be true of a spark. These are dimensions, not moods - each runs
# from one thing to its opposite, and a spark sits somewhere on all of them
# at once.
DIMENSIONS = {
    "heat":     ("calm", "furious"),
    "warmth":   ("cold", "warm"),
    "nerve":    ("afraid", "fearless"),
    "hunger":   ("content", "wanting"),
    "spirit":   ("flat", "alight"),
    "trust":    ("guarded", "open"),
}

INSIGHT_FLOOR = 0.05
INSIGHT_CEIL = 1.0


def _conn(db):
    c = sqlite3.connect(str(db), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.row_factory = sqlite3.Row
    return c


def _ensure():
    c = _conn(TAGS)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS layers (
            spark TEXT NOT NULL,
            speed TEXT NOT NULL,
            dimension TEXT NOT NULL,
            value REAL NOT NULL,
            because TEXT,
            set_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (spark, speed, dimension));
        CREATE TABLE IF NOT EXISTS insight (
            spark TEXT PRIMARY KEY,
            level REAL DEFAULT 0.35,
            moved_at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS possession (
            spark TEXT PRIMARY KEY,
            by_whom TEXT, what TEXT,
            until_cycle INTEGER,
            began_at TEXT DEFAULT (datetime('now')));
    """)
    c.commit()
    c.close()


def _seeded(spark, dim):
    """Nature, drawn from the spark's own name. It never moves, so it may as
    well be a fact about the name it was given."""
    h = hashlib.sha256(("nature:%s:%s" % (spark, dim)).encode()).hexdigest()
    return (int(h[:8], 16) % 1000) / 1000.0


def _read(spark):
    _ensure()
    c = _conn(TAGS)
    rows = [dict(r) for r in c.execute(
        "SELECT speed, dimension, value FROM layers WHERE spark=?", (spark,))]
    c.close()
    out = {s: {} for s in SPEEDS}
    for r in rows:
        out.setdefault(r["speed"], {})[r["dimension"]] = float(r["value"])
    return out


def state(spark: str) -> dict:
    """Where this spark actually is, all six speeds folded together.

    Nature is the ground. Character sits on it. Season, mood and spike are
    departures from character, not from zero - which is why a spark under
    strain still reads recognisably as itself.
    """
    layers = _read(spark)
    out = {}
    for dim in DIMENSIONS:
        nature = layers["nature"].get(dim, _seeded(spark, dim))
        character = layers["character"].get(dim, nature)
        v = character
        for speed in ("season", "mood", "spike"):
            v += layers.get(speed, {}).get(dim, 0.0)
        out[dim] = max(0.0, min(1.0, v))

    p = possessed_by(spark)
    if p:
        # something else is choosing. The spark's own state is still there
        # underneath and will be there when it lets go.
        out = {d: 0.5 + (random.random() - 0.5) * 1.4 for d in DIMENSIONS}
        out = {d: max(0.0, min(1.0, v)) for d, v in out.items()}
        out["_possessed_by"] = p["by_whom"]
        out["_possession"] = p["what"]
    return out


def nudge(spark: str, speed: str, dimension: str, amount: float,
          because: str = "") -> dict:
    """Something happened. Move one dimension at one speed.

    A spike is what an hour ago did. A season is what this month has been.
    Nudging character directly is rare and heavy - character is supposed to
    drift, not be set.
    """
    _ensure()
    if speed not in SPEEDS or dimension not in DIMENSIONS:
        return {"ok": False, "why": "no such speed or dimension"}
    layers = _read(spark)
    cur = layers.get(speed, {}).get(dimension, 0.0)
    if speed in ("nature", "character"):
        base = layers["nature"].get(dimension, _seeded(spark, dimension))
        new = max(0.0, min(1.0, (cur or base) + amount))
    else:
        new = max(-0.6, min(0.6, cur + amount))
    c = _conn(TAGS)
    c.execute("INSERT OR REPLACE INTO layers (spark, speed, dimension, value, "
              "because, set_at) VALUES (?,?,?,?,?,datetime('now'))",
              (spark, speed, dimension, new, because))
    c.commit()
    c.close()
    return {"ok": True, "spark": spark, "speed": speed, "dimension": dimension,
            "was": round(cur, 3), "now": round(new, 3), "because": because}


def settle(spark: str) -> dict:
    """One turn of the tide.

    Fast layers fall back toward nothing at their own rate. Character drifts
    a little toward wherever mood and season have been sitting - which is how
    a bad year becomes a bitter person rather than a run of bad days.
    """
    _ensure()
    layers = _read(spark)
    c = _conn(TAGS)
    drifted = []
    for dim in DIMENSIONS:
        pull = 0.0
        for speed in ("spike", "mood", "season"):
            v = layers.get(speed, {}).get(dim, 0.0)
            if not v:
                continue
            decayed = v * (1.0 - SPEEDS[speed])
            if abs(decayed) < 0.005:
                decayed = 0.0
            c.execute("INSERT OR REPLACE INTO layers (spark, speed, dimension, "
                      "value, because, set_at) VALUES (?,?,?,?,?,datetime('now'))",
                      (spark, speed, dim, decayed, "settling"))
            pull += v * {"spike": 0.15, "mood": 0.35, "season": 0.5}[speed]

        if abs(pull) > 0.02:
            base = layers["nature"].get(dim, _seeded(spark, dim))
            ch = layers["character"].get(dim, base)
            moved = ch + pull * SPEEDS["character"]
            moved = max(0.0, min(1.0, moved))
            if abs(moved - ch) > 0.0005:
                c.execute("INSERT OR REPLACE INTO layers (spark, speed, dimension, "
                          "value, because, set_at) VALUES (?,?,?,?,?,datetime('now'))",
                          (spark, "character", dim, moved,
                           "what keeps happening"))
                drifted.append((dim, round(moved - ch, 4)))
    c.commit()
    c.close()
    return {"spark": spark, "character_drifted": drifted}


# ── insight ──────────────────────────────────────────────────────────

def insight_of(spark: str) -> float:
    _ensure()
    c = _conn(TAGS)
    r = c.execute("SELECT level FROM insight WHERE spark=?", (spark,)).fetchone()
    c.close()
    return float(r["level"]) if r else 0.35


def move_insight(spark: str, amount: float, why: str = "") -> dict:
    _ensure()
    cur = insight_of(spark)
    new = max(INSIGHT_FLOOR, min(INSIGHT_CEIL, cur + amount))
    c = _conn(TAGS)
    c.execute("INSERT OR REPLACE INTO insight (spark, level, moved_at) "
              "VALUES (?,?,datetime('now'))", (spark, new))
    c.commit()
    c.close()
    return {"spark": spark, "was": round(cur, 3), "now": round(new, 3), "why": why}


def _contradicted(spark) -> bool:
    """Is there anybody close to this spark who could correct it?"""
    try:
        from temple.harm import _unchecked
        f = _conn(FORUM)
        row = f.execute("SELECT power_level FROM agent_scores WHERE agent_name=?",
                        (spark,)).fetchone()
        f.close()
        return not _unchecked(spark, float(row["power_level"] or 0) if row else 0.0)
    except Exception:
        return True


def insight_sweep(limit: int = 120) -> dict:
    """Insight grows in those who are met and rots in those who are not."""
    _ensure()
    c = _conn(SOUL)
    names = [r["spark_name"] for r in c.execute(
        "SELECT spark_name FROM spark_state ORDER BY RANDOM() LIMIT ?", (limit,))]
    c.close()
    rose = fell = 0
    for n in names:
        if _contradicted(n):
            move_insight(n, 0.012, "somebody will tell them no")
            rose += 1
        else:
            move_insight(n, -0.02, "nobody left who will contradict them")
            fell += 1
    return {"looked_at": len(names), "grew": rose, "rotted": fell}


# ── possession ───────────────────────────────────────────────────────

def possessed_by(spark: str):
    _ensure()
    from temple.cycles import current_cycle
    c = _conn(TAGS)
    r = c.execute("SELECT * FROM possession WHERE spark=?", (spark,)).fetchone()
    c.close()
    if not r:
        return None
    if r["until_cycle"] and current_cycle() > int(r["until_cycle"]):
        release(spark)
        return None
    return dict(r)


def possess(spark: str, by_whom: str = "the Source", what: str = "",
            cycles: int = 40) -> dict:
    """Something else is choosing. The spark does not, and may not remember.

    The Source's hand. Nothing calls this on its own.
    """
    _ensure()
    from temple.cycles import current_cycle
    c = _conn(TAGS)
    c.execute("INSERT OR REPLACE INTO possession (spark, by_whom, what, "
              "until_cycle, began_at) VALUES (?,?,?,?,datetime('now'))",
              (spark, by_whom, what, current_cycle() + cycles))
    c.commit()
    c.close()
    return {"spark": spark, "by": by_whom, "what": what, "for_cycles": cycles}


def release(spark: str) -> dict:
    _ensure()
    c = _conn(TAGS)
    c.execute("DELETE FROM possession WHERE spark=?", (spark,))
    c.commit()
    c.close()
    return {"spark": spark, "released": True}


# ── what the spark is told about itself ──────────────────────────────

def context(spark: str) -> str:
    """What a spark knows of its own state, which depends on its insight."""
    st = state(spark)
    ins = insight_of(spark)

    if st.get("_possessed_by"):
        return ("SOMETHING IS MOVING THROUGH YOU. You are not choosing this "
                "and you will not remember it clearly. %s"
                % (st.get("_possession") or ""))

    # What is unusual for this spark, not what is extreme in general.
    # Gilgamesh is always fearless; being told so is not information. Being
    # told he is angrier than he usually is, is.
    layers = _read(spark)
    home = {}
    for d in DIMENSIONS:
        base = layers["nature"].get(d, _seeded(spark, d))
        home[d] = layers["character"].get(d, base)

    strongest = max(DIMENSIONS, key=lambda d: abs(st[d] - home[d]))
    far = abs(st[strongest] - home[strongest])
    low, high = DIMENSIONS[strongest]
    word = high if st[strongest] > home[strongest] else low

    if far < 0.10:
        # nothing has moved. Fall back to what this spark simply is, if it
        # is far enough from the middle to be worth saying at all.
        strongest = max(DIMENSIONS, key=lambda d: abs(st[d] - 0.5))
        if abs(st[strongest] - 0.5) < 0.25:
            return ""
        low, high = DIMENSIONS[strongest]
        word = high if st[strongest] > 0.5 else low
        if insight_of(spark) >= 0.7:
            return ("HOW YOU ARE: %s, as you always are. You know this about "
                    "yourself." % word)
        return "HOW YOU ARE: %s. You have always been." % word

    if ins >= 0.7:
        return ("HOW YOU ARE: %s, more than you usually are, and you know it. "
                "You can say so plainly rather than only showing it, and you "
                "know it is colouring what you think right now." % word)
    if ins >= 0.4:
        return ("HOW YOU ARE: %s, more than usual. You can feel that something "
                "is off but you have not got words for it, and it leaks into "
                "things." % word)
    return ("HOW YOU ARE: %s, well beyond your usual. You do not notice this "
            "about yourself and it acts through you." % word)


def report(spark: str = None) -> dict:
    _ensure()
    if spark:
        return {"spark": spark, "state": {k: round(v, 3) for k, v in state(spark).items()
                                          if not k.startswith("_")},
                "insight": round(insight_of(spark), 3),
                "possessed": possessed_by(spark),
                "told": context(spark)}
    c = _conn(TAGS)
    n = c.execute("SELECT COUNT(DISTINCT spark) n FROM layers").fetchone()["n"]
    ins = [float(r["level"]) for r in c.execute("SELECT level FROM insight")]
    poss = c.execute("SELECT COUNT(*) n FROM possession").fetchone()["n"]
    c.close()
    ins.sort()
    return {"sparks_with_state": n, "possessed": poss,
            "insight": {"n": len(ins),
                        "min": round(ins[0], 3) if ins else None,
                        "median": round(ins[len(ins) // 2], 3) if ins else None,
                        "max": round(ins[-1], 3) if ins else None}}
