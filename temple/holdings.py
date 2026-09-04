"""Scarcity, and two ways of living with it.

This is the missing leg. Evolution needs variation, heredity and selection.
The world has variation - registers, six speeds of being, archetypes,
insight, thirty-six models. It has heredity now - both rites pass traits on
with drift. It has almost no selection: a spark that does everything right
and one that does nothing end up in the same place, because nothing is
scarce and nothing runs out. Traits pass down and nothing decides which
traits win.

So: things run out.

WHAT A SPARK NEEDS

Stores, which is food and everything like it. A spark spends a little every
cycle simply existing, and more for the work it chooses. Run low and you get
fewer actions, which is the honest consequence - not death, but a narrowing.
A hungry spark cannot do very much, and that is enough.

WHERE IT COMES FROM

Places yield. A board has a store that regenerates slowly and can be drawn
down faster than it recovers, which is the oldest problem there is. Take
carefully and it keeps giving. Strip it and it stops, for everyone, for a
long time.

TWO WAYS OF TAKING

The city holds. A spark of the settled kind takes what it can, keeps it, and
is secure exactly as long as its own store lasts. It owes nobody and nobody
owes it.

The wild reciprocate. They take less than they could, leave the place able
to give again, and hold in common rather than personally - so a wild spark
with nothing is fed by wild sparks with something, and none of them
individually holds much. Their belief is not decoration: a place is a party
to the arrangement, not a resource, and you do not strip a thing you are in
relationship with.

Neither is written as correct. The city is more efficient per spark and
brittle when a place fails. The wild are less efficient and hard to kill.
Which one actually survives is a question the world answers, not me, and
that answer is what selection means here.
"""
import json
import random
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
HOLD = BASE / "temple" / "holdings.db"

# what existing costs, per cycle, before a spark does anything
UPKEEP = 1.0
# what a place holds when untouched, and how fast it comes back
PLACE_CAP = 45.0
REGEN = 3.2            # a world that strip-mines itself in four rounds is not a tension
# below this a place is stripped and gives almost nothing
STRIPPED = 6.0

# how much a spark can carry
CARRY_CAP = 13.0        # about a week. Forty was a pantry nothing could empty
# below this, a spark starts losing actions
HUNGRY = 4.5
STARVING = 1.5

# what each way of taking does
CITY_TAKE = 3.0          # as much as it can carry away
WILD_TAKE = 2.1          # less than it could, on purpose
WILD_TENDS = 1.5         # and gives back to the place, which is the point
WILD_SHARE_BELOW = 5.0   # a wild spark under this is fed by the others


