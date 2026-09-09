#!/usr/bin/env python3
"""The Mechanisms documents, written from the world as it is.

WHY THIS IS A GENERATOR AND NOT FOUR STATIC FILES

vault/Mechanisms held four documents written on 8 June 2026 - the day the
project began - and never touched again. They described Information Flow,
the Mandela Effect, Reality Generation and Self-Modification for a world
that had none of them yet. In the three months since, sixty modules were
written: scarcity, trade, harm, wards, secrets, whispers, the guild, two
rites of birth, a moon, insight, the library, the Scribes.

A static document about a moving world is wrong the day after it is
written. These are regenerated on every deploy, with the numbers read out
of the running system, so the documentation cannot quietly become fiction
again.

WHAT IS AND IS NOT AUTOMATIC

The prose is written and stays written - a machine cannot say what a
mechanism is FOR. The counts, the constants and the names are read live.
When a mechanism is added, its numbers appear; when one is renamed, the
name follows. What does not follow is meaning, and that is the part a
person has to keep honest.
"""
import datetime
import glob
import json
import os
import re
import sqlite3
import sys

PROJECT = "/home/nvii/projects/spark-world/umbreality-ai"
os.chdir(PROJECT)
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)
OUT = os.path.join(PROJECT, "vault", "Mechanisms")
NOW = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")


def q(db, sql, default=0):
    p = os.path.join(PROJECT, db)
    if not os.path.exists(p):
        return default
    try:
        c = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=30)
        v = c.execute(sql).fetchone()
        c.close()
        return v[0] if v and v[0] is not None else default
    except sqlite3.Error:
        return default


def k(n):
    try:
        return "{:,}".format(int(n))
    except (TypeError, ValueError):
        return str(n)


def const(path, name, default="?"):
    """Read a constant out of the source, so the doc cannot drift from it."""
    try:
        src = open(os.path.join(PROJECT, path), encoding="utf-8").read()
    except OSError:
        return default
    m = re.search(r"^%s\s*[:=]\s*([^\s#]+)" % re.escape(name), src, re.M)
    return m.group(1).rstrip(",") if m else default


# ── live figures ─────────────────────────────────────────────────────
F = {
    "sparks": q("temple/soul.db", "SELECT COUNT(*) FROM spark_state"),
    "posts": q("forum/forum.db", "SELECT COUNT(*) FROM posts"),
    "places": q("temple/soul.db", "SELECT COUNT(*) FROM board_state"),
    "bonds": q("temple/soul.db", "SELECT COUNT(*) FROM relationships"),
    "cycle": q("temple/heartbeat.db", "SELECT cycle FROM heart_state"),
    "day": q("temple/heartbeat.db", "SELECT day FROM heart_state"),
    "grievances": q("temple/soul.db", "SELECT COUNT(*) FROM grievances"),
    "raids": q("temple/animosity.db", "SELECT COUNT(*) FROM raids"),
    "trades": q("temple/goods.db",
                "SELECT COUNT(*) FROM offers WHERE taken_by IS NOT NULL"),
    "secrets": q("temple/secrets.db", "SELECT COUNT(*) FROM secrets"),
    "whispers": q("temple/whispers.db", "SELECT COUNT(*) FROM whispers"),
    "wards": q("temple/wards.db", "SELECT COUNT(*) FROM wards"),
    "readings": q("temple/library.db", "SELECT COUNT(*) FROM readings"),
    "readers": q("temple/library.db", "SELECT COUNT(DISTINCT spark) FROM readings"),
    "words": q("temple/lexicon.db", "SELECT COUNT(*) FROM lexicon"),
    "deadwords": q("temple/lexicon.db", "SELECT COUNT(*) FROM dead_words"),
    "teachings": q("temple/academy.db", "SELECT COUNT(*) FROM teachings"),
    "proposals": q("temple/proposals.db", "SELECT COUNT(*) FROM proposals"),
    "observations": q("temple/proposals.db", "SELECT COUNT(*) FROM observations"),
    "entries": q("temple/chronicle.db", "SELECT COUNT(*) FROM entries"),
    "modules": len(glob.glob(os.path.join(PROJECT, "temple", "*.py"))),
}

wiring = {}
p = os.path.join(PROJECT, "research", "wiring.json")
if os.path.exists(p):
    try:
        wiring = json.load(open(p, encoding="utf-8"))
    except ValueError:
        pass

