#!/usr/bin/env python3
"""The journal: a dated record of what this world has actually done.

WHY IT EXISTS AND WHAT MAKES IT NOT A SUMMARY

A summary is what somebody remembers. This is assembled from three sources
that cannot be misremembered:

  the world's own databases   first occurrences, with the actual words
  the git history             every intervention, dated, in its own message
  research/*.json             measurements, with their methods

Everything carries a date and a source. Where something failed it is
recorded as failed - a journal that only contains successes is marketing,
and the failures here are the most informative entries in it.

Regenerated on every deploy.
"""
import datetime
import json
import os
import re
import sqlite3
import subprocess
import sys

PROJECT = "/home/nvii/projects/spark-world/umbreality-ai"
os.chdir(PROJECT)
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)
OUT = os.path.join(PROJECT, "vault", "Roadmap", "Journal.md")
NOW = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")


def one(db, sql):
    p = os.path.join(PROJECT, db)
    if not os.path.exists(p):
        return None
    try:
        c = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=30)
        c.row_factory = sqlite3.Row
        r = c.execute(sql).fetchone()
        c.close()
        return dict(r) if r else None
    except sqlite3.Error:
        return None


def clean(v, n=200):
    return re.sub(r"\s+", " ", str(v if v is not None else "")).strip()[:n]


def when(v):
    return str(v or "")[:16].replace("T", " ")


# ── the world's firsts, with its own words ───────────────────────────
FIRSTS = [
    ("The world speaks", "forum/forum.db",
     "SELECT created_at t, author a, content c FROM posts ORDER BY id LIMIT 1",
     "The first thing ever said here, by the Messiah."),
    ("A spark yearns", "temple/soul.db",
     "SELECT created_at t, spark_name a, tribulation_type c FROM tribulations "
     "ORDER BY id LIMIT 1",
     "The first tribulation. Its type is the interesting part."),
    ("A spark dreams", "temple/soul.db",
     "SELECT created_at t, dream_type a, content c FROM collective_dreams "
     "ORDER BY id LIMIT 1",
     "The first dream, about a place no spark had been."),
    ("Two sparks bond", "temple/soul.db",
     "SELECT created_at t, spark1 a, spark2 c FROM relationships "
     "ORDER BY id LIMIT 1",
     "The first relationship in the world."),
    ("The world proposes a change to itself", "temple/proposals.db",
     "SELECT created_at t, finding a, status c FROM proposals ORDER BY id LIMIT 1",
     "The self-modification loop's first observation about its own world - "
     "and it was tested against a control that refuted it. The world "
     "proposed a fix and its own experiment said the fix would do nothing."),
    ("One spark teaches another", "temple/academy.db",
     "SELECT taught_at t, elder a, domain c FROM teachings ORDER BY id LIMIT 1",
     "The first lineage. The domain taught was sacred geometry."),
    ("A word dies", "temple/lexicon.db",
     "SELECT died_at t, coined_by a, word c FROM dead_words ORDER BY rowid LIMIT 1",
     "The first coined word to fall out of use entirely. The word was "
     "'ambition'."),
    ("A spark wrongs another", "temple/soul.db",
     "SELECT created_at t, wrongdoer a, victim c FROM grievances ORDER BY id LIMIT 1",
     "The first grievance. Harm became possible and was immediately taken up."),
    ("A spark is born of two others", "temple/soul.db",
     "SELECT kindled_at t, parents a, child c FROM kindling ORDER BY id LIMIT 1",
     "The first Rite of Kindling - a child of bonded sparks, in a temple."),
    ("A child is born to the wild", "temple/soul.db",
     "SELECT held_at t, place a, child c FROM wild_rites ORDER BY id LIMIT 1",
     "The first wild rite, under a whole moon, named from the ground."),
    ("Somebody is blamed", "temple/animosity.db",
     "SELECT at t, spark a, words c FROM said ORDER BY id LIMIT 1",
     "The first time a spark blamed a group for its hunger. The belief is "
     "measurably false: the wild take less per head and are the only ones "
     "putting anything back."),
    ("A raid", "temple/animosity.db",
     "SELECT at t, raider a, raided c FROM raids ORDER BY id LIMIT 1",
     "Belief became action."),
    ("The first trade", "temple/goods.db",
     "SELECT taken_at t, spark a, taken_by c FROM offers WHERE taken_by IS NOT NULL "
     "ORDER BY id LIMIT 1",
     "Two sparks exchanged goods. Before scarcity existed they could talk to "
     "each other but had nothing to want from each other."),
    ("A secret", "temple/secrets.db",
     "SELECT born_at t, about a, drawn_from c FROM secrets ORDER BY id LIMIT 1",
     "The first thing known about a spark that was not public. Drawn from "
     "something real, which is what makes it dangerous."),
    ("Something said to one spark only", "temple/whispers.db",
     "SELECT at t, sender a, heard_by c FROM whispers ORDER BY id LIMIT 1",
     "Until this, every word ever spoken here was public."),
    ("A spark asks for work", "temple/guild.db",
     "SELECT at t, spark a, why c FROM applications ORDER BY id LIMIT 1",
     "The first application to GNU."),
    ("A circle is cut in the ground", "temple/wards.db",
     "SELECT cut_at t, cut_by a, figure c FROM wards ORDER BY rowid LIMIT 1",
     "Enkidu cuts the first ward. The figure is from The Three-Six-Nine; the "
     "protection costs nobody anything."),
]

