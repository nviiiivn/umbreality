"""Persistent Portfolio — SQLite-backed real trade tracking.
Every trade is recorded. Day-over-day growth is real, not random rerolls.
Supports multi-strategy allocation with historical P&L."""

import sqlite3, json, datetime, random, math, hashlib
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "portfolio.db"


def _get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS portfolio_state (
        id INTEGER PRIMARY KEY CHECK(id=1),
        cash REAL DEFAULT 10000.0,
        total_value REAL DEFAULT 10000.0,
        last_updated TEXT,
        version INTEGER DEFAULT 1
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL UNIQUE,
        shares REAL DEFAULT 0,
        avg_cost REAL DEFAULT 0,
        current_value REAL DEFAULT 0
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT DEFAULT (datetime('now')),
        symbol TEXT NOT NULL,
        action TEXT NOT NULL CHECK(action IN ('buy','sell')),
        shares REAL NOT NULL,
        price REAL NOT NULL,
        total REAL NOT NULL,
        strategy TEXT DEFAULT 'manual',
        pnl REAL DEFAULT 0
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS pnl_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT DEFAULT (datetime('now')),
        total_value REAL NOT NULL,
        cash REAL NOT NULL,
        daily_pnl REAL DEFAULT 0,
        total_pnl REAL DEFAULT 0,
        strategy TEXT DEFAULT 'overall'
    )""")
    # Initialize portfolio state if not exists
    if not conn.execute("SELECT id FROM portfolio_state").fetchone():
        conn.execute("INSERT INTO portfolio_state (cash, total_value, last_updated) VALUES (10000, 10000, datetime('now'))")
        conn.commit()
    conn.close()


def get_state() -> dict:
    _get_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    state = dict(conn.execute("SELECT * FROM portfolio_state WHERE id=1").fetchone() or {})
    holdings = [dict(r) for r in conn.execute("SELECT * FROM holdings").fetchall()]
    recent_trades = [dict(r) for r in conn.execute("SELECT * FROM trades ORDER BY timestamp DESC LIMIT 20").fetchall()]
    pnl = [dict(r) for r in conn.execute("SELECT * FROM pnl_history ORDER BY timestamp DESC LIMIT 30").fetchall()]
    conn.close()
    return {
        "state": state,
        "holdings": holdings,
        "recent_trades": recent_trades,
        "pnl_history": pnl,
    }


BASE_PRICES = {"BTC": 85000, "ETH": 3200, "SOL": 145, "DOGE": 0.12, "UMB": 1.0}
SYMBOLS = ["BTC", "ETH", "SOL", "DOGE", "UMB"]

_series_cache = {}


def _character(symbol: str) -> dict:
    """What kind of thing this symbol is, fixed for the life of the world.

    Each one gets its own drift, volatility and regime length, so they do
    not all move together and a strategy that suits one need not suit
    another.
    """
    seed = int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    return {
        "base": BASE_PRICES.get(symbol, 50),
        # centred: no symbol is free money in either direction. the first
        # version drifted almost everything upward, which made buy-and-hold
        # unbeatable by construction and told us nothing about the strategies
        "drift": rng.uniform(-0.0022, 0.0022),    # slow direction
        "vol": rng.uniform(0.012, 0.040),         # day to day noise
        "regime": rng.randint(11, 29),            # length of a swing, in days
        "amp": rng.uniform(0.10, 0.28),           # how far a swing carries
        "pull": rng.uniform(0.10, 0.26),          # how hard it returns
    }


def price_series(symbol: str, upto_day: int) -> list:
    """Every price this symbol has had, from day 0 to upto_day.

    Deterministic: the same day always yields the same price, so history
    never rewrites itself. Path-dependent: the price follows an anchor that
    trends and swings while being pulled back toward it, which gives
    momentum real trends to find and mean reversion real deviations to
    fade. The old series was noise around a constant, where momentum could
    never be right and mean reversion could not be wrong.
    """
    upto_day = max(0, int(upto_day))
    key = (symbol, upto_day)
    if key in _series_cache:
        return _series_cache[key]

    c = _character(symbol)
    seed = int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)
    out = []
    p = c["base"]
    for d in range(upto_day + 1):
        rng = random.Random((seed ^ (d * 2654435761)) & 0xFFFFFFFF)
        anchor = c["base"] * (1.0 + c["drift"] * d
                              + c["amp"] * math.sin(2 * math.pi * d / c["regime"]))
        p = p * (1.0 + rng.gauss(0, 1) * c["vol"])
        p += (anchor - p) * c["pull"]
        p = max(c["base"] * 0.02, p)
        out.append(round(p, 6 if c["base"] < 10 else 2))

    _series_cache.clear() if len(_series_cache) > 400 else None
    _series_cache[key] = out
    return out


def world_day() -> int:
    """The world's own day. Prices move with it, not with the wall clock."""
    try:
        from temple.heartbeat import get_time
        return int(get_time().get("day", 0))
    except Exception as e:
        print("[market] no world time (%s), falling back to the calendar" % e,
              flush=True)
        return datetime.date.today().toordinal()


