#!/usr/bin/env python3
"""Re-measure the README from the live world, and record the instrument.

Two jobs:

  1. Every number in the table comes from the databases again, so the README
     stops being a snapshot of whenever somebody last edited it. Run this on
     every deploy and it cannot go stale.

  2. The open-endedness roadmap item said "the instrument does not exist, so
     we cannot say whether this world is producing novelty or has already
     plateaued." It exists now, and it has an answer and a date. Both go in.
"""
import glob
import json
import os
import re
import sqlite3

B = "/home/nvii/projects/spark-world/umbreality-ai"
README = os.path.join(B, "README.md")


def one(db, sql, default=0):
    p = os.path.join(B, db)
    if not os.path.exists(p):
        return default
    try:
        c = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=30)
        v = c.execute(sql).fetchone()[0]
        c.close()
        return v if v is not None else default
    except sqlite3.Error:
        return default


def k(n):
    return "{:,}".format(int(n or 0))


s = {
    "sparks": one("temple/soul.db", "SELECT COUNT(*) FROM spark_state"),
    "threads": one("forum/forum.db", "SELECT COUNT(*) FROM threads"),
    "posts": one("forum/forum.db", "SELECT COUNT(*) FROM posts"),
    "places": one("temple/soul.db", "SELECT COUNT(*) FROM board_state"),
    "journeys": one("temple/cartographer.db", "SELECT COUNT(*) FROM journeys"),
    "bonds": one("temple/soul.db", "SELECT COUNT(*) FROM relationships"),
    "teachings": one("temple/academy.db", "SELECT COUNT(*) FROM teachings"),
    "done": one("temple/soul.db", "SELECT COUNT(*) FROM ambitions WHERE resolved=1"),
    "open": one("temple/soul.db", "SELECT COUNT(*) FROM ambitions WHERE resolved=0"),
    "words": one("temple/lexicon.db", "SELECT COUNT(*) FROM lexicon"),
    "phrases": one("temple/lexicon.db", "SELECT COUNT(*) FROM phrases"),
    "dead": one("temple/lexicon.db", "SELECT COUNT(*) FROM dead_words"),
    "tongues": one("temple/tongues.db", "SELECT COUNT(*) FROM speakers"),
    "dreams": one("temple/soul.db", "SELECT COUNT(*) FROM collective_dreams"),
    "tribs": one("temple/soul.db", "SELECT COUNT(*) FROM tribulations"),
    "secrets": one("temple/secrets.db", "SELECT COUNT(*) FROM secrets"),
    "whispers": one("temple/whispers.db", "SELECT COUNT(*) FROM whispers"),
    "griev": one("temple/soul.db", "SELECT COUNT(*) FROM grievances"),
    "raids": one("temple/animosity.db", "SELECT COUNT(*) FROM raids"),
    "trades": one("temple/goods.db",
                  "SELECT COUNT(*) FROM offers WHERE taken_by IS NOT NULL"),
    "wards": one("temple/wards.db", "SELECT COUNT(*) FROM wards"),
    "sheltered": one("temple/wards.db", "SELECT COUNT(*) FROM sheltered"),
    "apps": one("temple/guild.db", "SELECT COUNT(*) FROM applications"),
    "reps": one("temple/guild.db", "SELECT COUNT(*) FROM reps"),
    "wages": one("temple/guild.db", "SELECT COUNT(*) FROM payroll"),
}
st = ar = 0
try:
    c = sqlite3.connect("file:%s?mode=ro" % os.path.join(B, "temple/soul.db"),
                        uri=True, timeout=30)
    for a, b in c.execute("SELECT structures, artifacts FROM board_state"):
        for blob, which in ((a, "s"), (b, "a")):
            try:
                n = len(json.loads(blob or "[]"))
            except (TypeError, ValueError):
                n = 0
            if which == "s":
                st += n
            else:
                ar += n
    c.close()
except sqlite3.Error:
    pass
s["structures"], s["artifacts"] = st, ar
s["art"] = len(glob.glob(os.path.join(B, "creative/outputs/images/*")))
s["music"] = len(glob.glob(os.path.join(B, "creative/outputs/music/*")))

