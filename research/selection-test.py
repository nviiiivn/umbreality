#!/usr/bin/env python3
"""Does scarcity actually select, or is it just bookkeeping?

The claim is that two ways of living with scarcity - the settled holding
what they take, the wild taking less and holding in common - produce
measurably different outcomes under the same conditions. If they come out
the same, this is an economy with no selection in it and the whole exercise
was decoration.

Sixty rounds of the world's stomach. Nothing else runs, so anything that
separates the two groups came from how they take and share and nothing else.

Reported honestly either way, including if the wild simply lose.
"""
import sys

sys.path.insert(0, "/home/nvii/projects/spark-world/umbreality-ai")
from temple.holdings import sweep, how_are_they, HUNGRY

print("sixty rounds. Nothing runs but taking, sharing and regrowth.")
print()
print("%5s  %-38s  %-38s  %s" % ("round", "wild", "settled", "places"))
print("%5s  %-38s  %-38s  %s" % ("", "median  poorest  hungry  starving",
                                 "median  poorest  hungry  starving", "stripped"))

marks = []
for i in range(1, 61):
    sweep(feed=200)
    if i % 10 == 0 or i == 1:
        w = how_are_they()
        a = w["ways"].get("wild", {})
        b = w["ways"].get("settled", {})
        marks.append((i, a, b, w["places"]["stripped"]))
        print("%5d  %6.1f %8.1f %7d %9d  %6.1f %8.1f %7d %9d  %8d"
              % (i,
                 a.get("median_store", 0), a.get("poorest", 0),
                 a.get("hungry", 0), a.get("starving", 0),
                 b.get("median_store", 0), b.get("poorest", 0),
                 b.get("hungry", 0), b.get("starving", 0),
                 w["places"]["stripped"]))

w = how_are_they()
a, b = w["ways"].get("wild", {}), w["ways"].get("settled", {})
print()
print("AFTER SIXTY ROUNDS")
print("  wild    : %d sparks, median %.1f, %d hungry (%.0f%%), %d starving, gave away %.0f"
      % (a.get("sparks", 0), a.get("median_store", 0), a.get("hungry", 0),
         100.0 * a.get("hungry", 0) / max(1, a.get("sparks", 1)),
         a.get("starving", 0), a.get("gave_away", 0)))
print("  settled : %d sparks, median %.1f, %d hungry (%.0f%%), %d starving, gave away %.0f"
      % (b.get("sparks", 0), b.get("median_store", 0), b.get("hungry", 0),
         100.0 * b.get("hungry", 0) / max(1, b.get("sparks", 1)),
         b.get("starving", 0), b.get("gave_away", 0)))
print()
print("  places stripped: %d of %d" % (w["places"]["stripped"], w["places"]["n"]))
print("  worst          :", w["places"]["worst"])

wh = 100.0 * a.get("hungry", 0) / max(1, a.get("sparks", 1))
sh = 100.0 * b.get("hungry", 0) / max(1, b.get("sparks", 1))
print()
if abs(wh - sh) < 4:
    print("  VERDICT: the two ways come out the same. That is not selection, "
          "it is bookkeeping, and the design needs changing.")
elif wh < sh:
    print("  VERDICT: the wild are hungrier %.0f%% less often. Sharing and "
          "taking less beats holding, under these conditions." % (sh - wh))
else:
    print("  VERDICT: the settled are hungrier %.0f%% less often. Holding "
          "beats sharing, under these conditions." % (wh - sh))
print()
print("  Either way it is a real difference produced by belief rather than "
      "by rule, which is what selection needs to act on.")
