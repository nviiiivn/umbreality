#!/usr/bin/env python3
"""Claim 1, retested. The first version could not have found anything.

Jensen-Shannon divergence maxes at 1.0. The first test read 0.9568 observed
against 0.9773 shuffled - both nearly at the ceiling, because most lexicon
words appear on exactly one board, so any two boards' distributions barely
overlap whatever you do. A measure pinned at its maximum cannot tell two
situations apart. That is the same saturation fault as the health metrics
and the honour score, and it invalidates the result rather than supporting
either answer.

The fix is to test only words that appear on more than one board. Those are
the words that could have gone either way: shared vocabulary, used at
different rates in different places. That is what dialect actually means -
not different words, but the same words in different proportions.

The null is unchanged in spirit: shuffle which board each usage belongs to.
"""
import math, random, sqlite3, statistics
from collections import Counter, defaultdict

random.seed(20260903)
TRIALS = 1000
LEX = "/home/nvii/projects/spark-world/umbreality-ai/temple/lexicon.db"

c = sqlite3.connect(LEX); c.row_factory = sqlite3.Row
rows = [dict(r) for r in c.execute("SELECT word, board, uses FROM lexicon")]
c.close()

boards_per_word = defaultdict(set)
for r in rows:
    boards_per_word[r["word"]].add(r["board"])
shared = {w for w, bs in boards_per_word.items() if len(bs) >= 2}

rows = [r for r in rows if r["word"] in shared]
print("lexicon rows total          : %d" % len(boards_per_word))
print("words appearing on 2+ boards: %d  (these are the testable ones)" % len(shared))
print("usages under test           : %d" % sum(r["uses"] or 1 for r in rows))

def js(p, q):
    keys = set(p) | set(q)
    tp, tq = sum(p.values()) or 1, sum(q.values()) or 1
    d = 0.0
    for k in keys:
        a, b = p.get(k, 0)/tp, q.get(k, 0)/tq
        m = (a+b)/2
        if a: d += 0.5*a*math.log2(a/m)
        if b: d += 0.5*b*math.log2(b/m)
    return d

def mean_pair(bmap):
    ns = sorted(bmap)
    v = [js(bmap[a], bmap[b]) for i, a in enumerate(ns) for b in ns[i+1:]]
    return statistics.mean(v) if v else 0.0

bm = defaultdict(Counter)
for r in rows:
    bm[r["board"]][r["word"]] += r["uses"] or 1
bm = {b: cc for b, cc in bm.items() if sum(cc.values()) >= 100}
print("boards compared             : %d  (%s)" % (len(bm), ", ".join(sorted(bm))))

keep = [r for r in rows if r["board"] in bm]
observed = mean_pair(bm)

labels = [r["board"] for r in keep]
pairs = [(r["word"], r["uses"] or 1) for r in keep]
null = []
for _ in range(TRIALS):
    sh = labels[:]; random.shuffle(sh)
    t = defaultdict(Counter)
    for (w, u), b in zip(pairs, sh):
        t[b][w] += u
    null.append(mean_pair(t))

m, sd = statistics.mean(null), statistics.pstdev(null)
z = (observed - m)/sd if sd else float("nan")
p = (sum(1 for x in null if x >= observed) + 1) / (TRIALS + 1)
print()
print("  observed divergence : %.4f   (ceiling is 1.0)" % observed)
print("  shuffled            : %.4f  (sd %.4f)" % (m, sd))
print("  headroom            : %.4f  — the measure can now move" % (1.0 - observed))
print("  z                   : %+.1f" % z)
print("  p                   : %.4f" % p)
print()
print("  %s" % ("SUPPORTED" if p < 0.01 else "NOT SUPPORTED"))

# what the dialects actually are, if there are any
print()
print("most place-specific words (rate on that board vs everywhere else):")
tot = Counter()
for b, cc in bm.items():
    for w, u in cc.items(): tot[w] += u
grand = sum(tot.values())
best = []
for b, cc in bm.items():
    bt = sum(cc.values())
    for w, u in cc.items():
        if u < 12: continue
        here = u/bt
        elsewhere = (tot[w]-u)/max(1, grand-bt)
        if elsewhere > 0:
            best.append((here/elsewhere, w, b, u))
best.sort(reverse=True)
for ratio, w, b, u in best[:14]:
    print("   %-16s %-12s %4d uses   %.1fx more common here" % (w, b, u, ratio))