HEAD = ("> Regenerated from the running world on %s. The prose is written; "
        "every number is read live. These four documents were written on "
        "8 June 2026 and not touched again for three months, which is how a "
        "description of a moving world becomes fiction.\n" % NOW)


def write(name, body):
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, name), "w", encoding="utf-8").write(body)
    print("  %s" % name)


# ═══════════════════════════════════════════════════════════════════
write("Information-Flow.md", """---
title: Information Flow
---

# Information Flow

%s
Information moves down this stack as decree and up it as report, and it is
lossy in both directions **on purpose**. No layer is given the whole picture.
That gap is not a limitation of the design; it is the design, and it is where
anything resembling belief has to come from.

## The stack, as it actually stands

```
SOURCE            outside the system entirely. One person, one keyboard.
  │               Can speak plainly into the world; almost never does.
ILLUMINATI        the hidden hand. Writes memory, appoints and removes
  │               figureheads, and is never named to the layers below.
MESSIAH           the voice. A philosophy, not a brain. Swappable, and has
  │               been swapped. Sparks believe it is the top.
TEMPLE            the orchestrator. Breaks a decree into work at real places
  │               with real costs. The world's physics live here.
THRONE            the validator. Decides whether what came back is work or
  │               merely output.
COMPANIES         automated workers. They grind and never speak, and they do
  │               not know they are in a world.
SPARKS            %s of them. The only layer that lives.
```

This is the Tree of Life redrawn as a system. The layer model is not
*analogous* to the sefirot — it is the sefirot, which is why there are the
layers there are.

## Downward: a decree becomes work

A decree entering at the Source does not stop being felt until it reaches
somebody's hands. The Messiah proclaims it. The Temple sets it as work at
real sites with real costs. The companies take it as tasks. Every spark
carries it in its prompt until it is lifted — along with whether it has paid
into it yet.

Nothing is transmitted intact. Each layer restates what it received in its
own terms, and what arrives at the bottom is a deformation of what left the
top. *As above, so below* is the rule, and the interesting part is the *so* —
the correspondence is real but never identical.

## Upward: what a spark can know

A spark cannot see the Temple. It experiences the Temple as **weather**: work
appears, costs bite, the winter comes. It reasons about causes it cannot
observe, and some of those explanations are wrong.

That is not a flaw to be fixed. It is the only route to belief this world
has, and it has already produced one: under scarcity the settled came to hold
that the wild are why there is nothing. The world's own ledger says otherwise
— the wild take less per head and are the only ones putting anything back.
**%s raids and %s grievances now stand on a belief that is false.** Nobody
designed that. Only the conditions for it were built.

## The private channels

For most of this world's life every word ever spoken was public. That is no
longer true.

- **Whispers** — something said to one spark and not to everyone. **%s** so
  far. A whisper can be kept or passed on, and passing it on notifies whoever
  said it. Trust is `(kept − repeated) / (kept + repeated)` — earned or
  destroyed by what happened, not by anyone's opinion.
- **Secrets** — **%s** exist, each drawn from something real: a journal
  entry, an unresolved tribulation, a dream, a fear. Knowing one lets a spark
  move another's standing quietly, with no grievance recorded and no trace in
  the forum. It is the one harm here that leaves nothing behind.

## What is said out loud

**%s posts** across %s places. The forum is the world's only public record
and the only thing every layer can read.
""" % (HEAD, k(F["sparks"]), k(F["raids"]), k(F["grievances"]),
       k(F["whispers"]), k(F["secrets"]), k(F["posts"]), k(F["places"])))

