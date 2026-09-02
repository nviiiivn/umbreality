"""Progress Guide — Learning loops for the stack.
Throne learns from past validations, scheduler adapts to company performance,
factions evolve based on real dynamics, Messiah regenerates from feedback."""

import json, sqlite3, datetime, os
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "guide.db"


def _get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS throne_lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT, task_type TEXT, quality REAL, creativity REAL,
        approved INTEGER, timestamp TEXT DEFAULT (datetime('now')),
        lesson TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS scheduler_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT, task_phase TEXT, output_quality REAL, creativity_score REAL,
        completed INTEGER, timestamp TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS faction_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        faction TEXT, strength REAL, event TEXT,
        timestamp TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS messiah_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version INTEGER, prompt_hash TEXT, trigger TEXT,
        performance_delta REAL, timestamp TEXT DEFAULT (datetime('now'))
    )""")
    return conn


def record_throne_lesson(company: str, task: str, quality: float, creativity: float, approved: bool):
    """Record a Throne validation for pattern learning."""
    task_type = task.split(":")[0] if ":" in task else task[:30]
    conn = _get_db()
    lesson = f"{'Approved' if approved else 'Rejected'} {company} on {task_type[:20]} (q={quality})"
    conn.execute(
        "INSERT INTO throne_lessons (company, task_type, quality, creativity, approved, lesson) VALUES (?,?,?,?,?,?)",
        (company, task_type, quality, creativity, 1 if approved else 0, lesson))
    conn.commit()
    conn.close()


def get_throne_insights() -> dict:
    """Analyze Throne history to find patterns and adjust thresholds."""
    conn = _get_db()
    
    # Which companies perform best at which task types
    rows = conn.execute("""
        SELECT company, task_type, AVG(quality) as avg_q, AVG(creativity) as avg_c,
               SUM(approved) as approvals, COUNT(*) as total
        FROM throne_lessons GROUP BY company, task_type
        HAVING total > 2 ORDER BY avg_q DESC
    """).fetchall()
    
    patterns = [dict(r) for r in rows]
    
    # Calculate dynamic quality threshold
    all_q = conn.execute("SELECT AVG(quality) as avg FROM throne_lessons").fetchone()
    dynamic_threshold = max(30, int((all_q["avg"] or 50) * 0.8))
    
    conn.close()
    return {
        "patterns": patterns[:10],
        "dynamic_quality_threshold": dynamic_threshold,
        "total_lessons": len(patterns),
    }


def record_scheduler_outcome(company: str, phase: str, quality: float, creativity: float, completed: bool):
    """Record how a company performed on a scheduler task."""
    conn = _get_db()
    conn.execute(
        "INSERT INTO scheduler_patterns (company, task_phase, output_quality, creativity_score, completed) VALUES (?,?,?,?,?)",
        (company, phase, quality, creativity, 1 if completed else 0))
    conn.commit()
    conn.close()


def get_scheduler_insights() -> dict:
    """Learn which companies perform best on which task phases."""
    conn = _get_db()
    rows = conn.execute("""
        SELECT company, task_phase, AVG(output_quality) as avg_q,
               AVG(creativity_score) as avg_c, COUNT(*) as tasks
        FROM scheduler_patterns GROUP BY company, task_phase
        HAVING tasks > 1 ORDER BY avg_q DESC
    """).fetchall()
    conn.close()
    return {"company_affinities": [dict(r) for r in rows]}


def record_faction_event(faction: str, strength: float, event: str):
    """Record a faction strength change."""
    conn = _get_db()
    conn.execute("INSERT INTO faction_history (faction, strength, event) VALUES (?,?,?)",
                 (faction, strength, event))
    conn.commit()
    conn.close()


def get_faction_history(faction: str = "") -> list:
    conn = _get_db()
    if faction:
        rows = conn.execute(
            "SELECT * FROM faction_history WHERE faction=? ORDER BY timestamp DESC LIMIT 20",
            (faction,)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM faction_history ORDER BY timestamp DESC LIMIT 50").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def record_messiah_version(version: int, trigger: str, perf_delta: float = 0):
    """Track Messiah regeneration events and their performance impact."""
    import hashlib
    conn = _get_db()
    try:
        prompt_text = open(Path(__file__).resolve().parent.parent / "messiah" / "current_prompt.json").read()
        prompt_hash = hashlib.md5(prompt_text.encode()).hexdigest()[:12]
    except:
        prompt_hash = "unknown"
    conn.execute("INSERT INTO messiah_versions (version, prompt_hash, trigger, performance_delta) VALUES (?,?,?,?)",
                 (version, prompt_hash, trigger, perf_delta))
    conn.commit()
    conn.close()


def adapt_thresholds() -> dict:
    """Dynamically adjust Throne quality threshold based on history."""
    insights = get_throne_insights()
    new_threshold = insights["dynamic_quality_threshold"]
    
    # Update the throne module's threshold
    import temple.throne as throne
    old = throne.QUALITY_THRESHOLD
    throne.QUALITY_THRESHOLD = new_threshold
    
    return {
        "old_threshold": old,
        "new_threshold": new_threshold,
        "reason": f"Auto-adjusted from {old} to {new_threshold} based on {insights['total_lessons']} validation patterns"
    }
