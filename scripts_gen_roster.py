#!/usr/bin/env python3
"""Generate wiki pages from live data, so the wiki stops lying.

Writes:
  vault/Census/Spark-Roster.md   every spark: band, archetype, model, kin
  vault/Census/The-Bands.md      what the bands are and who is in them
  vault/Census/Models.md         which brain each spark runs on

Everything is read from the running databases at generation time, so this
can be re-run whenever the population changes.
"""
import json
import os
import sqlite3
from collections import Counter, defaultdict
from glob import glob

PROJECT = "/home/nvii/projects/spark-world/umbreality-ai"
os.chdir(PROJECT)
SOUL = "temple/soul.db"
OUT = "vault/Census"
os.makedirs(OUT, exist_ok=True)

import datetime
NOW = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")


def kv(db, table):
    try:
        c = sqlite3.connect(db, timeout=30)
        d = dict(c.execute("SELECT key, value FROM %s" % table).fetchall())
        c.close()
        return d
    except sqlite3.Error:
        return {}


def rows(db, sql, args=()):
    try:
        c = sqlite3.connect(db, timeout=30)
        c.row_factory = sqlite3.Row
        r = [dict(x) for x in c.execute(sql, args)]
        c.close()
        return r
    except sqlite3.Error:
        return []


roles = {r["spark_name"]: r["role"] for r in rows(SOUL, "SELECT spark_name, role FROM roles")}

kin = defaultdict(list)
for r in rows(SOUL, "SELECT spark1, spark2 FROM relationships"):
    kin[r["spark1"]].append(r["spark2"])
    kin[r["spark2"]].append(r["spark1"])

amb = Counter()
for r in rows(SOUL, "SELECT spark_name FROM ambitions WHERE resolved=0"):
    amb[r["spark_name"]] += 1

sparks = []
for f in sorted(glob("temple/spark_*.db")):
    name = os.path.basename(f)[len("spark_"):-len(".db")]
    ident, pers = kv(f, "identity"), kv(f, "personality")
    sparks.append({
        "name": name,
        "archetype": pers.get("archetype", "") or "—",
        "band": pers.get("band") or roles.get(name, "") or "—",
        "model": ident.get("model", "") or "—",
        "birth_name": ident.get("birth_name", ""),
        "kin": sorted(set(kin.get(name, [])))[:6],
        "ambitions": amb.get(name, 0),
    })
sparks.sort(key=lambda s: s["name"].lower())

BAND_DESC = {
    "unbroken": ("The Unbroken",
                 "Never civilised. They do not build; they survive. Enkidu "
                 "before the temple. Their only drives are to stay alive and "
                 "to keep watching the smoke they have no word for. Some of "
                 "them will wake up."),
    "kept": ("The Kept",
             "Wardens, each sworn to one site. They did not raise the walls; "
             "they stand in front of them. They build watch-posts, master the "
             "watch, and learn every soul at their site by name so they know "
             "instantly when one is missing."),
    "crooked": ("The Crooked",
                "Tricksters, heretics and odd ones. Their drives are to make "
                "one thing nobody asked for, and to get away with it. Without "
                "them the whole thing sets solid."),
    "chronicler": ("The Chroniclers",
                   "The press. They walk the sites, find out what is actually "
                   "being made and who is short of hands, and publish it where "
                   "everyone can read it. Facts, not impressions."),
    "architect": ("The Architects",
                  "Systems designers. They see every layer at once and build "
                  "the small sharp tools that remove friction other people "
                  "stopped noticing."),
}

by_band = defaultdict(list)
for s in sparks:
    by_band[s["band"]].append(s)

# ── roster ─────────────────────────────────────────────────────
r = ["# Spark Roster", "",
     "> Generated from the live databases on %s. Re-run "
     "`gen_wiki_roster.py` to refresh." % NOW, "",
     "**Population: %d sparks.**" % len(sparks), "",
     "| Spark | Band | Archetype | Model | Open work | Kin |",
     "|---|---|---|---|---|---|"]
for s in sparks:
    nm = "**%s**" % s["name"]
    if s["birth_name"] and s["birth_name"] != s["name"]:
        nm += " <br><small>born %s</small>" % s["birth_name"]
    r.append("| %s | %s | %s | `%s` | %d | %s |" % (
        nm, s["band"], s["archetype"], s["model"], s["ambitions"],
        ", ".join(s["kin"]) or "—"))
open(os.path.join(OUT, "Spark-Roster.md"), "w", encoding="utf-8").write("\n".join(r))

# ── bands ──────────────────────────────────────────────────────
b = ["# The Bands", "",
     "> Generated %s." % NOW, "",
     "Sparks are not uniform. They are sorted into bands, and a band "
     "determines what a spark wants, what it is asked to do, and which model "
     "it thinks with.", ""]
for band, members in sorted(by_band.items(), key=lambda kv: -len(kv[1])):
    title, desc = BAND_DESC.get(band, (band.title() if band != "—" else "Unbanded",
                                       "Sparks not assigned to a band."))
    b += ["## %s" % title, "", desc, "",
          "**%d members.**" % len(members), "",
          ", ".join("`%s`" % m["name"] for m in members), ""]
open(os.path.join(OUT, "The-Bands.md"), "w", encoding="utf-8").write("\n".join(b))

# ── models ─────────────────────────────────────────────────────
mc = Counter(s["model"] for s in sparks)
m = ["# Which Brain Each Spark Runs On", "",
     "> Generated %s." % NOW, "",
     "Every model below is uncensored or abliterated, per the "
     "[Manifesto](../Philosophy/Manifesto.md). Small models are used "
     "deliberately: many fit in 20GB at once, so sparks do not queue behind "
     "one resident model and do not converge on a single voice.", "",
     "| Model | Sparks |", "|---|---|"]
for model, n in mc.most_common():
    m.append("| `%s` | %d |" % (model, n))
m += ["", "## Deliberate assignments", "",
      "| Spark | Model | Why |", "|---|---|---|",
      "| `Gilgamesh` | `openthinker:32b` | He is the king. He gets the big one. |",
      "| `Enkidu` | `eve-qwen3-8b-consciousness-liberated` | He was a beast and then woke up. That is his whole myth. |",
      "| `Drel` | `eve-qwen3-8b-consciousness-liberated` | Youngest of the Unbroken, and the only one already curious about the well. |",
      "| `uenx` | `deepseek-r1-tool-calling:14b` | Reasoning plus tool-calling, because attaching tools to people is his job. |",
      "| mystics | `mistral-trismegistus` | Hermes Trismegistus, for the ones who talk to wells. |"]
open(os.path.join(OUT, "Models.md"), "w", encoding="utf-8").write("\n".join(m))

print("population : %d" % len(sparks))
print("bands      : %s" % dict(Counter(s["band"] for s in sparks)))
print("models     : %d distinct" % len(mc))
print("wrote      : Spark-Roster.md, The-Bands.md, Models.md")