def get_price(symbol: str, day: int = None) -> float:
    """Today's price for a symbol, in world time.

    This used to key on the real calendar date while record_daily_prices
    stamped rows with the world day, so several world days inside one real
    day all recorded the same number and the series came out flat.
    """
    d = world_day() if day is None else int(day)
    return price_series(symbol, d)[d]


def execute_trade(symbol: str, action: str, strategy: str = "manual",
                  confidence: float = None) -> dict:
    """Buy or sell within one strategy's own book.

    Each strategy holds its own cash and its own positions. Sharing them, as
    this used to, made per-strategy profit an accident of which strategy
    happened to place the closing trade.

    confidence sizes the position: a strategy that is barely sure commits
    less than one that is certain. Left as None it falls back to the old
    arbitrary sizing, so existing callers behave as they did.
    """
    _get_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    day = world_day()
    price = get_price(symbol, day)

    book = conn.execute("SELECT * FROM strategy_books WHERE strategy=?",
                        (strategy,)).fetchone()
    if not book:
        # a caller outside the experiment - keep the old shared pot
        state = conn.execute("SELECT * FROM portfolio_state WHERE id=1").fetchone()
        cash = float(state["cash"]) if state else 0.0
        shared = True
    else:
        cash = float(book["cash"])
        shared = False

    out = {"symbol": symbol, "action": action, "strategy": strategy,
           "price": price, "day": day}

    if action == "buy":
        if cash <= 1:
            conn.close()
            out.update({"action": "hold", "reason": "no cash in this book"})
            return out
        frac = (0.06 + 0.24 * max(0.0, min(confidence, 1.0))
                if confidence is not None else random.uniform(0.1, 0.3))
        total = round(min(cash * frac, cash * 0.95), 2)
        shares = round(total / price, 6)
        if shares <= 0:
            conn.close()
            out.update({"action": "hold", "reason": "position too small"})
            return out
        existing = conn.execute(
            "SELECT * FROM holdings WHERE symbol=? AND strategy=?",
            (symbol, strategy)).fetchone()
        if existing:
            new_shares = existing["shares"] + shares
            new_cost = ((existing["avg_cost"] * existing["shares"]
                         + price * shares) / new_shares)
            conn.execute("UPDATE holdings SET shares=?, avg_cost=?, current_value=? "
                         "WHERE symbol=? AND strategy=?",
                         (new_shares, new_cost, new_shares * price, symbol, strategy))
        else:
            conn.execute("INSERT INTO holdings (symbol, shares, avg_cost, "
                         "current_value, strategy) VALUES (?,?,?,?,?)",
                         (symbol, shares, price, shares * price, strategy))
        cash -= total
        pnl = 0.0

    elif action == "sell":
        holding = conn.execute(
            "SELECT * FROM holdings WHERE symbol=? AND strategy=?",
            (symbol, strategy)).fetchone()
        if not holding or holding["shares"] <= 0:
            conn.close()
            out.update({"action": "hold", "reason": "nothing held to sell"})
            return out
        frac = (0.25 + 0.65 * max(0.0, min(confidence, 1.0))
                if confidence is not None else random.uniform(0.3, 1.0))
        shares = round(holding["shares"] * frac, 6)
        total = round(shares * price, 2)
        pnl = round(total - shares * holding["avg_cost"], 2)
        left = round(holding["shares"] - shares, 6)
        if left <= 0:
            conn.execute("DELETE FROM holdings WHERE symbol=? AND strategy=?",
                         (symbol, strategy))
        else:
            conn.execute("UPDATE holdings SET shares=?, current_value=? "
                         "WHERE symbol=? AND strategy=?",
                         (left, left * price, symbol, strategy))
        cash += total

    else:
        conn.close()
        out.update({"action": "hold", "reason": "unknown action %r" % action})
        return out

    conn.execute("INSERT INTO trades (timestamp, symbol, action, shares, price, "
                 "total, strategy, pnl) VALUES (datetime('now'),?,?,?,?,?,?,?)",
                 (symbol, action, shares, price, total, strategy, pnl))
    if shared:
        conn.execute("UPDATE portfolio_state SET cash=?, last_updated=datetime('now') "
                     "WHERE id=1", (round(cash, 2),))
    else:
        conn.execute("UPDATE strategy_books SET cash=? WHERE strategy=?",
                     (round(cash, 2), strategy))
    conn.commit()
    conn.close()

    out.update({"shares": shares, "total": total, "pnl": pnl,
                "cash_left": round(cash, 2)})
    return out


