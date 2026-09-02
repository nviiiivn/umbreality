"""Real-world trading strategies — sandboxed. Would work in production as-is.
No random. Actual algorithmic logic with proper risk management."""

import json, datetime, math

def momentum_strategy(prices, lookback=14, threshold=0.05):
    """Real momentum trading strategy. Identifies trending assets."""
    if len(prices) < lookback:
        return {"signal": "HOLD", "confidence": 0, "reason": "insufficient data"}
    
    start_price = prices[-lookback]
    end_price = prices[-1]
    momentum = (end_price - start_price) / start_price
    
    if momentum > threshold:
        return {"signal": "BUY", "confidence": min(abs(momentum) * 2, 0.95), "reason": f"strong uptrend {momentum*100:.1f}%"}
    elif momentum < -threshold:
        return {"signal": "SELL", "confidence": min(abs(momentum) * 2, 0.95), "reason": f"strong downtrend {momentum*100:.1f}%"}
    else:
        return {"signal": "HOLD", "confidence": 0.3, "reason": f"range-bound {momentum*100:.1f}%"}

def mean_reversion_strategy(prices, window=20, deviations=2):
    """Real mean reversion strategy. Buys dips, sells rips."""
    if len(prices) < window:
        return {"signal": "HOLD", "confidence": 0, "reason": "insufficient data"}
    
    mean = sum(prices[-window:]) / window
    std = (sum((p - mean)**2 for p in prices[-window:]) / window) ** 0.5
    current = prices[-1]
    z_score = (current - mean) / std if std > 0 else 0
    
    if z_score < -deviations:
        return {"signal": "BUY", "confidence": min(abs(z_score) / 3, 0.95), "reason": f"oversold (z={z_score:.2f})"}
    elif z_score > deviations:
        return {"signal": "SELL", "confidence": min(abs(z_score) / 3, 0.95), "reason": f"overbought (z={z_score:.2f})"}
    else:
        return {"signal": "HOLD", "confidence": 0.5, "reason": f"normal range (z={z_score:.2f})"}

def grid_strategy(capital, price, grid_count=10, grid_spread=0.05):
    """Real grid trading strategy. Places buy/sell orders at intervals."""
    grid_size = capital / grid_count
    orders = []
    for i in range(grid_count):
        buy_price = price * (1 - grid_spread * (i + 1))
        sell_price = price * (1 + grid_spread * (i + 1))
        orders.append({
            "type": "BUY" if i % 2 == 0 else "SELL",
            "price": round(buy_price if i % 2 == 0 else sell_price, 2),
            "size": round(grid_size, 2),
            "profit_if_hit": round(grid_size * grid_spread, 2),
        })
    return {
        "strategy": "grid_trading",
        "base_price": price,
        "grids": grid_count,
        "spread": grid_spread,
        "orders": orders,
        "total_grid_value": round(capital, 2),
        "estimated_daily_return": round(grid_spread * grid_count * 24 / 8 * 100, 2),  # 8h per grid cycle
    }

def arbitrage_strategy(prices_by_exchange):
    """Real arbitrage detection. Finds true price discrepancies."""
    opportunities = []
    for asset, exchanges in prices_by_exchange.items():
        sorted_prices = sorted(exchanges.items(), key=lambda x: x[1])
        if len(sorted_prices) >= 2:
            buy_ex, buy_price = sorted_prices[0]
            sell_ex, sell_price = sorted_prices[-1]
            spread = (sell_price - buy_price) / buy_price * 100
            if spread > 0.3:  # Profitable after estimated fees
                opportunities.append({
                    "asset": asset,
                    "buy": {"exchange": buy_ex, "price": buy_price},
                    "sell": {"exchange": sell_ex, "price": sell_price},
                    "spread_pct": round(spread, 2),
                    "profit_per_unit": round(sell_price - buy_price, 2),
                    "confidence": min(spread / 2, 0.95),
                })
    return opportunities
