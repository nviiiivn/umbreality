#!/usr/bin/env python3
"""The true map — drawn from where things actually are.

The old hand-drawn maps are kept as historical record: a map made with worse
information is still a real document, and how a place was once believed to
look is part of its history. This one is different. It is redrawn on every
deploy from the live geography and from what is actually standing in each
place, so it is never out of date and never flattering.

Distances here are the distances sparks pay to cross. A hearth on the outer
belt is genuinely far from the Forum, and the drawing says so.

Lives in the project, not /tmp - the deploy pipeline used to depend on
scratch files that got cleared, which broke it silently.
"""
import json
import os
import sqlite3
import sys

PROJECT = "/home/nvii/projects/spark-world/umbreality-ai"
os.chdir(PROJECT)
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

from temple.cartographer import GEOGRAPHY, _sync_geography

_sync_geography()

OUT = "vault/images/world-true.svg"
W, H = 1900, 1200

# ── what stands where ────────────────────────────────────────────────
built = {}
try:
    c = sqlite3.connect("temple/soul.db", timeout=20)
    for name, st, ar in c.execute(
            "SELECT board_name, structures, artifacts FROM board_state"):
        try:
            built[name] = len(json.loads(st or "[]")) + len(json.loads(ar or "[]"))
        except ValueError:
            built[name] = 0
    c.close()
except sqlite3.Error as e:
    print("could not read what is built: %s" % e)

# ── where everyone is standing ───────────────────────────────────────
here = {}
try:
    c = sqlite3.connect("temple/cartographer.db", timeout=20)
    for board, cnt in c.execute("SELECT current_board, COUNT(*) FROM explorers "
                                "GROUP BY 1"):
        here[board] = cnt
    c.close()
except sqlite3.Error:
    pass

# ── the shrines, so the road is visible ──────────────────────────────
shrine_at = {}
try:
    from temple.pilgrimage import SHRINES
    shrine_at = {s["board"]: s for s in SHRINES}
except Exception:
    pass

# ── projection ───────────────────────────────────────────────────────
pts = {k: (v.get("x", 0), v.get("y", 0)) for k, v in GEOGRAPHY.items()}
if not pts:
    raise SystemExit("no geography to draw")
xs = [p[0] for p in pts.values()]
ys = [p[1] for p in pts.values()]
minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
padx, pady = 150, 120


def project(x, y):
    sx = (x - minx) / (maxx - minx or 1)
    sy = (y - miny) / (maxy - miny or 1)
    return (round(padx + sx * (W - 2 * padx)),
            round(pady + sy * (H - 2 * pady)))


FOUNDING = {"forum", "uruk", "library", "monastery", "temple", "coliseum",
            "bazaar", "lyceum", "press", "gnu", "god", "the-whole-system"}

COL_HEARTH = "#9d8ae0"
COL_SITE = "#d9c98a"
COL_WILD = "#d17777"
COL_SHRINE = "#7fd1c4"
COL_INK = "#eeebf6"

s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
     'viewBox="0 0 %d %d" font-family="Georgia,serif">' % (W, H, W, H),
     '<defs><radialGradient id="bg" cx="48%" cy="42%" r="75%">'
     '<stop offset="0%" stop-color="#1a1726"/>'
     '<stop offset="100%" stop-color="#12101a"/></radialGradient></defs>',
     '<rect width="%d" height="%d" fill="url(#bg)"/>' % (W, H)]

# ── the Wild, which is not a settlement ──────────────────────────────
if "the-wild" in pts:
    wx, wy = project(*pts["the-wild"])
    s += ['<circle cx="%d" cy="%d" r="190" fill="%s" opacity="0.06"/>'
          % (wx, wy, COL_WILD),
          '<circle cx="%d" cy="%d" r="190" fill="none" stroke="%s" '
          'stroke-width="1.2" stroke-dasharray="10 12" opacity="0.45"/>'
          % (wx, wy, COL_WILD),
          '<text x="%d" y="%d" fill="%s" font-size="19" font-style="italic" '
          'text-anchor="middle" opacity="0.8">The Wild</text>'
          % (wx, wy - 205, COL_WILD),
          '<text x="%d" y="%d" fill="%s" font-size="12" text-anchor="middle" '
          'opacity="0.6">nothing built · something always watching</text>'
          % (wx, wy - 188, COL_WILD)]

# ── the hearths, sized by what has been raised in them ───────────────
s.append("<g>")
for name in sorted(pts):
    if not name.startswith("hearth-"):
        continue
    x, y = project(*pts[name])
    b = built.get(name, 0)
    r = 5 + min(b, 6)
    op = 0.10 if not b else min(0.45 + b * 0.06, 0.85)
    s.append('<circle cx="%d" cy="%d" r="%d" fill="%s" fill-opacity="%.2f" '
             'stroke="%s" stroke-width="1"><title>%s — %d built</title></circle>'
             % (x, y, r, COL_HEARTH, op, COL_HEARTH, name, b))
    if b:
        s.append('<text x="%d" y="%d" fill="%s" font-size="9" '
                 'text-anchor="middle" font-family="monospace">%d</text>'
                 % (x, y + 3, COL_INK, b))
s.append("</g>")

# ── the built places ─────────────────────────────────────────────────
s.append("<g>")
for name in sorted(pts):
    if name.startswith("hearth-") or name == "the-wild":
        continue
    x, y = project(*pts[name])
    g = GEOGRAPHY.get(name, {})
    pretty = g.get("name", name.replace("-", " ").title())
    b = built.get(name, 0)
    standing = here.get(name, 0)
    founding = name in FOUNDING
    r = (14 if founding else 9) + min(b // 3, 8)
    col = COL_SHRINE if name in shrine_at else COL_SITE
    s.append('<circle cx="%d" cy="%d" r="%d" fill="%s" fill-opacity="0.16" '
             'stroke="%s" stroke-width="%s"><title>%s — %d built, %d here</title>'
             '</circle>'
             % (x, y, r, col, col, "2" if founding else "1.2",
                pretty, b, standing))
    if name in shrine_at:
        s.append('<circle cx="%d" cy="%d" r="%d" fill="none" stroke="%s" '
                 'stroke-width="1" stroke-dasharray="3 4" opacity="0.7"/>'
                 % (x, y, r + 6, COL_SHRINE))
    s.append('<text x="%d" y="%d" fill="%s" font-size="%d" '
             'text-anchor="middle">%s</text>'
             % (x, y - r - 9, COL_INK, 16 if founding else 12, pretty))
    bits = []
    if b:
        bits.append("%d built" % b)
    if standing:
        bits.append("%d here" % standing)
    if name in shrine_at:
        bits.append(shrine_at[name]["blessing"])
    if bits:
        s.append('<text x="%d" y="%d" fill="%s" font-size="10" '
                 'text-anchor="middle" opacity="0.65">%s</text>'
                 % (x, y + r + 15, COL_INK, " · ".join(bits)))
s.append("</g>")

# ── legend ───────────────────────────────────────────────────────────
s += ['<g opacity="0.75">',
      '<text x="40" y="%d" fill="%s" font-size="13">Drawn from the live '
      'world. Circles grow with what has been raised there.</text>'
      % (H - 58, COL_INK),
      '<text x="40" y="%d" fill="%s" font-size="12">Dashed ring — a shrine '
      'stands here. Violet — a hearth. The distances are the ones sparks '
      'pay to cross.</text>' % (H - 38, COL_SHRINE),
      '</g>', '</svg>']

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(s))
print("wrote %s/%s (%d bytes, %d places, %d shrines)"
      % (PROJECT, OUT, os.path.getsize(OUT), len(pts), len(shrine_at)))
