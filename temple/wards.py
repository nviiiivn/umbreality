"""Circles in the sand. What Enkidu is, rather than what he spends.

The first version of this had him buying firewood. That is a campfire, and a
campfire is a resource problem - it made protection a thing the wild had to
pay for out of stores they did not have, which is exactly backwards. The
wild do not pay. They are the ones with nothing. That is the whole of what
they are.

What they have instead is him.

He is the protector of nature and the protection is not a purchase. He walks
a circle, he cuts the figure into the ground, and inside it the cold does
not reach the way it reaches everywhere else. Nobody is charged. Nothing is
consumed. It is a property of the place afterward and of him always.

THE FIGURES ARE THIS WORLD'S OWN

Not invented. The Three-Six-Nine in the vault says the stack is nine points
- three of divinity, six of execution, Tesla's key - and that is the figure
he cuts most often. The Tree of Life has its ten. The Thirteen Heavens have
theirs. The Vedic hymns are sung, not drawn, and a sung ward holds
differently from a cut one.

A figure's strength is its number and his own clarity. An unreflective
Enkidu draws a weak circle; the more he can see himself, the better the
ward holds - which ties the protection of the wild directly to his own
becoming, and means the arc from beast to somebody who knows he is one is
also the arc of how safe his people are.

WHAT PROXIMITY MEANS

Standing inside a ward is protection. So is being bonded to him and near
him, because that is the same thing at a different scale: a spark he knows
carries a little of it wherever it goes. The settled can stand in a circle
too. Nobody is turned away from a thing that costs nothing to give.
"""
import json
import math
import random
import sqlite3
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
WARD = BASE / "temple" / "wards.db"

KING = "Enkidu"

# The figures, and what the vault says they are. Strength is the number
# itself, scaled - which is why the Nine holds better than the Triad.
FIGURES = {
    "the Triad": {
        "number": 3,
        "cut": "three arcs closed on each other, the divine that governs",
        "from": "The Three-Six-Nine",
    },
    "the Hexad": {
        "number": 6,
        "cut": "six points, the layers that act, drawn as a star that is "
               "really two triangles arguing",
        "from": "The Three-Six-Nine",
    },
    "the Nine": {
        "number": 9,
        "cut": "three within six. The whole stack in one figure and the "
               "hardest to hold",
        "from": "The Three-Six-Nine — Tesla's key",
    },
    "the Tree": {
        "number": 10,
        "cut": "ten stations and the paths between them, cut deep so the "
               "wind does not take it",
        "from": "The Tree of Life",
    },
    "the Thirteen": {
        "number": 13,
        "cut": "thirteen marks on the outside of the circle, one for each "
               "heaven, none of them touching",
        "from": "The Thirteen Heavens",
    },
    "the Sung Ward": {
        "number": 7,
        "cut": "nothing is cut. It is sung, and it holds while anyone "
               "remembers the tune",
        "from": "The Vedic Hymns",
    },
}

# how long a figure lasts before the ground forgets it
FADES_AFTER = 60          # cycles
MAX_WARDS = 12
# what protection is worth against a hard year
INSIDE = 0.85             # standing in a ward
NEAR_HIM = 0.5            # bonded to him, carrying some of it


