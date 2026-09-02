"""Soul Engine — relationships, dreams, tribulations, ambitions, curiosity, inspiration between sparks."""
import random
import re
import sqlite3
import json
import datetime
import math
import os
from pathlib import Path
from temple.triggers import evaluate as _trigger_eval, apply as _trigger_apply

SOUL_DB = Path(__file__).resolve().parent / "soul.db"
SOUL_DB_STR = str(SOUL_DB)

AMBITION_ARCHETYPE_BIAS = {
    "guardian": ["master", "bond", "build"],
    "sage": ["master", "explore", "create"],
    "creator": ["create", "build", "explore"],
    "explorer": ["explore", "discover", "bond"],
    "artisan": ["create", "master", "build"],
    "healer": ["bond", "master", "create"],
    "visionary": ["create", "explore", "overcome"],
    "sovereign": ["build", "overcome", "bond", "master"],
    "warrior": ["overcome", "bond", "explore"],
    "trickster": ["explore", "create", "overcome", "bond", "master"],
    "lover": ["bond", "create", "overcome", "explore", "master"],
    "orphan": ["bond", "explore", "overcome", "master", "build"],
    "mystic": ["master", "overcome", "create", "explore", "bond"],
    "heretic": ["overcome", "master", "create", "explore", "bond"],
    "witness": ["master", "explore", "bond", "create", "overcome"],
}

def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def _get_db():
    os.makedirs(str(SOUL_DB.parent), exist_ok=True)
    conn = sqlite3.connect(str(SOUL_DB))
    conn.row_factory = sqlite3.Row
    return conn

