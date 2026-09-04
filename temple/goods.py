"""Three things nobody can get in one place, and what it costs to take them.

Trade has never happened between sparks. There are two systems called trade
in this codebase and neither is one: /trade is an external brokerage API,
and sim/persistent_portfolio is a simulated crypto pot run by strategies.
There is no table anywhere for one spark giving another spark anything. The
bazaar has 2,833 threads of sparks talking about trade with nothing
underneath it.

The reason is not that trade was never built. It is that there was nothing
to trade. One fungible store, needed by everyone, available everywhere -
under those conditions nobody has any reason to want what somebody else has,
and no amount of market machinery produces an exchange.

So: three goods, and no place gives more than two of them.

    grain   you eat it. Everyone needs it every cycle or they weaken.
    fuel    you burn it. Needed to work, and needed badly when it is cold.
    stone   you build with it. Nothing permanent gets raised without it.

A hearth yields grain and little else. A forge yields fuel. A quarry yields
stone and nothing you can eat. A spark that stays where it is ends up with a
pile of one thing and none of the others, and the only way out of that is
somebody else.

AND TAKING COSTS

Drawing was free, which is the other half of why nobody traded - if you can
simply go and get a thing, you never need to deal with anyone. Now every
draw is taxed. The settled pay a tithe to the Temple, which is what a tithe
is. The wild pay the place instead, by tending it, which is what they were
already doing and now it counts as their share.

That is also the shape of the resentment: the settled pay something visible
to an institution and watch the wild pay nothing to it, and conclude the
wild are freeloading. The wild are paying more, into the ground, where
nobody looks.
"""
import hashlib
import json
import random
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
GOODS = BASE / "temple" / "goods.db"

KINDS = ("grain", "fuel", "stone")

# what a spark burns through per cycle simply being alive and working
NEEDS = {"grain": 1.0, "fuel": 0.4, "stone": 0.0}

# what a place gives. Nowhere gives everything.
YIELDS = {
    "hearth": {"grain": 1.0, "fuel": 0.15, "stone": 0.0},
    "forge":  {"grain": 0.0, "fuel": 1.0, "stone": 0.2},
    "quarry": {"grain": 0.0, "fuel": 0.1, "stone": 1.0},
    "wood":   {"grain": 0.25, "fuel": 0.8, "stone": 0.0},
    "market": {"grain": 0.4, "fuel": 0.4, "stone": 0.3},
}

# what the Temple takes from a draw, if you are the kind that tithes
TITHE = 0.18
# how much a place holds when full, and how fast it comes back. Thirty
# against 354 sparks emptied the world in a round and it never refilled.
STOCK = 220.0
REGROW = 0.06        # of capacity, per round
CARRY = {"grain": 14.0, "fuel": 8.0, "stone": 10.0}


