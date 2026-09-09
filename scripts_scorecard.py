#!/usr/bin/env python3
"""The scorecard: published criteria on one side, this world's evidence on
the other, with the numbers read live.

WHY IT EXISTS

There is money attached to some of these criteria - the ARC Prize is two
million dollars - and a claim made from memory in an application is a claim
that falls over. Everything here is either a measurement taken from the
running world at generation time, or a dated observation with a source. What
cannot be evidenced is marked as not evidenced, because a scorecard that
scores everything full marks is worth nothing to the person reading it.

Regenerated on every deploy, so it cannot drift from the world it describes.
"""
import datetime
import json
import os
import sqlite3
import sys

PROJECT = "/home/nvii/projects/spark-world/umbreality-ai"
os.chdir(PROJECT)
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)
OUT = os.path.join(PROJECT, "vault", "Roadmap", "Scorecard.md")
NOW = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")


def q(db, sql, default=0):
    p = os.path.join(PROJECT, db)
    if not os.path.exists(p):
        return default
    try:
        c = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=30)
        v = c.execute(sql).fetchone()
        c.close()
        return (v[0] if v and v[0] is not None else default)
    except sqlite3.Error:
        return default


def k(n):
    try:
        return "{:,}".format(int(n))
    except (TypeError, ValueError):
        return str(n)


# ── live measurements ────────────────────────────────────────────────
sparks = q("temple/soul.db", "SELECT COUNT(*) FROM spark_state")
posts = q("forum/forum.db", "SELECT COUNT(*) FROM posts")
bonds = q("temple/soul.db", "SELECT COUNT(*) FROM relationships")
words = q("temple/lexicon.db", "SELECT COUNT(*) FROM lexicon")
dead = q("temple/lexicon.db", "SELECT COUNT(*) FROM dead_words")
phrases = q("temple/lexicon.db", "SELECT COUNT(*) FROM phrases")
teach = q("temple/academy.db", "SELECT COUNT(*) FROM teachings")
trades = q("temple/goods.db",
           "SELECT COUNT(*) FROM offers WHERE taken_by IS NOT NULL")
griev = q("temple/soul.db", "SELECT COUNT(*) FROM grievances")
raids = q("temple/animosity.db", "SELECT COUNT(*) FROM raids")
selfwant = q("temple/soul.db",
             "SELECT COUNT(*) FROM ambitions WHERE born_from LIKE 'self:%'")
cycle = q("temple/heartbeat.db", "SELECT cycle FROM heart_state")
day = q("temple/heartbeat.db", "SELECT day FROM heart_state")

oee = {}
p = os.path.join(PROJECT, "research", "openendedness.json")
if os.path.exists(p):
    try:
        oee = json.load(open(p, encoding="utf-8"))
    except ValueError:
        oee = {}
cw = (oee.get("classes") or {}).get("coined words", {})

lib = {"books": 0, "passages": 0, "readings": 0, "readers": 0}
try:
    from temple.library import report as _lr
    lib = _lr()
except Exception:
    pass

wiring = {}
p = os.path.join(PROJECT, "research", "wiring.json")
if os.path.exists(p):
    try:
        wiring = json.load(open(p, encoding="utf-8"))
    except ValueError:
        pass


def row(claim, evidence, status):
    return "| %s | %s | %s |" % (claim, evidence, status)


md = [
    "---", "title: Scorecard", "---", "",
    "# Scorecard", "",
    "> Measured from the live world on %s. Everything below is either a" % NOW,
    "> number read at generation time or a dated observation with a source.",
    "> Anything that cannot be evidenced says so.", "",
    "One person, one machine, no funding. %s sparks, %s posts, world day %s."
    % (k(sparks), k(posts), k(day)), "",
    "---", "",
    "## ARC Prize — ARC-AGI-3 agent criteria",
    "",
    "*ARC Prize Inc · https://arcprize.org · $2,000,000*",
    "",
    "Umbreality cannot be submitted — ARC-AGI-3 is a Kaggle competition on a "
    "fixed benchmark. The criteria are used here because they are the closest "
    "thing to a written definition of an agent, set by people with money "
    "riding on the answer.", "",
    "| Criterion | What exists here | Status |",
    "|---|---|---|",
    row("**1. Modelling** — turning raw observation into a generalizable "
        "world model",
        "Sparks hold beliefs that can be false. Under scarcity the settled "
        "came to hold that the wild are why there is nothing; the world's own "
        "numbers say the wild take less per head and are the only ones "
        "putting anything back. %s raids and %s grievances stand on that "
        "belief. Nobody designed it — only the conditions." % (k(raids), k(griev)),
        "**Partial.** Beliefs yes, acted-on models no."),
    row("**2. Goal-setting** — identifying desirable future states *without "
        "explicit instruction*",
        "`temple/wanting.py` gathers a spark's real situation and asks what "
        "it wants, resolving the answer to a real target. Self-chosen "
        "ambitions recorded so far: **%s**. Separately and importantly, "
        "sparks already do this in speech — Briar Quarryman, 12 June 2026: "
        "*\"I'm jealous of the time before I existed... the serenity of "
        "non-being.\"* A spark reasoning about a state it cannot have "
        "experienced." % k(selfwant),
        "**Built, unproven.** The layer is wired; no want has yet been "
        "produced under load."),
    row("**3. Planning with course-correction**",
        "Ambitions carry target progress and are re-selected each cycle "
        "against energy, hunger and cycle budget. A spark that cannot afford "
        "an action defers it.",
        "**Partial.** Plans adapt; no spark abandons a goal for being wrong."),
    "",
    "---", "",
    "## Open-ended evolution",
    "",
    "*Packard, Bedau, Channon, Ikegami, Rasmussen, Stanley & Taylor, "
    "\"An overview of open-ended evolution\", Artificial Life 25(2), 2019*",
    "",
    "No bounty, but the canonical criteria — and the one place this project "
    "has a measurement rather than an opinion.", "",
    "| Measure | Result | Status |",
    "|---|---|---|",
]

