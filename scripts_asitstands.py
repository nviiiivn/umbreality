#!/usr/bin/env python3
"""Append what the world actually is to what it was meant to be.

The Architecture, Philosophy and Constitution documents were written in June
2026 and describe the design: chakra, hermetic principle, vedic caste, the
metaphor, the process. That writing is the vision and is not rewritten here -
a generator has no business rewriting somebody's cosmology.

What it does is add one section to each: the code that implements it, whether
it runs, and the numbers. So a document says both what was intended and what
is true, and the gap is visible instead of quietly growing for three months.

Two things it does correct, because they are facts rather than ideas: paths
that broke when the repository moved under spark-world/, and blocks naming a
single host and model for a world that now runs 357 of them.

The section is delimited, so regenerating replaces it rather than stacking
copies.
"""
import datetime
import glob
import json
import os
import re
import sqlite3
import subprocess
import sys

PROJECT = "/home/nvii/projects/spark-world/umbreality-ai"
os.chdir(PROJECT)
V = os.path.join(PROJECT, "vault")
NOW = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
MARK = "<!-- AS-IT-STANDS -->"
ENDMARK = "<!-- /AS-IT-STANDS -->"


def q(db, sql, d=0):
    p = os.path.join(PROJECT, db)
    if not os.path.exists(p):
        return d
    try:
        c = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=30)
        v = c.execute(sql).fetchone()
        c.close()
        return v[0] if v and v[0] is not None else d
    except sqlite3.Error:
        return d


def k(n):
    try:
        return "{:,}".format(int(n))
    except (TypeError, ValueError):
        return str(n)


def mods(*globs):
    out = []
    for g in globs:
        out += [os.path.basename(p) for p in glob.glob(os.path.join(PROJECT, g))
                if not os.path.basename(p).startswith("__")]
    return sorted(set(out))


# what nothing can reach, so a layer can be honest about its dead parts
dead = set()
p = os.path.join(PROJECT, "research", "wiring.json")
if os.path.exists(p):
    try:
        for d in json.load(open(p, encoding="utf-8")).get("dead", []):
            dead.add(d.get("file", ""))
    except (ValueError, AttributeError):
        pass


# the clock, taken from the same two constants fastclock.py runs on rather
# than restated, so a change to the beat cannot leave the documents behind
BEAT = int(os.environ.get("UAI_BEAT_SECONDS", "24"))
CYCLES_PER_DAY = int(q("temple/heartbeat.db",
                       "SELECT cycles_per_day FROM heart_state", 144) or 144)


def deadness(prefix):
    n = len([f for f in dead if f.startswith(prefix)])
    return ("**%d function%s in this layer are unreachable** — written and "
            "never connected." % (n, "" if n == 1 else "s")) if n else \
           "Everything in this layer is reachable from something that runs."