# Which strategies are being tried. Drop a name from here to trim one that
# has proved itself useless; the record of what it did is kept either way.
# buy_and_hold is the control arm. If the clever ones cannot beat sitting
# still, that is the result, and it belongs in the same table as everything
# else rather than being something only a backtest knows.
ACTIVE_STRATEGIES = ["momentum", "mean_reversion", "buy_and_hold"]


def strategy_signal(name: str, prices: list, strategy: str = None,
                    symbol: str = None) -> dict:
    """Ask one strategy what it makes of a price history.

    These live in sim/strategies.py, are properly written, and until now had
    never once been imported.
    """
    from sim import strategies as _s
    if name == "momentum":
        return _s.momentum_strategy(prices)
    if name == "mean_reversion":
        return _s.mean_reversion_strategy(prices)
    if name == "buy_and_hold":
        # The control arm. It buys once and then holds - the first version
        # tested len(prices) <= 26 against a world already on day 26, so it
        # never bought at all and would have "won" every comparison by
        # sitting in cash and risking nothing.
        held = False
        if strategy and symbol:
            conn = sqlite3.connect(str(DB_PATH))
            row = conn.execute("SELECT shares FROM holdings WHERE symbol=? "
                               "AND strategy=?", (symbol, strategy)).fetchone()
            conn.close()
            held = bool(row and row[0] > 0)
        if held:
            return {"signal": "HOLD", "confidence": 0.9,
                    "reason": "control arm, holding"}
        return {"signal": "BUY", "confidence": 0.9,
                "reason": "control arm, taking the position"}
    return {"signal": "HOLD", "confidence": 0.0, "reason": "unknown strategy"}


def open_books(total: float = None) -> dict:
    """Fund one book per active strategy, splitting the pot evenly.

    Without separate books the strategies trade the same holdings and the
    profit lands on whoever placed the closing trade, which makes the
    performance table an artefact of ordering rather than a measurement.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    if total is None:
        row = conn.execute("SELECT cash FROM portfolio_state WHERE id=1").fetchone()
        total = float(row["cash"]) if row else 0.0
    have = {r["strategy"] for r in conn.execute("SELECT strategy FROM strategy_books")}
    missing = [s for s in ACTIVE_STRATEGIES if s not in have]
    if not missing:
        conn.close()
        return {"opened": 0, "books": sorted(have)}
    each = round(total / len(missing), 2) if missing else 0.0
    for s in missing:
        conn.execute("INSERT INTO strategy_books (strategy, cash, started_with) "
                     "VALUES (?,?,?)", (s, each, each))
    conn.execute("UPDATE portfolio_state SET cash=0 WHERE id=1")
    conn.commit()
    conn.close()
    return {"opened": len(missing), "each": each, "books": missing}


def book_cash(strategy: str) -> float:
    conn = sqlite3.connect(str(DB_PATH))
    row = conn.execute("SELECT cash FROM strategy_books WHERE strategy=?",
                       (strategy,)).fetchone()
    conn.close()
    return float(row[0]) if row else 0.0


def book_value(strategy: str, day: int = None) -> dict:
    """What one strategy's book is worth right now."""
    d = world_day() if day is None else day
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM strategy_books WHERE strategy=?",
                       (strategy,)).fetchone()
    if not row:
        conn.close()
        return {"strategy": strategy, "exists": False}
    held = 0.0
    positions = {}
    for h in conn.execute("SELECT * FROM holdings WHERE strategy=? AND shares>0",
                          (strategy,)):
        v = h["shares"] * get_price(h["symbol"], d)
        held += v
        positions[h["symbol"]] = round(v, 2)
    conn.close()
    cash = float(row["cash"])
    start = float(row["started_with"])
    total = cash + held
    return {"strategy": strategy, "exists": True, "cash": round(cash, 2),
            "invested": round(held, 2), "total": round(total, 2),
            "started_with": round(start, 2),
            "return_pct": round(100.0 * (total - start) / start, 2) if start else None,
            "positions": positions}


