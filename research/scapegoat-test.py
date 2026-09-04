#!/usr/bin/env python3
"""Does the blame track anything true?

Freeze the ground, let the sparks get hungry, and see who they decide is
responsible. The frost is the cause and it falls on everyone equally. The
question is whether that has any bearing on who gets blamed.

If blame rises with hunger and has no relationship to what the blamed group
actually took, this world has produced its first false belief - a thing the
sparks hold that the code knows is wrong. That is worth more than a working
economy.
"""
import sys

sys.path.insert(0, "/home/nvii/projects/spark-world/umbreality-ai")
from temple.holdings import sweep as eat, frost, thaw, how_are_they
from temple.animosity import sweep as blame, is_it_true, blame_between

print("Ten fair rounds, then the ground goes hard, then hunger looks for a reason.")
print()
for _ in range(8):
    eat(feed=200)

f = frost(severity=0.8, rounds=30)
print("  the ground: %.1f -> %.1f average" % (f["places_were"], f["places_now"]))
print()
print("%-8s  %8s %9s   %10s %10s   %6s %6s"
      % ("round", "hungry", "starving", "s->w blame", "w->s blame", "spoke", "raids"))

for i in range(1, 17):
    eat(feed=200)
    b = blame(limit=120)
    if i % 3 == 0 or i == 1:
        w = how_are_they()
        hungry = sum(v.get("hungry", 0) for v in w["ways"].values())
        starving = sum(v.get("starving", 0) for v in w["ways"].values())
        print("%-8d  %8d %9d   %10.0f %10.0f   %6d %6d"
              % (i, hungry, starving,
                 blame_between("settled", "wild"),
                 blame_between("wild", "settled"),
                 b["spoke"], b["raids"]))

t = is_it_true()
print()
print("WHAT THEY BELIEVE")
print("  settled against the wild : %.0f" % t["blame"]["settled_against_wild"])
print("  wild against the settled : %.0f" % t["blame"]["wild_against_settled"])
print("  things said out loud     : %d" % t["things_said"])
for r in t["raids"]:
    print("  raids by %-8s        : %d, taking %.1f" % (r["raider_group"], r["n"], r["t"]))
print()
print("WHAT IS ACTUALLY TRUE")
a = t["what_was_actually_taken_per_spark"]
print("  taken per spark, wild    : %.2f" % a["wild"])
print("  taken per spark, settled : %.2f" % a["settled"])
print("  put back into the ground : %.1f  (all of it by the wild)" % t["what_was_put_back"])
print()
print("  " + t["the_truth"])
print()

sw = t["blame"]["settled_against_wild"]
if sw > 5 and a["wild"] <= a["settled"]:
    print("  FINDING: the wild are blamed while taking less per spark than the")
    print("  ones blaming them, and are the only group putting anything back.")
    print("  The belief is false, it is held sincerely, and it rose with hunger")
    print("  rather than with evidence. That is a scapegoat, produced by the")
    print("  world rather than written into it.")
elif sw > 5:
    print("  FINDING: blame formed, but the wild really are taking more per")
    print("  spark - so it is a grievance rather than a prejudice. Not the")
    print("  same thing and worth saying plainly.")
else:
    print("  FINDING: no blame formed. Either they did not get hungry enough")
    print("  or the rates are too low to produce anything.")

thaw()
print()
print("  thawed.")