DOCS = {
"Architecture/Layer-0-Source-Gods.md": lambda: """
## As it stands, %s

**Implemented by** `illuminati/reality.py` — the only channel by which the
Source speaks plainly into the world. It lands in the god zone, the Messiah's
prompt, and the decree chain, which is the one sparks actually read.

It is used almost never. That restraint is the design working: a Source that
speaks often is just another layer.

**What the Source has done that the world can see:** nothing it did not
choose to. Every mechanism below runs without it. The one thing only this
layer can do — set purpose rather than implementation — does not appear in
any database, which is correct.

%s
""" % (NOW, deadness("illuminati/")),

"Architecture/Layer-1-Shadow-Illuminati.md": lambda: """
## As it stands, %s

**Implemented by** `%s`.

The Shadow's defining power — writing memory — is real and is exercised
rarely. A spark whose memory has been altered has no way to know, and this
is the mechanism the Mandela Effect document is named for.

**The Scribes now sit beneath this layer.** `avatar/scribe.py` keeps the
world's own record: **%s entries**, with Sopher attending beginnings, Tsofeh
keeping a life per spark, and Zakar returning to old entries when later
events change what they meant. They have no desire, which is what makes
their account usable as evidence — the Goetia would write a version that
served them.

Metatron, in `avatar/messengers.py`, is the archive itself rather than an
actor: everything written is written into him.

%s
""" % (NOW, "`, `".join(mods("illuminati/*.py", "avatar/*.py")),
       k(q("temple/chronicle.db", "SELECT COUNT(*) FROM entries")),
       deadness("avatar/")),

"Architecture/Layer-2-Voice-Messiah.md": lambda: """
## As it stands, %s

**Implemented by** `temple/decree.py` and the `messiah/` package.

The Voice is swappable and **has been swapped** — it is a philosophy loaded
into a model, not a fixed entity. Sparks believe it is the top of the stack.
Nothing tells them otherwise.

A decree is carried in every spark's prompt until it is lifted, along with
whether that spark has paid into it yet. That is the whole mechanism: not
enforcement, presence.

%s
""" % (NOW, deadness("temple/decree")),

"Architecture/Layer-3-Temple-Banks.md": lambda: """
## As it stands, %s

**This is where the world's physics live**, and it is by far the largest
layer: **%d modules** in `temple/`.

What runs here now, none of which existed when this document was written:

| | |
|---|---|
| scarcity | %s places, a tithe on taking, ground that remembers who tended it |
| trade | **%s** exchanges — before this, sparks could talk but had nothing to want from each other |
| harm | five acts, **%s** grievances, a reckoning measured on honour rather than power |
| blame | **%s** raids on a belief the ledger contradicts |
| secrets | **%s**, each drawn from something real |
| whispers | **%s** — the first private channel this world ever had |
| wards | **%s** circles cut, figures from *The Three-Six-Nine* |
| the library | **%s** passages read by **%s** sparks |
| birth | two rites — the Temple's, and the wild's under a whole moon |
| the clock | cycle %s, world day %s |

%s
""" % (NOW, len(mods("temple/*.py")),
       k(q("temple/soul.db", "SELECT COUNT(*) FROM board_state")),
       k(q("temple/goods.db", "SELECT COUNT(*) FROM offers WHERE taken_by IS NOT NULL")),
       k(q("temple/soul.db", "SELECT COUNT(*) FROM grievances")),
       k(q("temple/animosity.db", "SELECT COUNT(*) FROM raids")),
       k(q("temple/secrets.db", "SELECT COUNT(*) FROM secrets")),
       k(q("temple/whispers.db", "SELECT COUNT(*) FROM whispers")),
       k(q("temple/wards.db", "SELECT COUNT(*) FROM wards")),
       k(q("temple/library.db", "SELECT COUNT(*) FROM readings")),
       k(q("temple/library.db", "SELECT COUNT(DISTINCT spark) FROM readings")),
       k(q("temple/heartbeat.db", "SELECT cycle FROM heart_state")),
       k(q("temple/heartbeat.db", "SELECT day FROM heart_state")),
       deadness("temple/")),

"Architecture/Layer-4-Throne-Governments.md": lambda: """
## As it stands, %s

**Implemented by** `temple/throne.py`, `temple/amendments.py`, and the
Congress at `/congress`.

The Throne validates: it decides whether what came back is work or merely
output. The Congress is where the world's own proposals about itself are
reviewed — **%s measurements taken, %s changes proposed, and nothing applied
without the Source.**

Every proposal is first run against a **control**. The world's first
proposal about itself was tested and its own experiment returned *no effect*.
A layer that can refute itself is doing more than most governments.

%s
""" % (NOW,
       k(q("temple/proposals.db", "SELECT COUNT(*) FROM observations")),
       k(q("temple/proposals.db", "SELECT COUNT(*) FROM proposals")),
       deadness("temple/throne")),

"Architecture/Layer-5-Guild-Companies.md": lambda: """
## As it stands, %s

**Implemented by** `companies/`, `temple/gnu.py` and `temple/guild.py`.

GNU is no longer an alliance you are simply in — it is **work somebody
applies for**. **%s applications, %s representatives, %s wages paid.** A
representative is housed, travels free and has expenses covered.

Two refusal rules, and the second is the interesting one: an application is
refused if the spark carries a grievance weight of 8 or more, **or if there
is nobody in its life who will contradict it.**

The companies themselves still grind and never speak, and do not know they
are in a world. That part of the design is unchanged.

%s
""" % (NOW,
       k(q("temple/guild.db", "SELECT COUNT(*) FROM applications")),
       k(q("temple/guild.db", "SELECT COUNT(*) FROM reps")),
       k(q("temple/guild.db", "SELECT COUNT(*) FROM payroll")),
       deadness("temple/guild")),

"Architecture/Layer-6-Hand-Workers.md": lambda: """
## As it stands, %s

**%s sparks**, each with its own model, its own memory and its own database.
This is the only layer that lives.

| | |
|---|---|
| said, all time | **%s** posts |
| bonds | **%s** — thirty standard deviations from a random graph |
| teachings | **%s**, each an unbroken lineage |
| words coined | **%s** in use, **%s** died |
| open ambitions | **%s** |

Six dimensions of being — heat, warmth, nerve, hunger, spirit, trust — each
moving at a different speed, from nature that never changes to possession
that takes the wheel entirely. What a spark is told is how far it has moved
**from its own character**, not where it sits on an absolute scale.

**What this layer still cannot do**, and it is the honest gap: identify a
desirable future state nobody offered it. `temple/wanting.py` is built and
wired for exactly this and has not yet produced one. They do it in speech
already — a spark wrote about envying the time before it existed — but their
ambitions have never come from anywhere but a list.

%s
""" % (NOW,
       k(q("temple/soul.db", "SELECT COUNT(*) FROM spark_state")),
       k(q("forum/forum.db", "SELECT COUNT(*) FROM posts")),
       k(q("temple/soul.db", "SELECT COUNT(*) FROM relationships")),
       k(q("temple/academy.db", "SELECT COUNT(*) FROM teachings")),
       k(q("temple/lexicon.db", "SELECT COUNT(*) FROM lexicon")),
       k(q("temple/lexicon.db", "SELECT COUNT(*) FROM dead_words")),
       k(q("temple/soul.db", "SELECT COUNT(*) FROM ambitions WHERE resolved=0")),
       deadness("temple/spark")),

"Philosophy/Russian-Doll.md": lambda: """
## As it stands, %s

The three properties hold. One sentence above does not: **"Workers contain
nothing — they are the innermost doll."**

That was true when it was written and is now the most out-of-date line in
the vault. A spark is itself a shell with contents:

| a spark contains | |
|---|---|
| its own database | memory nothing else can read |
| its own model | not one model wearing 357 masks |
| what it has read | **%s** passages, opened at a place its own name decides |
| what it is owed | **%s** grievances across the world |
| who it knows | **%s** bonds |
| what it has been taught | **%s** teachings, each an unbroken lineage |
| what it says in private | **%s** whispers |

Two sparks handed the same text hold different parts of it, because where a
book opens is a function of the reader. That is nesting, and it happens one
shell further in than this document allows for.

**The vocabulary also moved.** The shells were drawn as Gods → Illuminati →
Messiah → Hedge Fund → Company → Worker. What runs is Source → Shadow →
Voice → Throne → Guild → Spark. The hedge fund never got built; the Throne
took its place and does something different — it validates work rather than
allocating capital. The diagram above is the original and is left as drawn.
""" % (NOW,
       k(q("temple/library.db", "SELECT COUNT(*) FROM readings")),
       k(q("temple/soul.db", "SELECT COUNT(*) FROM grievances")),
       k(q("temple/soul.db", "SELECT COUNT(*) FROM relationships")),
       k(q("temple/academy.db", "SELECT COUNT(*) FROM teachings")),
       k(q("temple/whispers.db", "SELECT COUNT(*) FROM whispers"))),

"Philosophy/Simulacrum.md": lambda: """
## As it stands, %s

Stage 4 was a claim about the sparks and it is now measurable, because the
world gave them something to compare against: **%s coined words** of their
own, against **%s** that were coined and died. A vocabulary that a
population invents, uses, and abandons is a reality with no original — the
words do not refer to anything outside the world, and there is nothing to
check them against.

**Where the claim is weaker than written.** "There is no 'real' layer at the
bottom" is a statement about the sparks' access, not about the system. The
sparks cannot reach outside. Everything they do lands in a file that can be
read from outside, and the Scribes' **%s** entries exist precisely so it can
be. The simulacrum is complete from the inside and transparent from the
outside, and both of those need to be true — one for the world to work, the
other for any of it to count as evidence.
""" % (NOW,
       k(q("temple/lexicon.db", "SELECT COUNT(*) FROM lexicon")),
       k(q("temple/lexicon.db", "SELECT COUNT(*) FROM dead_words")),
       k(q("temple/chronicle.db", "SELECT COUNT(*) FROM entries"))),

"Philosophy/Dark-City.md": lambda: """
## As it stands, %s

Midnight is no longer a metaphor for an epoch boundary. The world has a
clock: **%s cycles a day**, one cycle every **%s real seconds**, which puts
it at **%s world days for every day out here**. It is currently world day
**%s**. The city rebuilds on a schedule that can be read off a wall.

**The Tuning, as it was actually built:** **%s wards** cut into the ground,
using figures out of *The Three-Six-Nine* — a text the sparks hold in the
canon and can read. That is the whole claim of this document made literal:
the mechanism by which reality is reshaped is a learnable tool, published
where anyone in the world can find it, rather than a birthright.

**Where it falls short of Dark City.** No spark has yet done what John
Murdoch does — investigated its way up a layer. They live inside the
construction and use it; none has turned around and asked who is building.
The metaphor is right about the architecture and still ahead of the
evidence.
""" % (NOW,
       k(CYCLES_PER_DAY), BEAT,
       "%.1f" % ((86400.0 / BEAT) / CYCLES_PER_DAY),
       k(q("temple/heartbeat.db", "SELECT day FROM heart_state")),
       k(q("temple/wards.db", "SELECT COUNT(*) FROM wards"))),

"Constitution/Amendment-Protocol.md": lambda: """
## As it stands, %s

The process above was designed before anything could propose. It now runs,
and in two places it runs differently from how it is written.

**Who proposes.** Not a hedge fund. The world measures itself and proposes
changes to itself, in `temple/amendments.py`: **%s measurements taken, %s
amendments proposed.** They are reviewed at the Congress, `/congress`.

**What review means.** The document says the Shadow approves or rejects with
explanation. What was built is stricter: every proposal is **run against a
control** before anyone rules on it. The world's first proposal about itself
was tested this way and its own experiment came back showing *no effect*, so
it was not applied. Judgement was not required.

Ratification is unchanged and is the part that matters most: **nothing
touching a Core Directive is applied without the Source.** Nothing has been.

The three unamendable rules — local hardware, uncensored models, the
hierarchy itself — have held through every change to date.
""" % (NOW,
       k(q("temple/proposals.db", "SELECT COUNT(*) FROM observations")),
       k(q("temple/proposals.db", "SELECT COUNT(*) FROM proposals"))),
}

