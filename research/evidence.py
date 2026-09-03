#!/usr/bin/env python3
"""Four claims about Umbreality, tested against their own null models.

Three months of a 298-agent world have produced 61,577 posts, 2,400 bonds,
842 teachings and a 2,854-word lexicon. None of it has ever been measured.
This measures it.

Every test here compares what the world did against what the same world
would look like if the interesting thing were not happening - shuffled
labels, rewired edges, a random graph of the same size. A number without a
null model is not evidence, it is decoration, and this world has already
produced two false positives that way: the sandbox reporting +0.0540 for
three unrelated proposals, and a "momentum" strategy that was a coin flip.

The claims are stated so they can fail. Where one fails, it is reported as
failed. An honest negative is worth more than a flattering number, because
the point of this file is to be shown to somebody who will check.
"""
import json
import math
import random
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path("/home/nvii/projects/spark-world/umbreality-ai")
SOUL = BASE / "temple" / "soul.db"
ACAD = BASE / "temple" / "academy.db"
FORUM = BASE / "forum" / "forum.db"
LEX = BASE / "temple" / "lexicon.db"

TRIALS = 1000
random.seed(20260903)          # reproducible: anyone can rerun and match


def rows(db, sql, args=()):
    c = sqlite3.connect(str(db), timeout=30)
    c.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in c.execute(sql, args)]
    finally:
        c.close()


def pvalue(observed, null, higher_is_interesting=True):
    """Proportion of null trials at least as extreme as what happened."""
    if higher_is_interesting:
        k = sum(1 for x in null if x >= observed)
    else:
        k = sum(1 for x in null if x <= observed)
    return (k + 1) / (len(null) + 1)          # add-one, never reports p=0


def zscore(observed, null):
    m = statistics.mean(null)
    s = statistics.pstdev(null)
    return (observed - m) / s if s else float("nan")


def verdict(p, threshold=0.01):
    return "SUPPORTED" if p < threshold else "NOT SUPPORTED"


def banner(n, claim):
    print()
    print("=" * 78)
    print("CLAIM %d  %s" % (n, claim))
    print("=" * 78)


# ══════════════════════════════════════════════════════════════════
# 1. Do the boards speak differently from each other?
# ══════════════════════════════════════════════════════════════════
def js_divergence(p, q):
    """Jensen-Shannon divergence between two word distributions."""
    keys = set(p) | set(q)
    tp, tq = sum(p.values()) or 1, sum(q.values()) or 1
    d = 0.0
    for k in keys:
        a, b = p.get(k, 0) / tp, q.get(k, 0) / tq
        m = (a + b) / 2
        if a:
            d += 0.5 * a * math.log2(a / m)
        if b:
            d += 0.5 * b * math.log2(b / m)
    return d


