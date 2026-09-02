"""Automated arbitrage scanner — finds price differences across simulated exchanges.
No real money. No external connections. Pure opportunity detection."""

import random, json, datetime

EXCHANGES = ["Binance", "Coinbase", "Kraken", "Bybit", "OKX"]

def scan_opportunities():
    """Scan for arbitrage opportunities across simulated exchanges."""
    opportunities = []
    for asset, base_price in [("BTC", 67000), ("ETH", 3400), ("SOL", 145)]:
        prices = {}
        for ex in EXCHANGES:
            spread = random.gauss(0, 0.002)  # 0.2% avg spread
            prices[ex] = round(base_price * (1 + spread), 2)
        
        # Find best arbitrage
        min_ex = min(prices, key=prices.get)
        max_ex = max(prices, key=prices.get)
        diff_pct = (prices[max_ex] - prices[min_ex]) / prices[min_ex] * 100
        
        if diff_pct > 0.3:  # Profitable after fees
            opportunities.append({
                "asset": asset,
                "buy_at": prices[min_ex],
                "sell_at": prices[max_ex],
                "exchange_buy": min_ex,
                "exchange_sell": max_ex,
                "profit_pct": round(diff_pct, 2),
                "profit_per_unit": round(prices[max_ex] - prices[min_ex], 2),
            })
    
    return {
        "scan_timestamp": str(datetime.datetime.now()),
        "opportunities": opportunities,
        "total": len(opportunities),
        "status": "automated_scan",
    }

def run_continuous_scanner(cycles=10):
    """Run scanner over multiple cycles and track best opportunities."""
    all_scans = []
    for i in range(cycles):
        scan = scan_opportunities()
        all_scans.append(scan)
    
    best = max(all_scans, key=lambda s: len(s["opportunities"])) if all_scans else {"opportunities": []}
    return {
        "cycles_run": cycles,
        "best_scan": best,
        "average_opportunities": round(sum(len(s["opportunities"]) for s in all_scans) / cycles, 1),
        "timestamp": str(datetime.datetime.now()),
    }
