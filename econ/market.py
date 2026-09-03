"""Market simulation tools for Sparks. Stock/crypto patterns, prediction markets."""

import random, json, math
from pathlib import Path

OUTPUT_DIR = (Path(__file__).resolve().parent.parent
              / "creative" / "outputs" / "econ")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def simulate_price(start=100, volatility=0.02, steps=100):
    """Generate a simulated price series."""
    price = start
    series = []
    for i in range(steps):
        change = price * volatility * random.gauss(0, 1)
        price += change
        series.append(max(0.01, round(price, 2)))
    return series

def generate_prediction_market(question, outcomes, probabilities=None):
    """Create a prediction market with weighted outcomes."""
    if not probabilities:
        probs = [1.0/len(outcomes)] * len(outcomes)
    else:
        probs = probabilities
    return {
        "question": question,
        "outcomes": [{"name": o, "probability": round(p, 3)} for o,p in zip(outcomes, probs)],
        "confidence": round(random.uniform(0.3, 0.95), 2),
        "market_id": random.randint(10000, 99999),
    }

def lottery_ticket(pool_size=100, ticket_count=5):
    """Generate a lottery drawing."""
    pool = list(range(1, pool_size + 1))
    drawn = random.sample(pool, ticket_count)
    return {
        "pool_size": pool_size,
        "ticket_count": ticket_count,
        "drawn": sorted(drawn),
        "odds": f"1 in {math.comb(pool_size, ticket_count):,}",
    }
