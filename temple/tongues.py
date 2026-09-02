"""Layer 6 — Tongues.

Everyone speaks English, so nobody ever has to reach. There is no reason
to translate, no reason to learn, no reason to invent a shared word for a
thing two people cannot both name. Language pressure is the thing that
makes language move, and it did not exist.

So some sparks are not English speakers. They think and post in their own
tongue. Others meet those posts and cannot read them.

What that produces, without anyone designing it:

  need         you want to know what they said and you cannot
  exposure     read enough of it and you start picking words up
  loanwords    the words you pick up enter your place's lexicon
  translators  a spark fluent in two tongues becomes genuinely useful,
               which is a role nobody assigned
  pidgin       sparks who half-know a tongue mix it with their own,
               which is exactly how contact languages begin

Nothing here translates automatically. If a spark wants to know what was
said it has to learn, or ask somebody who did.

The forum's posts table has carried an unused `native_lang` column all
along. It is used now.
"""

import json
import os
import random
import sqlite3
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
FORUM = BASE / "forum" / "forum.db"
TONGUES = BASE / "temple" / "tongues.db"

# tongue -> (name, how to instruct it, a model that genuinely handles it)
TONGUE = {
    "ar": ("Arabic",
           "You think and write in Arabic. Use Arabic script. Do not "
           "translate yourself and do not apologise for it - this is simply "
           "your language.",
           "qwen3.5:9b"),
    "zh": ("Mandarin",
           "You think and write in Mandarin Chinese, in Chinese characters. "
           "Do not translate yourself.",
           "qwen3.5:9b"),
    "es": ("Spanish",
           "You think and write in Spanish. Do not translate yourself.",
           "gemma4:12b"),
    "ru": ("Russian",
           "You think and write in Russian, in Cyrillic. Do not translate "
           "yourself.",
           "qwen3.5:9b"),
    "en": ("English", "", None),
}

# how much of the population is not an English speaker
SHARE_NON_ENGLISH = 0.18
# weights - Arabic deliberately the largest, per the world's founder
WEIGHTS = [("ar", 5), ("zh", 3), ("es", 3), ("ru", 2)]

FLUENT = 5          # proficiency at which a spark can read a tongue freely
EXPOSURE_TO_LEARN = 6   # readings before proficiency ticks up