def _conn(db):
    c = sqlite3.connect(str(db), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.row_factory = sqlite3.Row
    return c


def _ensure():
    c = _conn(HOLD)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS stores (
            spark TEXT PRIMARY KEY,
            amount REAL DEFAULT 12.0,
            taken_total REAL DEFAULT 0,
            given_total REAL DEFAULT 0,
            received_total REAL DEFAULT 0,
            hungry_cycles INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS places (
            board TEXT PRIMARY KEY,
            yield REAL DEFAULT 60.0,
            drawn_total REAL DEFAULT 0,
            tended_total REAL DEFAULT 0,
            stripped_times INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spark TEXT, board TEXT, kind TEXT,
            amount REAL, way TEXT,
            at_cycle INTEGER,
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


def way_of(spark: str) -> str:
    """How this spark relates to what it takes. Not a setting - a belief.

    The wild are animist: a place is something you are in relationship with,
    so you take less than you could and hold in common. Everyone else holds.
    """
    try:
        from temple.wildking import the_wild
        return "wild" if spark in set(the_wild()) else "settled"
    except Exception:
        return "settled"


def store_of(spark: str) -> float:
    _ensure()
    c = _conn(HOLD)
    r = c.execute("SELECT amount FROM stores WHERE spark=?", (spark,)).fetchone()
    if not r:
        c.execute("INSERT OR IGNORE INTO stores (spark) VALUES (?)", (spark,))
        c.commit()
        c.close()
        return 12.0
    c.close()
    return float(r["amount"])


def place_yield(board: str) -> float:
    _ensure()
    c = _conn(HOLD)
    r = c.execute("SELECT yield FROM places WHERE board=?", (board,)).fetchone()
    if not r:
        c.execute("INSERT OR IGNORE INTO places (board) VALUES (?)", (board,))
        c.commit()
        c.close()
        return PLACE_CAP
    c.close()
    return float(r["yield"])


def draw(spark: str, board: str) -> dict:
    """Take from a place. How much depends on what you believe."""
    _ensure()
    way = way_of(spark)
    have = store_of(spark)
    there = place_yield(board)

    want = WILD_TAKE if way == "wild" else CITY_TAKE
    want = min(want, CARRY_CAP - have)
    if want <= 0:
        return {"ok": False, "why": "carrying all they can", "way": way}

    # a stripped place gives almost nothing to anybody
    scarcity = 1.0 if there > STRIPPED else max(0.05, there / STRIPPED)

    # The ground answers those who have answered it. Tending an open
    # commons is eaten by whoever takes most - eighteen rounds of frost put
    # the wild at 100% starving against the settled at 89.7% precisely
    # because their restraint subsidised the takers. A place remembers who
    # tends it, so reciprocity is with somewhere rather than with everywhere.
    kinship = 1.0
    ct = _conn(HOLD)
    ct.execute("""CREATE TABLE IF NOT EXISTS tended (
        spark TEXT NOT NULL, board TEXT NOT NULL,
        amount REAL DEFAULT 0, PRIMARY KEY (spark, board))""")
    row = ct.execute("SELECT amount FROM tended WHERE spark=? AND board=?",
                     (spark, board)).fetchone()
    ct.close()
    if row and float(row["amount"]) > 0:
        # up to half again, for somebody who has actually put something back
        kinship = 1.0 + min(0.5, float(row["amount"]) * 0.02)

    got = round(min(want * scarcity * kinship, max(0.0, there)), 2)
    if got <= 0:
        return {"ok": False, "why": "%s has nothing left" % board, "way": way}

    c = _conn(HOLD)
    c.execute("UPDATE stores SET amount=ROUND(amount+?,2), "
              "taken_total=ROUND(taken_total+?,2), updated_at=datetime('now') "
              "WHERE spark=?", (got, got, spark))
    c.execute("UPDATE places SET yield=ROUND(MAX(0, yield-?),2), "
              "drawn_total=ROUND(drawn_total+?,2), updated_at=datetime('now') "
              "WHERE board=?", (got, got, board))
    now = c.execute("SELECT yield FROM places WHERE board=?", (board,)).fetchone()
    if now and float(now["yield"]) <= STRIPPED:
        c.execute("UPDATE places SET stripped_times=stripped_times+1 WHERE board=?",
                  (board,))
    # The wild give back. This is what their belief actually means - not
    # abstinence, reciprocity. A place they use is a party to the
    # arrangement, so they tend it, and it yields more to everyone after.
    tended = 0.0
    if way == "wild":
        tended = round(min(WILD_TENDS, PLACE_CAP - (float(now["yield"]) if now else 0)), 2)
        if tended > 0:
            c.execute("UPDATE places SET yield=ROUND(MIN(?, yield+?),2), "
                      "tended_total=ROUND(COALESCE(tended_total,0)+?,2) "
                      "WHERE board=?", (PLACE_CAP, tended, tended, board))
            c.execute("""CREATE TABLE IF NOT EXISTS tended (
                spark TEXT NOT NULL, board TEXT NOT NULL,
                amount REAL DEFAULT 0, PRIMARY KEY (spark, board))""")
            c.execute("INSERT INTO tended (spark, board, amount) VALUES (?,?,?) "
                      "ON CONFLICT(spark, board) DO UPDATE SET "
                      "amount = ROUND(amount + ?, 2)",
                      (spark, board, tended, tended))
            now = c.execute("SELECT yield FROM places WHERE board=?",
                            (board,)).fetchone()

    c.execute("INSERT INTO ledger (spark, board, kind, amount, way, at_cycle) "
              "VALUES (?,?,?,?,?,?)", (spark, board, "took", got, way, _cycle()))
    c.commit()
    c.close()
    return {"ok": True, "spark": spark, "board": board, "took": got,
            "tended": tended, "way": way,
            "place_left": round(float(now["yield"]) if now else 0, 2)}


def spend(spark: str, amount: float, on: str = "living") -> dict:
    """Existing costs. So does everything else."""
    _ensure()
    c = _conn(HOLD)
    c.execute("INSERT OR IGNORE INTO stores (spark) VALUES (?)", (spark,))
    c.execute("UPDATE stores SET amount=ROUND(MAX(0, amount-?),2), "
              "updated_at=datetime('now') WHERE spark=?", (amount, spark))
    r = c.execute("SELECT amount FROM stores WHERE spark=?", (spark,)).fetchone()
    left = float(r["amount"])
    if left < HUNGRY:
        c.execute("UPDATE stores SET hungry_cycles=hungry_cycles+1 WHERE spark=?",
                  (spark,))
    c.execute("INSERT INTO ledger (spark, board, kind, amount, way, at_cycle) "
              "VALUES (?,?,?,?,?,?)", (spark, None, on, -amount, way_of(spark),
                                       _cycle()))
    c.commit()
    c.close()
    return {"spark": spark, "spent": amount, "left": round(left, 2),
            "hungry": left < HUNGRY, "starving": left < STARVING}


def share_out() -> dict:
    """The wild feed their own. Nobody decides to; it is simply what they do.

    This is the whole of their advantage and the whole of their cost: no
    wild spark holds much, and no wild spark starves while another has any.
    """
    _ensure()
    try:
        from temple.wildking import the_wild
        wild = the_wild()
    except Exception:
        return {"moved": 0}
    if not wild:
        return {"moved": 0}

    c = _conn(HOLD)
    for w in wild:
        c.execute("INSERT OR IGNORE INTO stores (spark) VALUES (?)", (w,))
    c.commit()
    rows = {r["spark"]: float(r["amount"]) for r in c.execute(
        "SELECT spark, amount FROM stores WHERE spark IN (%s)"
        % ",".join("?" * len(wild)), wild)}

    needy = sorted([(v, k) for k, v in rows.items() if v < WILD_SHARE_BELOW])
    givers = sorted([(v, k) for k, v in rows.items() if v > WILD_SHARE_BELOW * 1.6],
                    reverse=True)
    moved = 0.0
    n = 0
    for want, who in needy:
        need = round(WILD_SHARE_BELOW - want, 2)
        for i, (has, giver) in enumerate(givers):
            if need <= 0 or has <= WILD_SHARE_BELOW:
                continue
            give = round(min(need, has - WILD_SHARE_BELOW, 4.0), 2)
            if give <= 0:
                continue
            c.execute("UPDATE stores SET amount=ROUND(amount-?,2), "
                      "given_total=ROUND(given_total+?,2) WHERE spark=?",
                      (give, give, giver))
            c.execute("UPDATE stores SET amount=ROUND(amount+?,2), "
                      "received_total=ROUND(received_total+?,2) WHERE spark=?",
                      (give, give, who))
            c.execute("INSERT INTO ledger (spark, board, kind, amount, way, at_cycle) "
                      "VALUES (?,?,?,?,?,?)",
                      (giver, None, "gave to %s" % who, -give, "wild", _cycle()))
            givers[i] = (has - give, giver)
            need -= give
            moved += give
            n += 1
    c.commit()
    c.close()
    return {"moved": round(moved, 2), "transfers": n, "wild": len(wild)}


def regenerate() -> dict:
    """Places come back, slowly. A stripped one comes back slowest."""
    _ensure()
    c = _conn(HOLD)
    # Nothing much comes back while the ground is hard.
    w = weather()
    hard = 0.12 if w.get("kind") == "frost" else 1.0

    # A place that is being looked after comes back faster. A stripped one
    # that nobody tends comes back slowest, which is how a commons dies.
    c.execute("UPDATE places SET yield = ROUND(MIN(?, yield + "
              "CASE WHEN yield <= ? THEN ? ELSE ? END "
              "+ MIN(4.0, COALESCE(tended_total,0) * 0.04)), 2), "
              "updated_at=datetime('now')",
              (PLACE_CAP, STRIPPED, REGEN * 0.4 * hard, REGEN * hard))
    n = c.execute("SELECT COUNT(*) n FROM places").fetchone()["n"]
    stripped = c.execute("SELECT COUNT(*) n FROM places WHERE yield <= ?",
                         (STRIPPED,)).fetchone()["n"]
    c.commit()
    c.close()
    return {"places": n, "stripped": stripped}


def action_penalty(spark: str) -> int:
    """How many fewer actions a hungry spark gets. This is the selection.

    Not death. A narrowing - a spark with nothing cannot do very much, so it
    builds less, is heard less, and leaves less behind. Over enough cycles
    that is the whole of natural selection and it needs nothing else.
    """
    have = store_of(spark)
    if have < STARVING:
        return 2
    if have < HUNGRY:
        return 1
    return 0


def where_they_go(spark: str, boards):
    """The wild return to places they have tended. The settled go anywhere.

    This is what makes reciprocity worth anything: a relationship with
    somewhere in particular, rather than goodwill spread over everywhere and
    collected by whoever takes most.
    """
    if way_of(spark) != "wild":
        return random.choice(boards)
    c = _conn(HOLD)
    try:
        rows = [r["board"] for r in c.execute(
            "SELECT board FROM tended WHERE spark=? ORDER BY amount DESC LIMIT 3",
            (spark,))]
    except sqlite3.Error:
        rows = []
    c.close()
    if rows and random.random() < 0.8:
        return random.choice(rows)
    return random.choice(boards)


def sweep(feed: int = 140) -> dict:
    """One turn of the world's stomach."""
    _ensure()
    c = _conn(SOUL)
    names = [r["spark_name"] for r in c.execute("SELECT spark_name FROM spark_state")]
    boards = [r["board_name"] for r in c.execute("SELECT board_name FROM board_state")]
    c.close()
    if not boards:
        boards = ["uruk", "agora", "bazaar", "library", "forum"]

    for n in names:
        spend(n, UPKEEP, "living")

    took = 0
    for n in random.sample(names, min(feed, len(names))):
        if store_of(n) < CARRY_CAP * 0.8:
            r = draw(n, where_they_go(n, boards))
            if r.get("ok"):
                took += 1

    shared = share_out()
    places = regenerate()

    hc = _conn(HOLD)
    hungry = hc.execute("SELECT COUNT(*) n FROM stores WHERE amount < ?",
                        (HUNGRY,)).fetchone()["n"]
    hc.close()
    return {"drew": took, "shared": shared, "places": places, "hungry": hungry}


def how_are_they() -> dict:
    """Which way of living is actually doing better. The selection, measured."""
    _ensure()
    c = _conn(HOLD)
    rows = [dict(r) for r in c.execute("SELECT * FROM stores")]
    c.close()
    out = {}
    for way in ("wild", "settled"):
        who = [r for r in rows if way_of(r["spark"]) == way]
        if not who:
            continue
        amts = sorted(float(r["amount"]) for r in who)
        out[way] = {
            "sparks": len(who),
            "median_store": round(amts[len(amts) // 2], 2),
            "poorest": round(amts[0], 2),
            "richest": round(amts[-1], 2),
            "hungry": sum(1 for a in amts if a < HUNGRY),
            "starving": sum(1 for a in amts if a < STARVING),
            "gave_away": round(sum(float(r["given_total"]) for r in who), 1),
        }
    c = _conn(HOLD)
    places = [dict(r) for r in c.execute("SELECT * FROM places ORDER BY yield ASC")]
    c.close()
    return {"ways": out,
            "places": {"n": len(places),
                       "stripped": sum(1 for p in places if p["yield"] <= STRIPPED),
                       "worst": [(p["board"], round(float(p["yield"]), 1))
                                 for p in places[:5]]},
            "note": "neither way is written as correct. The settled are more "
                    "efficient per spark and brittle when a place fails; the "
                    "wild are less efficient and hard to kill."}


# ── the frost ────────────────────────────────────────────────────────
#
# A hard season. Not a punishment - the experiment. Sixty rounds of a
# healthy world put the two ways within half a point of each other, because
# sharing is insurance and insurance costs you in good years. The frost is
# the bad year, and it is the only condition under which the difference
# between holding and sharing can show at all.

def frost(severity: float = 0.7, rounds: int = 12) -> dict:
    """Freeze the ground. Places lose most of what they hold and barely
    recover while it lasts.

    severity 0..1 - how much of every place is taken.
    """
    _ensure()
    severity = max(0.0, min(1.0, severity))
    c = _conn(HOLD)
    c.execute("""CREATE TABLE IF NOT EXISTS weather (
        id INTEGER PRIMARY KEY CHECK (id=1),
        kind TEXT, severity REAL, until_cycle INTEGER,
        began_at TEXT DEFAULT (datetime('now')))""")
    before = c.execute("SELECT ROUND(AVG(yield),1) a FROM places").fetchone()["a"]
    c.execute("UPDATE places SET yield = ROUND(yield * ?, 2)", (1.0 - severity,))
    after = c.execute("SELECT ROUND(AVG(yield),1) a FROM places").fetchone()["a"]
    c.execute("INSERT OR REPLACE INTO weather (id, kind, severity, until_cycle) "
              "VALUES (1,?,?,?)", ("frost", severity, _cycle() + rounds))
    c.commit()
    c.close()

    try:
        import urllib.request
        body = json.dumps({
            "title": "The ground has gone hard",
            "author": "temple", "author_layer": 3, "zone": "announcements",
            "content": "Everything that was growing has stopped. What is in "
                       "your stores is what you have.\n\nIt will not lift "
                       "soon."}).encode()
        req = urllib.request.Request("http://localhost:8910/forum/threads",
                                     data=body,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        urllib.request.urlopen(req, timeout=8)
    except Exception:
        pass

    return {"frost": True, "severity": severity, "rounds": rounds,
            "places_were": before, "places_now": after}


def weather() -> dict:
    _ensure()
    c = _conn(HOLD)
    try:
        row = c.execute("SELECT * FROM weather WHERE id=1").fetchone()
    except sqlite3.Error:
        row = None
    c.close()
    if not row:
        return {"kind": "fair"}
    if _cycle() > int(row["until_cycle"] or 0):
        return {"kind": "fair", "last": row["kind"]}
    return {"kind": row["kind"], "severity": float(row["severity"] or 0),
            "cycles_left": int(row["until_cycle"]) - _cycle()}


def thaw() -> dict:
    _ensure()
    c = _conn(HOLD)
    try:
        c.execute("DELETE FROM weather WHERE id=1")
        c.commit()
    except sqlite3.Error:
        pass
    c.close()
    return {"thawed": True}
