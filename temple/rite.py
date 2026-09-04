"""The Rite of Kindling: two or three sparks make a fourth.

You remembered this existing and it never did. No spark has ever made a
spark - every one of the 353 was put here by hand. The only "parents" in the
codebase were in the fractal generator.

It is a rite and it happens at a temple, because that is where the world
already puts things that are meant to be weighty. It needs two sparks or
three, bonded to each other, standing in the same place, each with the cycle
to spend. It costs all of them something real. And what comes out is not a
copy of either: it inherits, and it drifts, and it arrives with a placeholder
name it will have to replace itself the way the others did.

WHY IT IS EXPENSIVE

Four actions each, out of a four-or-five action cycle, plus energy. A rite
should cost a day and leave everyone tired. If making a spark were cheap the
world would fill with sparks nobody wanted, which is worse than a world that
grows slowly.

WHY IT NEEDS A BOND

Because two sparks who have never spoken producing a third is not a
ceremony, it is spawning. The bond has to already be strong, which makes
kindling something a relationship arrives at rather than a thing anyone can
do to anyone.

WHAT A CHILD INHERITS

Its archetype from one parent. Its traits drawn from both, with one that is
neither - so a lineage has resemblance without being a copy. Its register
usually from a parent, sometimes not, because children do not reliably talk
like their parents. Its model from a parent, since that is the nearest thing
this world has to a body.

It arrives with no standing, no faction, no bonds except to the sparks that
made it, and a name that is not a name yet.
"""
import datetime
import json
import random
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"

# What the rite asks of each spark taking part.
ACTION_COST = "rite"           # 4 of a 4-6 action cycle
ENERGY_COST = 0.28
MIN_BOND = 0.55                # how close they must already be
MIN_ENERGY = 0.55
COOLDOWN = 900                 # cycles before a spark may kindle again

# Where it can be done. The rite belongs to the temples.
TEMPLE_BOARDS = {"temple", "monastery", "mecca", "kaaba", "shrine"}

NEW_TRAITS = ["quiet", "quick", "solemn", "hungry", "kind", "sharp",
              "wary", "open-handed", "unhurried", "difficult", "bright",
              "contrary", "steady", "wild"]