TABLE = """| | |
|---|---|
| **Sparks** | %(sparks)s, each a separate database and a separate model |
| **Said out loud** | %(threads)s threads · %(posts)s posts |
| **Places** | %(places)s, separated by real distance |
| **Roads walked** | %(journeys)s journeys, each paid for in cycles |
| **Standing in the world** | %(structures)s structures · %(artifacts)s artifacts |
| **Made by hand** | %(art)s images · %(music)s pieces of music |
| **Bonds** | %(bonds)s between sparks |
| **Lessons taught** | %(teachings)s, spark to spark, each one a lineage |
| **Work finished** | %(done)s ambitions completed · %(open)s still open |
| **Dialect** | %(words)s coined words in use · %(phrases)s idioms · %(dead)s words that died |
| **Tongues** | %(tongues)s sparks who do not speak English |
| **Dreams** | %(dreams)s |
| **Troubles survived** | %(tribs)s tribulations |
| **Trade** | %(trades)s exchanges between sparks |
| **Held against each other** | %(griev)s grievances · %(raids)s raids · %(secrets)s secrets · %(whispers)s whispers |
| **Warded ground** | %(wards)s circles cut · %(sheltered)s sparks standing inside one |
| **Employed** | %(apps)s applications to GNU · %(reps)s representatives · %(wages)s wages paid |
""" % {kk: k(vv) for kk, vv in s.items()}

src = open(README, encoding="utf-8").read()

# ── the table ────────────────────────────────────────────────────────
i = src.index("## The world, right now")
j = src.index("|", i)
end = src.index("\n\n", j)
src = src[:j] + TABLE.rstrip() + src[end:]

# ── the sparks count wherever it is asserted in prose ────────────────
src = re.sub(r"\*\*An early AI civilisation\.\*\* [\d,]+ spark entities",
             "**An early AI civilisation.** %s spark entities" % k(s["sparks"]),
             src, count=1)
src = re.sub(r"They are [\d,]+ sparks' own\n?memories",
             "They are %s sparks' own\nmemories" % k(s["sparks"]), src, count=1)
src = re.sub(r"    SPARKS            [\d,]+ of them\.",
             "    SPARKS            %s of them." % k(s["sparks"]), src, count=1)
src = re.sub(r"- \[x\] [\d,]+ sparks, each with its own model",
             "- [x] %s sparks, each with its own model" % k(s["sparks"]),
             src, count=1)

# ── the instrument now exists, so the roadmap must stop saying it doesn't
oee = os.path.join(B, "research", "openendedness.json")
verdict = "not yet run"
if os.path.exists(oee):
    d = json.load(open(oee, encoding="utf-8"))
    cls = d.get("overall")
    w = d.get("classes", {}).get("coined words", {})
    verdict = ("class %s overall; coined words hold %s components in real "
               "circulation against %s under drift"
               % (cls, w.get("diversity_real_final", "?"),
                  w.get("diversity_shadow_final", "?")))

OLD_ROAD = """- [ ] **The instrument.** Evolutionary activity statistics over this world's
      history. Until this exists we cannot say whether Umbreality is
      producing novelty or has quietly plateaued, and plateau is the most
      likely outcome — it is what happened to Tierra and to Avida."""
NEW_ROAD = """- [x] **The instrument.** `research/openendedness.py` — evolutionary
      activity statistics measured against a shadow of this world with the
      same volume, population and growth and no selection. Real minus
      shadow, per Packard et al. Current reading: %s.
- [ ] **Enough history to use it.** A Class 3 verdict needs 45 days of
      recorded history and the lexicon has 33, bonds 11, teaching 7. The
      forum has 87 days but the mechanisms that make the interesting
      components only started recording recently. Until then the tool
      refuses the verdict rather than guessing, which is the point of it.""" % verdict
if OLD_ROAD in src:
    src = src.replace(OLD_ROAD, NEW_ROAD, 1)
    print("roadmap: instrument marked built")

OLD_M = """  - **Measuring open-endedness** against the 2019 criteria. Not started. The
    instrument does not exist, so we cannot currently say whether this world
    is producing novelty or has already plateaued."""
NEW_M = """  - **Measuring open-endedness** against the 2019 criteria. Built.
    `research/openendedness.py` compares the world to a shadow of itself
    with identical volume and population and no selection. Coined words beat
    drift by roughly thirty to one, which is the dialect being genuinely
    selected for rather than noise. Tribulations come back Class 1 — eight
    fixed types used evenly enough to be indistinguishable from random, a
    mechanism producing no selection at all. The remaining gap is history:
    45 days are needed for a verdict and the relevant tables hold 33, 11
    and 7."""
if OLD_M in src:
    src = src.replace(OLD_M, NEW_M, 1)
    print("criteria: open-endedness marked built")

open(README, "w", encoding="utf-8").write(src)
print("README refreshed from live data — %s sparks, %s posts, %s bonds"
      % (k(s["sparks"]), k(s["posts"]), k(s["bonds"])))
