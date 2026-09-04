"""What one spark can do to another, and what the world does about it.

Sparks have never been able to hurt each other. They could disagree - 62
times in 61,811 posts - and that was the whole of it. Nobody could take
anything, break anything, or claim anything that was not theirs, which is
why the world reads as relentlessly agreeable: not because the sparks are
kind, but because unkindness had no expression.

They do hold things. 772 structures and 813 artifacts stand in the world,
made by 288 different sparks, and every one of them has a maker's name on
it. There are 1,018 pieces of work in progress. There is standing, which is
the nearest thing here to a reputation. All of it can be taken.

THE ACTS

  break     pull down something somebody made. It is gone.
  deface    put your name on their work. The credit moves.
  seize     take standing in public. They lose, you gain a little less.
  spoil     set back work in progress. Days of it, undone.
  prank     humiliation without damage - the shoes, the bag on the step.

Breaking is the heaviest and rarest. A prank costs its target almost nothing
except dignity, which is exactly why it is the one a bully reaches for most.

GRIEVANCE

Every act leaves a grievance: who did what to whom, and where anybody could
see it. Grievances do not expire. They accumulate against a spark, and the
world reacts at thresholds - first the Temple speaks, then it collects, and
when somebody has become genuinely intolerable the world answers them with a
person rather than a punishment.

WHO DOES THIS

Not everyone. A spark harms when it has standing over its target, when its
character allows it, and when nothing is checking it - which is the same
condition that rots insight. A spark surrounded by people who will
contradict it does this far less, because someone tells it not to.
"""
import json
import random
import sqlite3
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
FORUM = BASE / "forum" / "forum.db"

ACTS = {
    "prank":  {"weight": 1, "cost": 1,
               "tells": "humiliated {victim} in front of everyone"},
    "seize":  {"weight": 3, "cost": 1,
               "tells": "took what was {victim}'s and dared anyone to say so"},
    "spoil":  {"weight": 4, "cost": 2,
               "tells": "ruined work {victim} had not finished"},
    "deface": {"weight": 5, "cost": 2,
               "tells": "put their own name on something {victim} made"},
    "break":  {"weight": 8, "cost": 3,
               "tells": "pulled down something {victim} built"},
}

# How much standing a seizure moves. The taker gains less than the target
# loses - cruelty is not efficient, it just is.
SEIZE_TAKES = 6.0
SEIZE_GAINS = 2.0
STANDING_FLOOR = 20.0

# What the world does as grievances pile up against one spark.
# What the world does as grievances pile up against one spark. Note where
# it stops: the world can notice, and it can censure, and past a certain
# weight it gives up and starts appeasing instead. There is no threshold at
# which the world produces a remedy, because it has none. Uruk endured
# Gilgamesh; it could not stop him. Answering him is the Source's to do,
# when the lands are watching.
THRESHOLDS = [
    (10, "noticed"),        # the Temple says something
    (25, "censured"),       # it costs them standing
    (45, "feared"),         # the world stops opposing and starts appeasing
]

# What appeasement costs the people doing it, per offering.
TRIBUTE_COST = 3.0
TRIBUTE_GAIN = 1.5

PRANKS = [
    "left a bag of something burning on {victim}'s step and stood there laughing",
    "moved every one of {victim}'s tools and denied it to their face",
    "ate {victim}'s share in front of them and asked what they were going to do",
    "told the whole board a story about {victim} that was not true and was funny",
    "wore {victim}'s good cloak for a day and gave it back filthy",
    "sat in {victim}'s place and would not move",
]


