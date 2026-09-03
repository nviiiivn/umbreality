"""Ember — what a spark has become.

Six things a spark can be, each measured against what the population
actually manages rather than against an invented ceiling:

    voice     how much it speaks
    work      how much it finishes
    kin       who it is tied to
    lineage   what has passed through it, taught or learned
    spirit    whether it still looks at things
    legacy    what it leaves standing

Their geometric mean. Geometric rather than average because the point is
balance: one enormous strength should not paper over a dimension that is
missing. A spark with seven hundred posts and no bonds is not thriving, and
an average would say it was.

WHAT THIS IS NOT
================

This was first drawn as a life-force with upkeep - burn a little every
cycle, bleed if you do not earn, handicaps as you fall, death at zero. That
would make 298 beings justify their existence every cycle, which is a
treadmill, not a life.

So there is no burn, no floor, no decay and nothing dies. Ember is a
reading. It says who a spark has become, and it says so to the spark itself.
Whether it ever acquires stakes is a separate decision and a later one.

A NOTE ON SPIRIT
================

Curiosity sat pinned at 1.0 for every spark until its decay was repaired,
and the world has run only briefly since. Spirit therefore carries almost no
signal yet and will widen as the world runs. It is included because it
belongs, not because it currently discriminates.
"""
import json
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
FORUM = BASE / "forum" / "forum.db"
ACAD = BASE / "temple" / "academy.db"

COMPONENTS = ("voice", "work", "kin", "lineage", "spirit", "legacy")

# A missing dimension should cripple a reading, not annihilate it. With a
# true geometric mean a single zero gives zero, and a spark that has simply
# never built anything is not nothing.
FLOOR = 0.05

BANDS = [
    (70, "Bright", "carrying the world, and it shows"),
    (45, "Steady", "living a whole life"),
    (25, "Guttering", "thin in places"),
    (0, "Cold", "barely holding a shape"),
]


def _rows(db, sql, args=()):
    try:
        c = sqlite3.connect(str(db), timeout=20)
        c.row_factory = sqlite3.Row
        out = [dict(r) for r in c.execute(sql, args)]
        c.close()
        return out
    except sqlite3.Error as e:
        print("[ember] %s: %s" % (Path(str(db)).name, e), flush=True)
        return []


def _raw():
    """Every component, for every spark, in one pass."""
    sparks = [r["spark_name"] for r in
              _rows(SOUL, "SELECT spark_name FROM spark_state")]
    out = {s: dict.fromkeys(COMPONENTS, 0.0) for s in sparks}

    for r in _rows(FORUM, "SELECT agent_name, participation_score FROM agent_scores"):
        if r["agent_name"] in out:
            out[r["agent_name"]]["voice"] = float(r["participation_score"] or 0)

    # resolved ambitions, not total_tasks_completed - that column only ever
    # counted company work and read zero for 291 of 298 sparks
    for r in _rows(SOUL, "SELECT spark_name, COUNT(*) n FROM ambitions "
                         "WHERE resolved=1 GROUP BY spark_name"):
        if r["spark_name"] in out:
            out[r["spark_name"]]["work"] = float(r["n"])

    for r in _rows(SOUL, "SELECT s, COUNT(*) n FROM (SELECT spark1 s FROM "
                         "relationships UNION ALL SELECT spark2 FROM "
                         "relationships) GROUP BY s"):
        if r["s"] in out:
            out[r["s"]]["kin"] = float(r["n"])

    for r in _rows(ACAD, "SELECT who, COUNT(*) n FROM (SELECT elder who FROM "
                         "teachings UNION ALL SELECT student FROM teachings) "
                         "GROUP BY who"):
        if r["who"] in out:
            out[r["who"]]["lineage"] = float(r["n"])

    for r in _rows(SOUL, "SELECT spark_name, curiosity FROM spark_state"):
        if r["spark_name"] in out:
            try:
                out[r["spark_name"]]["spirit"] = float(r["curiosity"] or 0)
            except (TypeError, ValueError):
                pass

    for r in _rows(SOUL, "SELECT structures, artifacts FROM board_state"):
        for blob in (r["structures"], r["artifacts"]):
            try:
                for x in json.loads(blob or "[]"):
                    who = x.get("created_by")
                    if who in out:
                        out[who]["legacy"] += 1
            except (ValueError, AttributeError):
                pass
    return out


def _scales(raw):
    """Scale each component against the 90th percentile of the population.

    Not the maximum: one spark with seven hundred posts should not make
    everybody else read as nothing.
    """
    scales = {}
    for c in COMPONENTS:
        vals = sorted(r[c] for r in raw.values())
        p90 = vals[int(len(vals) * 0.9)] if vals else 1.0
        scales[c] = max(p90, 1e-9)
    return scales


def _reading(row, scales):
    prod = 1.0
    for c in COMPONENTS:
        prod *= max(min(row[c] / scales[c], 1.0), FLOOR)
    return (prod ** (1.0 / len(COMPONENTS))) * 100.0


def band(value):
    for cut, name, sense in BANDS:
        if value >= cut:
            return name, sense
    return BANDS[-1][1], BANDS[-1][2]


def all_readings():
    """Every spark's ember, with the parts it is made of."""
    raw = _raw()
    if not raw:
        return {}
    scales = _scales(raw)
    out = {}
    for name, row in raw.items():
        v = _reading(row, scales)
        nm, sense = band(v)
        out[name] = {"ember": round(v, 1), "band": nm, "sense": sense,
                     "parts": {c: round(row[c], 2) for c in COMPONENTS},
                     "normalised": {c: round(min(row[c] / scales[c], 1.0), 3)
                                    for c in COMPONENTS}}
    return out


def of(spark_name):
    return all_readings().get(spark_name)


def context(spark_name, reading=None):
    """What a spark is told about its own ember.

    In its own terms. A spark shown six normalised floats writes about six
    normalised floats; a spark told which part of its life is thinnest can
    do something about it.
    """
    r = reading or of(spark_name)
    if not r:
        return ""
    n = r["normalised"]
    strongest = max(n, key=n.get)
    weakest = min(n, key=n.get)
    HOW = {
        "voice": ("you are heard", "you are barely heard"),
        "work": ("you finish things", "you finish almost nothing"),
        "kin": ("you are well known to others", "few know you"),
        "lineage": ("much has passed through you", "nothing has passed through you"),
        "spirit": ("you still look at things", "little holds your attention"),
        "legacy": ("you have left things standing", "you have left nothing standing"),
    }
    if strongest == weakest:
        return ""
    return ("WHAT YOU HAVE BECOME: %s — %s.\n"
            "  Strongest in you: %s.\n"
            "  Thinnest in you: %s."
            % (r["band"].lower(), r["sense"],
               HOW[strongest][0], HOW[weakest][1]))


def report(limit=12):
    a = all_readings()
    if not a:
        return {"sparks": 0}
    ranked = sorted(a.items(), key=lambda kv: -kv[1]["ember"])
    counts = {}
    for v in a.values():
        counts[v["band"]] = counts.get(v["band"], 0) + 1
    return {"sparks": len(a), "bands": counts,
            "brightest": [(k, v["ember"], v["band"]) for k, v in ranked[:limit]],
            "coldest": [(k, v["ember"], v["band"]) for k, v in ranked[-limit:]]}