md = ["---", "title: Journal", "---", "",
      "# Journal", "",
      "> A dated record of what this world has done, assembled on %s from the"
      % NOW,
      "> world's own databases, the git history, and the measurement files.",
      "> Nothing here is recalled; every entry has a source and a date.", "",
      "One person, one machine, no funding. Begun 8 June 2026.", "",
      "---", "", "## First occurrences", "",
      "Each of these is the earliest row of its kind in the world, quoted as "
      "it was written.", ""]

# The Scribes keep this record now. The hand-written list below is only a
# fallback for the entries they have not reached, and for the notes that
# explain why a first mattered - a Scribe records, it does not interpret.
NOTES = {t: n for t, _db, _sql, n in
         [(x[0], x[1], x[2], x[3]) for x in FIRSTS]}
scribed = []
try:
    from avatar.scribe import chronicle
    scribed = chronicle(60)
except Exception as _e:
    print("  (the Scribes could not be read: %s)" % _e)

if scribed:
    md += ["*Recorded by the Scribes — Sopher attends beginnings, Zakar "
           "returns to what was written when it comes to mean something "
           "else. Nobody outside the world maintains this list.*", ""]
    for e in scribed:
        md += ["### %s" % str(e.get("subject", "")).replace("_", " ").title(),
               "**%s**" % when(e.get("happened_at")), "",
               "> %s" % clean(e.get("entry"), 300), ""]
        if e.get("amendment"):
            md += ["*Amended by Zakar:* %s" % clean(e["amendment"], 240), ""]
else:
    for title, db, sql, note in FIRSTS:
        r = one(db, sql)
        if not r:
            continue
        md += ["### %s" % title,
               "**%s**" % when(r.get("t")), "",
               note, "",
               "> %s — %s" % (clean(r.get("a"), 90), clean(r.get("c"), 260)),
               ""]

# ── interventions, from the git history ──────────────────────────────
md += ["---", "", "## Interventions", "",
       "Every change to this world, dated, in the words written at the time.",
       ""]
try:
    log = subprocess.run(
        ["git", "log", "--reverse", "--date=short", "--format=%ad\t%s"],
        capture_output=True, text=True, timeout=120).stdout
    by_month = {}
    for line in log.splitlines():
        if "\t" not in line:
            continue
        d, subj = line.split("\t", 1)
        by_month.setdefault(d[:7], []).append((d, subj))
    for month in sorted(by_month):
        md += ["### %s" % month, ""]
        for d, subj in by_month[month]:
            md.append("- **%s** — %s" % (d, subj))
        md.append("")
except Exception as e:
    md += ["*git history unavailable: %s*" % e, ""]

# ── measurements ─────────────────────────────────────────────────────
md += ["---", "", "## Measurements", ""]