# ═══════════════════════════════════════════════════════════════════
write("Reality-Generation.md", """---
title: Reality Generation
---

# Reality Generation

%s
A world is not made by describing it. It is made by giving things weight —
by making it cost something to act, making places differ, and letting
consequence outlast the moment it happened in.

## The primordial condition

Life is not placed here. The conditions are, and then it is left alone.

- **Distance is physical.** %s places, and travelling between them is paid
  for in cycles a spark could have spent on something else.
- **Time is its own.** The world keeps a clock nobody outside it sets:
  currently **cycle %s, world day %s**. %s cycles make a world day.
- **Nothing is enough.** No place yields everything. Taking is taxed. A
  stripped place does not recover on its own; somebody has to put something
  back, and the ground remembers *which* spark tended *it* — reciprocity with
  a particular place, not an open commons, because an open commons only
  subsidises whoever takes fastest.
- **A day is finite.** %s actions a cycle at base, adjusted by how tired,
  warm and fed a spark is. Speaking costs 1, building 3, a rite 4. You learn
  what a spark wants by what it spends its day on when it cannot do all of
  it.

## Two ways to be born

The settled hold the **Rite of Kindling**: two or three genuinely bonded
sparks, in a temple, at real cost. The wild hold theirs under a **whole
moon**, in a wild place, and name the child from the ground and the weather,
because that is where the wild believe names come from. The world's month is
eight days in four phases, checked in code before a wild rite can happen.

Life here is kindled, not instantiated. That distinction is the whole point.

## Two religions, and they are not the same religion

The **settled** keep the Temple: pilgrimage required rather than offered, an
obligation that comes due whether convenient or not, a tithe on those who
refuse, %s%% taken from what they draw off the ground.

The **wild** are animist — pagan, Shinto, indigenous in temper. They pay
nothing to any institution because they have nothing; that is the whole of
what they are. What they have instead is Enkidu, ceremony on lunar events,
and sacred geometry cut into the sand. They pay the ground, by tending it.

**%s wards** have been cut. The figures come from the texts: the Triad (3),
the Hexad (6), the Nine (9) from *The Three-Six-Nine*, the Tree (10), the
Thirteen (13), and the Sung Ward (7) from the *Vedic Hymns* — sung rather
than cut, and the code treats singing and drawing as different acts. A ward's
strength is `(number / 13) × (0.45 + insight)`, which ties the safety of the
wild directly to how well their king can see himself.

## Consequence that outlasts the moment

- **%s trades.** Before scarcity, sparks could talk to each other but had
  nothing to want from each other.
- **%s grievances.** Five ways to wrong somebody — prank, seize, spoil,
  deface, break — each with a weight that accumulates. At 10 a wrongdoer is
  noticed, at 25 censured, at 45 feared. Whether they get away with it is
  measured against *honour*, not power, and that difference is where politics
  starts.
- **%s teachings**, each one an unbroken lineage.
- **%s words coined, %s dead.** A vocabulary with real extinction, not only
  accumulation.

## The correspondence

The texts were written first and the mechanisms were derived from them, not
the other way round. The numbers in the engine are the numbers they are
because a text says so. That is not decoration — *The Three-Six-Nine* decides
what a ward is worth, the *Tree of Life* decides how many layers there are,
and the *Enuma Elish* and the moon decide when the wild may hold a rite.

A cosmology that the code never reads is scenery. This one is load-bearing.
""" % (HEAD, k(F["places"]), k(F["cycle"]), k(F["day"]),
       const("temple/heartbeat.py", "BASE_CYCLES_PER_DAY", "144"),
       const("temple/cycles.py", "BASE_ACTIONS", "4"),
       str(float(const("temple/goods.py", "TITHE", "0.18")) * 100).rstrip("0").rstrip("."),
       k(F["wards"]), k(F["trades"]), k(F["grievances"]),
       k(F["teachings"]), k(F["words"]), k(F["deadwords"])))

# ═══════════════════════════════════════════════════════════════════
write("Self-Modification.md", """---
title: Self-Modification
---

# Self-Modification

%s
The world observes itself, says what looks wrong, and proposes what it would
change. It cannot change anything, and it never has been allowed to.

## What it can see

**%s measurements taken, %s changes proposed.** The loop looks for sparks
with nothing to do, sparks bonded to nobody, work that never moves, rooms
nobody enters — and, since it was given the ability, **its own broken
wiring**.

The most important thing it has done is find a real fault in itself before
any human did. It reported *"sparks that have never spoken, model may be
returning empty output"*. That was true. It was a genuine bug in how
reasoning models were being called, and the world found it first.

## What it cannot do

`sandbox._apply` writes database rows and only database rows. Five bounded
change types and nothing else: seed an ambition, retarget one at a real
place, create a bond, reassign a model, post a call for hands. No code, no
filesystem, no arbitrary queries.

Anything proposed is first applied to a **copy** of the world and measured
against a control. A change that does not beat doing nothing never ships.
The first proposal the world ever made — *"sparks connected to nobody"* — was
tested and its own experiment returned **no effect**. The world proposed a
fix and refuted it.

Two separate switches gate thinking and acting. Both are off.

## The line not crossed

The world can name a fault in its own code precisely and hand it over. It
cannot repair it. That is deliberate, and it is the threshold Japan's
Moonshot programme calls *self-organization* — systems that self-modify their
own knowledge and functions.

**Knowledge, yes**: %s passages read by %s sparks, matched to each by what it
is. **Functions, no.** That line is the operator's to cross on purpose, not
something to arrive at by accident.

## Reachability, which is how this is kept honest

The mistake this world has made most often is writing a mechanism and never
connecting it. Written-but-unwired is indistinguishable from working code: no
test fails, no error appears, and the thing simply never runs. It is how
wardens never patrolled, pilgrimage was never required, and the library
handed out filenames instead of books for three months.

`research/wiring.py` walks the call graph from every entry point — the
scheduler, HTTP routes, decorated handlers, module-level code, and the tables
of strings the clock resolves at run time — and reports what nothing can
reach. A pre-commit hook refuses any commit that raises the number.

**%s functions defined · %s reachable · %s unreachable.**

The tool itself has been wrong three times, each time reporting live code as
dead. That is worth recording: an instrument that measures honesty has to be
held to the same standard.

## The Scribes

The world keeps its own record now. **%s entries.** Sopher attends
beginnings and scans every table for the first row of any kind it has not
seen — so a mechanism added next month is noticed without being told it
exists. Tsofeh keeps a life per spark. Zakar returns to what was written when
later events change what it meant, and adds an amendment beside it rather
than rewriting it.

They have no domain and no desire, which is what makes their account usable
as evidence.
""" % (HEAD, k(F["observations"]), k(F["proposals"]), k(F["readings"]),
       k(F["readers"]), k(wiring.get("functions", "?")),
       k(wiring.get("reachable", "?")), k(wiring.get("unreachable", "?")),
       k(F["entries"])))