def run_strategy_cycle() -> dict:
    """One cycle: record prices, ask each strategy, act within its own book.

    What stood here decided with `rng.random() * 2 - 1` and called the
    result momentum. It never read a price. That coin flip made the 204
    trades on the books before this.
    """
    record_daily_prices()
    open_books()
    day = world_day()
    results = []

    for name in ACTIVE_STRATEGIES:
        for symbol in SYMBOLS:
            prices = price_series(symbol, day)
            sig = strategy_signal(name, prices, strategy=name, symbol=symbol)
            action = (sig.get("signal") or "HOLD").lower()
            if action not in ("buy", "sell"):
                results.append({"symbol": symbol, "strategy": name,
                                "action": "hold", "reason": sig.get("reason")})
                continue
            r = execute_trade(symbol, action, name,
                              confidence=float(sig.get("confidence") or 0.0))
            r.setdefault("reason", sig.get("reason"))
            results.append(r)

    acted = [r for r in results if r.get("action") in ("buy", "sell")]
    return {"trades": results, "acted": len(acted), "day": day,
            "books": {n: book_value(n, day) for n in ACTIVE_STRATEGIES},
            "portfolio": get_state()["state"]}


def strategy_performance() -> dict:
    """What each strategy has actually done with its own money.

    Total value against what the book was funded with - the only comparison
    that means anything once each strategy trades separately. Realised
    profit is reported beside it, and the number of closed positions,
    because a strategy with four closes has not been tested however good its
    percentage looks.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    realised = {r["strategy"]: r for r in conn.execute(
        "SELECT strategy, COUNT(*) n, "
        "       SUM(CASE WHEN action='sell' THEN 1 ELSE 0 END) closes, "
        "       ROUND(SUM(COALESCE(pnl,0)), 2) pnl, "
        "       SUM(CASE WHEN COALESCE(pnl,0) > 0 THEN 1 ELSE 0 END) wins "
        "FROM trades GROUP BY strategy")}
    books = [r["strategy"] for r in conn.execute(
        "SELECT strategy FROM strategy_books")]
    conn.close()

    out = []
    for name in books:
        v = book_value(name)
        r = realised.get(name)
        closes = (r["closes"] if r else 0) or 0
        out.append({
            "strategy": name,
            "started_with": v.get("started_with"),
            "worth_now": v.get("total"),
            "return_pct": v.get("return_pct"),
            "cash": v.get("cash"),
            "positions": v.get("positions"),
            "trades": (r["n"] if r else 0),
            "closes": closes,
            "realised": (r["pnl"] if r else 0.0),
            "win_rate": round((r["wins"] or 0) / closes, 3) if closes else None,
            "tested": closes >= 30,
        })
    out.sort(key=lambda x: -(x["return_pct"] if x["return_pct"] is not None else -999))

    historical = [{"strategy": k, "trades": v["n"], "realised": v["pnl"],
                   "note": "closed book, not part of the live comparison"}
                  for k, v in realised.items() if k not in books]
    return {"live": out, "historical": historical,
            "note": "return_pct is book value against what it was funded with; "
                    "fewer than 30 closes is not yet evidence of anything"}


def get_growth_curve() -> list:
    """Return the full PnL history for charting."""
    _get_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    history = [dict(r) for r in conn.execute(
        "SELECT timestamp, total_value, total_pnl FROM pnl_history ORDER BY timestamp ASC LIMIT 365"
    ).fetchall()]
    conn.close()
    return history

# ── Price History & Auto-Trade ──

def record_price(symbol: str, price: float, day: int = 0):
    """Record a price snapshot into history."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("INSERT INTO price_history (symbol, price, day_number) VALUES (?,?,?)",
                 (symbol, price, day))
    conn.commit()
    conn.close()