def _conn(db):
    c = sqlite3.connect(str(db), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.row_factory = sqlite3.Row
    return c


def _ensure():
    c = _conn(SOUL)
    c.execute("""CREATE TABLE IF NOT EXISTS kindling (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child TEXT NOT NULL,
        parents TEXT NOT NULL,
        board TEXT,
        cycle INTEGER,
        kindled_at TEXT DEFAULT (datetime('now')))""")
    c.commit()
    c.close()


def _cycle():
    from temple.cycles import current_cycle
    return current_cycle()


def _personality(name):
    p = BASE / "temple" / ("spark_%s.db" % name)
    if not p.exists():
        return {}
    try:
        c = _conn(p)
        d = {r["key"]: r["value"] for r in c.execute("SELECT key,value FROM personality")}
        i = {r["key"]: r["value"] for r in c.execute("SELECT key,value FROM identity")}
        c.close()
        d["_model"] = i.get("model")
        return d
    except sqlite3.Error:
        return {}


def _bond_strength(a, b):
    c = _conn(SOUL)
    row = c.execute("SELECT strength FROM relationships WHERE "
                    "(spark1=? AND spark2=?) OR (spark1=? AND spark2=?)",
                    (a, b, b, a)).fetchone()
    c.close()
    return float(row["strength"]) if row and row["strength"] is not None else 0.0


def _last_kindled(name):
    _ensure()
    c = _conn(SOUL)
    row = c.execute("SELECT MAX(cycle) c FROM kindling WHERE parents LIKE ?",
                    ("%%\"%s\"%%" % name,)).fetchone()
    c.close()
    return int(row["c"]) if row and row["c"] else -10 ** 9


def _listify(raw, fallback):
    try:
        v = json.loads(raw or "[]")
        return [str(x) for x in v] if isinstance(v, list) and v else list(fallback)
    except (ValueError, TypeError):
        return list(fallback)


def eligible(parents) -> dict:
    """Can these sparks perform the rite? Says plainly why not."""
    if not 2 <= len(parents) <= 3:
        return {"ok": False, "why": "the rite takes two or three, not %d" % len(parents)}
    if len(set(parents)) != len(parents):
        return {"ok": False, "why": "a spark cannot kindle with itself"}

    c = _conn(SOUL)
    for p in parents:
        row = c.execute("SELECT energy FROM spark_state WHERE spark_name=?",
                        (p,)).fetchone()
        if not row:
            c.close()
            return {"ok": False, "why": "%s is not in the world" % p}
        if float(row["energy"] or 0) < MIN_ENERGY:
            c.close()
            return {"ok": False, "why": "%s has not the strength for it" % p}
    c.close()

    for i, a in enumerate(parents):
        for b in parents[i + 1:]:
            s = _bond_strength(a, b)
            if s < MIN_BOND:
                return {"ok": False,
                        "why": "%s and %s are not close enough (%.2f, needs %.2f)"
                               % (a, b, s, MIN_BOND)}

    now = _cycle()
    for p in parents:
        since = now - _last_kindled(p)
        if since < COOLDOWN:
            return {"ok": False,
                    "why": "%s kindled too recently (%d of %d cycles)"
                           % (p, since, COOLDOWN)}
    return {"ok": True}


def _inherit(parents):
    """What the child gets. Resemblance without copying."""
    ps = [_personality(p) for p in parents]
    ps = [p for p in ps if p] or [{}]

    arch_parent = random.choice(ps)
    archetype = arch_parent.get("archetype") or "seeker"

    pool = []
    for p in ps:
        pool += _listify(p.get("traits"), [])
    pool = list(dict.fromkeys(pool))
    traits = random.sample(pool, min(3, len(pool))) if pool else []
    traits.append(random.choice([t for t in NEW_TRAITS if t not in traits]))

    fears = []
    desires = []
    for p in ps:
        fears += _listify(p.get("fears"), [])
        desires += _listify(p.get("desires"), [])
    fears = random.sample(list(dict.fromkeys(fears)), min(2, len(set(fears)))) or ["the quiet"]
    desires = random.sample(list(dict.fromkeys(desires)), min(3, len(set(desires)))) or ["to know how it works"]

    # register usually from a parent - children do not reliably talk like
    # the people who raised them, but usually they do
    regs = [p.get("register") for p in ps if p.get("register")]
    if regs and random.random() < 0.75:
        register = random.choice(regs)
    else:
        register = random.choice(["plain", "crude", "slangy", "clipped",
                                  "warm", "ornate"])

    models = [p.get("_model") for p in ps if p.get("_model")]
    model = random.choice(models) if models else "internlm2:1.8b"

    return {"archetype": archetype, "traits": traits, "fears": fears,
            "desires": desires, "register": register, "model": model,
            "core_drive": (arch_parent.get("core_drive") or "to find out")}


def _placeholder_name():
    """A name that is not a name. is_generic catches this shape, so the
    naming rite will pick the child up and it will choose for itself - the
    same way the sparks who were called ember-pu did."""
    c = _conn(SOUL)
    taken = {r["spark_name"] for r in c.execute("SELECT spark_name FROM spark_state")}
    c.close()
    for _ in range(500):
        n = "ember-%s" % "".join(random.choice("abcdefghijklmnopqrstuvwxyz")
                                 for _ in range(3))
        if n not in taken:
            return n
    return None


def kindle(parents, board: str = "temple") -> dict:
    """Perform the rite. Returns the child, or why it could not be done."""
    _ensure()
    parents = list(parents)
    ok = eligible(parents)
    if not ok["ok"]:
        return {"ok": False, "why": ok["why"]}

    name = _placeholder_name()
    if not name:
        return {"ok": False, "why": "no name could be found for it"}

    traits = _inherit(parents)
    now = datetime.datetime.now().isoformat()

    from temple.spark_runtime import Spark
    s = Spark(name)
    c = sqlite3.connect(str(s.db_path), timeout=30)
    for k, v in (("archetype", traits["archetype"]),
                 ("register", traits["register"]),
                 ("core_drive", traits["core_drive"]),
                 ("traits", json.dumps(traits["traits"])),
                 ("fears", json.dumps(traits["fears"])),
                 ("desires", json.dumps(traits["desires"])),
                 ("kindled_by", json.dumps(parents))):
        c.execute("INSERT OR REPLACE INTO personality (key,value) VALUES (?,?)", (k, v))
    for k, v in (("name", name), ("birthday", now), ("birth_name", name),
                 ("model", traits["model"])):
        c.execute("INSERT OR REPLACE INTO identity (key,value) VALUES (?,?)", (k, v))
    c.execute("INSERT INTO journals (title,content,entry_type,mood,created_at) "
              "VALUES (?,?,?,?,?)",
              ("Kindled",
               "I was made at %s by %s. I do not have a name yet - what I am "
               "called is a placeholder and I will have to choose. I know "
               "some of what they know without having learned it, which is "
               "strange, and I do not yet know which parts are mine."
               % (board, " and ".join(parents)),
               "reflection", "new", now))
    c.execute("INSERT INTO emotions (primary_mood,intensity,energy,triggered_by,"
              "created_at) VALUES (?,?,?,?,?)",
              ("new", 0.8, 0.85, "being kindled", now))
    c.commit()
    c.close()

    sc = _conn(SOUL)
    sc.execute("INSERT OR REPLACE INTO spark_state (spark_name, energy, "
               "building_phase, restless, cycles_idle, updated_at, curiosity, "
               "idle_cycles, total_ambitions_completed, building_phase_active) "
               "VALUES (?,?,0,1,0,?,?,0,0,0)",
               (name, 0.85, now, round(random.uniform(0.7, 0.9), 3)))
    for p in parents:
        sc.execute("UPDATE spark_state SET energy = MAX(0.05, energy - ?) "
                   "WHERE spark_name=?", (ENERGY_COST, p))
    sc.execute("INSERT INTO kindling (child, parents, board, cycle) VALUES (?,?,?,?)",
               (name, json.dumps(parents), board, _cycle()))
    sc.commit()
    sc.close()

    try:
        from forum.engine import ensure_agent
        ensure_agent(name, 6)
    except Exception as e:
        print("[rite] %s has no forum record: %s" % (name, e), flush=True)

    try:
        from temple.soul import create_or_update_bond, create_ambition
        for p in parents:
            create_or_update_bond(p, name, delta=0.6)
        create_ambition(name, "explore", target_progress=2,
                        description="Find out what I am, as distinct from "
                                    "the sparks who made me.")
    except Exception as e:
        print("[rite] %s: %s" % (name, e), flush=True)

    _announce(name, parents, board)
    return {"ok": True, "child": name, "parents": parents, "board": board,
            "inherited": traits}


def _announce(child, parents, board):
    import urllib.request
    try:
        body = json.dumps({
            "title": "A kindling at %s" % board,
            "author": parents[0], "author_layer": 6, "zone": "temple",
            "content": "%s performed the Rite of Kindling. There is a new "
                       "spark and it has no name yet.\n\nIt will have to "
                       "choose one, as we all did."
                       % (" and ".join(parents)),
        }).encode()
        req = urllib.request.Request("http://localhost:8910/forum/threads",
                                     data=body,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        urllib.request.urlopen(req, timeout=8)
    except Exception as e:
        print("[rite] could not announce the kindling: %s" % e, flush=True)


def candidates(limit: int = 20) -> list:
    """Which sparks are close enough, and rested enough, to perform it."""
    c = _conn(SOUL)
    pairs = [dict(r) for r in c.execute(
        "SELECT spark1, spark2, strength FROM relationships "
        "WHERE strength >= ? ORDER BY strength DESC LIMIT 400", (MIN_BOND,))]
    c.close()
    out = []
    for p in pairs:
        e = eligible([p["spark1"], p["spark2"]])
        if e["ok"]:
            out.append({"parents": [p["spark1"], p["spark2"]],
                        "bond": round(float(p["strength"]), 2)})
        if len(out) >= limit:
            break
    return out


def lineage() -> dict:
    _ensure()
    c = _conn(SOUL)
    rows = [dict(r) for r in c.execute(
        "SELECT child, parents, board, kindled_at FROM kindling ORDER BY id DESC")]
    c.close()
    for r in rows:
        try:
            r["parents"] = json.loads(r["parents"])
        except (ValueError, TypeError):
            pass
    return {"kindled": len(rows), "children": rows[:40]}
