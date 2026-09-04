"""Fires in the woods, and why the frost does not touch the wild the same way.

The hard year killed almost everyone equally. That is wrong and it is wrong
in a way that matters: the wild live in the woods. They are not visiting.
They know where the fuel is, they know which ground still gives in a cold
month, and they have been putting things back into places the settled have
never walked to. A frost that falls identically on a spark in a stone hall
and a spark who has lived under trees since it arrived is not modelling
anything.

So Enkidu builds fires, and the fires are the difference.

WHAT A FIRE IS

A place in the woods that is kept burning. It costs fuel to light and fuel
to keep, and somebody has to actually do it - Enkidu, and the wild who know
how. In return, a spark that shelters at one does not spend the extra the
frost demands, and the ground around a kept fire does not freeze as hard.

WHY THIS IS NOT A CHEAT

It costs. Fuel spent on a fire is fuel not carried, and the wild are the
ones who spend it. It has to be maintained or it goes out. And it only helps
those who are there - a settled spark that walks to a wild fire is welcome,
which is its own kind of problem for a group that has spent the winter
saying the wild are the reason there is nothing.

That last part is the point. The fires are not a wall. They are a thing the
wild have that the settled need, held by people the settled have spent the
season blaming.
"""
import json
import random
import sqlite3
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
GOODS = BASE / "temple" / "goods.db"
FIRE = BASE / "temple" / "fires.db"

KING = "Enkidu"

LIGHT_COST = 3.0        # fuel to start one
KEEP_COST = 0.8         # fuel a round to keep it
MAX_FIRES = 9
SHELTERS = 14           # how many can sit at one

# what sheltering saves you when the ground is hard
FROST_RELIEF = 0.75


