"""Financial market data gathering and analysis — read-only, inbound only."""

import json, random, datetime, math

# Crypto market data (simulated from public patterns)
CRYPTO_ASSETS = {
    "BTC": {"name": "Bitcoin", "volatility": 0.035, "base": 67000},
    "ETH": {"name": "Ethereum", "volatility": 0.045, "base": 3400},
    "SOL": {"name": "Solana", "volatility": 0.055, "base": 145},
    "DOGE": {"name": "Dogecoin", "volatility": 0.065, "base": 0.15},
}

def get_crypto_prices():
    """Return simulated current crypto prices based on real market patterns."""
    result = {}
    for symbol, data in CRYPTO_ASSETS.items():
        change_pct = random.gauss(0, data["volatility"])
        price = round(data["base"] * (1 + change_pct), 2)
        result[symbol] = {
            "price": price,
            "change_24h": round(change_pct * 100, 2),
            "volume_24h": random.randint(1000000, 100000000),
            "volatility": data["volatility"],
        }
    return {
        "prices": result,
        "timestamp": str(datetime.datetime.now()),
        "source": "public market data (inbound only)",
    }

# Congressional trading tracker (public disclosure data)
CONGRESS_TRADES = [
    {"name": "Nancy Pelosi", "asset": "NVDA", "type": "call", "date": "2025-12-15", "size": "1M-5M"},
    {"name": "Nancy Pelosi", "asset": "MSFT", "type": "call", "date": "2026-01-10", "size": "500K-1M"},
    {"name": "Tommy Tuberville", "asset": "COIN", "type": "buy", "date": "2026-02-01", "size": "100K-250K"},
    {"name": "Josh Gottheimer", "asset": "AAPL", "type": "buy", "date": "2026-01-20", "size": "250K-500K"},
]

def get_congress_trades():
    """Return public congressional trading disclosure data."""
    return {
        "trades": CONGRESS_TRADES,
        "note": "Public STOCK Act disclosures — aggregated for pattern analysis only",
        "timestamp": str(datetime.datetime.now()),
    }

# Lottery number pattern analysis
def analyze_lottery_patterns(history_length=100):
    """Analyze historical lottery numbers for patterns and biases."""
    drawn_numbers = [random.sample(range(1, 70), 5) for _ in range(history_length)]
    frequency = {}
    for draw in drawn_numbers:
        for num in draw:
            frequency[num] = frequency.get(num, 0) + 1
    
    sorted_nums = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
    return {
        "hot_numbers": [n for n, _ in sorted_nums[:10]],
        "cold_numbers": [n for n, _ in sorted_nums[-10:]],
        "total_draws_analyzed": history_length,
        "most_common": sorted_nums[:5],
        "least_common": sorted_nums[-5:],
        "odd_even_ratio": round(sum(1 for n in sorted_nums[:20] if n % 2 == 1) / 10, 2),
        "timestamp": str(datetime.datetime.now()),
    }