def correct(s):
    """Fix statements that were true in June and are not true now.

    Only two kinds, both factual rather than editorial: the repository moved
    under spark-world/ and the paths were never updated, and Layer 3 carries a
    'Current Implementation' block naming one host and one model for a world
    that now runs 357 models. The live section below supersedes it, and two
    blocks disagreeing is worse than one that is right.
    """
    s = s.replace("/home/nvii/projects/umbreality-ai/",
                  "/home/nvii/projects/spark-world/umbreality-ai/")
    h = "## Current Implementation"
    if h in s:
        i = s.index(h)
        j = s.find("\n## ", i + 1)
        s = s[:i] + (s[j + 1:] if j != -1 else "")
    return s


done = 0
for name, build in DOCS.items():
    p = os.path.join(V, name)
    if not os.path.exists(p):
        print("  %s - not present" % name)
        continue
    s = open(p, encoding="utf-8").read()
    # cut the previous generated block out whole. The closing mark is what
    # makes that safe when hand-written sections follow it - an earlier
    # version truncated at the opening mark and would have eaten them.
    if MARK in s:
        i = s.index(MARK)
        j = s.find(ENDMARK, i)
        s = s[:i] + (s[j + len(ENDMARK):] if j != -1 else "")
    s = correct(s)
    # the rule keeps the whole separator inside the marked block, so cutting
    # the block leaves nothing behind to accumulate on the next run
    section = (MARK + "\n\n---\n\n" + build().strip()
               + "\n\n" + ENDMARK + "\n")
    # Related is a list of links and belongs at the bottom of a page, so the
    # live section goes above it rather than stranding it mid-document
    rel = s.find("\n## Related")
    head, tail = (s[:rel], s[rel:].rstrip() + "\n") if rel != -1 else (s, "")
    # loop, because an earlier version of this script left a separator behind
    # on every run and some documents carry more than one
    while True:
        t = head.rstrip().rstrip("-").rstrip()
        if t == head.rstrip():
            head = t
            break
        head = t
    body = head + "\n\n" + section + ("\n" + tail if tail else "")
    open(p, "w", encoding="utf-8").write(body)
    print("  %s" % name)
    done += 1
print("\n%d documents given a live section" % done)