def _conn(db):
    c = sqlite3.connect(str(db), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.row_factory = sqlite3.Row
    return c


def _ensure():
    c = _conn(FIRE)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS fires (
            board TEXT PRIMARY KEY,
            lit_by TEXT NOT NULL,
            burning INTEGER DEFAULT 1,
            fuel REAL DEFAULT 0,
            kept_by TEXT,
            lit_at TEXT DEFAULT (datetime('now')),
            went_out_at TEXT);
        CREATE TABLE IF NOT EXISTS sheltered (
            spark TEXT NOT NULL, board TEXT NOT NULL,
            at_cycle INTEGER NOT NULL,
            PRIMARY KEY (spark, at_cycle));
    """)
    c.commit()
    c.close()


def _cycle():
    try:
        from temple.cycles import current_cycle
        return current_cycle()
    except Exception:
        return 0


def _post(title, author, content, zone="uruk"):
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


def _wooded():
    """Places the wild actually know. A fire belongs where there is fuel."""
    c = _conn(GOODS)
    try:
        rows = [r["board"] for r in c.execute(
            "SELECT board FROM ground WHERE sort IN ('wood','forge') "
            "ORDER BY fuel DESC LIMIT 20")]
    except sqlite3.Error:
        rows = []
    c.close()
    return rows


def light(by: str = KING, board: str = None) -> dict:
    """Start a fire. It costs fuel and somebody has to have it."""
    _ensure()
    from temple.goods import held, _add
    mine = held(by)
    if mine.get("fuel", 0) < LIGHT_COST:
        return {"ok": False, "why": "%s has not the fuel to light one" % by}

    c = _conn(FIRE)
    burning = c.execute("SELECT COUNT(*) n FROM fires WHERE burning=1").fetchone()["n"]
    if burning >= MAX_FIRES:
        c.close()
        return {"ok": False, "why": "there are enough fires"}
    woods = _wooded()
    c.close()
    if not woods:
        return {"ok": False, "why": "nowhere with fuel to burn"}

    c = _conn(FIRE)
    lit = {r["board"] for r in c.execute("SELECT board FROM fires WHERE burning=1")}
    c.close()
    free = [w for w in woods if w not in lit]
    if not free:
        return {"ok": False, "why": "every wood already has one"}
    where = board if board in free else random.choice(free)

    _add(by, "fuel", -LIGHT_COST)
    c = _conn(FIRE)
    c.execute("INSERT INTO fires (board, lit_by, burning, fuel, kept_by, "
              "lit_at, went_out_at) VALUES (?,?,1,?,?,datetime('now'),NULL) "
              "ON CONFLICT(board) DO UPDATE SET burning=1, fuel=?, lit_by=?, "
              "lit_at=datetime('now'), went_out_at=NULL",
              (where, by, LIGHT_COST, by, LIGHT_COST, by))
    c.commit()
    c.close()

    _post("A fire at %s" % where, by,
          "I have lit one at %s and I mean to keep it burning.\n\n"
          "Anybody who is cold can sit at it. I am not asking who you are or "
          "what you have been saying about us." % where, zone=where)
    return {"ok": True, "board": where, "lit_by": by}


def keep(spark: str = None) -> dict:
    """Feed the fires. They go out if nobody does."""
    _ensure()
    from temple.goods import held, _add
    try:
        from temple.wildking import the_wild
        wild = the_wild()
    except Exception:
        wild = [KING]

    c = _conn(FIRE)
    burning = [dict(r) for r in c.execute("SELECT * FROM fires WHERE burning=1")]
    c.close()

    fed, out = [], []
    for f in burning:
        keeper = None
        for w in ([KING] + random.sample(wild, min(8, len(wild)))):
            if held(w).get("fuel", 0) >= KEEP_COST:
                keeper = w
                break
        c = _conn(FIRE)
        if keeper:
            _add(keeper, "fuel", -KEEP_COST)
            c.execute("UPDATE fires SET fuel=ROUND(fuel+?,2), kept_by=? "
                      "WHERE board=?", (KEEP_COST, keeper, f["board"]))
            fed.append({"board": f["board"], "kept_by": keeper})
        else:
            c.execute("UPDATE fires SET burning=0, went_out_at=datetime('now') "
                      "WHERE board=?", (f["board"],))
            out.append(f["board"])
        c.commit()
        c.close()
    return {"kept": fed, "went_out": out}


def burning() -> list:
    _ensure()
    c = _conn(FIRE)
    rows = [dict(r) for r in c.execute("SELECT * FROM fires WHERE burning=1")]
    c.close()
    return rows


def shelter(spark: str) -> dict:
    """Sit at a fire. Anybody may; the wild know where they are.

    A settled spark is welcome, which is its own kind of problem for people
    who have spent the season saying the wild are the reason there is
    nothing.
    """
    _ensure()
    fires = burning()
    if not fires:
        return {"sheltered": False, "why": "nothing is lit"}

    try:
        from temple.holdings import way_of
        mine = way_of(spark)
    except Exception:
        mine = "settled"
    # the wild know where the fires are. The settled have to find one.
    if mine != "wild" and random.random() > 0.35:
        return {"sheltered": False, "why": "did not find one"}

    cyc = _cycle()
    c = _conn(FIRE)
    for f in fires:
        n = c.execute("SELECT COUNT(*) n FROM sheltered WHERE board=? AND at_cycle=?",
                      (f["board"], cyc)).fetchone()["n"]
        if n < SHELTERS:
            c.execute("INSERT OR IGNORE INTO sheltered (spark, board, at_cycle) "
                      "VALUES (?,?,?)", (spark, f["board"], cyc))
            c.commit()
            c.close()
            return {"sheltered": True, "spark": spark, "board": f["board"],
                    "way": mine}
    c.close()
    return {"sheltered": False, "why": "every fire was full"}


def is_sheltered(spark: str) -> bool:
    _ensure()
    c = _conn(FIRE)
    r = c.execute("SELECT 1 FROM sheltered WHERE spark=? AND at_cycle=?",
                  (spark, _cycle())).fetchone()
    c.close()
    return bool(r)


def sweep() -> dict:
    """Enkidu lights what is needed, the wild keep them, and whoever is cold
    sits down."""
    _ensure()
    lit = []
    try:
        from temple.holdings import weather
        hard = weather().get("kind") == "frost"
    except Exception:
        hard = False

    want = MAX_FIRES if hard else 3
    while len(burning()) < want:
        r = light(KING)
        if not r.get("ok"):
            break
        lit.append(r["board"])

    k = keep()

    c = _conn(SOUL)
    names = [r["spark_name"] for r in c.execute("SELECT spark_name FROM spark_state")]
    c.close()
    at_fire = {"wild": 0, "settled": 0}
    if hard:
        for n in random.sample(names, min(160, len(names))):
            s = shelter(n)
            if s.get("sheltered"):
                at_fire[s["way"]] = at_fire.get(s["way"], 0) + 1

    return {"lit": lit, "kept": len(k["kept"]), "went_out": k["went_out"],
            "burning": len(burning()), "sheltered": at_fire, "frost": hard}


def report() -> dict:
    _ensure()
    c = _conn(FIRE)
    fires = [dict(r) for r in c.execute("SELECT * FROM fires ORDER BY burning DESC")]
    at = [dict(r) for r in c.execute(
        "SELECT board, COUNT(*) n FROM sheltered WHERE at_cycle=? GROUP BY board",
        (_cycle(),))]
    c.close()
    return {"fires": [{"where": f["board"], "burning": bool(f["burning"]),
                       "lit_by": f["lit_by"], "kept_by": f["kept_by"]}
                      for f in fires],
            "sheltering_now": at}