def claim_dialect():
    banner(1, "Different places in the world speak differently.")
    print("""
The lexicon's most-used words are ordinary English - delicate, guidance,
happy - so the interesting claim is NOT that sparks invented words. They did
not. The claim is dialect: that the bazaar and the library, given the same
language, drifted to different characteristic vocabulary the way two
villages do.

TEST      Mean Jensen-Shannon divergence between every pair of boards'
          word distributions.
NULL      The same words and counts, with board labels shuffled. If place
          has no effect, a word is as likely to belong to one board as
          another, and the divergence should not change.
""")
    lex = rows(LEX, "SELECT word, board, uses FROM lexicon")
    if not lex:
        print("  no lexicon; cannot test")
        return None

    boards = defaultdict(Counter)
    for r in lex:
        boards[r["board"]][r["word"]] += r["uses"] or 1
    boards = {b: c for b, c in boards.items() if sum(c.values()) >= 200}
    names = sorted(boards)
    print("  boards with enough speech to compare: %d  (%s)"
          % (len(names), ", ".join(names)))
    if len(names) < 2:
        print("  fewer than two boards; cannot test")
        return None

    def mean_pairwise(bmap):
        ns = sorted(bmap)
        vals = [js_divergence(bmap[a], bmap[b])
                for i, a in enumerate(ns) for b in ns[i + 1:]]
        return statistics.mean(vals) if vals else 0.0

    observed = mean_pairwise(boards)

    flat = [(r["word"], r["uses"] or 1) for r in lex]
    labels = [r["board"] for r in lex]
    labels = [b for b in labels if b in boards]
    flat = [f for f, r in zip(flat, lex) if r["board"] in boards]

    null = []
    for _ in range(TRIALS):
        shuffled = labels[:]
        random.shuffle(shuffled)
        bm = defaultdict(Counter)
        for (w, u), b in zip(flat, shuffled):
            bm[b][w] += u
        null.append(mean_pairwise(bm))

    p = pvalue(observed, null)
    print()
    print("  observed divergence : %.4f" % observed)
    print("  shuffled            : %.4f  (sd %.4f, n=%d)"
          % (statistics.mean(null), statistics.pstdev(null), TRIALS))
    print("  z                   : %+.1f" % zscore(observed, null))
    print("  p                   : %.4f" % p)
    print()
    print("  %s" % verdict(p))
    return {"claim": "dialect divergence between places", "observed": observed,
            "null_mean": statistics.mean(null), "z": zscore(observed, null),
            "p": p, "verdict": verdict(p)}


# ══════════════════════════════════════════════════════════════════
# 2. Does knowledge actually travel, or only get handed over once?
# ══════════════════════════════════════════════════════════════════
def claim_transmission():
    banner(2, "Knowledge passes through sparks, not just to them.")
    print("""
Anyone can teach. The question is whether a thing learned is then taught
onward - whether the world has chains rather than only pairs. A spark taught
astronomy who later teaches astronomy to somebody else is transmission; two
unrelated lessons are not.

TEST      Number of 2-step chains A->B->C within the same domain, where B
          learned it before B taught it. Order matters: teaching something
          before you learned it is not transmission.
NULL      Students reshuffled among the same teachings, keeping every
          teacher's load and every domain's size. Chains that survive that
          are chains that chance produces anyway.
""")
    t = rows(ACAD, "SELECT elder, student, domain, taught_at FROM teachings "
                   "WHERE elder IS NOT NULL AND student IS NOT NULL")
    if not t:
        print("  no teachings; cannot test")
        return None
    print("  teachings: %d   distinct domains: %d   distinct teachers: %d"
          % (len(t), len({r['domain'] for r in t}), len({r['elder'] for r in t})))

    def chains(recs):
        by_domain = defaultdict(list)
        for r in recs:
            by_domain[r["domain"]].append(r)
        total = 0
        for dom, rs in by_domain.items():
            learned = defaultdict(list)      # who learned it, and when
            for r in rs:
                learned[r["student"]].append(r["taught_at"])
            for r in rs:
                # r.elder teaching: did the elder learn this domain earlier?
                earlier = [ts for ts in learned.get(r["elder"], [])
                           if ts and r["taught_at"] and ts < r["taught_at"]]
                if earlier:
                    total += 1
        return total

    observed = chains(t)

    null = []
    students = [r["student"] for r in t]
    for _ in range(TRIALS):
        sh = students[:]
        random.shuffle(sh)
        fake = [dict(r, student=s) for r, s in zip(t, sh)]
        null.append(chains(fake))

    p = pvalue(observed, null)
    print()
    print("  observed chains : %d" % observed)
    print("  shuffled        : %.1f  (sd %.1f, n=%d)"
          % (statistics.mean(null), statistics.pstdev(null), TRIALS))
    print("  z               : %+.1f" % zscore(observed, null))
    print("  p               : %.4f" % p)
    print()
    print("  %s" % verdict(p))
    return {"claim": "knowledge passes onward", "observed": observed,
            "null_mean": statistics.mean(null), "z": zscore(observed, null),
            "p": p, "verdict": verdict(p)}


