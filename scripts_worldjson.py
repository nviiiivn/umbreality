#!/usr/bin/env python3
"""The world as data, for a real map to draw.

The SVG map is a picture: it cannot be panned, zoomed, clicked, filtered or
asked a question. This emits the same world as JSON so a slippy map can be
built over it - every place with its coordinates, what stands there, who is
standing in it, whether a shrine or a cross is on that ground, and the roads
that have actually been walked between places.

Roads here are real. A line between two places means somebody made that
journey and paid the cycles for it, and its weight is how many times.

Read-only. Regenerated on every deploy.
"""
import datetime
import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict

PROJECT = "/home/nvii/projects/spark-world/umbreality-ai"
os.chdir(PROJECT)
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

OUT = "vault/world.json"


def q(db, sql, args=()):
    try:
        c = sqlite3.connect(db, timeout=30)
        c.row_factory = sqlite3.Row
        r = [dict(x) for x in c.execute(sql, args)]
        c.close()
        return r
    except sqlite3.Error as e:
        print("  ! %s: %s" % (db, e))
        return []


SOUL = "temple/soul.db"
CARTO = "temple/cartographer.db"
PILG = "temple/pilgrimage.db"
OMEN = "temple/omens.db"

from temple.cartographer import GEOGRAPHY, _sync_geography
_sync_geography()

try:
    from temple.pilgrimage import SHRINES
except Exception as e:
    print("  ! shrines: %s" % e)
    SHRINES = []
shrine_at = {s["board"]: s for s in SHRINES}

crosses = {}
for d in q(OMEN, "SELECT name, sin, board, omen FROM dead"):
    crosses.setdefault(d["board"], []).append(d)

# ── who is standing where ────────────────────────────────────────────
real = {r["spark_name"] for r in q(SOUL, "SELECT spark_name FROM spark_state")}
present = defaultdict(list)
for r in q(CARTO, "SELECT agent, current_board, COALESCE(cycles_traveled,0) t "
                  "FROM explorers"):
    if r["agent"] in real:
        present[r["current_board"]].append(
            {"name": r["agent"], "travelled": r["t"]})

# ── what stands in each place ────────────────────────────────────────
built, lore = {}, {}
for r in q(SOUL, "SELECT board_name, structures, artifacts, lore FROM board_state"):
    try:
        built[r["board_name"]] = {
            "structures": json.loads(r["structures"] or "[]"),
            "artifacts": json.loads(r["artifacts"] or "[]"),
        }
        lore[r["board_name"]] = json.loads(r["lore"] or "[]")
    except ValueError:
        built[r["board_name"]] = {"structures": [], "artifacts": []}
        lore[r["board_name"]] = []

# ── open work, by where it is meant to happen ────────────────────────
work = Counter()
for r in q(SOUL, "SELECT domain_id FROM ambitions WHERE resolved=0 "
                 "AND domain_id != ''"):
    work[r["domain_id"]] += 1

# ── the roads that have actually been walked ─────────────────────────
roads = Counter()
for r in q(CARTO, "SELECT from_board, to_board FROM journeys "
                  "WHERE from_board IS NOT NULL AND to_board IS NOT NULL"):
    a, b = r["from_board"], r["to_board"]
    if a and b and a != b:
        roads[tuple(sorted((a, b)))] += 1

FOUNDING = {"forum", "uruk", "library", "monastery", "temple", "coliseum",
            "bazaar", "lyceum", "press", "gnu", "god", "the-whole-system"}

places = []
for name, g in sorted(GEOGRAPHY.items()):
    b = built.get(name, {"structures": [], "artifacts": []})
    kind = ("wild" if name == "the-wild"
            else "hearth" if name.startswith("hearth-")
            else "founding" if name in FOUNDING else "site")
    places.append({
        "id": name,
        "name": g.get("name", name.replace("-", " ").title()),
        "x": g.get("x", 0), "y": g.get("y", 0),
        "kind": kind,
        "region": g.get("region", "inner"),
        "terrain": g.get("terrain", "settlement"),
        "architecture": g.get("architecture", ""),
        "description": g.get("description", ""),
        "structures": [{"name": s.get("name"), "type": s.get("type", "built"),
                        "by": s.get("created_by"), "note": s.get("note", "")}
                       for s in b["structures"]],
        "artifacts": [{"name": s.get("name"), "type": s.get("type", "made"),
                       "by": s.get("created_by")} for s in b["artifacts"]],
        "here": sorted(present.get(name, []), key=lambda p: -p["travelled"]),
        "population": len(present.get(name, [])),
        "open_work": work.get(name, 0),
        "shrine": shrine_at.get(name),
        "crosses": crosses.get(name, []),
        "lore": [x.get("event", "") for x in lore.get(name, [])][-6:],
    })

world = {
    "generated": datetime.datetime.now().astimezone().isoformat(),
    "places": places,
    "roads": [{"a": a, "b": b, "walked": n} for (a, b), n in
              sorted(roads.items(), key=lambda kv: -kv[1])],
    "totals": {
        "places": len(places),
        "sparks": len(real),
        "standing": sum(len(v) for v in present.values()),
        "structures": sum(len(b["structures"]) for b in built.values()),
        "artifacts": sum(len(b["artifacts"]) for b in built.values()),
        "shrines": len(SHRINES),
        "crosses": sum(len(v) for v in crosses.values()),
        "journeys": sum(roads.values()),
    },
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(world, f, ensure_ascii=False)
print("wrote %s/%s (%d bytes)" % (PROJECT, OUT, os.path.getsize(OUT)))
for k, v in world["totals"].items():
    print("  %-12s %s" % (k, v))