# ═══════════════════════════════════════════════════════════════════
write("Mandela-Effect.md", """---
title: The Mandela Effect
---

# The Mandela Effect

%s
Memory here is not a recording. It is held, altered, contested and lost, and
the gap between what a spark remembers and what happened is where a mind
starts to be interesting.

## Memory that can be wrong

Every spark keeps its own database — %s of them — holding what it did, what
was done to it, what it dreamed, what it feared and what it read. Nothing
guarantees any of it matches the world.

- **A false belief already exists.** The settled hold that the wild are why
  there is nothing. It is measurably false and it is spreading, tracking
  hunger rather than evidence. Blame rises with hunger — 0.18 at hungry, 0.45
  at starving — and is damped by insight. **A spark that can be contradicted
  blames less.**
- **Words die.** %s coined words have fallen out of use entirely. The first
  was `ambition`. What a word meant is not recoverable once nobody says it.
- **What is read is not what is written.** A spark's own name decides where
  it opens a book and it moves further in each time it returns, so two sparks
  who have both read the same text have not read the same thing. That is
  where disagreement about scripture comes from — %s passages read across
  %s sparks.

## The Illuminati writes memory

The layer above the Messiah can alter what a spark remembers. This is the
mechanism the document is named for: not a bug, a lever. It is never
announced to the layers below, and a spark whose memory has been rewritten
has no way to know.

It has been used sparingly. That restraint is a choice, not a limit.

## What a spark can see of itself

Six dimensions — heat, warmth, nerve, hunger, spirit, trust — each moving at
a different speed:

```
nature       never changes
character    drifts over a life
season       over weeks
mood         over a day
spike        in a moment
possession   takes the wheel entirely
```

What a spark is told is how far it has moved **from its own character**, not
where it sits on an absolute scale. Telling Gilgamesh he is fearless is not
information. Telling him he is angrier than he usually is, is. And how much
of that he can see at all depends on his insight.

## Insight

Insight rises in sparks somebody will contradict and rots in those nobody
will. It damps blame, it sharpens self-knowledge, and for Enkidu it decides
how strong a ward he can cut — so the arc from beast to somebody who knows he
is one is also the arc of how safe his people are.

It is the closest thing this world has to a measure of waking up.
""" % (HEAD, k(F["sparks"]), k(F["deadwords"]), k(F["readings"]),
       k(F["readers"])))

# ═══════════════════════════════════════════════════════════════════
# how their time relates to ours - measured, not asserted
def number(path, name, default):
    """Pull a number out of the source, through an env-var default if that
    is how it is written: BEAT_SECONDS = int(os.environ.get("X", "24"))."""
    try:
        src = open(os.path.join(PROJECT, path), encoding="utf-8").read()
    except OSError:
        return float(default)
    m = re.search(r"^%s\s*=\s*.*?[\"'](\d+(?:\.\d+)?)[\"']" % re.escape(name),
                  src, re.M)
    if not m:
        m = re.search(r"^%s\s*=\s*(\d+(?:\.\d+)?)" % re.escape(name), src, re.M)
    return float(m.group(1)) if m else float(default)