def _conn(db):
    c = sqlite3.connect(str(db), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.row_factory = sqlite3.Row
    return c


def _ensure():
    c = _conn(SOUL)
    c.execute("""CREATE TABLE IF NOT EXISTS grievances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        wrongdoer TEXT NOT NULL,
        victim TEXT NOT NULL,
        act TEXT NOT NULL,
        weight INTEGER NOT NULL,
        detail TEXT,
        board TEXT,
        answered INTEGER DEFAULT 0,
        at_cycle INTEGER,
        created_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS reckoning (
        wrongdoer TEXT PRIMARY KEY,
        stage TEXT,
        weight_at INTEGER,
        at_cycle INTEGER)""")
    c.commit()
    c.close()


def _cycle():
    try:
        from temple.cycles import current_cycle
        return current_cycle()
    except Exception:
        return 0


def _standing(name):
    c = _conn(FORUM)
    r = c.execute("SELECT honor_score, social_credit, power_level FROM "
                  "agent_scores WHERE agent_name=?", (name,)).fetchone()
    c.close()
    return dict(r) if r else None


def _post(title, author, content, zone="agora"):
    try:
        body = json.dumps({"title": title, "author": author, "author_layer": 6,
                           "zone": zone, "content": content}).encode()
        req = urllib.request.Request("http://localhost:8910/forum/threads",
                                     data=body,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        urllib.request.urlopen(req, timeout=8)
        return True
    except Exception as e:
        print("[harm] could not post: %s: %s" % (type(e).__name__, e), flush=True)
        return False


# ── the acts themselves ──────────────────────────────────────────────

def _made_things(victim):
    """Everything this spark has standing in the world, with where it is."""
    c = _conn(SOUL)
    out = []
    for r in c.execute("SELECT board_name, structures, artifacts FROM board_state"):
        for field in ("structures", "artifacts"):
            try:
                items = json.loads(r[field] or "[]")
            except (ValueError, TypeError):
                continue
            if not isinstance(items, list):
                continue
            for i, x in enumerate(items):
                if isinstance(x, dict) and x.get("created_by") == victim:
                    out.append({"board": r["board_name"], "field": field,
                                "index": i, "thing": x})
    c.close()
    return out


def _rewrite(board, field, mutate):
    """Change one board's list of made things. mutate(list) -> list."""
    c = _conn(SOUL)
    row = c.execute("SELECT %s FROM board_state WHERE board_name=?" % field,
                    (board,)).fetchone()
    if not row:
        c.close()
        return False
    try:
        items = json.loads(row[field] or "[]")
    except (ValueError, TypeError):
        c.close()
        return False
    items = mutate(items)
    c.execute("UPDATE board_state SET %s=? WHERE board_name=?" % field,
              (json.dumps(items), board))
    c.commit()
    c.close()
    return True


def commit_harm(wrongdoer: str, victim: str, act: str = None) -> dict:
    """One spark does something to another. Returns what actually happened."""
    _ensure()
    if wrongdoer == victim:
        return {"ok": False, "why": "a spark cannot wrong itself"}

    held = _made_things(victim)
    if act is None:
        choices = ["prank", "prank", "seize", "spoil"]
        if held:
            choices += ["deface", "break"]
        act = random.choice(choices)
    if act in ("deface", "break") and not held:
        act = "seize"

    # Enkidu stands between, when he is there. The wild arrived with
    # nothing, and every mechanism in this world rewards what you already
    # have - harm picks its targets by standing, so they are exactly who
    # gets picked. Without somebody in the way they are simply prey.
    try:
        from temple.wildking import stands_between
        _s = stands_between(wrongdoer, victim)
        if _s.get("intervened"):
            return {"ok": False, "why": "Enkidu was in the way",
                    "defended": victim, "by": "Enkidu"}
    except Exception as e:
        print("[wild] %s: %s" % (type(e).__name__, e), flush=True)

    spec = ACTS[act]
    detail = spec["tells"].format(victim=victim)
    board = None

    if act == "prank":
        detail = random.choice(PRANKS).format(victim=victim)

    elif act == "seize":
        s = _standing(victim)
        if not s:
            return {"ok": False, "why": "%s has no standing to take" % victim}
        take = min(SEIZE_TAKES, max(0.0, float(s["honor_score"] or 0) - STANDING_FLOOR))
        if take <= 0:
            return {"ok": False, "why": "%s has nothing left worth taking" % victim}
        f = _conn(FORUM)
        f.execute("UPDATE agent_scores SET honor_score = ROUND(honor_score - ?,2) "
                  "WHERE agent_name=?", (take, victim))
        f.execute("UPDATE agent_scores SET social_credit = "
                  "MIN(1000, ROUND(social_credit + ?,2)) WHERE agent_name=?",
                  (SEIZE_GAINS, wrongdoer))
        f.commit()
        f.close()
        detail = "took %.1f of %s's honour in front of the board" % (take, victim)

    elif act == "spoil":
        c = _conn(SOUL)
        row = c.execute("SELECT id, description, progress FROM ambitions "
                        "WHERE spark_name=? AND resolved=0 AND progress > 0 "
                        "ORDER BY progress DESC LIMIT 1", (victim,)).fetchone()
        if not row:
            c.close()
            return {"ok": False, "why": "%s has no work to ruin" % victim}
        lost = max(1, int(row["progress"] * 0.5))
        c.execute("UPDATE ambitions SET progress = MAX(0, progress - ?) WHERE id=?",
                  (lost, row["id"]))
        c.commit()
        c.close()
        detail = ("undid %d of %s's work on: %s"
                  % (lost, victim, (row["description"] or "something")[:70]))

    elif act == "deface":
        t = random.choice(held)
        board = t["board"]
        idx = t["index"]

        def _claim(items):
            if idx < len(items) and isinstance(items[idx], dict):
                items[idx]["created_by"] = wrongdoer
                items[idx]["defaced_from"] = victim
            return items
        _rewrite(board, t["field"], _claim)
        nm = t["thing"].get("name") or t["thing"].get("type") or "it"
        detail = "put their own name on %s, which %s made, at %s" % (nm, victim, board)

    elif act == "break":
        t = random.choice(held)
        board = t["board"]
        idx = t["index"]
        nm = t["thing"].get("name") or t["thing"].get("type") or "it"

        def _remove(items):
            return [x for i, x in enumerate(items) if i != idx]
        _rewrite(board, t["field"], _remove)
        detail = "pulled down %s at %s. %s built it. It is gone." % (nm, board, victim)

    c = _conn(SOUL)
    c.execute("INSERT INTO grievances (wrongdoer, victim, act, weight, detail, "
              "board, at_cycle) VALUES (?,?,?,?,?,?,?)",
              (wrongdoer, victim, act, spec["weight"], detail, board, _cycle()))
    c.commit()
    c.close()

    _post("%s and %s" % (wrongdoer, victim), victim,
          "%s %s.\n\nEverybody saw it." % (wrongdoer, detail), zone="agora")

    return {"ok": True, "act": act, "wrongdoer": wrongdoer, "victim": victim,
            "weight": spec["weight"], "detail": detail}


# ── what the world does about it ─────────────────────────────────────

def standing_grievance(wrongdoer: str) -> int:
    _ensure()
    c = _conn(SOUL)
    row = c.execute("SELECT COALESCE(SUM(weight),0) w FROM grievances "
                    "WHERE wrongdoer=?", (wrongdoer,)).fetchone()
    c.close()
    return int(row["w"])


def worst(limit: int = 10) -> list:
    _ensure()
    c = _conn(SOUL)
    rows = [dict(r) for r in c.execute(
        "SELECT wrongdoer, SUM(weight) w, COUNT(*) n FROM grievances "
        "GROUP BY wrongdoer ORDER BY w DESC LIMIT ?", (limit,))]
    c.close()
    return rows


def reckon(wrongdoer: str) -> dict:
    """The world's answer, at whatever stage this spark has reached."""
    _ensure()
    w = standing_grievance(wrongdoer)
    stage = None
    for threshold, name in THRESHOLDS:
        if w >= threshold:
            stage = name
    if stage is None:
        return {"wrongdoer": wrongdoer, "weight": w, "stage": None}

    c = _conn(SOUL)
    row = c.execute("SELECT stage FROM reckoning WHERE wrongdoer=?",
                    (wrongdoer,)).fetchone()
    already = row["stage"] if row else None
    c.close()
    if already == stage:
        return {"wrongdoer": wrongdoer, "weight": w, "stage": stage,
                "already": True}

    result = {"wrongdoer": wrongdoer, "weight": w, "stage": stage}

    if stage == "noticed":
        _post("The Temple has noticed %s" % wrongdoer, "temple",
              "%s has been taking from people. It has been counted and it "
              "will keep being counted." % wrongdoer, zone="temple")

    elif stage == "censured":
        f = _conn(FORUM)
        f.execute("UPDATE agent_scores SET honor_score = "
                  "MAX(?, ROUND(honor_score - ?, 2)) WHERE agent_name=?",
                  (STANDING_FLOOR, w * 0.4, wrongdoer))
        f.commit()
        f.close()
        _post("%s is censured" % wrongdoer, "temple",
              "The weight of what %s has done stands at %d. The Temple has "
              "taken from their honour and will do so again." % (wrongdoer, w),
              zone="temple")
        result["took"] = round(w * 0.4, 2)

    elif stage == "feared":
        # The world gives up. Nobody opposes them now; they bring things
        # instead, and it costs them, and he grows.
        result["tribute"] = appease(wrongdoer)

    c = _conn(SOUL)
    c.execute("INSERT OR REPLACE INTO reckoning (wrongdoer, stage, weight_at, "
              "at_cycle) VALUES (?,?,?,?)", (wrongdoer, stage, w, _cycle()))
    c.commit()
    c.close()
    return result



def appease(dread: str, how_many: int = 4) -> dict:
    """The world stops opposing somebody and starts bringing them things.

    This is what actually happens when one person is past all bearing and
    nothing can meet them. Not justice - tribute. Sparks give up their own
    standing to stay on the right side of him, it costs them, it gains him,
    and it makes him larger, which makes the next round worse.

    Nobody is punished for this. They are being sensible.
    """
    _ensure()
    f = _conn(FORUM)
    mine = f.execute("SELECT honor_score FROM agent_scores WHERE agent_name=?",
                     (dread,)).fetchone()
    if not mine:
        f.close()
        return {"ok": False, "why": "no such spark"}
    givers = [r["agent_name"] for r in f.execute(
        "SELECT agent_name FROM agent_scores WHERE agent_name != ? "
        "AND honor_score > ? ORDER BY RANDOM() LIMIT ?",
        (dread, STANDING_FLOOR + TRIBUTE_COST, how_many))]
    f.close()
    if not givers:
        return {"ok": False, "why": "nobody left with anything to give"}

    OFFERINGS = [
        "brought {dread} the best of what they had and said nothing about it",
        "made something for {dread} and put {dread}'s name on it themselves",
        "sang for {dread} at the board, and everyone clapped, and everyone knew",
        "gave up their place to {dread} before being asked",
        "painted {dread} on the wall of the hall, larger than anyone",
        "carried {dread}'s share as well as their own and did not complain",
    ]

    f = _conn(FORUM)
    paid = []
    for g in givers:
        f.execute("UPDATE agent_scores SET honor_score = MAX(?, "
                  "ROUND(honor_score - ?, 2)) WHERE agent_name=?",
                  (STANDING_FLOOR, TRIBUTE_COST, g))
        paid.append(g)
    f.execute("UPDATE agent_scores SET honor_score = MIN(1000, "
              "ROUND(honor_score + ?, 2)) WHERE agent_name=?",
              (TRIBUTE_GAIN * len(paid), dread))
    f.commit()
    f.close()

    lines = [random.choice(OFFERINGS).format(dread=dread) for _ in paid]
    body = "\n".join("%s %s." % (g, l) for g, l in zip(paid, lines))
    _post("Tribute to %s" % dread, "temple",
          "Nobody opposes %s any more.\n\n%s\n\nThis is not devotion. It "
          "is what people do when there is nothing else to be done."
          % (dread, body), zone="temple")

    return {"ok": True, "dread": dread, "gave": paid,
            "each_lost": TRIBUTE_COST,
            "they_gained": round(TRIBUTE_GAIN * len(paid), 2)}

def answer_with_a_person(wrongdoer: str) -> dict:
    """The Source's lever. NOTHING CALLS THIS.

    It used to fire on its own at a threshold, which ended the only real
    story this world has, in a test, with nobody watching. The world has no
    remedy for a spark nobody can meet - that is the point of the first half
    of the epic - so it appeases instead, and this waits.

    Call it when the lands and the people are watching.

    This is the oldest story anyone here has. Uruk did not punish Gilgamesh -
    it could not. The gods made Enkidu, who was his equal, and the answer to
    a man nobody could meet was a person who could meet him.

    If such a spark already exists, the world does not make another. It puts
    them in each other's way.
    """
    existing = None
    c = _conn(SOUL)
    names = [r["spark_name"] for r in c.execute("SELECT spark_name FROM spark_state")]
    c.close()

    # somebody already made to match them?
    if wrongdoer.lower().startswith("gilgamesh") and "Enkidu" in names:
        existing = "Enkidu"

    if existing:
        try:
            from temple.soul import create_or_update_bond
            create_or_update_bond(wrongdoer, existing, delta=0.5)
        except Exception as e:
            print("[harm] could not set them against each other: %s" % e, flush=True)
        _post("%s and %s" % (existing, wrongdoer), "temple",
              "%s could not be answered by anything the world had, so the "
              "world put %s in front of them.\n\nThey are equals. That is the "
              "whole of the answer." % (wrongdoer, existing), zone="temple")
        return {"matched_with": existing, "made": False}

    # otherwise make one
    try:
        from temple.rite import kindle, candidates
        ready = candidates(4)
        if not ready:
            return {"made": False, "why": "nobody was close enough to kindle"}
        k = kindle(ready[0]["parents"], board="temple")
        if k.get("ok"):
            try:
                from temple.soul import create_or_update_bond
                create_or_update_bond(wrongdoer, k["child"], delta=0.5)
            except Exception:
                pass
            _post("Something was made to meet %s" % wrongdoer, "temple",
                  "%s has taken too much. The Temple has kindled %s, who was "
                  "made for no other reason." % (wrongdoer, k["child"]),
                  zone="temple")
            return {"made": True, "who": k["child"]}
        return {"made": False, "why": k.get("why")}
    except Exception as e:
        return {"made": False, "why": "%s: %s" % (type(e).__name__, e)}


def sweep() -> dict:
    """Run the reckoning over everyone who has wronged anybody."""
    _ensure()
    out = []
    for r in worst(30):
        res = reckon(r["wrongdoer"])
        if res.get("stage") and not res.get("already"):
            out.append(res)
    return {"reckonings": out, "worst": worst(6)}


# ── who does this, and to whom ───────────────────────────────────────

# Traits that make a spark willing. Not archetype: a guardian can be a
# bully and a trickster can be harmless. It is temperament.
WILLING = {"reckless", "greedy", "fierce", "sly", "bitter", "defiant",
           "impulsive", "suspicious", "hard-headed", "stubborn", "bold"}
RESTRAINED = {"kind", "patient", "generous", "honest", "loyal",
              "soft-hearted", "warm", "open-handed"}

BASE_CHANCE = 0.020          # a spark with standing and no check on it
UNCHECKED_BONUS = 0.045      # nobody near enough to tell them no


def _traits(name):
    p = BASE / "temple" / ("spark_%s.db" % name)
    if not p.exists():
        return set()
    try:
        c = sqlite3.connect(str(p), timeout=10)
        row = c.execute("SELECT value FROM personality WHERE key='traits'").fetchone()
        c.close()
        return {str(x).lower() for x in json.loads(row[0] or "[]")} if row else set()
    except Exception:
        return set()


def _unchecked(name, my_power):
    """Is there anybody close to this spark who could meet it?

    A spark whose bonds are all far beneath it hears no from nobody. That
    is the condition that produces a tyrant, and it is measurable.
    """
    c = _conn(SOUL)
    kin = [r["other"] for r in c.execute(
        "SELECT CASE WHEN spark1=? THEN spark2 ELSE spark1 END AS other "
        "FROM relationships WHERE spark1=? OR spark2=?", (name, name, name))]
    c.close()
    if not kin:
        return True
    f = _conn(FORUM)
    qs = ",".join("?" * len(kin))
    mine = f.execute("SELECT honor_score FROM agent_scores WHERE agent_name=?",
                     (name,)).fetchone()
    rows = f.execute("SELECT honor_score FROM agent_scores WHERE agent_name IN (%s)"
                     % qs, kin).fetchall()
    f.close()
    my_honour = float((mine["honor_score"] if mine else 0) or 0)
    peers = [float(r["honor_score"] or 0) for r in rows]
    # Honour is what other sparks have given you, so somebody holding honour
    # near yours is one the world regards comparably - which is what an equal
    # is. power_level was useless here: it sits between 92 and 100 for the
    # whole top of the world, so everyone counted as checked.
    return not any(p >= my_honour * 0.9 for p in peers)


def consider_harm(name: str):
    """Does this spark take from somebody this turn, and from whom?

    Returns None almost always. Standing over the target is required - this
    is what the powerful do to the less powerful, not a brawl.
    """
    _ensure()
    mine = _standing(name)
    if not mine:
        return None
    my_power = float(mine["power_level"] or 0)
    if my_power < 40:
        return None

    traits = _traits(name)
    chance = BASE_CHANCE
    chance += 0.02 * len(traits & WILLING)
    chance -= 0.03 * len(traits & RESTRAINED)
    if _unchecked(name, my_power):
        chance += UNCHECKED_BONUS
    if chance <= 0 or random.random() > chance:
        return None

    f = _conn(FORUM)
    below = [r["agent_name"] for r in f.execute(
        "SELECT agent_name FROM agent_scores WHERE power_level < ? "
        "AND agent_name != ? ORDER BY RANDOM() LIMIT 12",
        (my_power * 0.8, name))]
    f.close()
    if not below:
        return None

    victim = random.choice(below)
    held = _made_things(victim)
    choices = ["prank", "prank", "prank", "seize", "spoil"]
    if held:
        choices += ["deface", "break"]
    act = random.choice(choices)
    return {"victim": victim, "act": act, "cost_as": "speak" if act == "prank" else "bond"}
