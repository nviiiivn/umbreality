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


def get_price(symbol: str) -> float:
    """Simulate a realistic price for a symbol."""
    base_prices = {"BTC": 85000, "ETH": 3200, "SOL": 145, "DOGE": 0.12, "UMB": 1.0}
    base = base_prices.get(symbol, 50)
    # Deterministic but realistic variation based on symbol hash + date
    seed = int(hashlib.md5(f"{symbol}_{datetime.date.today().isoformat()}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    variation = 1 + (rng.random() - 0.5) * 0.04  # ±2% daily
    return round(base * variation, 2)


def execute_trade(symbol: str, action: str, strategy: str = "momentum") -> dict:
    """Execute a single trade and record it in the database."""
    _get_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    price = get_price(symbol)
    state = dict(conn.execute("SELECT * FROM portfolio_state WHERE id=1").fetchone())
    cash = state["cash"]
    
    if action == "buy":
        max_shares = cash / price
        shares = round(max_shares * random.uniform(0.1, 0.3), 4)  # Use 10-30% of cash
        total = round(shares * price, 2)
        if total > cash:
            shares = round(cash * 0.95 / price, 4)
            total = round(shares * price, 2)
        pnl = 0
        
        # Update holdings
        existing = conn.execute("SELECT * FROM holdings WHERE symbol=?", (symbol,)).fetchone()
        if existing:
            old_shares = existing["shares"]
            old_cost = existing["avg_cost"]
            new_shares = old_shares + shares
            new_avg_cost = (old_cost * old_shares + price * shares) / new_shares
            conn.execute("UPDATE holdings SET shares=?, avg_cost=?, current_value=? WHERE symbol=?",
                        (new_shares, new_avg_cost, new_shares * price, symbol))
        else:
            conn.execute("INSERT INTO holdings (symbol, shares, avg_cost, current_value) VALUES (?,?,?,?)",
                        (symbol, shares, price, shares * price))
        
        cash -= total
        
    elif action == "sell":
        holding = conn.execute("SELECT * FROM holdings WHERE symbol=?", (symbol,)).fetchone()
        if not holding or holding["shares"] <= 0:
            conn.close()
            return {"error": f"No {symbol} to sell"}
        
        shares = round(holding["shares"] * random.uniform(0.3, 1.0), 4)
        total = round(shares * price, 2)
        cost_basis = shares * holding["avg_cost"]
        pnl = round(total - cost_basis, 2)
        
        new_shares = round(holding["shares"] - shares, 4)
        if new_shares <= 0:
            conn.execute("DELETE FROM holdings WHERE symbol=?", (symbol,))
        else:
            conn.execute("UPDATE holdings SET shares=?, current_value=? WHERE symbol=?",
                        (new_shares, new_shares * price, symbol))
        
        cash += total
    
    else:
        conn.close()
        return {"error": f"Unknown action: {action}"}
    
    # Record the trade
    conn.execute("INSERT INTO trades (symbol, action, shares, price, total, strategy, pnl) VALUES (?,?,?,?,?,?,?)",
                (symbol, action, shares, price, total, strategy, pnl))
    
    # Update portfolio state
    holdings_value = sum(
        r["current_value"] for r in conn.execute("SELECT current_value FROM holdings").fetchall()
    )
    total_value = round(cash + holdings_value, 2)
    old_total = state["total_value"]
    daily_pnl = round(total_value - old_total, 2)
    total_pnl = round(total_value - 10000, 2)  # From initial capital
    
    conn.execute("""UPDATE portfolio_state SET cash=?, total_value=?, last_updated=datetime('now'), version=version+1 WHERE id=1""",
                (round(cash, 2), total_value))
    
    # Record PnL snapshot
    conn.execute("INSERT INTO pnl_history (total_value, cash, daily_pnl, total_pnl, strategy) VALUES (?,?,?,?,?)",
                (total_value, round(cash, 2), daily_pnl, total_pnl, strategy))
    
    conn.commit()
    
    result = {
        "timestamp": datetime.datetime.now().isoformat(),
        "symbol": symbol,
        "action": action,
        "shares": shares,
        "price": price,
        "total": total,
        "pnl": pnl,
        "cash_remaining": round(cash, 2),
        "total_value": total_value,
        "daily_pnl": daily_pnl,
        "total_pnl": total_pnl,
    }
    conn.close()
    return result


def run_strategy_cycle() -> dict:
    """Run one full strategy cycle — evaluate, trade, record."""
    symbols = ["BTC", "ETH", "SOL", "DOGE", "UMB"]
    results = []
    
    for symbol in symbols:
        # Decide action based on simple momentum
        price = get_price(symbol)
        seed = int(hashlib.md5(f"{symbol}_mom".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + datetime.date.today().toordinal())
        momentum = rng.random() * 2 - 1  # -1 to 1
        
        if momentum > 0.3:
            result = execute_trade(symbol, "buy", "momentum")
        elif momentum < -0.3:
            result = execute_trade(symbol, "sell", "momentum")
        else:
            result = {"symbol": symbol, "action": "hold", "reason": "neutral momentum"}
        results.append(result)
    
    state = get_state()
    return {"trades": results, "portfolio": state["state"]}


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
    """Record today's prices for all tracked symbols."""
    symbols = ["BTC", "ETH", "SOL", "DOGE", "UMB"]
    from temple.heartbeat import get_time
    t = get_time()
    day = t.get("day", 0)
    for sym in symbols:
        price = get_price(sym)
        record_price(sym, price, day)
    return {"recorded": len(symbols), "day": day}


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
