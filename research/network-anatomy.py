#!/usr/bin/env python3
"""Who the hubs are, and whether they got there honestly."""
import sqlite3, statistics, sys
from collections import defaultdict, Counter
sys.path.insert(0, "/home/nvii/projects/spark-world/umbreality-ai")
B = "/home/nvii/projects/spark-world/umbreality-ai/"

s = sqlite3.connect(B+"temple/soul.db"); s.row_factory = sqlite3.Row
rel = [dict(r) for r in s.execute(
    "SELECT spark1, spark2, bond_type, strength, created_at FROM relationships "
    "WHERE spark1 IS NOT NULL AND spark2 IS NOT NULL AND spark1 != spark2")]
deg = Counter()
adj = defaultdict(set)
for r in rel:
    deg[r["spark1"]] += 1; deg[r["spark2"]] += 1
    adj[r["spark1"]].add(r["spark2"]); adj[r["spark2"]].add(r["spark1"])

f = sqlite3.connect(B+"forum/forum.db")
posts = dict(f.execute("SELECT author, COUNT(*) FROM posts GROUP BY author"))
scores = {r[0]: r[1] for r in f.execute("SELECT agent_name, power_level FROM agent_scores")}

vals = sorted(deg.values())
print("BONDS PER SPARK")
print("  median %d   mean %.1f   max %d   top 5%% hold %.0f%% of all bonds"
      % (vals[len(vals)//2], statistics.mean(vals), vals[-1],
         100.0*sum(vals[-len(vals)//20:])/sum(vals)))
print()
print("THE HUBS")
print("  %-24s %6s %8s %9s  %s" % ("spark","bonds","posts","power","bond types"))
for name, d in deg.most_common(12):
    types = Counter(r["bond_type"] for r in rel if name in (r["spark1"], r["spark2"]))
    print("  %-24s %6d %8d %9.1f  %s" % (name, d, posts.get(name,0),
          scores.get(name,0), dict(types.most_common(3))))

print()
print("DID POSTING CAUSE THE BONDS?")
common = [n for n in deg if n in posts]
if len(common) > 10:
    xs = [posts[n] for n in common]; ys = [deg[n] for n in common]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((a-mx)*(b-my) for a,b in zip(xs,ys))
    den = (sum((a-mx)**2 for a in xs)*sum((b-my)**2 for b in ys))**0.5
    print("  correlation between posts written and bonds held: r = %.3f" % (num/den if den else 0))
    print("  (high r would mean bonds are just a by-product of talking a lot)")

print()
print("HOW BONDS GET MADE")
print(" ", dict(Counter(r["bond_type"] for r in rel).most_common()))
print()
print("WHEN")
by_day = Counter((r["created_at"] or "?")[:10] for r in rel)
for d, n in sorted(by_day.items())[-8:]:
    print("   %s  %4d" % (d, n))

print()
print("ISOLATED / NEARLY ISOLATED")
allsparks = [r[0] for r in s.execute("SELECT spark_name FROM spark_state")]
lonely = sorted((deg.get(n,0), n) for n in allsparks)[:8]
print(" ", [(n,d) for d,n in lonely])
s.close(); f.close()