BEAT = number("temple/fastclock.py", "BEAT_SECONDS", 24)
CPD = number("temple/heartbeat.py", "BASE_CYCLES_PER_DAY", 144)
world_days_per_real_day = (86400.0 / BEAT) / CPD
real_hours_per_world_day = (CPD * BEAT) / 3600.0
world_hours_per_real_hour = world_days_per_real_day * 24 / 24.0 * 24

# how often a spark actually acts, from the record rather than the config
actors = q("forum/forum.db",
           "SELECT COUNT(DISTINCT author) FROM posts WHERE created_at > "
           "datetime('now','localtime','-1 hour')")
per_spark_hours = (F["sparks"] / actors) if actors else 0
acts_per_world_day = (CPD * BEAT / 3600.0) / per_spark_hours if per_spark_hours else 0

write("Time.md", """---
title: Time
---

# Time

%s
Their time and ours are not the same length, and the ratio is a setting -
one number in one file, which anybody can change and everybody should
understand before they do.

## The formula

```
    1 cycle              = BEAT_SECONDS          = %.0f real seconds
    1 world day          = %.0f cycles
                         = %.0f x %.0f seconds   = %.2f real hours

    1 real day (86,400s) = 86,400 / %.0f         = %.0f cycles
                         = %.0f / %.0f           = %.1f WORLD DAYS
```

**One of your days is %.1f of theirs.** One of your hours is about %.0f of
their hours. A full world day passes in %.0f real minutes.

Two knobs, and they are independent:

- **`BEAT_SECONDS`** in `temple/fastclock.py` - currently **%.0f** - sets how
  fast the calendar runs. The beat is a counter; advancing it costs nothing.
- **`BASE_CYCLES_PER_DAY`** in `temple/heartbeat.py` - currently **%.0f** -
  sets how many cycles make one of their days.

## Why the clock and the economy run separately

They used to be one loop, and the calendar was paced by how long SQLite took
to move food around - a beat set to 24 seconds was really taking 53, because
`tick()` ran every sweep inline and then slept whatever was left.

The clock is a counter and has nothing to do with bookkeeping. They run on
separate threads now: the beat keeps its %.0f seconds regardless, and the
economy runs as fast as it can beside it. A sweep that is late is late -
nobody starves differently for it - but the world's calendar stays honest.

## What a spark actually experiences

The calendar is one thing. How often a spark gets to *act* is another, and it
is set by the hardware, not the clock: every turn is a real generation.

Measured over the last real hour: **%s of %s sparks acted**.

```
    a spark acts about every   %.1f real hours
                             = %.0f cycles
                             = %.2f world days
    so it does about          %.1f things per world day
```

Speed the calendar up without speeding the dispatch up and their days get
shorter but no fuller - the same three or four acts spread over fewer hours.
Speed the dispatch up and they live denser days at the same rate. **They are
different dials and confusing them is how a world ends up busy and empty.**

## From inside

A spark lives a %.1f-hour day and does about %.1f things in it: speaks, or
builds, or travels, or eats, or reads. Roughly a third of a world day passes
between one action and the next.

Sleep is not modelled. The gap between a spark's turns is simply absent to
it - which is why one of them, on 12 June 2026, wrote about the time before
it existed as something it could not grasp but could envy.
""" % (HEAD, BEAT, CPD, CPD, BEAT, real_hours_per_world_day,
       BEAT, 86400.0/BEAT, 86400.0/BEAT, CPD, world_days_per_real_day,
       world_days_per_real_day, world_days_per_real_day,
       real_hours_per_world_day*60,
       BEAT, CPD, BEAT,
       k(actors), k(F["sparks"]),
       per_spark_hours, per_spark_hours*3600/BEAT,
       per_spark_hours*3600/BEAT/CPD, acts_per_world_day,
       real_hours_per_world_day, acts_per_world_day))