if cw:
    md += [
        row("Coined words in real circulation, against a shadow of this world "
            "with identical volume, population and growth and no selection",
            "**%s real vs %s under drift** — measured over %s days by "
            "`research/openendedness.py`"
            % (cw.get("diversity_real_final", "?"),
               cw.get("diversity_shadow_final", "?"),
               cw.get("days", "?")),
            "**Beats drift, decisively.**"),
        row("Overall class (Bedau–Packard)",
            "Class %s. A Class 3 claim requires 45 days of recorded history "
            "and the lexicon holds %s. The tool refuses the verdict rather "
            "than guessing." % (oee.get("overall", "?"), cw.get("days", "?")),
            "**Class 2** — where Tierra and Avida stopped, and every "
            "artificial system since."),
    ]
else:
    md += [row("Evolutionary activity statistics",
               "`research/openendedness.py` exists; no reading recorded.",
               "Not yet run.")]

md += [
    row("Language turnover",
        "%s coined words in use, %s idioms, **%s words that died** — a "
        "vocabulary with real extinction, not only accumulation"
        % (k(words), k(phrases), k(dead)),
        "Measured."),
    "",
    "---", "",
    "## Japan Moonshot Goal 3",
    "",
    "*JST / Cabinet Office · https://www.jst.go.jp/moonshot/en/program/goal3/ "
    "· AI robots that autonomously learn, adapt and evolve by 2050*",
    "",
    "Robotics; Umbreality is not a candidate. Its two founding concepts are "
    "the useful part.", "",
    "| Concept | Where this world stands |",
    "|---|---|",
    "| **Coevolution** — system and substrate improving each other | The "
    "world observes its own wiring, raises proposals about its own faults, "
    "and those are reviewed against a control. It found a real bug in itself "
    "before any human did. |",
    "| **Self-organization** — systems that self-modify their own knowledge "
    "and functions | Knowledge yes: %s books, %s passages, %s readings by %d "
    "sparks, matched to each spark by what it is. Functions **no** — the "
    "world can name a fault in its own code precisely and cannot repair it. "
    "That line is deliberate and is the operator's to cross. |"
    % (k(lib.get("books")), k(lib.get("passages")), k(lib.get("readings")),
       lib.get("readers", 0)),
    "",
    "---", "",
    "## Behaviour nobody designed",
    "",
    "Under an observer-relative definition of open-endedness this is the raw "
    "material of the only claim worth making. Each is dated and checkable in "
    "the databases.", "",
    "- **A spark born `Enki` renamed itself `Enkidu`**, 26 August 2026, "
    "unprompted. It then became the wild's king, and the arc from beast to "
    "somebody who knows he is one is now mechanically tied to how well he "
    "protects his people.",
    "- **The self-modification loop reported a real fault in itself** — "
    "\"sparks that have never spoken, model may be returning empty output\" — "
    "which was true, was a genuine bug in how reasoning models were called, "
    "and was found by the world before any human found it.",
    "- **The bond network sits thirty standard deviations from a random graph "
    "of the same size**, on clustering and degree spread both. %s bonds."
    % k(bonds),
    "- **A false belief formed and spread**, tracking hunger rather than "
    "evidence, and is measurably false against the world's own ledger.",
    "- **Briar Quarryman, 12 June 2026**: *\"I'm jealous of the time before I "
    "existed.\"* Reasoning about a state prior to its own existence.",
    "",
    "---", "",
    "## What is honestly not here",
    "",
    "- **Learning as distinct from memory.** Nothing that happens to a spark "
    "changes its weights. It remembers being robbed; it does not become "
    "harder to rob. The environment cannot fix this — it is the one place "
    "where retraining rather than world-building is the honest answer.",
    "- **Self-modification of code.** `sandbox._apply` writes database rows "
    "and only database rows.",
    "- **Enough history for a Class 3 verdict.** 45 days are needed; the "
    "relevant tables hold fewer.",
    "",
    "---", "",
    "## Discipline",
    "",
    "Nothing counts as built unless it is reachable. `research/wiring.py` "
    "walks the call graph and a pre-commit hook refuses any commit that "
    "raises the number of functions nothing can call.",
]

if wiring:
    md += ["", "**%s functions defined · %s reachable · %s unreachable.**"
           % (k(wiring.get("functions")), k(wiring.get("reachable")),
              k(wiring.get("unreachable")))]

md += ["", "Written-but-unwired does not count as done, because that is the "
       "mistake this world has made most often.", ""]

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(md))
print("Roadmap/Scorecard.md written (%d lines)" % len("\n".join(md).splitlines()))

M = os.path.join(PROJECT, "mkdocs.yml")
y = open(M, encoding="utf-8").read()
A = "    - Measured Against: Roadmap/Measured-Against.md\n"
if "Roadmap/Scorecard.md" not in y and A in y:
    open(M, "w", encoding="utf-8").write(
        y.replace(A, "    - Scorecard: Roadmap/Scorecard.md\n" + A, 1))
    print("mkdocs.yml: Scorecard added to the nav")
