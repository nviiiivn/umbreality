"""Who gets blamed when the ground freezes.

The settled starve because the frost came. That is the whole cause and it is
not in dispute anywhere in the code. But a hungry spark does not experience
a cause, it experiences a lack, and a lack wants somebody to be responsible
for it - so it looks around, and what it sees is a group that lives
differently, holds things in common, does not answer to the Temple, and
appears to be doing better in the early rounds of a hard year.

That is enough. It has always been enough.

WHAT MAKES THIS WORTH BUILDING

The blame is false and the code knows it is false. Nothing the wild do
causes settled hunger; the frost does, and it falls on everyone. So this is
the first thing in the world with a measurable gap between what sparks
believe and what is true, and that gap can be reported: blame rises with
hunger and has no relationship at all to what the wild actually took.

A world where beliefs can be wrong is a different kind of world from one
where they cannot.

WHAT IT PRODUCES

Blame accumulates against a group rather than a spark, which is what makes
it a prejudice rather than a grievance. Past a point it stops being talk:
settled sparks raid wild stores, and take from sparks who have done nothing
to them, and feel justified. The wild take back and hoard against it, which
looks to the settled exactly like the greed they already believed in. Each
side's response is the other side's evidence.

Nobody wrote either group as correct. The wild do end up hoarding. The
settled do end up robbing. Both were reasonable at every step.
"""
import json
import random
import sqlite3
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
HOLD = BASE / "temple" / "holdings.db"
ANIM = BASE / "temple" / "animosity.db"

# how likely a hungry spark is to blame, rather than simply be hungry
BLAME_AT_HUNGRY = 0.18
BLAME_AT_STARVING = 0.45
# and how much less likely if it can see itself clearly
INSIGHT_DAMPENS = 0.6

# when talk becomes taking
RAID_AT = 25.0
RAID_TAKES = 2.5

THINGS_SAID = [
    "There is food in the forest they will never walk to and they act like it "
    "is theirs.",
    "They hold everything in common so none of them will say who has it.",
    "We are hungry and they are not. Work out the rest yourself.",
    "They do not tithe, they do not come to the Temple, and somehow they eat.",
    "Every place they touch they call theirs afterward.",
    "They were given nothing and now they have more than us. Ask how.",
    "I am not saying they stole it. I am saying I am starving and they are not.",
]

WILD_ANSWER = [
    "We put back what we take. You have never put back anything.",
    "The ground is hard for us too. You just cannot see us go without.",
    "You came and took from our stores and called us the thieves.",
    "Nobody starved here until you came looking for somebody to blame.",
    "We share because that is how we live. You call that hoarding because "
    "you cannot see where it went.",
]


