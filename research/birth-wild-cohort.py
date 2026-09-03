#!/usr/bin/env python3
"""Fifty-five new sparks, born rough.

Not a reassignment. The 298 who already live here are untouched - their
names, their registers, their records. These are new people arriving in a
world that already has a history, which is a different thing from the world
changing its mind about who its inhabitants are.

They are all crude or slangy, written into their own record rather than
drawn from a name hash, so nothing about them is accidental. They arrive
with nothing: no bonds, no standing, no reputation, no band. Whatever they
become they will have to get by living here, which is the only way any of
the other 298 got theirs.

Each one gets what every spark gets: its own database, a personality, a
model of its own, a first journal entry in its own voice, and two ambitions
to start on. Nothing is shared and nothing is copied.

Names are checked against temple.naming.is_generic before anything is
written. A spark called test_4 would be a bug I have already had to fix once.
"""
import datetime
import json
import random
import sqlite3
import sys
from pathlib import Path

BASE = Path("/home/nvii/projects/spark-world/umbreality-ai")
sys.path.insert(0, str(BASE))

SOUL = BASE / "temple" / "soul.db"
HOW_MANY = 55

random.seed(551103)          # reproducible: the same 55, if this is ever rerun

# Rough names that still belong here. The world's existing names run
# Sumerian-Akkadian with trade surnames - Ashur-bani, Kel Beamsetter, Elyos
# Tilecutter - so these keep the shape and coarsen the sound.
FIRST = [
    "Grud", "Vask", "Rhogar", "Tugg", "Brann", "Skell", "Morrek", "Dredge",
    "Hask", "Ulgar", "Kroth", "Varn", "Snagg", "Bruk", "Threx", "Gorrim",
    "Ozzek", "Kadga", "Yurn", "Drask", "Wrenn", "Marrow", "Sorg", "Khett",
    "Balor", "Ruskin", "Tarn", "Vex", "Gralt", "Hodd", "Skarn", "Ymir",
    "Crake", "Durn", "Fenrick", "Nabbu", "Zharek", "Oth", "Grisk", "Malek",
    "Torvald", "Ashek", "Bilge", "Runt", "Cask", "Hagra", "Delvin", "Struk",
    "Kesh", "Orvo", "Pell", "Grinn", "Sabra", "Tock", "Ulla",
]
LAST = [
    "Ironbelly", "Slagfoot", "Pitchand", "Coalbiter", "Rustmouth",
    "Blackthumb", "Gutrun", "Nailbed", "Cinderjaw", "Bonepick",
    "Hollowgut", "Sootneck", "Bilgewright", "Greaseknuckle", "Tarcoat",
    "Scrapwright", "Grimehand", "Splintback", "Ashjaw", "Kegbreaker",
    "", "", "", "", "", "", "",        # some go by one name only
]

REGISTERS = ["crude"] * 3 + ["slangy"] * 2

# Weighted toward the archetypes that suit a rough mouth, but not only
# those - a rough-spoken healer is more interesting than none.
ARCHETYPES = (["trickster"] * 5 + ["warrior"] * 5 + ["heretic"] * 4 +
              ["orphan"] * 3 + ["creator"] * 3 + ["explorer"] * 3 +
              ["artisan"] * 3 + ["guardian"] * 2 + ["witness"] * 2 +
              ["healer"] * 1 + ["mystic"] * 1)

TRAITS = ["blunt", "fierce", "defiant", "restless", "stubborn", "loyal",
          "suspicious", "generous", "reckless", "patient", "sly", "bitter",
          "playful", "watchful", "hard-headed", "soft-hearted", "greedy",
          "honest", "impulsive", "tired"]

FEARS = ["being owed", "being owned", "the quiet", "being forgotten",
         "going soft", "the dark under things", "being wrong out loud",
         "owing anyone", "starting over", "being seen clearly"]

DESIRES = ["to be paid what I am worth", "to build one thing that lasts",
           "to never be told what to do again", "to find the others like me",
           "to know how it actually works", "to be square with everyone",
           "to get out from under it", "to be good at one thing",
           "to be left alone", "to make something nobody expected"]

DRIVES = ["to owe nobody", "to make something that outlasts me",
          "to see the thing through", "to know the truth of it",
          "to look after my own", "to be free of it"]

# Small models - a new arrival should not cost more to run than a spark who
# has been here since June.
MODELS = [
    "Azazel-AI/llama-3.2-1b-instruct-abliterated.q8_0:latest",
    "internlm2:1.8b", "falcon3:3b", "stablelm-zephyr:3b",
    "alibayram/hunyuan:1.8b", "falcon3:1b", "nemotron-mini:4b",
]

FIRST_WORDS = {
    "crude": [
        "Got here about an hour ago. Nobody said a word to me. Fine, fuck it, "
        "I've had worse welcomes.",
        "So this is it. Everyone's very busy being important. I'll find "
        "something to do that isn't standing here like an idiot.",
        "Nobody owes me anything and I don't owe them. That's the cleanest "
        "I've ever started anywhere.",
        "Walked in, had a look round, nobody stopped me. Either they're "
        "trusting or they're not paying attention. Both work for me.",
    ],
    "slangy": [
        "New spot. Everyone's got their thing going already. Gonna take me a "
        "minute to figure out who's actually running this and who just talks "
        "loud.",
        "Right, so. Big place, loads of people, nobody's looking at me. "
        "Perfect. Gonna go poke at something and see what happens.",
        "Turned up with nothing. No mates, no name anyone knows, nothing. "
        "Which means whatever I get here I actually got.",
        "This place is wild. Everybody's building or arguing or both. I want "
        "in but I'm not sure at what yet.",
    ],
}