# ══════════════════════════════════════════════════════════════════
# 3. Is the society a society, or 298 sparks bumping into each other?
# ══════════════════════════════════════════════════════════════════
def claim_network():
    banner(3, "Who knows whom is structured, not random.")
    print("""
2,400 bonds among 298 sparks. If they formed at random the graph would look
like any other graph of that size. Real societies do not: friends of friends
are friends, and a few people know far more people than the average.

TEST      Clustering (do a spark's acquaintances know each other?) and the
          spread of how many bonds each spark has.
NULL      Erdos-Renyi: the same 298 sparks and the same number of bonds,
          thrown down at random, 1000 times.
""")
    rel = rows(SOUL, "SELECT spark1, spark2 FROM relationships "
                     "WHERE spark1 IS NOT NULL AND spark2 IS NOT NULL "
                     "AND spark1 != spark2")
    nodes = sorted({r["spark1"] for r in rel} | {r["spark2"] for r in rel})
    idx = {n: i for i, n in enumerate(nodes)}
    edges = {tuple(sorted((idx[r["spark1"]], idx[r["spark2"]]))) for r in rel}
    n, m = len(nodes), len(edges)
    print("  sparks in the graph: %d    distinct bonds: %d" % (n, m))
    if n < 10 or m < 10:
        print("  too small; cannot test")
        return None

    def stats(edge_set, n):
        adj = defaultdict(set)
        for a, b in edge_set:
            adj[a].add(b)
            adj[b].add(a)
        # global clustering = 3*triangles / connected triples
        tri = 0
        triples = 0
        for v in range(n):
            nb = list(adj[v])
            d = len(nb)
            triples += d * (d - 1) / 2
            for i in range(d):
                for j in range(i + 1, d):
                    if nb[j] in adj[nb[i]]:
                        tri += 1
        clustering = (tri / triples) if triples else 0.0
        degs = [len(adj[v]) for v in range(n)]
        return clustering, (statistics.pstdev(degs) / statistics.mean(degs)
                            if statistics.mean(degs) else 0.0)

    obs_c, obs_h = stats(edges, n)

    null_c, null_h = [], []
    all_pairs_n = n * (n - 1) // 2
    for _ in range(TRIALS):
        e = set()
        while len(e) < m:
            a = random.randrange(n)
            b = random.randrange(n)
            if a != b:
                e.add((min(a, b), max(a, b)))
        c, h = stats(e, n)
        null_c.append(c)
        null_h.append(h)

    p_c = pvalue(obs_c, null_c)
    p_h = pvalue(obs_h, null_h)
    print()
    print("  clustering   observed %.4f   random %.4f (sd %.4f)   z %+.1f   p %.4f"
          % (obs_c, statistics.mean(null_c), statistics.pstdev(null_c),
             zscore(obs_c, null_c), p_c))
    print("  degree spread observed %.4f   random %.4f (sd %.4f)   z %+.1f   p %.4f"
          % (obs_h, statistics.mean(null_h), statistics.pstdev(null_h),
             zscore(obs_h, null_h), p_h))
    print()
    print("  clustering    %s" % verdict(p_c))
    print("  degree spread %s" % verdict(p_h))
    return {"claim": "the bond network is structured",
            "clustering": {"observed": obs_c, "null_mean": statistics.mean(null_c),
                           "z": zscore(obs_c, null_c), "p": p_c,
                           "verdict": verdict(p_c)},
            "degree_spread": {"observed": obs_h, "null_mean": statistics.mean(null_h),
                              "z": zscore(obs_h, null_h), "p": p_h,
                              "verdict": verdict(p_h)}}