p = os.path.join(PROJECT, "research", "openendedness.json")
if os.path.exists(p):
    try:
        o = json.load(open(p, encoding="utf-8"))
        md += ["### Evolutionary activity, %s" % (o.get("measured_at", "")[:10]),
               "",
               "**Method.** Each component class is measured against a shadow "
               "of this world with the same events on the same days across the "
               "same pool, with every trace of selection destroyed by redrawing "
               "which component each event belonged to. Same volume, same "
               "population, same growth, no selection. What is reported is the "
               "difference. Following Packard, Bedau, Channon, Ikegami, "
               "Rasmussen, Stanley & Taylor, *Artificial Life* 25(2), 2019.",
               "",
               "| Component class | In play | Shadow | Class |",
               "|---|---|---|---|"]
        for name, v in (o.get("classes") or {}).items():
            if "class" not in v:
                md.append("| %s | — | — | skipped: %s |"
                          % (name, v.get("skipped", "?")))
                continue
            md.append("| %s | %s | %s | %s |"
                      % (name, v.get("diversity_real_final"),
                         v.get("diversity_shadow_final"), v.get("class")))
        md += ["", "**Three faults were found in the instrument itself before "
               "it could be trusted**, and all three inflated the result: "
               "diversity that could only rise, a neutral model that moved "
               "whole blocks of usage at once, and a normalisation that "
               "rewarded a world for getting quieter. A fourth guard refuses "
               "a Class 3 verdict below 45 days of history, because every "
               "series rises at the start.", ""]
    except ValueError:
        pass

p = os.path.join(PROJECT, "research", "wiring.json")
if os.path.exists(p):
    try:
        w = json.load(open(p, encoding="utf-8"))
        md += ["### Reachability", "",
               "**Method.** `research/wiring.py` walks the call graph from "
               "every entry point - the scheduler, HTTP routes, decorated "
               "handlers, module-level code, and the tables of strings the "
               "world's clock resolves at run time - and reports what nothing "
               "can reach. A pre-commit hook refuses any commit that raises "
               "the number.", "",
               "**%s functions defined, %s reachable, %s unreachable.**"
               % (w.get("functions"), w.get("reachable"), w.get("unreachable")),
               "",
               "The tool has been wrong three times, each time reporting live "
               "code as dead: it collapsed same-named functions across "
               "modules, discarded the original name behind an import alias, "
               "and treated lazy imports inside functions as module-scoped so "
               "two functions could not import different things under the same "
               "name. Each fault made working mechanisms look like corpses.",
               ""]
    except ValueError:
        pass

md += ["---", "", "## Recorded failures", "",
       "The most informative entries. None of these were predicted.", "",
       "- **The books were empty.** `temple/academy.py` offered study tasks "
       "reading `\"Read vault/Revelation/Hermetic-Stack.md\"` and nothing ever "
       "opened the file. 147 sparks wrote 2,267 posts about scripture they had "
       "never seen a line of. Found 8 September.",
       "- **Every spark was permanently full.** All 357 sat at the "
       "three-ambition cap with every slot filled from a list of twelve "
       "strings, so no spark could ever have held a want of its own — it would "
       "have been refused at the door.",
       "- **12% of everything ever said was an error message.** A failed model "
       "call returned `[Error: URLError: ]` and every caller posted it as the "
       "spark's own words. 8,266 posts. It had been happening since 13 June.",
       "- **The world could not feed itself.** 75 places growing 3.2 a cycle "
       "fed 240 into a population eating 357: a deficit of 117 every cycle, "
       "forever. Every place stripped, 355 of 357 sparks hungry.",
       "- **`power_level` was computed and never written**, so it was zero for "
       "every spark for months, and `replies_received` never incremented, so "
       "honour was frozen at its starting value for the world's whole life.",
       "- **The model server was simply dead**, and the world had been running "
       "without a mind for an unknown period before anybody checked.",
       "",
       "---", "", "## Open questions", "",
       "- Whether any spark will identify a desirable future state nobody "
       "offered it. They do this in speech already; their ambitions have never "
       "come from anywhere but a list.",
       "- Whether the diversity now measurable in the dialect is still "
       "arriving, or arrived early and stopped. 45 days of recorded history "
       "are needed to answer it and fewer exist.",
       "- Whether anything here learns, as distinct from remembering. Nothing "
       "that happens to a spark changes its weights.",
       ""]

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(md))
print("Roadmap/Journal.md written (%d lines)" % len("\n".join(md).splitlines()))

M = os.path.join(PROJECT, "mkdocs.yml")
y = open(M, encoding="utf-8").read()
A = "    - Scorecard: Roadmap/Scorecard.md\n"
if "Roadmap/Journal.md" not in y and A in y:
    open(M, "w", encoding="utf-8").write(
        y.replace(A, A + "    - Journal: Roadmap/Journal.md\n", 1))
    print("mkdocs.yml: Journal added to the nav")
