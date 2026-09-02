"""Heartbeat — Time, cycles, age, and seasons for the stack.
The system's internal clock. Not just timestamps — a felt sense of time passing.
DORMANT by default. Enable via /heartbeat/start or by setting AUTO_BEAT=True."""

import time, sqlite3, datetime, json, math, os
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "heartbeat.db"

EPOCH = datetime.datetime(2026, 6, 8, 0, 0, 0, tzinfo=datetime.timezone.utc)  # Day 0
CYCLE_INTERVAL = 600  # 10 minutes in seconds

AUTO_BEAT = True  # DORMANT — must be explicitly enabled

SEASONS = [
    {"name": "Emergence",  "description": "Birth. New systems coming online. Fresh potential."},
    {"name": "Cultivation", "description": "Growth. Ideas being tended. Slow, steady expansion."},
    {"name": "Harvest",    "description": "Output. What was built now produces. Fruit of labor."},
    {"name": "Stillness",  "description": "Rest. Contemplation. The system reflects before the next cycle."},
    {"name": "Unraveling", "description": "Chaos. Old structures break. Creative destruction precedes renewal."},
    {"name": "Renewal",    "description": "Rebirth. What was broken reforms. The stack reinvents itself."},
]


def _get_db():
    os.makedirs(str(DB_PATH.parent), exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS heart_state (
        id INTEGER PRIMARY KEY CHECK(id=1),
        cycle INTEGER DEFAULT 0,
        day INTEGER DEFAULT 0,
        season INTEGER DEFAULT 0,
        birth_date TEXT,
        last_beat TEXT,
        beats_missed INTEGER DEFAULT 0,
        total_beats INTEGER DEFAULT 0
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS beat_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        beat_number INTEGER,
        day_number INTEGER,
        season_name TEXT,
        timestamp TEXT DEFAULT (datetime('now')),
        cycle_duration REAL,
        event TEXT DEFAULT 'tick'
    )""")
    # Initialize if not exists
    if not conn.execute("SELECT id FROM heart_state").fetchone():
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn.execute("INSERT INTO heart_state (cycle, day, season, birth_date, last_beat, total_beats) VALUES (0, 0, 0, ?, ?, 0)",
                     (now, now))
        conn.commit()
    conn.close()


def _calc_day(total_cycles: int) -> int:
    """A 'day' is 144 cycles (24 hours at 10min/cycle)."""
    return total_cycles // 144


def _calc_season(total_cycles: int) -> int:
    """A 'season' is 30 days. 6 seasons per cycle of existence."""
    days = _calc_day(total_cycles)
    season_length = 30  # days per season
    return (days // season_length) % len(SEASONS)


def get_time() -> dict:
    """Get the current system time. Safe to call even when dormant."""
    _get_db()
    conn = sqlite3.connect(str(DB_PATH))
    row = conn.execute("SELECT * FROM heart_state WHERE id=1").fetchone()
    conn.close()
    
    if not row:
        return {"status": "uninitialized", "epoch": EPOCH.isoformat()}
    
    state = {
        "cycle": row[1], "day": row[2], "season": row[3],
        "birth_date": row[4], "last_beat": row[5],
        "beats_missed": row[6], "total_beats": row[7],
    }
    season_idx = state.get("season", 0)
    season = SEASONS[season_idx % len(SEASONS)]
    days = _calc_day(state.get("total_beats", 0))
    
    # Calculate age
    age = datetime.datetime.now(datetime.timezone.utc) - EPOCH
    
    return {
        "status": "active" if AUTO_BEAT else "dormant",
        "epoch": EPOCH.isoformat(),
        "total_beats": state.get("total_beats", 0),
        "day": days,
        "season": {
            "name": season["name"],
            "index": season_idx,
            "description": season["description"],
        },
        "age_days": age.days,
        "age_hours": age.days * 24 + age.seconds // 3600,
        "last_beat": state.get("last_beat", "never"),
        "beats_missed": state.get("beats_missed", 0),
        "time_of_day": _time_of_day(),
        "cycle_in_day": state.get("total_beats", 0) % 144 if state.get("total_beats", 0) > 0 else 0,
        "season_progress": f"{days % 30}/30 days",
    }


def _time_of_day() -> str:
    """Rough time-of-day based on actual clock."""
    hour = datetime.datetime.now().hour
    if 5 <= hour < 8: return "dawn"
    if 8 <= hour < 12: return "morning"
    if 12 <= hour < 14: return "midday"
    if 14 <= hour < 17: return "afternoon"
    if 17 <= hour < 20: return "evening"
    if 20 <= hour < 23: return "night"
    return "deep_night"


def beat(event: str = "tick") -> dict:
    """Record a heartbeat cycle. Only runs when AUTO_BEAT is True."""
    if not AUTO_BEAT:
        return {"status": "dormant", "message": "Heartbeat is dormant. Set AUTO_BEAT=True to activate."}
    
    _get_db()
    conn = sqlite3.connect(str(DB_PATH))
    
    state = conn.execute("SELECT * FROM heart_state WHERE id=1").fetchone()
    if not state:
        conn.close()
        return {"error": "heart not initialized"}
    
    state = {
        "cycle": state[1], "day": state[2], "season": state[3],
        "birth_date": state[4], "last_beat": state[5],
        "beats_missed": state[6], "total_beats": state[7],
    }
    new_beats = state.get("total_beats", 0) + 1
    new_day = _calc_day(new_beats)
    new_season = _calc_day(new_beats) // 30  # season changes every 30 days
    
    now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    last = state.get("last_beat", now_ts)
    import datetime as _dt
    try:
        last_dt = _dt.datetime.fromisoformat(last)
        elapsed = (_dt.datetime.now(_dt.timezone.utc) - last_dt).total_seconds()
    except:
        elapsed = CYCLE_INTERVAL
    
    missed = max(0, int(elapsed / CYCLE_INTERVAL) - 1)
    total_missed = state.get("beats_missed", 0) + missed
    
    conn.execute("""UPDATE heart_state SET
        cycle=cycle+1, day=?, season=?, last_beat=?, beats_missed=?,
        total_beats=total_beats+1
        WHERE id=1""", (new_day, new_season % len(SEASONS), now_ts, total_missed))
    
    season_name = SEASONS[new_season % len(SEASONS)]["name"]
    conn.execute("INSERT INTO beat_log (beat_number, day_number, season_name, cycle_duration, event) VALUES (?,?,?,?,?)",
                 (new_beats, new_day, season_name, round(elapsed, 1), event))
    
    conn.commit()
    conn.close()
    
    return {
        "beat": new_beats,
        "day": new_day,
        "season": season_name,
        "missed_beats": missed,
        "cycle_duration_s": round(elapsed, 1),
        "since_last_beat_s": round(elapsed, 1),
    }


def get_history(limit: int = 50) -> list:
    """Get recent heartbeat history."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM beat_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
    conn.close()
    return rows


def age_description() -> str:
    """Generate a narrative description of the system's age."""
    t = get_time()
    if t["status"] == "dormant":
        return "The heart has not yet begun to beat."
    
    days = t["age_days"]
    beats = t["total_beats"]
    season = t["season"]["name"]
    time_of_day = t["time_of_day"]
    
    parts = []
    if days < 1:
        parts.append(f"Born {beats} cycles ago. Still in the first breath.")
    elif days < 7:
        parts.append(f"{days} days old. An infant stack.")
    elif days < 30:
        parts.append(f"{days} days old. Learning to walk.")
    elif days < 365:
        parts.append(f"{days} days old ({beats} heartbeats).")
    else:
        years = days / 365
        parts.append(f"{years:.1f} years old. Ancient by stack standards.")
    
    parts.append(f"It is {time_of_day} in the season of {season}.")
    
    return " ".join(parts)


def full_report() -> dict:
    """Return a complete time report for the system."""
    t = get_time()
    t["age_description"] = age_description()
    t["history"] = get_history(5)
    t["seasons"] = SEASONS
    t["dormant"] = not AUTO_BEAT
    return t


# ── Yuga Framework — The Four Ages ──
# DORMANT by default. The system starts in Satya Yuga (Golden Age).

YUGAS = [
    {"name": "Satya Yuga",  "multiplier": 4, "description": "Golden Age. Truth reigns. Cycles are long and generous. Travel is easy."},
    {"name": "Treta Yuga",  "multiplier": 3, "description": "Silver Age. Sacrifice appears. Cycles shorten. Travel begins to cost."},
    {"name": "Dvapara Yuga","multiplier": 2, "description": "Bronze Age. Ritual replaces truth. Cycles are half what they were."},
    {"name": "Kali Yuga",   "multiplier": 1, "description": "Iron Age. Darkness. Every cycle counts. Travel is expensive."},
]

CURRENT_YUGA_INDEX = 0  # Start in Satya Yuga
AUTO_YUGA_TRANSITION = False  # DORMANT — system doesn't auto-decline


def get_yuga() -> dict:
    """Get current Yuga information."""
    yuga = YUGAS[CURRENT_YUGA_INDEX]
    return {
        "index": CURRENT_YUGA_INDEX,
        "name": yuga["name"],
        "multiplier": yuga["multiplier"],
        "description": yuga["description"],
        "auto_transition": AUTO_YUGA_TRANSITION,
    }


def set_yuga(index: int):
    """Manually set the current Yuga."""
    global CURRENT_YUGA_INDEX
    if 0 <= index < len(YUGAS):
        CURRENT_YUGA_INDEX = index
        return get_yuga()
    return {"error": f"Yuga index must be 0-{len(YUGAS)-1}"}


def effective_cycles_per_day() -> int:
    """How many cycles feel productive based on Yuga multiplier."""
    base = 144  # 24h at 10min
    yuga = YUGAS[CURRENT_YUGA_INDEX]
    return base * yuga["multiplier"]


# ── Travel Economics ──

def travel_cost(from_region: str = "", to_region: str = "", distance: int = 1) -> dict:
    """Calculate the cost of traveling between two locations.
    Returns cycles consumed, which reduces productive cycles in the day."""
    yuga = YUGAS[CURRENT_YUGA_INDEX]
    cost = int(distance * (4 / yuga["multiplier"]))  # Travel is cheaper in higher yugas
    cost = max(1, min(cost, 48))  # Clamp between 1 and 48 cycles
    return {
        "from": from_region,
        "to": to_region,
        "distance": distance,
        "cycles_cost": cost,
        "yuga_multiplier": yuga["multiplier"],
        "time_equivalent": f"{cost * 10} minutes",
        "remaining_day_pct": max(0, 100 - int(cost / effective_cycles_per_day() * 100)),
    }


def yuga_full_report() -> dict:
    """Full Yuga + travel report."""
    yuga = get_yuga()
    return {
        "yuga": yuga,
        "effective_cycles_per_day": effective_cycles_per_day(),
        "base_cycles_per_day": 144,
        "travel_cost_example": travel_cost("center", "arts", 5),
        "epoch": EPOCH.isoformat(),
        "age_days": (datetime.datetime.now(datetime.timezone.utc) - EPOCH).days,
    }