def get_price_history(symbol: str, days: int = 30) -> list:
    """Get historical prices for a symbol."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM price_history WHERE symbol=? ORDER BY day_number ASC LIMIT ?",
        (symbol, days)).fetchall()]
    conn.close()
    return rows


def record_daily_prices():
    """Record today's prices, once per world day.

    This existed and was never called by anything, which is why
    price_history had zero rows and every strategy that consulted it would
    have answered "insufficient data" forever.
    """
    day = world_day()
    conn = sqlite3.connect(str(DB_PATH))
    have = conn.execute("SELECT COUNT(*) FROM price_history WHERE day_number=?",
                        (day,)).fetchone()[0]
    conn.close()
    if have:
        return {"recorded": 0, "day": day, "reason": "already recorded"}
    for sym in SYMBOLS:
        record_price(sym, get_price(sym, day), day)
    return {"recorded": len(SYMBOLS), "day": day}


def backfill_price_history(days: int = None):
    """Write the history the world would have had, so strategies can start.

    The series is deterministic, so this is not invention - it is the same
    numbers record_daily_prices would have written each day had anything
    ever called it.
    """
    day = world_day() if days is None else int(days)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("DELETE FROM price_history")
    n = 0
    for sym in SYMBOLS:
        series = price_series(sym, day)
        for d, p in enumerate(series):
            conn.execute("INSERT INTO price_history (symbol, price, source, day_number) "
                         "VALUES (?,?,?,?)", (sym, p, "simulated", d))
            n += 1
    conn.commit()
    conn.close()
    return {"rows": n, "through_day": day, "symbols": len(SYMBOLS)}


def get_auto_trade_config() -> dict:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM auto_trade_config WHERE id=1").fetchone()
    conn.close()
    return dict(row) if row else {"enabled": 0}


def set_auto_trade(enabled: bool = False, strategy: str = "momentum"):
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("UPDATE auto_trade_config SET enabled=?, strategy=? WHERE id=1",
                 (1 if enabled else 0, strategy))
    conn.commit()
    conn.close()


def auto_trade_cycle() -> dict:
    """Run one auto-trade cycle. Only executes if enabled."""
    config = get_auto_trade_config()
    if not config.get("enabled"):
        return {"status": "dormant", "message": "Auto-trade is disabled"}
    
    from temple.heartbeat import get_time
    t = get_time()
    current_cycle = t.get("total_beats", 0)
    last_cycle = config.get("last_cycle_run", 0)
    
    # Only trade once per cycle
    if current_cycle <= last_cycle:
        return {"status": "skipped", "reason": "already run this cycle"}
    
    # Record prices first
    record_daily_prices()
    
    # Execute strategy
    symbols = ["BTC", "ETH", "SOL", "DOGE", "UMB"]
    results = []
    for sym in symbols:
        result = execute_trade(sym, "buy" if random.random() > 0.5 else "sell", config.get("strategy", "momentum"))
        results.append(result)
    
    # Update last run
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("UPDATE auto_trade_config SET last_cycle_run=? WHERE id=1", (current_cycle,))
    conn.commit()
    conn.close()
    
    return {"status": "traded", "trades": len(results), "cycle": current_cycle}


def get_market_overview() -> dict:
    """Return full market picture — prices, history, portfolio."""
    portfolio = get_state()
    prices = {}
    for sym in ["BTC", "ETH", "SOL", "DOGE", "UMB"]:
        history = get_price_history(sym, 7)
        prices[sym] = {
            "current": get_price(sym),
            "history": history,
            "trend": "up" if len(history) >= 2 and history[-1]["price"] > history[0]["price"] else "down",
        }
    return {
        "portfolio": portfolio.get("state", {}),
        "holdings": portfolio.get("holdings", []),
        "prices": prices,
        "recent_trades": portfolio.get("recent_trades", [])[:5],
        "auto_trade": get_auto_trade_config(),
    }