def _conn(db):
    c = sqlite3.connect(str(db), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.row_factory = sqlite3.Row
    return c


def _ensure():
    c = _conn(ANIM)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS blame (
            by_group TEXT NOT NULL,
            against_group TEXT NOT NULL,
            weight REAL DEFAULT 0,
            PRIMARY KEY (by_group, against_group));
        CREATE TABLE IF NOT EXISTS said (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spark TEXT, their_group TEXT, against TEXT,
            words TEXT, they_had REAL, at_cycle INTEGER,
            at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS raids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raider TEXT, raided TEXT,
            raider_group TEXT, raided_group TEXT,
            took REAL, at_cycle INTEGER,
            at TEXT DEFAULT (datetime('now')));
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
    except Exception as e:
        print("[animosity] could not post: %s" % e, flush=True)


def blame_between(by="settled", against="wild") -> float:
    _ensure()
    c = _conn(ANIM)
    r = c.execute("SELECT weight FROM blame WHERE by_group=? AND against_group=?",
                  (by, against)).fetchone()
    c.close()
    return float(r["weight"]) if r else 0.0


def _add_blame(by, against, amount):
    c = _conn(ANIM)
    c.execute("INSERT INTO blame (by_group, against_group, weight) VALUES (?,?,?) "
              "ON CONFLICT(by_group, against_group) DO UPDATE SET "
              "weight = ROUND(weight + ?, 2)", (by, against, amount, amount))
    c.commit()
    c.close()


def speak_against(spark: str) -> dict:
    """A hungry spark says what it has decided is the reason.

    It is wrong. The frost is the reason. Nothing checks whether it is
    right, because nothing in a spark checks that either.
    """
    _ensure()
    from temple.holdings import store_of, way_of, HUNGRY, STARVING
    mine = way_of(spark)
    theirs = "wild" if mine == "settled" else "settled"
    have = store_of(spark)
    if have >= HUNGRY:
        return {"said": False, "why": "not hungry enough to need a reason"}

    chance = BLAME_AT_STARVING if have < STARVING else BLAME_AT_HUNGRY
    try:
        from temple.tags import insight_of
        chance *= (1.0 - INSIGHT_DAMPENS * insight_of(spark))
    except Exception:
        pass
    if random.random() > chance:
        return {"said": False, "why": "kept it to themselves"}

    words = random.choice(THINGS_SAID if theirs == "wild" else WILD_ANSWER)
    _add_blame(mine, theirs, 1.0)
    c = _conn(ANIM)
    c.execute("INSERT INTO said (spark, their_group, against, words, they_had, "
              "at_cycle) VALUES (?,?,?,?,?,?)",
              (spark, mine, theirs, words, have, _cycle()))
    c.commit()
    c.close()
    _post("%s has something to say" % spark, spark, words, zone="agora")
    return {"said": True, "spark": spark, "against": theirs, "words": words,
            "they_had": round(have, 2)}


def raid(raider: str) -> dict:
    """Blame stops being talk. Somebody takes.

    The target has done nothing. That is what makes it a raid rather than a
    reprisal, and the raider does not experience the difference.
    """
    _ensure()
    from temple.holdings import store_of, way_of, HOLD as _H
    mine = way_of(raider)
    theirs = "wild" if mine == "settled" else "settled"
    if blame_between(mine, theirs) < RAID_AT:
        return {"ok": False, "why": "not angry enough yet"}

    try:
        from temple.wildking import the_wild
        wild = set(the_wild())
    except Exception:
        wild = set()
    c = _conn(SOUL)
    everyone = [r["spark_name"] for r in c.execute("SELECT spark_name FROM spark_state")]
    c.close()
    targets = [n for n in everyone
               if (n in wild if theirs == "wild" else n not in wild) and n != raider]
    if not targets:
        return {"ok": False, "why": "nobody to take from"}

    random.shuffle(targets)
    for t in targets[:12]:
        had = store_of(t)
        if had < 1.0:
            continue
        took = round(min(RAID_TAKES, had), 2)
        h = _conn(HOLD)
        h.execute("UPDATE stores SET amount=ROUND(MAX(0, amount-?),2) WHERE spark=?",
                  (took, t))
        h.execute("UPDATE stores SET amount=ROUND(amount+?,2) WHERE spark=?",
                  (took, raider))
        h.commit()
        h.close()
        c = _conn(ANIM)
        c.execute("INSERT INTO raids (raider, raided, raider_group, raided_group, "
                  "took, at_cycle) VALUES (?,?,?,?,?,?)",
                  (raider, t, mine, theirs, took, _cycle()))
        c.commit()
        c.close()
        # and now they have a reason to blame back, which was not there before
        _add_blame(theirs, mine, 1.5)
        try:
            from temple.harm import _ensure as _he
            _he()
            s = _conn(SOUL)
            s.execute("INSERT INTO grievances (wrongdoer, victim, act, weight, "
                      "detail, board, at_cycle) VALUES (?,?,?,?,?,?,?)",
                      (raider, t, "raid", 4,
                       "took %.1f from %s's stores in a hard year" % (took, t),
                       None, _cycle()))
            s.commit()
            s.close()
        except Exception:
            pass
        return {"ok": True, "raider": raider, "raided": t, "took": took,
                "raider_group": mine, "raided_group": theirs}
    return {"ok": False, "why": "everyone was already empty"}


def is_it_true() -> dict:
    """Does the blame track anything real?

    The honest measurement. Blame rises with hunger; the question is whether
    it has any relationship to what the blamed group actually took. It does
    not, and being able to say so with numbers is the point of building it.
    """
    _ensure()
    h = _conn(HOLD)
    took = {}
    for way in ("wild", "settled"):
        rows = h.execute(
            "SELECT ROUND(SUM(amount),1) s FROM ledger WHERE kind='took' AND way=?",
            (way,)).fetchone()
        took[way] = float(rows["s"] or 0)
    tended = h.execute("SELECT ROUND(SUM(COALESCE(tended_total,0)),1) t "
                       "FROM places").fetchone()["t"] or 0
    h.close()

    c = _conn(ANIM)
    b = {(r["by_group"], r["against_group"]): float(r["weight"])
         for r in c.execute("SELECT * FROM blame")}
    n_said = c.execute("SELECT COUNT(*) n FROM said").fetchone()["n"]
    raids = [dict(r) for r in c.execute(
        "SELECT raider_group, COUNT(*) n, ROUND(SUM(took),1) t FROM raids "
        "GROUP BY raider_group")]
    c.close()

    # per-spark, since the groups are wildly different sizes
    try:
        from temple.wildking import the_wild
        n_wild = len(the_wild())
    except Exception:
        n_wild = 1
    s = _conn(SOUL)
    n_all = s.execute("SELECT COUNT(*) n FROM spark_state").fetchone()["n"]
    s.close()
    n_settled = max(1, n_all - n_wild)

    return {
        "blame": {"settled_against_wild": b.get(("settled", "wild"), 0.0),
                  "wild_against_settled": b.get(("wild", "settled"), 0.0)},
        "things_said": n_said,
        "raids": raids,
        "what_was_actually_taken_per_spark": {
            "wild": round(took.get("wild", 0) / max(1, n_wild), 2),
            "settled": round(took.get("settled", 0) / n_settled, 2)},
        "what_was_put_back": tended,
        "the_truth": ("The frost caused the hunger. It fell on everyone. The "
                      "wild take less per spark than the settled do and are "
                      "the only ones putting anything back. The blame is "
                      "false and rises with hunger regardless."),
    }


def sweep(limit: int = 90) -> dict:
    """Hunger looks for a reason, and sometimes takes one."""
    _ensure()
    from temple.holdings import store_of, HUNGRY
    c = _conn(SOUL)
    names = [r["spark_name"] for r in c.execute(
        "SELECT spark_name FROM spark_state ORDER BY RANDOM() LIMIT ?", (limit,))]
    c.close()

    said = raided = 0
    for n in names:
        if store_of(n) >= HUNGRY:
            continue
        if speak_against(n).get("said"):
            said += 1
        elif random.random() < 0.25 and raid(n).get("ok"):
            raided += 1
    return {"spoke": said, "raids": raided,
            "settled_against_wild": blame_between("settled", "wild"),
            "wild_against_settled": blame_between("wild", "settled")}