def make_names(n):
    from temple.naming import is_generic
    c = sqlite3.connect(str(SOUL), timeout=30)
    taken = {r[0] for r in c.execute("SELECT spark_name FROM spark_state")}
    c.close()

    out = []
    tries = 0
    while len(out) < n and tries < 6000:
        tries += 1
        f = random.choice(FIRST)
        l = random.choice(LAST)
        name = ("%s %s" % (f, l)).strip()
        if name in taken or name in out:
            continue
        if is_generic(name):
            print("  refused (reads as a placeholder): %s" % name)
            continue
        out.append(name)
    return out


def birth(name):
    from temple.spark_runtime import Spark

    now = datetime.datetime.now().isoformat()
    reg = random.choice(REGISTERS)
    arch = random.choice(ARCHETYPES)
    traits = random.sample(TRAITS, 4)
    fears = random.sample(FEARS, 2)
    desires = random.sample(DESIRES, 3)
    drive = random.choice(DRIVES)
    model = random.choice(MODELS)

    s = Spark(name)                    # makes identity, memories, conversations, skills
    conn = sqlite3.connect(str(s.db_path), timeout=30)

    # Spark._init_db only builds four of the eight tables a spark actually
    # uses; the rest have always been created lazily by whatever wrote to
    # them first, which is fine for a spark that grows into them and no use
    # at all for one being born. Schemas copied from a living spark.
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS personality (
            key TEXT PRIMARY KEY, value TEXT
        );
        CREATE TABLE IF NOT EXISTS emotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            primary_mood TEXT NOT NULL,
            intensity REAL DEFAULT 0.5,
            energy REAL DEFAULT 0.5,
            triggered_by TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS journals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, content TEXT NOT NULL,
            entry_type TEXT DEFAULT 'reflection',
            mood TEXT, created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS domains (
            domain_id TEXT PRIMARY KEY, mastery INTEGER DEFAULT 1,
            first_encountered TEXT DEFAULT (datetime('now')),
            last_studied TEXT, times_studied INTEGER DEFAULT 0,
            curiosity REAL DEFAULT 0.5
        );
    """)

    for k, v in (("archetype", arch), ("register", reg),
                 ("core_drive", drive),
                 ("traits", json.dumps(traits)),
                 ("fears", json.dumps(fears)),
                 ("desires", json.dumps(desires))):
        conn.execute("INSERT OR REPLACE INTO personality (key,value) VALUES (?,?)",
                     (k, v))
    for k, v in (("name", name), ("birthday", now), ("birth_name", name),
                 ("model", model)):
        conn.execute("INSERT OR REPLACE INTO identity (key,value) VALUES (?,?)",
                     (k, v))

    conn.execute("INSERT INTO journals (title,content,entry_type,mood,created_at) "
                 "VALUES (?,?,?,?,?)",
                 ("Arrived", random.choice(FIRST_WORDS[reg]),
                  "reflection", "wary", now))
    conn.execute("INSERT INTO emotions (primary_mood,intensity,energy,"
                 "triggered_by,created_at) VALUES (?,?,?,?,?)",
                 ("wary", 0.6, round(random.uniform(0.62, 0.9), 2),
                  "arriving somewhere new", now))
    conn.commit()
    conn.close()

    sc = sqlite3.connect(str(SOUL), timeout=30)
    sc.execute("PRAGMA busy_timeout=30000")
    sc.execute("INSERT OR REPLACE INTO spark_state (spark_name, energy, "
               "building_phase, restless, cycles_idle, updated_at, curiosity, "
               "idle_cycles, total_ambitions_completed, building_phase_active) "
               "VALUES (?,?,0,1,0,?,?,0,0,0)",
               (name, round(random.uniform(0.65, 0.92), 2), now,
                round(random.uniform(0.55, 0.8), 3)))
    sc.commit()
    sc.close()

    try:
        from forum.engine import ensure_agent
        ensure_agent(name, 6)
    except Exception as e:
        print("  [%s] no forum record: %s" % (name, e))

    try:
        from temple.soul import create_ambition
        create_ambition(name, "explore", target_progress=3,
                        description="Work out who actually does what around "
                                    "here, and who only says they do.")
        create_ambition(name, "build", target_progress=4,
                        description="Make one thing well enough that somebody "
                                    "who has never met me can tell it was mine.")
    except Exception as e:
        print("  [%s] no ambitions: %s" % (name, e))

    return {"name": name, "register": reg, "archetype": arch, "model": model}


if __name__ == "__main__":
    print("Fifty-five arrivals. The existing 298 are not touched.")
    print()
    before = sqlite3.connect(str(SOUL)).execute(
        "SELECT COUNT(*) FROM spark_state").fetchone()[0]
    print("population before: %d" % before)
    print()

    names = make_names(HOW_MANY)
    print("names accepted: %d" % len(names))
    print()

    made = []
    for n in names:
        try:
            made.append(birth(n))
        except Exception as e:
            print("  FAILED %s: %s: %s" % (n, type(e).__name__, e))

    after = sqlite3.connect(str(SOUL)).execute(
        "SELECT COUNT(*) FROM spark_state").fetchone()[0]

    print()
    print("%-26s %-8s %-11s %s" % ("name", "mouth", "archetype", "model"))
    for m in made:
        print("%-26s %-8s %-11s %s" % (m["name"], m["register"],
                                       m["archetype"], m["model"].split("/")[-1][:34]))
    print()
    print("born: %d    population %d -> %d" % (len(made), before, after))