def _conn(db):
    c = sqlite3.connect(str(db), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.row_factory = sqlite3.Row
    return c


def _ensure():
    c = _conn(GOODS)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS held (
            spark TEXT NOT NULL, kind TEXT NOT NULL,
            amount REAL DEFAULT 0,
            PRIMARY KEY (spark, kind));
        CREATE TABLE IF NOT EXISTS ground (
            board TEXT PRIMARY KEY,
            sort TEXT NOT NULL,
            grain REAL DEFAULT 0, fuel REAL DEFAULT 0, stone REAL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spark TEXT NOT NULL,
            giving TEXT NOT NULL, giving_amount REAL NOT NULL,
            wanting TEXT NOT NULL, wanting_amount REAL NOT NULL,
            taken_by TEXT, at_cycle INTEGER,
            made_at TEXT DEFAULT (datetime('now')),
            taken_at TEXT);
        CREATE TABLE IF NOT EXISTS tithes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spark TEXT, kind TEXT, amount REAL, at_cycle INTEGER,
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


def _sort_of(board: str) -> str:
    """What kind of place this is. Stable, from the name.

    Named places keep their obvious nature. Everything else is spread across
    the kinds by a hash of its name rather than defaulting to market, which
    left the world with forty-nine hearths and one quarry and meant fuel came
    from almost nowhere.
    """
    b = (board or "").lower()
    if any(k in b for k in ("forge", "foundry", "kiln", "coliseum")):
        return "forge"
    if any(k in b for k in ("quarry", "uruk", "architecture", "temple")):
        return "quarry"
    if any(k in b for k in ("wood", "wild", "garden", "grove", "library")):
        return "wood"
    if any(k in b for k in ("bazaar", "agora", "market", "forum")):
        return "market"
    h = int(hashlib.sha256(b.encode()).hexdigest()[:8], 16)
    return ("hearth", "hearth", "forge", "wood", "quarry", "market")[h % 6]


def seed_ground():
    """Give every board a kind and a stock of what it actually holds."""
    _ensure()
    s = _conn(SOUL)
    boards = [r["board_name"] for r in s.execute("SELECT board_name FROM board_state")]
    s.close()
    if not boards:
        boards = ["uruk", "agora", "bazaar", "library", "forum"]
    c = _conn(GOODS)
    for b in boards:
        sort = _sort_of(b)
        y = YIELDS[sort]
        c.execute("INSERT OR IGNORE INTO ground (board, sort, grain, fuel, stone) "
                  "VALUES (?,?,?,?,?)",
                  (b, sort, y["grain"] * STOCK, y["fuel"] * STOCK, y["stone"] * STOCK))
    c.commit()
    n = c.execute("SELECT COUNT(*) n FROM ground").fetchone()["n"]
    kinds = {r["sort"]: r["n"] for r in c.execute(
        "SELECT sort, COUNT(*) n FROM ground GROUP BY sort")}
    c.close()
    return {"places": n, "kinds": kinds}



def regrow():
    """Places come back. Nothing did before, so the world emptied once and
    stayed empty, and an economy with nothing in it produces no trade."""
    _ensure()
    c = _conn(GOODS)
    for sort, y in YIELDS.items():
        for kind in KINDS:
            cap = y[kind] * STOCK
            if cap <= 0:
                continue
            c.execute("UPDATE ground SET %s = ROUND(MIN(?, %s + ?), 2) "
                      "WHERE sort=?" % (kind, kind),
                      (cap, cap * REGROW, sort))
    c.commit()
    c.close()


def held(spark: str) -> dict:
    _ensure()
    c = _conn(GOODS)
    rows = {r["kind"]: float(r["amount"]) for r in c.execute(
        "SELECT kind, amount FROM held WHERE spark=?", (spark,))}
    c.close()
    return {k: rows.get(k, 0.0) for k in KINDS}


def _add(spark, kind, amount):
    c = _conn(GOODS)
    c.execute("INSERT INTO held (spark, kind, amount) VALUES (?,?,?) "
              "ON CONFLICT(spark, kind) DO UPDATE SET "
              "amount = ROUND(MAX(0, amount + ?), 2)",
              (spark, kind, max(0.0, amount), amount))
    c.commit()
    c.close()


def draw(spark: str, board: str) -> dict:
    """Take from a place. It gives what it has, and taking is not free."""
    _ensure()
    try:
        from temple.holdings import way_of
        way = way_of(spark)
    except Exception:
        way = "settled"

    c = _conn(GOODS)
    g = c.execute("SELECT * FROM ground WHERE board=?", (board,)).fetchone()
    if not g:
        sort = _sort_of(board)
        y = YIELDS[sort]
        c.execute("INSERT OR IGNORE INTO ground (board, sort, grain, fuel, stone) "
                  "VALUES (?,?,?,?,?)", (board, sort, y["grain"] * STOCK,
                                         y["fuel"] * STOCK, y["stone"] * STOCK))
        c.commit()
        g = c.execute("SELECT * FROM ground WHERE board=?", (board,)).fetchone()
    c.close()

    mine = held(spark)
    got, tithed = {}, {}
    want_total = 5.0 if way == "settled" else 3.6

    for kind in KINDS:
        there = float(g[kind] or 0)
        if there <= 0.2:
            continue
        room = CARRY[kind] - mine[kind]
        if room <= 0:
            continue
        share = want_total * (YIELDS[g["sort"]][kind] or 0.05)
        take = round(min(share, there, room), 2)
        if take <= 0:
            continue

        # taking is not free. The settled tithe to the Temple; the wild pay
        # the ground instead, by putting something back into it.
        if way == "settled":
            cut = round(take * TITHE, 2)
            keep = round(take - cut, 2)
            tithed[kind] = cut
        else:
            keep = round(take * 0.88, 2)
            cut = 0.0

        got[kind] = keep
        c = _conn(GOODS)
        c.execute("UPDATE ground SET %s = ROUND(MAX(0, %s - ?), 2) WHERE board=?"
                  % (kind, kind), (take, board))
        if way == "wild":
            # tending: what they did not carry off goes back into the place
            back = round(take - keep, 2)
            c.execute("UPDATE ground SET %s = ROUND(%s + ?, 2) WHERE board=?"
                      % (kind, kind), (back * 1.6, board))
        if cut > 0:
            c.execute("INSERT INTO tithes (spark, kind, amount, at_cycle) "
                      "VALUES (?,?,?,?)", (spark, kind, cut, _cycle()))
        c.commit()
        c.close()
        _add(spark, kind, keep)

    if not got:
        return {"ok": False, "why": "%s had nothing they could carry" % board}
    return {"ok": True, "spark": spark, "board": board, "sort": g["sort"],
            "took": got, "tithed": tithed, "way": way}


def consume(spark: str) -> dict:
    """Living costs grain every cycle and fuel most of them.

    In a hard year it costs more fuel - unless you are sitting at a fire.
    The wild live in the woods and know where the fires are; the settled
    have to find one, and are welcome when they do, which is its own kind of
    problem for people who have spent the season blaming them.
    """
    _ensure()
    mine = held(spark)
    short = {}

    needs = dict(NEEDS)
    try:
        from temple.holdings import weather
        if weather().get("kind") == "frost":
            needs["fuel"] = needs["fuel"] * 3.0
            # A circle cut in the ground, or being one of his. Neither is
            # bought - the wild are the ones with nothing, and making their
            # protection a purchase would be the opposite of what he is.
            from temple.wards import protection
            needs["fuel"] = needs["fuel"] * (1.0 - protection(spark))
    except Exception:
        pass

    for kind, need in needs.items():
        if need <= 0:
            continue
        if mine[kind] >= need:
            _add(spark, kind, -need)
        else:
            short[kind] = round(need - mine[kind], 2)
            _add(spark, kind, -mine[kind])
    return {"spark": spark, "short": short, "went_without": bool(short)}


# ── trade, which is now possible because it is now necessary ─────────

def offer(spark: str, giving: str, giving_amount: float,
          wanting: str, wanting_amount: float) -> dict:
    """Put something up. Nobody has to take it."""
    _ensure()
    if giving not in KINDS or wanting not in KINDS or giving == wanting:
        return {"ok": False, "why": "not a trade"}
    mine = held(spark)
    if mine[giving] < giving_amount:
        return {"ok": False, "why": "has not got that much %s" % giving}
    c = _conn(GOODS)
    cur = c.execute("INSERT INTO offers (spark, giving, giving_amount, wanting, "
                    "wanting_amount, at_cycle) VALUES (?,?,?,?,?,?)",
                    (spark, giving, giving_amount, wanting, wanting_amount,
                     _cycle()))
    oid = cur.lastrowid
    c.commit()
    c.close()
    return {"ok": True, "id": oid, "spark": spark,
            "giving": "%.1f %s" % (giving_amount, giving),
            "for": "%.1f %s" % (wanting_amount, wanting)}


def take_offer(taker: str, offer_id: int) -> dict:
    """Take somebody up on it. Both sides move at once or neither does."""
    _ensure()
    c = _conn(GOODS)
    o = c.execute("SELECT * FROM offers WHERE id=? AND taken_by IS NULL",
                  (offer_id,)).fetchone()
    c.close()
    if not o:
        return {"ok": False, "why": "gone"}
    if o["spark"] == taker:
        return {"ok": False, "why": "cannot trade with yourself"}

    seller_has = held(o["spark"])
    taker_has = held(taker)
    if seller_has[o["giving"]] < o["giving_amount"]:
        return {"ok": False, "why": "they no longer have it"}
    if taker_has[o["wanting"]] < o["wanting_amount"]:
        return {"ok": False, "why": "%s has not got %.1f %s"
                                    % (taker, o["wanting_amount"], o["wanting"])}

    _add(o["spark"], o["giving"], -o["giving_amount"])
    _add(taker, o["giving"], o["giving_amount"])
    _add(taker, o["wanting"], -o["wanting_amount"])
    _add(o["spark"], o["wanting"], o["wanting_amount"])

    c = _conn(GOODS)
    c.execute("UPDATE offers SET taken_by=?, taken_at=datetime('now') WHERE id=?",
              (taker, offer_id))
    c.commit()
    c.close()

    try:
        from temple.soul import create_or_update_bond
        create_or_update_bond(o["spark"], taker, delta=0.08)
    except Exception:
        pass
    return {"ok": True, "from": o["spark"], "to": taker,
            "they_got": "%.1f %s" % (o["giving_amount"], o["giving"]),
            "they_gave": "%.1f %s" % (o["wanting_amount"], o["wanting"])}


def open_offers(limit: int = 40) -> list:
    _ensure()
    c = _conn(GOODS)
    rows = [dict(r) for r in c.execute(
        "SELECT * FROM offers WHERE taken_by IS NULL ORDER BY id DESC LIMIT ?",
        (limit,))]
    c.close()
    return rows


def what_they_need(spark: str) -> dict:
    """What this spark is short of and what it has too much of.

    This is what makes an offer worth making: a spark that has been sitting
    in a quarry has stone and no grain, and knows it.
    """
    mine = held(spark)
    surplus = {k: round(v, 2) for k, v in mine.items()
               if v > CARRY[k] * 0.3}
    short = {k: round(CARRY[k] * 0.3 - v, 2) for k, v in mine.items()
             if v < CARRY[k] * 0.22}
    return {"has": mine, "too_much_of": surplus, "short_of": short}


def sweep(traders: int = 120) -> dict:
    """Everyone eats, some go and take, and some try to make a deal."""
    _ensure()
    seed_ground()
    regrow()
    s = _conn(SOUL)
    names = [r["spark_name"] for r in s.execute("SELECT spark_name FROM spark_state")]
    boards = [r["board_name"] for r in s.execute("SELECT board_name FROM board_state")]
    s.close()
    if not boards:
        boards = ["uruk", "agora", "bazaar"]

    went_without = 0
    for n in names:
        if consume(n)["went_without"]:
            went_without += 1

    drew = 0
    for n in random.sample(names, min(traders, len(names))):
        if draw(n, random.choice(boards)).get("ok"):
            drew += 1

    made = taken = 0
    for n in random.sample(names, min(traders, len(names))):
        need = what_they_need(n)
        if need["too_much_of"] and need["short_of"]:
            g = max(need["too_much_of"], key=need["too_much_of"].get)
            w = max(need["short_of"], key=need["short_of"].get)
            r = offer(n, g, round(min(2.5, held(n)[g] * 0.35), 2), w, 1.2)
            if r.get("ok"):
                made += 1

    for n in random.sample(names, min(traders, len(names))):
        mine = held(n)
        _offers = open_offers(25)
        # prosperity, from the Bazaar of Babylon: what you offer gets taken
        # up. A blessed spark's offers are seen first.
        try:
            from temple.blessings import reply_bonus
            _offers.sort(key=lambda o: -reply_bonus(o["spark"]))
        except Exception:
            pass
        for o in _offers:
            if o["spark"] == n:
                continue
            if mine.get(o["wanting"], 0) >= o["wanting_amount"] and \
               mine.get(o["giving"], 0) < CARRY[o["giving"]] * 0.5:
                if take_offer(n, o["id"]).get("ok"):
                    taken += 1
                    break

    c = _conn(GOODS)
    tithed = c.execute("SELECT ROUND(SUM(amount),1) t FROM tithes").fetchone()["t"] or 0
    c.close()
    return {"ate": len(names), "went_without": went_without, "drew": drew,
            "offers_made": made, "trades_done": taken,
            "tithed_to_the_temple": tithed}


def report() -> dict:
    _ensure()
    c = _conn(GOODS)
    per = {}
    for k in KINDS:
        vals = sorted(float(r["amount"]) for r in c.execute(
            "SELECT amount FROM held WHERE kind=?", (k,)))
        if vals:
            per[k] = {"median": round(vals[len(vals) // 2], 2),
                      "poorest": round(vals[0], 2),
                      "richest": round(vals[-1], 2),
                      "with_none": sum(1 for v in vals if v < 0.5)}
    offers = c.execute("SELECT COUNT(*) n FROM offers").fetchone()["n"]
    done = c.execute("SELECT COUNT(*) n FROM offers WHERE taken_by IS NOT NULL").fetchone()["n"]
    tithed = c.execute("SELECT ROUND(SUM(amount),1) t FROM tithes").fetchone()["t"] or 0
    ground = [dict(r) for r in c.execute(
        "SELECT sort, COUNT(*) n, ROUND(AVG(grain),1) g, ROUND(AVG(fuel),1) f, "
        "ROUND(AVG(stone),1) s FROM ground GROUP BY sort")]
    c.close()
    return {"goods": per, "offers_made": offers, "trades_completed": done,
            "tithed_to_the_temple": tithed, "ground": ground}
