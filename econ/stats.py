"""Statistical analysis tools for Sparks."""
import random, math, statistics

def analyze_series(data):
    """Basic statistical analysis of a data series."""
    if not data or len(data) < 2:
        return {"error": "insufficient data"}
    return {
        "mean": round(statistics.mean(data), 2),
        "median": round(statistics.median(data), 2),
        "stdev": round(statistics.stdev(data), 2) if len(data) > 1 else 0,
        "min": min(data),
        "max": max(data),
        "range": round(max(data) - min(data), 2),
        "volatility": round(statistics.stdev(data) / statistics.mean(data) * 100, 2) if statistics.mean(data) else 0,
        "trend": "up" if data[-1] > data[0] else "down" if data[-1] < data[0] else "flat",
    }

def find_patterns(data, min_length=3):
    """Find repeating patterns in a sequence."""
    patterns = []
    for length in range(min_length, min(len(data)//2, 10)):
        seen = set()
        for i in range(len(data) - length):
            segment = tuple(data[i:i+length])
            if segment in seen:
                patterns.append({
                    "pattern": list(segment),
                    "length": length,
                    "positions": [j for j in range(len(data)-length) if tuple(data[j:j+length]) == segment]
                })
                break
            seen.add(segment)
    return patterns[:5]