# ══════════════════════════════════════════════════════════════════
# 4. Do sparks become different from one another?
# ══════════════════════════════════════════════════════════════════
def claim_specialisation():
    banner(4, "Sparks specialise instead of all doing the same things.")
    print("""
Each spark keeps its own record of what it has studied and how often. If
they are interchangeable, every spark's attention is spread the same way
across the same domains. If they specialise, each one's attention is
concentrated, and concentrated on different things.

TEST      Mean normalised entropy of each spark's study distribution. Low
          entropy means a spark concentrates.
NULL      The same total study events redealt across domains in proportion
          to how popular each domain is overall - so domain popularity is
          preserved and only the per-spark concentration is destroyed.
""")
    spark_dbs = sorted((BASE / "temple").glob("spark_*.db"))
    per_spark = {}
    domain_totals = Counter()
    for p in spark_dbs:
        try:
            c = sqlite3.connect(str(p), timeout=20)
            d = {r[0]: r[1] or 0 for r in
                 c.execute("SELECT domain_id, times_studied FROM domains")}
            c.close()
        except sqlite3.Error:
            continue
        d = {k: v for k, v in d.items() if v > 0}
        if sum(d.values()) >= 5:
            per_spark[p.stem[6:]] = d
            for k, v in d.items():
                domain_totals[k] += v
    print("  sparks with a real study record: %d   domains in play: %d"
          % (len(per_spark), len(domain_totals)))
    if len(per_spark) < 20:
        print("  too few; cannot test")
        return None

    def norm_entropy(d):
        tot = sum(d.values())
        if tot <= 0 or len(d) < 2:
            return 0.0
        h = -sum((v / tot) * math.log2(v / tot) for v in d.values() if v)
        return h / math.log2(len(domain_totals)) if len(domain_totals) > 1 else 0.0

    observed = statistics.mean(norm_entropy(d) for d in per_spark.values())

    doms = list(domain_totals)
    weights = [domain_totals[k] for k in doms]
    null = []
    for _ in range(TRIALS // 5):        # each trial redeals every spark
        vals = []
        for d in per_spark.values():
            n_events = sum(d.values())
            drawn = Counter(random.choices(doms, weights=weights, k=n_events))
            vals.append(norm_entropy(drawn))
        null.append(statistics.mean(vals))

    p = pvalue(observed, null, higher_is_interesting=False)
    print()
    print("  observed mean entropy : %.4f   (lower = more specialised)" % observed)
    print("  redealt at random     : %.4f  (sd %.4f, n=%d)"
          % (statistics.mean(null), statistics.pstdev(null), len(null)))
    print("  z                     : %+.1f" % zscore(observed, null))
    print("  p                     : %.4f" % p)
    print()
    print("  %s" % verdict(p))
    return {"claim": "sparks specialise", "observed": observed,
            "null_mean": statistics.mean(null), "z": zscore(observed, null),
            "p": p, "verdict": verdict(p)}


if __name__ == "__main__":
    print("UMBREALITY — FOUR CLAIMS, TESTED")
    print("298 sparks · 61,577 posts · 2,400 bonds · 842 teachings · 2,854 words")
    print("%d null trials per test · seed 20260903 · reproducible" % TRIALS)

    out = {}
    for fn, key in ((claim_dialect, "dialect"),
                    (claim_transmission, "transmission"),
                    (claim_network, "network"),
                    (claim_specialisation, "specialisation")):
        try:
            out[key] = fn()
        except Exception as e:
            import traceback
            print("\n  TEST FAILED: %s: %s" % (type(e).__name__, e))
            traceback.print_exc()
            out[key] = {"error": str(e)}

    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    for k, v in out.items():
        if not v:
            print("  %-16s could not be tested" % k)
        elif "verdict" in v:
            print("  %-16s %-14s  p=%.4f  z=%+.1f" % (k, v["verdict"], v["p"], v["z"]))
        elif "clustering" in v:
            print("  %-16s clustering %-14s p=%.4f" % (k, v["clustering"]["verdict"],
                                                       v["clustering"]["p"]))
            print("  %-16s degrees    %-14s p=%.4f" % ("", v["degree_spread"]["verdict"],
                                                       v["degree_spread"]["p"]))
        else:
            print("  %-16s %s" % (k, v))

    with open("/home/nvii/Sandbox/tools/evidence-results.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print("written to /home/nvii/Sandbox/tools/evidence-results.json")
