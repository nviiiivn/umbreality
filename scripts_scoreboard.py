#!/usr/bin/env python3
"""Does the trading actually work, or does it just look busy?

160 trades and a portfolio up 0.75%. That number on its own means nothing:
if simply buying the same assets and sitting still would have made more, the
strategies are worse than doing nothing and every trade is noise with fees
attached.

So this measures the only comparison that matters - the strategies against
holding - plus, per strategy, whether it wins more than it loses and how far
down it has ever taken the account.

The point is to know the answer before any real money is anywhere near it.
An honest negative result is worth more here than an encouraging one, since
the encouraging one is what costs you money.
"""
import os
import sqlite3
from collections import defaultdict

os.chdir("/home/nvii/projects/spark-world/umbreality-ai")
PORT = "sim/portfolio.db"
START_CASH = 10000.0


def rows(sql, args=()):
    c = sqlite3.connect(PORT, timeout=30)
    c.row_factory = sqlite3.Row
    out = [dict(r) for r in c.execute(sql, args)]
    c.close()
    return out


trades = rows("SELECT * FROM trades ORDER BY id")
state = rows("SELECT * FROM portfolio_state LIMIT 1")
if not trades:
    raise SystemExit("no trades yet")

now_value = float(state[0]["total_value"]) if state else START_CASH
first, last = trades[0]["timestamp"], trades[-1]["timestamp"]

print("=" * 70)
print("THE ACCOUNT")
print("=" * 70)
print("  started with     ${:,.2f}".format(START_CASH))
print("  worth now        ${:,.2f}".format(now_value))
print("  return           %+.2f%%" % ((now_value / START_CASH - 1) * 100))
print("  trades           %d" % len(trades))
print("  first trade      %s" % first)
print("  latest trade     %s" % last)

# ── what holding would have done ─────────────────────────────────────
# buy each symbol the strategies ever touched, equally weighted, at the
# first price we ever saw for it; value it at the last price we ever saw
firstpx, lastpx = {}, {}
for t in trades:
    s = t["symbol"]
    if s not in firstpx:
        firstpx[s] = float(t["price"] or 0)
    lastpx[s] = float(t["price"] or 0)

# price_history is better if it has more recent marks
for r in rows("SELECT symbol, price FROM price_history ORDER BY id"):
    s = r["symbol"]
    if s not in firstpx:
        firstpx[s] = float(r["price"] or 0)
    lastpx[s] = float(r["price"] or 0)

syms = [s for s in firstpx if firstpx[s] > 0]
if syms:
    each = START_CASH / len(syms)
    held = sum(each * (lastpx[s] / firstpx[s]) for s in syms)
    print()
    print("=" * 70)
    print("AGAINST DOING NOTHING")
    print("=" * 70)
    print("  buy all %d equally on day one and never touch it:" % len(syms))
    print("    would be worth ${:,.2f}   ({:+.2f}%)".format(
        held, (held / START_CASH - 1) * 100))
    print("  the strategies:")
    print("    are worth      ${:,.2f}   ({:+.2f}%)".format(
        now_value, (now_value / START_CASH - 1) * 100))
    diff = now_value - held
    print()
    if diff > 0:
        print("  >>> trading is AHEAD of holding by ${:,.2f} ({:+.2f}%)".format(
            diff, diff / START_CASH * 100))
    else:
        print("  >>> trading is BEHIND holding by ${:,.2f} ({:.2f}%).".format(
            abs(diff), diff / START_CASH * 100))
        print("      On this record the strategies are worse than sitting "
              "still. Do not put real money behind them.")
    print()
    print("  per symbol, first seen -> last seen:")
    for s in sorted(syms):
        print("    %-8s %10.4f -> %10.4f   %+.1f%%"
              % (s, firstpx[s], lastpx[s],
                 (lastpx[s] / firstpx[s] - 1) * 100))

# ── per strategy ─────────────────────────────────────────────────────
print()
print("=" * 70)
print("PER STRATEGY")
print("=" * 70)
by = defaultdict(lambda: {"buys": 0, "sells": 0, "pnl": 0.0,
                          "wins": 0, "losses": 0})
for t in trades:
    k = t.get("strategy") or "unnamed"
    b = by[k]
    if (t["action"] or "").lower() == "buy":
        b["buys"] += 1
    else:
        b["sells"] += 1
    p = float(t.get("pnl") or 0)
    b["pnl"] += p
    if p > 0:
        b["wins"] += 1
    elif p < 0:
        b["losses"] += 1

print("  %-18s %6s %6s %8s %8s %10s" %
      ("strategy", "buys", "sells", "wins", "losses", "realised"))
for k in sorted(by, key=lambda x: -by[x]["pnl"]):
    b = by[k]
    print("  %-18s %6d %6d %8d %8d %10.2f"
          % (k, b["buys"], b["sells"], b["wins"], b["losses"], b["pnl"]))

closed = sum(b["wins"] + b["losses"] for b in by.values())
if not closed:
    print()
    print("  NOTE: every trade records pnl = 0. Nothing has been marked as a")
    print("  win or a loss, so win rate cannot be computed and the strategy")
    print("  table above is only counting activity, not success. That needs")
    print("  fixing before any of this can be trusted.")

# ── how far down it has been ─────────────────────────────────────────
hist = rows("SELECT * FROM pnl_history ORDER BY id")
if hist:
    key = "total_value" if "total_value" in hist[0] else None
    if not key:
        for cand in ("value", "equity", "balance", "pnl"):
            if cand in hist[0]:
                key = cand
                break
    if key:
        peak, worst = START_CASH, 0.0
        for h in hist:
            v = float(h.get(key) or 0)
            peak = max(peak, v)
            if peak:
                worst = min(worst, (v - peak) / peak)
        print()
        print("=" * 70)
        print("WORST IT HAS BEEN")
        print("=" * 70)
        print("  deepest drop from a high: %.2f%%" % (worst * 100))
        print("  (%d marks recorded)" % len(hist))
else:
    print()
    print("  No value history is being recorded, so drawdown cannot be")
    print("  measured. That is the second thing to fix.")