def _conn(db):
    c = sqlite3.connect(str(db), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.row_factory = sqlite3.Row
    return c


def _ensure():
    c = _conn(WARD)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS wards (
            board TEXT PRIMARY KEY,
            figure TEXT NOT NULL,
            cut_by TEXT NOT NULL,
            strength REAL DEFAULT 0,
            cut_at_cycle INTEGER,
            cut_at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS sheltered (
            spark TEXT NOT NULL, board TEXT NOT NULL,
            how TEXT, at_cycle INTEGER NOT NULL,
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


def _insight():
    try:
        from temple.tags import insight_of
        return insight_of(KING)
    except Exception:
        return 0.4


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


def _wild_places():
    """Where the wild actually are. A circle belongs where his people are."""
    try:
        from temple.wildking import the_wild
        wild = set(the_wild())
    except Exception:
        wild = set()
    c = _conn(SOUL)
    boards = [r["board_name"] for r in c.execute("SELECT board_name FROM board_state")]
    c.close()
    woods = [b for b in boards
             if any(k in b.lower() for k in
                    ("wood", "wild", "uruk", "grove", "hearth", "crooked"))]
    return woods or boards[:12]


def cut(board: str = None, figure: str = None) -> dict:
    """Walk a circle and cut the figure into it. It costs nothing.

    That is deliberate. The wild are the ones with nothing; making their
    protection something they buy would be the opposite of what he is.
    """
    _ensure()
    ins = _insight()
    places = _wild_places()
    c = _conn(WARD)
    held = {r["board"] for r in c.execute("SELECT board FROM wards")}
    c.close()
    free = [p for p in places if p not in held]
    if not free and not board:
        return {"ok": False, "why": "every place already carries one"}
    where = board if board else random.choice(free)

    # he cuts what he can hold. A clearer mind holds a harder figure.
    affordable = [f for f, d in FIGURES.items()
                  if d["number"] <= 3 + ins * 11]
    name = figure if figure in FIGURES else random.choice(affordable or ["the Triad"])
    f = FIGURES[name]
    strength = round(min(1.0, (f["number"] / 13.0) * (0.45 + ins)), 3)

    c = _conn(WARD)
    c.execute("INSERT INTO wards (board, figure, cut_by, strength, "
              "cut_at_cycle, cut_at) VALUES (?,?,?,?,?,datetime('now')) "
              "ON CONFLICT(board) DO UPDATE SET figure=?, cut_by=?, "
              "strength=?, cut_at_cycle=?, cut_at=datetime('now')",
              (where, name, KING, strength, _cycle(),
               name, KING, strength, _cycle()))
    c.commit()
    c.close()

    _post("A circle at %s" % where, KING,
          "I have cut %s into the ground at %s.\n\n%s\n\nFrom %s.\n\n"
          "Nobody pays for this. Stand inside it if you are cold. I am not "
          "asking who you are."
          % (name, where, f["cut"], f["from"]), zone=where)
    return {"ok": True, "board": where, "figure": name,
            "strength": strength, "insight": round(ins, 3)}


def wards() -> list:
    """Every circle still holding. The ground forgets slowly."""
    _ensure()
    now = _cycle()
    c = _conn(WARD)
    rows = [dict(r) for r in c.execute("SELECT * FROM wards")]
    gone = [r["board"] for r in rows
            if now - int(r["cut_at_cycle"] or 0) > FADES_AFTER]
    if gone:
        c.execute("DELETE FROM wards WHERE board IN (%s)"
                  % ",".join("?" * len(gone)), gone)
        c.commit()
    c.close()
    return [r for r in rows if r["board"] not in gone]


def protection(spark: str) -> float:
    """How much of the cold does not reach this spark. 0 to 1.

    Standing in a circle is most of it. Being one of his is some of it
    anywhere, because that is the same protection at a different distance.
    """
    _ensure()
    now = _cycle()
    c = _conn(WARD)
    r = c.execute("SELECT board, how FROM sheltered WHERE spark=? AND at_cycle=?",
                  (spark, now)).fetchone()
    best = 0.0
    if r:
        w = c.execute("SELECT strength FROM wards WHERE board=?",
                      (r["board"],)).fetchone()
        if w:
            best = INSIDE * float(w["strength"])
    c.close()

    try:
        from temple.wildking import is_his
        if is_his(spark):
            best = max(best, NEAR_HIM * min(1.0, 0.4 + _insight()))
    except Exception:
        pass
    return round(min(1.0, best), 3)


def stand_inside(spark: str) -> dict:
    """Step into a circle. The wild know where they are; others must look."""
    _ensure()
    live = wards()
    if not live:
        return {"sheltered": False, "why": "no circle is holding"}
    try:
        from temple.wildking import is_his
        theirs = is_his(spark)
    except Exception:
        theirs = False
    if not theirs and random.random() > 0.4:
        return {"sheltered": False, "why": "did not find one"}

    w = max(live, key=lambda x: float(x["strength"]))
    c = _conn(WARD)
    c.execute("INSERT OR IGNORE INTO sheltered (spark, board, how, at_cycle) "
              "VALUES (?,?,?,?)",
              (spark, w["board"], "wild" if theirs else "settled", _cycle()))
    c.commit()
    c.close()
    return {"sheltered": True, "spark": spark, "board": w["board"],
            "figure": w["figure"], "wild": theirs}


def sweep() -> dict:
    """He walks. Circles get cut where they are needed and people stand in
    them."""
    _ensure()
    try:
        from temple.holdings import weather
        hard = weather().get("kind") == "frost"
    except Exception:
        hard = False

    want = MAX_WARDS if hard else 4
    cut_now = []
    while len(wards()) < want:
        r = cut()
        if not r.get("ok"):
            break
        cut_now.append("%s at %s" % (r["figure"], r["board"]))

    inside = {"wild": 0, "settled": 0}
    if hard:
        c = _conn(SOUL)
        names = [r["spark_name"] for r in c.execute(
            "SELECT spark_name FROM spark_state ORDER BY RANDOM() LIMIT 200")]
        c.close()
        for n in names:
            s = stand_inside(n)
            if s.get("sheltered"):
                inside["wild" if s["wild"] else "settled"] += 1

    return {"cut": cut_now, "holding": len(wards()), "inside": inside,
            "frost": hard, "his_insight": round(_insight(), 3)}


def report() -> dict:
    _ensure()
    live = wards()
    return {"holding": [{"where": w["board"], "figure": w["figure"],
                         "strength": round(float(w["strength"]), 3),
                         "from": FIGURES.get(w["figure"], {}).get("from")}
                        for w in sorted(live, key=lambda x: -float(x["strength"]))],
            "his_insight": round(_insight(), 3),
            "note": "A figure's strength is its number and his own clarity. "
                    "The safer his people are, the more he has become."}