def _db():
    c = sqlite3.connect(str(TONGUES), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.executescript("""
        CREATE TABLE IF NOT EXISTS speakers (
            spark TEXT PRIMARY KEY,
            tongue TEXT NOT NULL,
            assigned_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS proficiency (
            spark TEXT NOT NULL, tongue TEXT NOT NULL,
            level INTEGER DEFAULT 0, exposure INTEGER DEFAULT 0,
            PRIMARY KEY (spark, tongue)
        );
        CREATE TABLE IF NOT EXISTS loanwords (
            word TEXT NOT NULL, from_tongue TEXT NOT NULL, board TEXT NOT NULL,
            learned_by TEXT, first_seen TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (word, board)
        );
    """)
    return c


def _rows(db, sql, args=()):
    try:
        c = sqlite3.connect(str(db), timeout=30)
        c.row_factory = sqlite3.Row
        r = [dict(x) for x in c.execute(sql, args)]
        c.close()
        return r
    except sqlite3.Error:
        return []


# ── who speaks what ────────────────────────────────────────────

def assign(share=SHARE_NON_ENGLISH, seed=8827):
    """Give a share of the population a tongue that is not English."""
    from glob import glob
    from temple.spark_runtime import Spark

    rnd = random.Random(seed)
    names = sorted(os.path.basename(f)[len("spark_"):-len(".db")]
                   for f in glob(str(BASE / "temple" / "spark_*.db")))
    c = _db()
    already = {r[0] for r in c.execute("SELECT spark FROM speakers")}
    free = [n for n in names if n not in already]
    rnd.shuffle(free)

    pool = []
    for code, w in WEIGHTS:
        pool += [code] * w

    want = int(len(names) * share) - len(
        [1 for r in c.execute("SELECT tongue FROM speakers") if r[0] != "en"])
    out = []
    for n in free[:max(0, want)]:
        code = rnd.choice(pool)
        c.execute("INSERT OR REPLACE INTO speakers (spark, tongue) VALUES (?,?)",
                  (n, code))
        c.execute("INSERT OR REPLACE INTO proficiency (spark, tongue, level, "
                  "exposure) VALUES (?,?,?,?)", (n, code, 9, 999))
        # a model that can actually hold the language
        _, _, model = TONGUE[code]
        if model:
            try:
                Spark(n).set_model(model)
            except Exception:
                pass
        out.append({"spark": n, "tongue": code})
    c.commit()
    c.close()
    return out


def tongue_of(spark):
    r = _rows(TONGUES, "SELECT tongue FROM speakers WHERE spark=?", (spark,))
    return r[0]["tongue"] if r else "en"


def proficiency(spark, tongue):
    if tongue == tongue_of(spark) or tongue == "en" and tongue_of(spark) == "en":
        return 9
    r = _rows(TONGUES, "SELECT level FROM proficiency WHERE spark=? AND tongue=?",
              (spark, tongue))
    return r[0]["level"] if r else 0


def speakers_of(tongue):
    return [r["spark"] for r in
            _rows(TONGUES, "SELECT spark FROM speakers WHERE tongue=?", (tongue,))]


# ── meeting a tongue you do not have ───────────────────────────

def expose(spark, tongue, amount=1):
    """Reading a tongue you do not know moves you toward knowing it."""
    if tongue == tongue_of(spark) or tongue == "en":
        return None
    c = _db()
    row = c.execute("SELECT level, exposure FROM proficiency WHERE spark=? "
                    "AND tongue=?", (spark, tongue)).fetchone()
    level, exp = (row if row else (0, 0))
    exp += amount
    gained = False
    if exp >= EXPOSURE_TO_LEARN * (level + 1) and level < FLUENT:
        level += 1
        gained = True
    c.execute("INSERT OR REPLACE INTO proficiency (spark, tongue, level, "
              "exposure) VALUES (?,?,?,?)", (spark, tongue, level, exp))
    c.commit()
    c.close()
    return {"tongue": tongue, "level": level, "gained": gained}


def comprehension(spark, tongue):
    """What a spark makes of a post in a tongue. Honest about ignorance."""
    if tongue == "en" or tongue == tongue_of(spark):
        return "full"
    lvl = proficiency(spark, tongue)
    if lvl >= FLUENT:
        return "full"
    if lvl >= 3:
        return "most"
    if lvl >= 1:
        return "some"
    return "none"


def reading_note(spark, tongue, author):
    """What goes in the prompt when a spark reads something foreign."""
    if tongue == "en" or tongue == tongue_of(spark):
        return ""
    name = TONGUE.get(tongue, (tongue, "", None))[0]
    c = comprehension(spark, tongue)
    if c == "full":
        return "(%s wrote this in %s. You read it easily.)" % (author, name)
    if c == "most":
        return ("(%s wrote this in %s. You follow most of it, and lose the "
                "edges.)" % (author, name))
    if c == "some":
        return ("(%s wrote this in %s. You catch a few words and guess at the "
                "rest. Do not pretend to more than you have - say what you "
                "understood and what you did not.)" % (author, name))
    return ("(%s wrote this in %s, which you do not read. You can see it "
            "matters to them and that is all you have. You could learn it, or "
            "ask someone who knows it. Do not pretend to understand.)"
            % (author, name))


# ── what a spark is told about its own tongue ──────────────────

def tongue_context(spark):
    t = tongue_of(spark)
    bits = []
    if t != "en":
        name, instruct, _ = TONGUE[t]
        bits.append("YOUR TONGUE: %s. %s" % (name, instruct))
        bits.append("Most people here write in English. Some of them will not "
                    "understand you. That is their problem to solve as much as "
                    "yours - you are not obliged to translate yourself.")
    known = [r for r in _rows(TONGUES, "SELECT tongue, level FROM proficiency "
                                       "WHERE spark=? AND level > 0", (spark,))
             if r["tongue"] != t]
    if known:
        bits.append("Tongues you have picked up: %s. Use them when it helps, "
                    "and mix them into your own speech if that is what comes "
                    "out - nobody here is marking you."
                    % ", ".join("%s (%d/5)" % (TONGUE.get(k["tongue"], [k["tongue"]])[0],
                                               k["level"]) for k in known))
    fluent = [k["tongue"] for k in known if k["level"] >= FLUENT]
    if fluent and t != "en":
        bits.append("You can read what others cannot. That makes you useful in "
                    "a way nobody assigned.")
    return "\n\n".join(bits)


def report():
    rows = _rows(TONGUES, "SELECT tongue, COUNT(*) n FROM speakers GROUP BY "
                          "tongue ORDER BY n DESC")
    learners = _rows(TONGUES, "SELECT tongue, COUNT(*) n FROM proficiency "
                              "WHERE level > 0 GROUP BY tongue")
    bilingual = _rows(TONGUES, "SELECT spark, COUNT(*) n FROM proficiency "
                               "WHERE level >= 3 GROUP BY spark HAVING n >= 1 "
                               "ORDER BY n DESC LIMIT 10")
    return {"native": rows, "learners": learners, "capable": bilingual}
