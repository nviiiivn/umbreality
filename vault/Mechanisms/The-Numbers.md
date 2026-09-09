---
title: The Numbers
---

# The Numbers

> Regenerated from the running world on 2026-09-09 05:06 PDT. The prose is written; every number is read live. These four documents were written on 8 June 2026 and not touched again for three months, which is how a description of a moving world becomes fiction.

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
holds the 144 cycles a day. They are load-bearing constants, not lore - and that is only
defensible if it is honest about which is which.