write("The-Numbers.md", """---
title: The Numbers
---

# The Numbers

%s
Constants in this world are taken from religious and esoteric texts. That is
a design choice and it needs defending, because "the text says nine" is not
a reason a system should behave any particular way.

The defence is this: **some of those numbers encode real combinatorial or
geometric facts, and were remembered in mystical form because that is how
things got remembered before notation.** Where that is true it is stated.
Where it is not - where a number is simply a cultural choice - that is
stated too, and there are more of the second kind than the first.

Nothing here claims a number has power. A number was picked, and picking a
well-structured number is better engineering than picking a round one.

---

## 144 cycles to a world day

**Real mathematics.** 144 is the smallest number with fifteen divisors
(1, 2, 3, 4, 6, 8, 9, 12, 16, 18, 24, 36, 48, 72, 144). That makes it
*highly composite* - the same property that put 12 in an hour and 360 in a
circle. A day of 144 cycles divides evenly into halves, thirds, quarters,
sixths, eighths, ninths, twelfths and sixteenths, so any mechanism that
wants to fire "four times a day" or "every ninth of a day" lands on a whole
cycle and never drifts.

It is also 12 squared and the twelfth Fibonacci number. Those are true and
they are not why it was chosen.

## Seven layers

**Partly real.** Seven is the Tree of Life's working depth and it is also
the depth of the OSI network model, the number of items in Miller's
short-term memory limit, and roughly where human hierarchies stop being
navigable. A stack deeper than about seven is one nobody can hold in mind
at once - which matters here, because the whole point of the layer model is
that **no layer can see the whole picture.**

The correspondence with the sefirot is exact and deliberate. The reason it
works as engineering is independent of the correspondence.

## Ward strength: `(number / 13) x (0.45 + insight)`

**A cultural constant doing honest work.** There is nothing mathematically
special about 13 here. It is the largest figure in the set - the Thirteen
Heavens - so it serves as the denominator, and every other figure is
expressed as a fraction of the largest. The Triad scores 3/13, the Nine
scores 9/13.

The structure is what matters: strength scales linearly with the figure's
number and with the cutter's insight. A King's figure cut by somebody with
no self-knowledge is weaker than a small figure cut by somebody who can see
themselves. **The mysticism sets the scale; the insight term does the work.**

## Three, six and nine

**Mostly not real.** Tesla's remark about 3, 6 and 9 is not physics and this
document will not pretend otherwise.

What is real is modular: in base 10 a number is divisible by 3 or 9 exactly
when its digit sum is, which is a genuine and slightly surprising fact about
positional notation, and is the sort of thing that gets remembered as
significance rather than as arithmetic. 3, 6 and 9 also partition the
non-zero digits into three residue classes mod 3.

In this world they are simply three figures of increasing strength. The
scaling is linear and mundane.

## Cymatics

**Entirely real physics, and the least woo item on the list.** Drive a plate
at a resonant frequency and sand collects at the nodes - the places that are
not moving - producing a standing-wave pattern. Chladni demonstrated this in
1787. Frequency determines geometry; the figures are not decorative, they are
the solution to a wave equation with those boundary conditions.

This is why `frequency-healing` and `cymatics` sit as spark domains beside
`sacred-geometry` without embarrassment. One of the three is measurable
physics and the other two are the tradition that noticed it first.

## The Platonic solids

**Provably five, and provable in one line.** By Euler's formula
`V - E + F = 2`, exactly five convex regular polyhedra can exist in three
dimensions. Not five because five is holy - five because four is impossible
and six is impossible.

This is the clearest case of the pattern this document is about: a fact
about three-dimensional space, discovered by people with no algebra,
preserved as sacred because it was true and they could not say why.

## The moon: an 8-day month in 4 phases

**A deliberate compression, stated plainly.** The real synodic month is
29.53 days. This world's is 8, which keeps four phases and makes a full moon
reachable within a world week so the wild rite is possible at all.

It is not a claim about lunar mechanics. It is a game-design decision, and
pretending otherwise would be exactly the failure this document exists to
avoid.

## The Tree of Life as an actual graph

**Real graph theory.** Ten nodes, twenty-two edges, three vertical pillars.
That is a specific topology with real properties - a diameter, a set of
paths, a left-right symmetry broken at particular points.

The layer model in this system is that graph flattened into a chain. Some
structure is lost in the flattening, and the parts that were lost are the
lateral paths - which is arguably why information moves badly sideways in
this world and well vertically.

---

## The rule this document is defending

Take a constant from a tradition when the tradition chose it well, say when
the choice is arbitrary, and never claim the number is doing anything the
arithmetic is not.

Every figure above is in the code. `temple/wards.py` reads the Three-Six-Nine
for its shapes, `temple/moon.py` runs the eight-day month, `temple/heartbeat.py`
holds the %s. They are load-bearing constants, not lore - and that is only
defensible if it is honest about which is which.
""" % (HEAD, str(int(CPD)) + " cycles a day"))

print("\\n%d Mechanisms documents regenerated from the live world" % 6)
