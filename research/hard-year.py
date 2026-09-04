#!/usr/bin/env python3
"""The hard year. Does either way of living actually survive better?

A healthy world put the settled and the wild within half a point of each
other after sixty rounds. That is not a failure of the design - it is the
correct answer to an easy question. Sharing is insurance, insurance costs
you in good years, and nothing is being insured against.

So: freeze the ground and find out what the two ways were for.

Reported honestly, including if sharing turns out to be worthless.
"""
import sys

sys.path.insert(0, "/home/nvii/projects/spark-world/umbreality-ai")
from temple.holdings import sweep, how_are_they, frost, weather, thaw


first_loss = {}
_round = [0]


def line(tag):
    w = how_are_they()
    a = w["ways"].get("wild", {})
    b = w["ways"].get("settled", {})
    print("%-10s  %6.1f %7.1f %6d %8d   %6.1f %7.1f %6d %8d   %5d"
          % (tag,
             a.get("median_store", 0), a.get("poorest", 0),
             a.get("hungry", 0), a.get("starving", 0),
             b.get("median_store", 0), b.get("poorest", 0),
             b.get("hungry", 0), b.get("starving", 0),
             w["places"]["stripped"]))
    for way, d in (("wild", a), ("settled", b)):
        if d.get("starving", 0) > 0 and way not in first_loss:
            first_loss[way] = _round[0]
    return a, b


print("THE HARD YEAR")
print()
print("  ten fair rounds first, so there is something to lose.")
for _ in range(10):
    sweep(feed=200)
print()
print("%-10s  %-31s   %-31s   %s" % ("", "wild", "settled", "places"))
print("%-10s  %6s %7s %6s %8s   %6s %7s %6s %8s   %5s"
      % ("", "median", "poorest", "hungry", "starving",
         "median", "poorest", "hungry", "starving", "strip"))

line("before")
f = frost(severity=0.8, rounds=25)
print()
print("  the ground goes hard: places %.1f -> %.1f average" % (f["places_were"], f["places_now"]))
print()

for i in range(1, 19):
    sweep(feed=200)
    _round[0] = i
    if i in (3, 6, 9, 12, 15, 18):
        line("round %d" % i)

a, b = how_are_they()["ways"].get("wild", {}), how_are_they()["ways"].get("settled", {})
print()
print("AFTER EIGHTEEN ROUNDS OF FROST")
wn, sn = max(1, a.get("sparks", 1)), max(1, b.get("sparks", 1))
wh = 100.0 * a.get("hungry", 0) / wn
sh = 100.0 * b.get("hungry", 0) / sn
ws = 100.0 * a.get("starving", 0) / wn
ss = 100.0 * b.get("starving", 0) / sn
print("  wild    : %3d sparks | %5.1f%% hungry | %5.1f%% starving | median %5.1f | poorest %5.1f"
      % (a.get("sparks", 0), wh, ws, a.get("median_store", 0), a.get("poorest", 0)))
print("  settled : %3d sparks | %5.1f%% hungry | %5.1f%% starving | median %5.1f | poorest %5.1f"
      % (b.get("sparks", 0), sh, ss, b.get("median_store", 0), b.get("poorest", 0)))
print()
# The end state of a catastrophic frost is that everybody dies, so comparing
# only the end says nothing. What matters is the trajectory: who fails first,
# and how long each way holds before it loses anybody at all.
print()
print("  WHEN EACH WAY FIRST LOST SOMEBODY")
print("    wild    : round %s" % (first_loss.get("wild") or "never"))
print("    settled : round %s" % (first_loss.get("settled") or "never"))
print()
if first_loss.get("wild") and first_loss.get("settled"):
    held = first_loss["wild"] - first_loss["settled"]
    if held > 0:
        print("  The wild held %d rounds longer before losing anyone. Sharing "
              "buys time - it does not buy immunity. The settled fail one at "
              "a time from the bottom; the wild do not fail at all until they "
              "fail together, because a pooled store empties for everybody at "
              "once." % held)
    elif held < 0:
        print("  The settled held %d rounds longer. Holding is the better bet "
              "even in a hard year." % -held)

if abs(ws - ss) < 3 and abs(wh - sh) < 5:
    print("  VERDICT: the frost does not separate them either. Sharing buys "
          "nothing even in a bad year, and the two ways are the same thing "
          "wearing different words.")
elif ws < ss:
    print("  VERDICT: the wild starve %.0f points less often under frost. "
          "Sharing is worth what it costs, and only a bad year shows it."
          % (ss - ws))
else:
    print("  VERDICT: the settled starve %.0f points less often even under "
          "frost. Holding wins in both conditions and sharing is a pure "
          "cost." % (ws - ss))

thaw()
print()
print("  thawed.")