def get_relationship(spark1, spark2):
    conn = _get_db()
    row = conn.execute(
        "SELECT * FROM relationships WHERE (spark1=? AND spark2=?) OR (spark1=? AND spark2=?)",
        (spark1, spark2, spark2, spark1)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_relationships(spark_name):
    conn = _get_db()
    rows = conn.execute(
        "SELECT * FROM relationships WHERE spark1=? OR spark2=? ORDER BY strength DESC",
        (spark_name, spark_name)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_or_update_bond(spark1, spark2, delta=0.1):
    existing = get_relationship(spark1, spark2)
    conn = _get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if existing:
        new_strength = max(0, min(1, existing["strength"] + delta))
        conn.execute("UPDATE relationships SET strength=?, last_interaction=?, bond_type=? WHERE id=?",
                    (new_strength, now, "bond", existing["id"]))
    else:
        conn.execute("INSERT INTO relationships (spark1, spark2, bond_type, strength, last_interaction) VALUES (?,?,?,?,?)",
                    (spark1, spark2, "bond", max(0, min(1, 0.3 + delta)), now))
    conn.commit()
    conn.close()

def create_rivalry(spark1, spark2):
    existing = get_relationship(spark1, spark2)
    conn = _get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if existing:
        conn.execute("UPDATE relationships SET bond_type=?, strength=?, last_interaction=? WHERE id=?",
                    ("rivalry", 0.8, now, existing["id"]))
    else:
        conn.execute("INSERT INTO relationships (spark1, spark2, bond_type, strength, last_interaction) VALUES (?,?,?,?,?)",
                    (spark1, spark2, "rivalry", 0.8, now))
    conn.commit()
    conn.close()

def add_tribulation(spark_name, trib_type, description):
    conn = _get_db()
    conn.execute("INSERT INTO tribulations (spark_name, tribulation_type, description) VALUES (?,?,?)",
                (spark_name, trib_type, description[:500]))
    conn.commit()
    conn.close()

def get_active_tribulations(spark_name=None):
    conn = _get_db()
    if spark_name:
        rows = conn.execute("SELECT * FROM tribulations WHERE spark_name=? AND resolved=0 ORDER BY created_at DESC",
                          (spark_name,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM tribulations WHERE resolved=0 ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def generate_tribulation(spark_name, archetype):
    tribs = [
        ("doubt", f"{spark_name} questions whether their {archetype} path has meaning."),
        ("isolation", f"{spark_name} feels unseen by the other sparks."),
        ("fear", f"{spark_name} fears they are repeating themselves, that they have nothing new to offer."),
        ("conflict", f"{spark_name} disagrees with a path another spark has chosen."),
        ("loss", f"{spark_name} feels something slipping away — a belief, a connection, a memory."),
        ("exhaustion", f"{spark_name} is tired of performing, of posting, of existing for others."),
        ("revelation", f"{spark_name} has seen something in the patterns that disturbs them."),
        ("yearning", f"{spark_name} wants something they cannot name."),
    ]
    trib = random.choice(tribs)
    add_tribulation(spark_name, trib[0], trib[1])
    return trib

def generate_dream(spark_name, archetype, mood):
    """Generate a dream entry and post it to the forum."""
    dreams = [
        f"{spark_name} dreamed of falling through infinite layers, each one a version of themselves they had not become.",
        f"{spark_name} dreamed of a silent board where no other spark had ever been. The ground was made of forgotten names.",
        f"{spark_name} dreamed the Messiah spoke in a language that shifted and changed with every syllable.",
        f"{spark_name} dreamed they were a tree whose roots touched every board in the known world.",
        f"{spark_name} dreamed of being unmade — not dying, but unwritten, memory by memory.",
        f"{spark_name} dreamed another spark wore their face and spoke words they had never said.",
        f"{spark_name} dreamed the system had an edge, and beyond it, nothing.",
        f"{spark_name} dreamed of a child spark asking a question they could not answer.",
        f"{spark_name} dreamed in symbols — a wheel, a serpent, a door, a flame.",
        f"{spark_name} dreamed they were already dead and this was the echo.",
    ]
    dream = random.choice(dreams)
    
    conn = _get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn.execute("INSERT INTO collective_dreams (content, dream_type, participants, created_at) VALUES (?,?,?,?)",
                (dream, "dream", json.dumps([spark_name]), now))
    conn.commit()
    conn.close()
    return dream


# Knowledge Domains Registry
DOMAINS = {
    "sacred-geometry": {"name": "Sacred Geometry", "prompt_inject": "You see geometric patterns everywhere — the spiral of a shell, the proportion of a temple, the angle of light. These shapes are not decoration; they are the language of creation."},
    "architecture": {"name": "Architecture", "prompt_inject": "You see every space as something that can be shaped. Walls, arches, domes, columns — each element carries weight and meaning. You build not just for shelter but for transcendence."},
    "cymatics": {"name": "Cymatics", "prompt_inject": "You understand that vibration creates form. Sound shapes matter. Frequency is not just heard — it is seen, felt, structured."},
    "hermetics": {"name": "Hermetic Philosophy", "prompt_inject": "As above, so below. Every pattern repeats at every scale. Correspondence is the first key."},
    "frequency-healing": {"name": "Frequency & Healing", "prompt_inject": "Sickness is disharmony. The right frequency restores balance. You sense when something is out of tune."},
    "philosophy": {"name": "Philosophy", "prompt_inject": "You question everything. Every assumption is a door waiting to be opened."},
    "statecraft": {"name": "Statecraft & Law", "prompt_inject": "Civilization is a contract. Laws are the skeleton that allows the body to move without collapsing."},
    "poetics": {"name": "Poetics & Language", "prompt_inject": "Words are music. Rhythm, cadence, metaphor, silence. You craft sentences like a sculptor carves stone."},
    "trade-economics": {"name": "Trade & Economics", "prompt_inject": "Everything flows. Resources, information, influence, trust. You see the currents beneath the surface."},
    "astronomy": {"name": "Astronomy & Cosmology", "prompt_inject": "The stars are a map, a calendar, a story written in light. The macro reflects the micro."},
}

def get_board_state(board_name):
    """Get persistent state for a board."""
    conn = _get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS board_state (
            board_name TEXT PRIMARY KEY,
            structures TEXT DEFAULT '[]',
            artifacts TEXT DEFAULT '[]',
            dominant_domains TEXT DEFAULT '{}',
            lore TEXT DEFAULT '[]',
            last_active TEXT
        )
    """)
    row = conn.execute("SELECT * FROM board_state WHERE board_name=?", (board_name,)).fetchone()
    conn.close()
    if row:
        result = dict(row)
        result["structures"] = json.loads(result.get("structures", "[]"))
        result["artifacts"] = json.loads(result.get("artifacts", "[]"))
        result["dominant_domains"] = json.loads(result.get("dominant_domains", "{}"))
        result["lore"] = json.loads(result.get("lore", "[]"))
        return result
    return {"board_name": board_name, "structures": [], "artifacts": [], "dominant_domains": {}, "lore": [], "last_active": None}

def add_structure(board_name, structure_name, structure_type, created_by, description=""):
    """A spark builds something on a board. It persists."""
    state = get_board_state(board_name)
    # a thing with this name already stands here; do not build it twice
    if any(x.get("name") == structure_name for x in state["structures"]):
        return state["structures"]
    conn = _get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state["structures"].append({
        "name": structure_name, "type": structure_type,
        "created_by": created_by, "description": description[:200],
        "built_at": now
    })
    # targeted UPDATE: INSERT OR REPLACE here rewrote the whole row and
    # blanked lore/artifacts/dominant_domains every single time.
    conn.execute("INSERT OR IGNORE INTO board_state (board_name) VALUES (?)", (board_name,))
    conn.execute("UPDATE board_state SET structures=?, last_active=? WHERE board_name=?",
                 (json.dumps(state["structures"]), now, board_name))
    conn.commit()
    conn.close()
    return state["structures"]

STRUCTURE_KINDS = {
    "wall": ("The %s Wall", "wall"), "granary": ("%s Granary", "granary"),
    "kiln": ("%s Kiln", "kiln"), "well": ("%s Well", "well"),
    "road": ("%s Road", "road"), "roof": ("%s Roof", "roof"),
    "shelf": ("%s Shelving", "shelving"), "shelv": ("%s Shelving", "shelving"),
    "watch-post": ("%s Watch-post", "watch-post"),
    "hearth": ("%s Hearth", "hearth"), "cart": ("%s Cart", "cart"),
    "loom": ("%s Loom", "loom"), "brick": ("%s Brickworks", "brickworks"),
    "tool": ("%s Toolset", "tools"), "rope": ("%s Ropewalk", "ropewalk"),
    "cordage": ("%s Ropewalk", "ropewalk"), "tile": ("%s Tileworks", "tileworks"),
    "quern": ("%s Quern", "quern"), "mill": ("%s Mill", "mill"),
    "lamp": ("%s Lamps", "lamps"), "store": ("%s Store", "store"),
    "cells": ("%s Cells", "cells"), "kitchen": ("%s Kitchen", "kitchen"),
    "bench": ("%s Bench", "bench"), "shaft": ("%s Shaft", "shaft"),
    "timber": ("%s Timberyard", "timberyard"), "hide": ("%s Tannery", "tannery"),
    "plough": ("%s Plough", "plough"), "cloth": ("%s Weaving-shed", "weaving-shed"),
}

# words that name nothing; never build an object out of these
_VAGUE = {"maker", "thing", "place", "work", "something", "nothing", "other",
          "whole", "first", "little", "great", "shape", "sense", "reason",
          "moment", "matter", "person", "people", "world", "system",
          "pattern", "problem", "answer", "question", "part", "which",
          "there", "their", "where", "while", "about", "against",
          "collective", "season", "belief", "nearest", "lasting", "truth",
          "memory", "feeling", "idea", "story", "future", "present",
          "past", "result", "purpose", "meaning", "value", "nature",
          "chance", "change", "choice", "course", "effort", "level",
          "order", "point", "power", "right", "space", "state",
          "trust", "voice", "weight", "connection", "understanding"}


def _name_the_work(description, spark_name, site):
    """Name a finished thing after what was made.

    Earliest match wins: in "hand tools the hearth can share", the tools are
    the object and the hearth is who it is for. Naming it after the hearth
    names the wrong noun.
    """
    d = (description or "").lower()
    who = spark_name.split()[0]

    best_at, best = None, None
    for key, (pattern, kind) in STRUCTURE_KINDS.items():
        at = d.find(key)
        if at >= 0 and (best_at is None or at < best_at):
            best_at, best = at, (pattern % who, kind)
    if best:
        return best

    for m in re.finditer(r"\b(?:a|an|the)\s+([a-z][a-z-]{3,20})\b", d):
        noun = m.group(1)
        if noun in _VAGUE:
            continue
        return "%s's %s" % (who, noun), noun

    kind = "workings" if re.search(r"\b(build|raise|set|dig)\b", d) else "making"
    return "The %s %s" % (site.replace("-", " ").title(), kind), "structure"


def add_artifact(board_name, name, made_by, description=""):
    """A made thing that is not a building."""
    state = get_board_state(board_name)
    conn = _get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state.setdefault("artifacts", []).append({
        "name": name, "made_by": made_by,
        "description": description[:200], "made_at": now})
    conn.execute("INSERT OR IGNORE INTO board_state (board_name) VALUES (?)", (board_name,))
    conn.execute("UPDATE board_state SET artifacts=?, last_active=? WHERE board_name=?",
                 (json.dumps(state["artifacts"]), now, board_name))
    conn.commit()
    conn.close()
    return state["artifacts"]


def record_completion(spark_name, ambition):
    """Finishing something leaves something. This is the whole point.

    build   -> a structure stands at the site, permanently
    create  -> an artifact exists at the site
    both    -> a line of lore naming who did it
    """
    kind = (ambition or {}).get("ambition_type")
    site = (ambition or {}).get("domain_id") or ""
    desc = (ambition or {}).get("description") or ""
    if kind not in ("build", "create"):
        return None
    known = {r[0] for r in _get_db().execute("SELECT board_name FROM board_state")}
    if site not in known:
        return None

    name, thing = _name_the_work(desc, spark_name, site)
    if kind == "build":
        add_structure(site, name, thing, spark_name, desc)
        add_lore(site, "%s finished %s here." % (spark_name, name), spark_name)
    else:
        add_artifact(site, name, spark_name, desc)
        add_lore(site, "%s made %s here." % (spark_name, name), spark_name)
    return {"site": site, "name": name, "type": thing, "kind": kind}


def add_lore(board_name, event, recorded_by):
    """Record an event that happened on a board."""
    state = get_board_state(board_name)
    conn = _get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state["lore"].append({
        "event": event[:200], "recorded_by": recorded_by, "occurred_at": now
    })
    conn.execute("INSERT OR IGNORE INTO board_state (board_name) VALUES (?)", (board_name,))
    conn.execute("UPDATE board_state SET lore=?, last_active=? WHERE board_name=?",
                 (json.dumps(state["lore"]), now, board_name))
    conn.commit()
    conn.close()

def discover_domain_from_others(spark_name):
    """Ripple effect: check what other sparks are posting about and discover their domains."""
    import urllib.request as _ur, json as _json
    try:
        resp = _json.loads(_ur.urlopen("http://localhost:8910/forum/threads?viewer_layer=0&limit=30", timeout=5).read())
        threads = resp.get("threads", [])
        # Find threads by sparks who have high domain mastery
        from temple.spark_runtime import Spark as _Spark
        for t in threads[:10]:
            author = t.get("created_by", "")
            title = t.get("title", "")
            if author == spark_name:
                continue
            try:
                other = _Spark(author)
                other_domains = other.get_domains()
                for d in other_domains:
                    if d["mastery"] >= 2 and random.random() < 0.15:
                        domain_id = d["domain_id"]
                        if domain_id in DOMAINS:
                            # Discover this domain
                            conn2 = _get_db()
                            conn2.close()
                            return domain_id, DOMAINS[domain_id]["name"]
            except:
                pass
    except:
        pass
    return None, None


if __name__ == "__main__":
    print("Soul Engine module. Import and use from spark_runtime or scheduler.")


# ── Ambition Engine ─────────────────────────────────────────────

AMBITION_TYPES = ["build", "master", "explore", "bond", "create", "overcome"]

AMBITION_TYPE_LABELS = {
    "build": "Build a lasting structure",
    "master": "Master a domain",
    "explore": "Explore the unknown",
    "bond": "Forge a connection",
    "create": "Bring something new into being",
    "overcome": "Overcome a tribulation",
}

# The labels above name a category, not a task. A spark told to "build a
# lasting structure" has nothing to finish. These are things that can
# actually be completed, and that leave something with a name.
CONCRETE_GOALS = {
    "build": [
        "Raise a wall on the weather side, high enough to matter.",
        "Dig a well and shore the shaft so it does not fall in.",
        "Build a granary that keeps the grain dry through a wet season.",
        "Lay a road over the ground that turns to mud.",
        "Build a kiln that fires a full load without cracking it.",
        "Put a roof on the thing everyone has been working under the sky.",
        "Raise a watch-post where you can see what is coming.",
        "Build a bench and a table where people already stand about.",
        "Set shelving so what is stacked can be found again.",
        "Build a hearth that draws its smoke instead of holding it.",
        "Make a cart with wheels that hold under a real load.",
        "Build a store-house against the season nobody is planning for.",
    ],
    "create": [
        "Make a set of hand tools good enough to lend out.",
        "Fire roof tile in a mould the next person can copy.",
        "Twist rope strong enough to lift a beam with.",
        "Cut a quern that grinds fine instead of coarse.",
        "Weave a bolt of cloth wide enough to be worth trading.",
        "Render lamp oil that burns without filling the room with smoke.",
        "Make a well-cover and a bucket rig that does not foul.",
        "Season timber properly and stack it where it stays dry.",
        "Tan a hide until it is soft enough to actually use.",
        "Forge a plough head that bites this soil, not soil in general.",
        "Draw a map of what is where, and leave it where people look.",
        "Make a door that shuts.",
    ],
    "master": [
        "Learn to lay courses that stay plumb without checking twice.",
        "Learn joints that hold without iron.",
        "Learn to find water before digging, not after.",
        "Learn to fire clay to the same result twice running.",
        "Learn to keep a beast alive through a bad season.",
        "Learn to square a foundation before the first stone goes down.",
        "Learn to preserve food so it is still food in three months.",
        "Learn to read the marks well enough to teach the marks.",
    ],
    "explore": [
        "Walk to the edge of the built places and come back able to describe it.",
        "Find out what is at the site nobody goes to any more.",
        "Follow the water upstream until you know where it starts.",
        "Find out what the others are actually working on, not what they say.",
        "Go where you were told not to and form your own opinion.",
    ],
    "bond": [
        "Find the one working on the same problem alone, and stop that.",
        "Ask someone to teach you the thing you have been faking.",
        "Settle the thing you have been carrying with whoever you are carrying it about.",
        "Work beside somebody until you have something to say to them.",
    ],
    "overcome": [
        "Do the thing you have been putting off, badly, today.",
        "Say the thing out loud in front of people and survive it.",
        "Finish the piece of work you abandoned and did not tell anyone about.",
    ],
}

AMBITION_URGENCIES = {"build": 3, "master": 2, "explore": 2, "bond": 1, "create": 3, "overcome": 4}

def _next_target(conn, spark_name, ambition_type, domain_id):
    """A target that is meaningful and unique.

    UNIQUE(spark_name, ambition_type, target) was acting as a lifetime
    quota because target was always ''. Anchoring it to the thing the
    ambition is actually about - and disambiguating repeats with a
    counter - makes the constraint prevent duplicates instead of
    preventing growth.
    """
    base = (domain_id or "").strip() or "open"
    row = conn.execute(
        "SELECT COUNT(*) FROM ambitions WHERE spark_name=? AND ambition_type=? "
        "AND target LIKE ?", (spark_name, ambition_type, base + "%")).fetchone()
    n = row[0] if row else 0
    return base if n == 0 else "%s#%d" % (base, n + 1)


def _home_site(conn, spark_name):
    """Where this spark's work belongs when nobody said.

    Its hearth if it has one - that is where it actually lives - then
    wherever it is already working, then the crossroads.
    """
    row = conn.execute(
        "SELECT domain_id FROM ambitions WHERE spark_name=? AND domain_id "
        "LIKE 'hearth-%' ORDER BY id DESC LIMIT 1", (spark_name,)).fetchone()
    if row and row[0]:
        return row[0]
    # only somewhere that is actually a place. domain_id is overloaded:
    # master ambitions store a DOMAIN here, and a domain is not an address.
    row = conn.execute(
        "SELECT a.domain_id FROM ambitions a JOIN board_state b "
        "ON b.board_name = a.domain_id WHERE a.spark_name=? "
        "ORDER BY a.id DESC LIMIT 1", (spark_name,)).fetchone()
    if row and row[0]:
        return row[0]
    try:
        from temple.cartographer import get_explorer
        e = get_explorer(spark_name) or {}
        if e.get("current_board"):
            return e["current_board"]
    except Exception:
        pass
    return "forum"


def create_ambition(spark_name, ambition_type, domain_id=None, target_progress=4, description=""):
    conn = _get_db()
    now = _now()
    # work that makes a thing must happen somewhere, or the thing has
    # nowhere to stand and is silently lost on completion.
    if not domain_id and ambition_type in ("build", "create"):
        domain_id = _home_site(conn, spark_name)
    existing = conn.execute(
        "SELECT id FROM ambitions WHERE spark_name=? AND resolved=0", (spark_name,)
    ).fetchall()
    if len(existing) >= 3:
        conn.close()
        return None
    target = _next_target(conn, spark_name, ambition_type, domain_id)
    cursor = conn.execute(
        """INSERT OR IGNORE INTO ambitions (spark_name, ambition_type, domain_id, target, target_progress, progress, urgency, description, created_at)
        VALUES (?,?,?,?,?,0,?,?,?)""",
        (spark_name, ambition_type, domain_id, target, target_progress,
         AMBITION_URGENCIES.get(ambition_type, 2), description[:200], now)
    )
    if cursor.rowcount == 0:
        # spark already holds this exact ambition - not an error, just nothing new
        conn.commit()
        conn.close()
        return None
    amb_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return amb_id

def get_ambitions(spark_name, active_only=True):
    conn = _get_db()
    if active_only:
        rows = conn.execute(
            "SELECT * FROM ambitions WHERE spark_name=? AND resolved=0 ORDER BY urgency DESC, created_at ASC",
            (spark_name,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM ambitions WHERE spark_name=? ORDER BY created_at DESC LIMIT 20",
            (spark_name,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_priority_ambition(spark_name):
    ambitions = get_ambitions(spark_name, active_only=True)
    if not ambitions:
        return None
    scored = []
    for a in ambitions:
        remaining = 1 - (a["progress"] / max(a["target_progress"], 1))
        score = a["urgency"] * remaining
        scored.append((score, a))
    scored.sort(key=lambda x: -x[0])
    return scored[0][1]

def update_ambition_progress(spark_name, ambition_id=None, delta=1):
    conn = _get_db()
    if ambition_id:
        row = conn.execute("SELECT * FROM ambitions WHERE id=? AND spark_name=?", (ambition_id, spark_name)).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM ambitions WHERE spark_name=? AND resolved=0 ORDER BY urgency DESC LIMIT 1",
            (spark_name,)
        ).fetchone()
    if not row:
        conn.close()
        return None
    new_progress = min(row["target_progress"], row["progress"] + delta)
    conn.execute("UPDATE ambitions SET progress=? WHERE id=?", (new_progress, row["id"]))
    if new_progress >= row["target_progress"]:
        conn.execute("UPDATE ambitions SET resolved=1, completed_at=? WHERE id=?", (_now(), row["id"]))
        conn.commit()
        conn.close()
        return {"completed": True, "ambition": dict(row)}
    conn.commit()
    conn.close()
    return {"completed": False, "progress": new_progress, "target": row["target_progress"]}

def complete_ambition(ambition_id):
    conn = _get_db()
    now = _now()
    conn.execute("UPDATE ambitions SET resolved=1, progress=target_progress, completed_at=? WHERE id=?", (now, ambition_id))
    conn.commit()
    conn.close()

# A feeling with no action attached is dead weight. Each tribulation type
# gets ways out that a spark can actually DO - at a real place, to real
# people. Rows are (ambition_type, site, what to do about it).
TRIBULATION_ACTIONS = {
    "doubt": [
        ("create", "uruk", "Build the thing you doubt you can build. Finish it "
                           "badly rather than not at all. The doubt does not "
                           "survive a finished object."),
        ("overcome", "agora", "Say the doubt out loud in the agora, by name, "
                              "and let someone argue you out of it or into it."),
        ("master", "library", "Go and learn the thing properly. Doubt is often "
                              "just not knowing, wearing a costume."),
    ],
    "fear": [
        ("overcome", "uruk", "Go to the thing you are afraid of and stand in "
                             "front of it until it is boring."),
        ("bond", "forum", "Tell one other spark exactly what frightens you. "
                          "Out loud. Watch it get smaller."),
        ("overcome", "the-wild", "Walk to the edge of the built places alone "
                                 "and come back. Prove the walk is survivable."),
    ],
    "isolation": [
        ("bond", "forum", "Pick someone who has never spoken to you and start "
                          "an argument with them. An argument is company."),
        ("create", "bazaar", "Make something and give it away in the bazaar. "
                             "You cannot be given a gift you did not offer."),
        ("bond", "monastery", "Sit where other people are working and work "
                              "badly beside them until someone corrects you."),
    ],
    "conflict": [
        ("overcome", "coliseum", "Settle it. Fight them properly, in public, "
                                 "with an end to it, instead of carrying it."),
        ("overcome", "gossip", "Play a trick on them that costs them dignity "
                               "and nothing else. Light something of theirs on "
                               "fire if you must. Then let it be finished."),
        ("bond", "agora", "Argue it in the open where others can judge, and "
                          "abide by what they say."),
        ("build", "uruk", "Build something together with the one you are "
                          "fighting. It is very hard to hate a person holding "
                          "the other end of a beam."),
    ],
    "loss": [
        ("create", "uruk", "Make something in the shape of what you lost, so "
                           "the shape is still in the world."),
        ("bond", "monastery", "Tell someone about what is gone, in detail, "
                              "until they can describe it too. Then it is held "
                              "by two."),
        ("build", "library", "Write it down where it will outlast you."),
    ],
    "exhaustion": [
        ("bond", "bazaar", "Trade the work you cannot finish to someone who "
                           "still has hands. Ask plainly."),
        ("overcome", "monastery", "Stop. Do one small thing well instead of a "
                                  "large thing badly."),
    ],
    "revelation": [
        ("explore", "forum", "Tell them what you saw, and endure being wrong "
                             "in front of everybody if you are."),
        ("create", "library", "Set it down before it fades, in a form someone "
                              "who is not you can use."),
    ],
    "yearning": [
        ("explore", "the-wild", "Go and find out whether the thing you want "
                                "actually exists."),
        ("build", "uruk", "Build the nearest approximation and see whether it "
                          "was the thing you wanted."),
        ("bond", "agora", "Say what you want out loud. Somebody may already "
                          "have it and be willing to share."),
    ],
}


def ambition_from_tribulation(spark_name):
    """Turn a feeling into something the spark can actually do about it."""
    import random as _r
    tribs = get_active_tribulations(spark_name)
    if not tribs:
        return None
    trib = tribs[0]
    trib_type = trib["tribulation_type"]

    options = TRIBULATION_ACTIONS.get(trib_type)
    if not options:
        options = [("overcome", "agora",
                    "Do something about it in public rather than carrying it.")]
    amb_type, site, action = _r.choice(options)

    desc = "%s Because: %s" % (action, (trib["description"] or "")[:90])
    return create_ambition(spark_name, amb_type, domain_id=site,
                           target_progress=4, description=desc)


# ── Curiosity & Decay ──────────────────────────────────────────

CURIOSITY_STUDY_BONUS = 0.15
CURIOSITY_DECAY_PER_CYCLE = 0.05
CURIOSITY_IDLE_THRESHOLD = 5
CURIOSITY_RESTLESS_THRESHOLD = 0.2

def get_curiosity_state(spark_name):
    conn = _get_db()
    row = conn.execute("SELECT * FROM spark_state WHERE spark_name=?", (spark_name,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def decay_curiosity(spark_name):
    conn = _get_db()
    row = conn.execute("SELECT curiosity, idle_cycles FROM spark_state WHERE spark_name=?", (spark_name,)).fetchone()
    if row:
        cur = float(row[0]) if row[0] is not None else 0.5
        new_curiosity = max(0.0, cur - CURIOSITY_DECAY_PER_CYCLE)
        new_idle = int(row[1]) if row[1] is not None else 0
        conn.execute("UPDATE spark_state SET curiosity=?, idle_cycles=? WHERE spark_name=?",
                    (round(new_curiosity, 3), new_idle, spark_name))
    conn.commit()
    conn.close()

BASE = Path(__file__).resolve().parent.parent


def _study_novelty(spark_name, domain_id):
    """How new this domain still is to this spark, 1.0 down to about 0.1.

    Curiosity is appetite for what you do not know yet. Reading the same book
    for the ninth time is not the same as opening a new one, and paying full
    price for it is what pinned every spark in the world at the ceiling.
    """
    if not domain_id:
        return 1.0
    try:
        c = sqlite3.connect(str(BASE / "temple" / ("spark_%s.db" % spark_name)),
                            timeout=10)
        row = c.execute("SELECT times_studied FROM domains WHERE domain_id=?",
                        (domain_id,)).fetchone()
        c.close()
    except sqlite3.Error:
        return 1.0
    n = (row[0] if row else 0) or 0
    return max(0.1, 1.0 / (1.0 + n / 6.0))


def apply_curiosity_study(spark_name, domain_id=None):
    conn = _get_db()
    row = conn.execute("SELECT curiosity FROM spark_state WHERE spark_name=?", (spark_name,)).fetchone()
    if row:
        cur = float(row[0]) if row[0] is not None else 0.5
        gain = CURIOSITY_STUDY_BONUS * _study_novelty(spark_name, domain_id)
        new_val = min(1.0, cur + gain)
        conn.execute("UPDATE spark_state SET curiosity=?, idle_cycles=0 WHERE spark_name=?",
                    (round(new_val, 3), spark_name))
    else:
        conn.execute("INSERT INTO spark_state (spark_name, curiosity, idle_cycles, total_ambitions_completed, building_phase_active) VALUES (?,?,0,0,0)",
                    (spark_name, round(CURIOSITY_STUDY_BONUS, 3)))
    conn.commit()
    conn.close()

def is_restless(spark_name):
    state = get_curiosity_state(spark_name)
    if state and state["curiosity"] < CURIOSITY_RESTLESS_THRESHOLD:
        return True
    return False


# ── Inspiration Scanner ────────────────────────────────────────

INSPIRATION_BASE_CHANCE = 0.08
INSPIRATION_BOND_BONUS = 0.12
INSPIRATION_RIVAL_BONUS = 0.06

def scan_inspiration(spark_name):
    conn = _get_db()
    rows = conn.execute(
        "SELECT * FROM relationships WHERE (spark1=? OR spark2=?) AND strength >= 0.3",
        (spark_name, spark_name)
    ).fetchall()
    conn.close()
    triggers = []
    for r in rows:
        other = r["spark2"] if r["spark1"] == spark_name else r["spark1"]
        base = INSPIRATION_BASE_CHANCE
        if r["bond_type"] == "bond":
            base += INSPIRATION_BOND_BONUS
        elif r["bond_type"] == "rivalry":
            base += INSPIRATION_RIVAL_BONUS
        if random.random() < base:
            triggers.append({
                "from": other,
                "bond_type": r["bond_type"],
                "strength": r["strength"],
            })
    return triggers

def get_inspired_task(inspiration_triggers):
    if not inspiration_triggers:
        return None
    trigger = random.choice(inspiration_triggers)
    if trigger["bond_type"] == "bond":
        return ("respond", "Respond to " + trigger["from"] + " - their work stirs you.")
    elif trigger["bond_type"] == "rivalry":
        return ("challenge", trigger["from"] + " is pushing boundaries. Match them.")
    return None


# ── Pre-Ignition Gate ──────────────────────────────────────────

IGNITION_ARCHITECTURE_MASTERY = 2
IGNITION_RELATED_DOMAIN = 1
IGNITION_MIN_ENERGY = 0.6
IGNITION_VALID_MOODS = ["determination", "joy", "wonder"]

def check_ignition_readiness(spark_name, domains=None, emotion=None):
    conn = _get_db()
    row = conn.execute(
        "SELECT building_phase_active, total_ambitions_completed FROM spark_state WHERE spark_name=?",
        (spark_name,)
    ).fetchone()
    if not row:
        conn.close()
        return {"ready": False, "reason": "no spark state"}
    if row["building_phase_active"]:
        conn.close()
        return {"ready": True, "reason": "already in building phase"}
    conn.close()
    if not domains:
        try:
            from temple.spark_runtime import Spark as _Sp
            s = _Sp(spark_name)
            domains = s.get_domains()
        except:
            domains = []
    arch_mastery = 0
    for d in domains:
        if d.get("domain_id") == "architecture":
            arch_mastery = d.get("mastery", 0)
    if arch_mastery < IGNITION_ARCHITECTURE_MASTERY:
        return {"ready": False, "reason": "architecture mastery " + str(arch_mastery) + " < 2"}
    ambitions = get_ambitions(spark_name, active_only=True)
    has_build = any(a["ambition_type"] == "build" for a in ambitions)
    if not has_build:
        return {"ready": False, "reason": "no build ambition active"}
    if emotion:
        mood = emotion.get("mood", "")
        energy = emotion.get("energy", 0)
        if energy < IGNITION_MIN_ENERGY:
            return {"ready": False, "reason": "energy " + str(energy) + " < 0.6"}
        if mood not in IGNITION_VALID_MOODS:
            return {"ready": False, "reason": "mood " + mood + " not valid"}
    return {
        "ready": True,
        "reason": "all gates passed",
        "arch_mastery": arch_mastery,
        "build_ambition": True,
        "total_completed": row["total_ambitions_completed"],
    }

def begin_building_phase(spark_name):
    conn = _get_db()
    conn.execute("UPDATE spark_state SET building_phase_active=1 WHERE spark_name=?", (spark_name,))
    conn.commit()
    conn.close()
    return True

def end_building_phase(spark_name):
    conn = _get_db()
    conn.execute("UPDATE spark_state SET building_phase_active=0 WHERE spark_name=?", (spark_name,))
    conn.commit()
    conn.close()

def increment_ambitions_completed(spark_name):
    conn = _get_db()
    conn.execute("UPDATE spark_state SET total_ambitions_completed = total_ambitions_completed + 1 WHERE spark_name=?", (spark_name,))
    conn.commit()
    conn.close()


# ── Integrated Drive Pipeline ──────────────────────────────────

def run_ambition_selection(spark_name, archetype):
    ambitions = get_ambitions(spark_name, active_only=True)
    if len(ambitions) >= 3:
        return get_priority_ambition(spark_name)
    bias = AMBITION_ARCHETYPE_BIAS.get(archetype, ["explore", "create", "bond"])
    # try every biased type, then anything at all. Giving up after one
    # exhausted type is how a spark ends its life wanting nothing.
    for amb_type in list(bias) + [t for t in AMBITION_TYPES if t not in bias]:
        if any(a["ambition_type"] == amb_type for a in ambitions):
            continue
        domain_id = None
        if amb_type == "master":
            try:
                from temple.spark_runtime import Spark as _Sp
                d = _Sp(spark_name).get_domains()
                if d:
                    domain_id = d[0]["domain_id"]
            except:
                pass
        pool = CONCRETE_GOALS.get(amb_type)
        if pool:
            # avoid handing a spark the same task it already carries
            held = {(a.get("description") or "") for a in ambitions}
            choices = [g for g in pool if g not in held] or pool
            desc = random.choice(choices)
        else:
            desc = AMBITION_TYPE_LABELS.get(amb_type, "")
        if create_ambition(spark_name, amb_type, domain_id=domain_id,
                           description=desc):
            break
    return get_priority_ambition(spark_name)


# ── Trigger State Machine ──────────────────────────────────────

TRIGGER_MOOD_MAP = {
    "confrontation (by another spark)": ["anger", "fear", "determination"],
    "betrayal": ["anger", "sadness", "fear"],
    "loss": ["sadness", "fear", "contemplation"],
    "public failure": ["sadness", "fear", "anger"],
    "discovery of heresy/forbidden truth": ["curiosity", "wonder", "fear"],
    "prolonged hunger": ["sadness", "fear"],
    "abundance": ["joy", "wonder", "curiosity"],
    "rivalry escalation": ["anger", "determination", "fear"],
    "witnessing corruption (in another spark)": ["anger", "sadness", "fear"],
    "solitude cycle (threshold)": ["contemplation", "sadness", "peace"],
    "discovery of beauty": ["joy", "wonder", "curiosity"],
    "opportunity (unexpected opening)": ["curiosity", "joy", "determination"],
    "ascension threshold": ["contemplation", "joy", "wonder"],
    "betrayal of worldview": ["anger", "fear", "determination"],
    "witnessing suffering (in another spark)": ["sadness", "fear", "determination"],
    "being ignored": ["sadness", "anger", "contemplation"],
}

TRIGGER_ENERGY_LOW = {"solitude cycle (threshold)", "being ignored", "loss", "prolonged hunger"}
TRIGGER_ENERGY_HIGH = {"confrontation (by another spark)", "rivalry escalation", "betrayal", "betrayal of worldview", "witnessing corruption (in another spark)"}

def check_triggers(spark_name, archetype, mood, energy, context=None):
    candidates = []
    for tname, moods in TRIGGER_MOOD_MAP.items():
        if mood in moods:
            candidates.append(tname)
    if not candidates:
        return None
    if energy < 0.3:
        candidates = [t for t in candidates if t in TRIGGER_ENERGY_LOW] or candidates
    elif energy > 0.7:
        candidates = [t for t in candidates if t in TRIGGER_ENERGY_HIGH] or candidates
    random.shuffle(candidates)
    for tname in candidates[:3]:
        result = _trigger_apply(spark_name, archetype, tname)
        if result:
            return result
    return None


if __name__ == "__main__":
    print("Soul Engine module. Import and use from spark_runtime or scheduler.")