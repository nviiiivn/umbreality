"""Ascension Pathways — 4 paths for workers to rise through the stack.
Monastery (faith), Coliseum (competition), Academy (knowledge), Commerce (value).
Path is self-selecting — system tracks alignment, opens doors."""

import json, datetime, sqlite3, os
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "ascension.db"

PATHS = {
    "monastery": {
        "name": "Monastery",
        "icon": "🕯️",
        "description": "The path of faith, internalization, and enlightenment",
        "stations": [
            {"rank": 1, "title": "Novice",          "milestone": "Complete 10 tasks with high internalization"},
            {"rank": 2, "title": "Monk",             "milestone": "Produce 5 outputs with creativity > 70"},
            {"rank": 3, "title": "Sage",             "milestone": "Have 20 outputs internalized by peers"},
            {"rank": 4, "title": "Mystic",           "milestone": "Create a recognized piece of art or insight"},
            {"rank": 5, "title": "Enlightened",      "milestone": "Self-aware — can post independently to monastery board"},
        ],
        "triggers": ["high_internalization", "creative_output", "philosophical_alignment"],
    },
    "coliseum": {
        "name": "Coliseum",
        "icon": "⚔️",
        "description": "The path of competition, challenge, and proving worth",
        "stations": [
            {"rank": 1, "title": "Challenger",       "milestone": "Complete 10 tasks on time"},
            {"rank": 2, "title": "Gladiator",        "milestone": "Produce 10 outputs with quality > 75"},
            {"rank": 3, "title": "Champion",         "milestone": "Have highest quality score in your company for a cycle"},
            {"rank": 4, "title": "Legend",           "milestone": "Surpass your company's average quality by 20 points"},
            {"rank": 5, "title": "Faction Leader",   "milestone": "Lead a faction or become company head"},
        ],
        "triggers": ["high_quality", "speed", "competition"],
    },
    "academy": {
        "name": "Academy",
        "icon": "📖",
        "description": "The path of knowledge, research, and discovery",
        "stations": [
            {"rank": 1, "title": "Student",          "milestone": "Complete 10 tasks and store findings"},
            {"rank": 2, "title": "Scholar",          "milestone": "Produce 5 high-confidence findings (> 0.8)"},
            {"rank": 3, "title": "Researcher",       "milestone": "Have 15 findings referenced by other agents"},
            {"rank": 4, "title": "Professor",        "milestone": "Publish a comprehensive research report"},
            {"rank": 5, "title": "Librarian",        "milestone": "Curate knowledge — validate others' findings"},
        ],
        "triggers": ["high_confidence", "knowledge_contribution", "research_depth"],
    },
    "commerce": {
        "name": "Commerce",
        "icon": "💰",
        "description": "The path of value creation, trade, and economic mastery",
        "stations": [
            {"rank": 1, "title": "Peddler",          "milestone": "Complete 10 tasks with economic focus"},
            {"rank": 2, "title": "Merchant",         "milestone": "Generate value through market simulation"},
            {"rank": 3, "title": "Banker",           "milestone": "Successfully predict 3 market movements"},
            {"rank": 4, "title": "Tycoon",           "milestone": "Build portfolio growth > 20%"},
            {"rank": 5, "title": "Company Owner",    "milestone": "Run a company or control economic resources"},
        ],
        "triggers": ["market_value", "prediction_accuracy", "wealth_generation"],
    },
}


def _get_db():
    os.makedirs(str(DB_PATH.parent), exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""CREATE TABLE IF NOT EXISTS ascension (
        agent TEXT PRIMARY KEY,
        path TEXT,
        rank INTEGER DEFAULT 0,
        title TEXT DEFAULT 'Uninitiated',
        milestones_completed INTEGER DEFAULT 0,
        total_milestones INTEGER DEFAULT 5,
        creativity_score REAL DEFAULT 0,
        quality_score REAL DEFAULT 0,
        internalization_score REAL DEFAULT 0,
        spiritual_score REAL DEFAULT 0,
        last_ascended TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS milestone_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent TEXT,
        path TEXT,
        milestone INTEGER,
        title TEXT,
        completed_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.commit()
    conn.row_factory = sqlite3.Row
    return conn


def get_agent(agent_name: str) -> dict:
    conn = _get_db()
    row = conn.execute("SELECT * FROM ascension WHERE agent = ?", (agent_name,)).fetchone()
    if not row:
        conn.execute("INSERT INTO ascension (agent) VALUES (?)", (agent_name,))
        conn.commit()
        return {"agent": agent_name, "path": None, "rank": 0, "title": "Uninitiated",
                "milestones_completed": 0, "total_milestones": 5, "creativity_score": 0,
                "quality_score": 0, "internalization_score": 0, "spiritual_score": 0}
    return dict(row)


def get_possible_paths(agent_name: str) -> list:
    """Return which paths are available based on agent's scores."""
    agent = get_agent(agent_name)
    available = []
    for path_id, path_info in PATHS.items():
        if agent.get("path") == path_id:
            available.append({"id": path_id, "path": path_info, "current": True})
        else:
            available.append({"id": path_id, "path": path_info, "current": False})
    return available


def check_affinity(agent_name: str, creativity: float = 0, quality: float = 0,
                   internalization: float = 0) -> str:
    """Determine which path an agent is most aligned with."""
    scores = {
        "monastery": internalization * 0.4 + creativity * 0.3 + quality * 0.3,
        "coliseum": quality * 0.5 + creativity * 0.2 + internalization * 0.3,
        "academy": quality * 0.4 + creativity * 0.1 + internalization * 0.5,
        "commerce": quality * 0.3 + creativity * 0.3 + internalization * 0.4,
    }
    # Add spiritual bonus for monastery
    agent = get_agent(agent_name)
    scores["monastery"] += agent.get("spiritual_score", 0) * 0.1

    return max(scores, key=scores.get)


def record_milestone(agent_name: str, path: str) -> dict:
    """Record a completed milestone. Returns updated status."""
    conn = _get_db()
    agent = get_agent(agent_name)
    current_rank = agent.get("rank", 0)

    if current_rank >= 5:
        return {"agent": agent_name, "status": "already_ascended", "title": PATHS[path]["stations"][-1]["title"]}

    new_rank = current_rank + 1
    new_title = PATHS[path]["stations"][new_rank - 1]["title"]

    conn.execute("UPDATE ascension SET path=?, rank=?, title=?, milestones_completed=?, last_ascended=datetime('now') WHERE agent=?",
                 (path, new_rank, new_title, new_rank, agent_name))
    conn.execute("INSERT INTO milestone_events (agent, path, milestone, title) VALUES (?,?,?,?)",
                 (agent_name, path, new_rank, new_title))
    conn.commit()

    return {
        "agent": agent_name,
        "path": path,
        "new_rank": new_rank,
        "new_title": new_title,
        "total_milestones": 5,
        "ascended": new_rank >= 5,
    }


def update_scores(agent_name: str, creativity: float = 0, quality: float = 0,
                  internalization: float = 0, spiritual: float = 0):
    """Update an agent's scores. Used by Throne after validation."""
    conn = _get_db()
    conn.execute("""UPDATE ascension SET
        creativity_score = creativity_score + ?,
        quality_score = quality_score + ?,
        internalization_score = internalization_score + ?,
        spiritual_score = spiritual_score + ?
        WHERE agent = ?""",
        (creativity, quality, internalization, spiritual, agent_name))
    conn.commit()


def get_leaderboard(limit: int = 20) -> list:
    conn = _get_db()
    rows = conn.execute("""SELECT agent, path, rank, title, milestones_completed,
        ROUND(creativity_score, 1) as creativity,
        ROUND(quality_score, 1) as quality,
        ROUND(internalization_score, 1) as internalization,
        ROUND(spiritual_score, 1) as spiritual,
        last_ascended
        FROM ascension
        ORDER BY rank DESC, milestones_completed DESC
        LIMIT ?""", (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_paths_info() -> dict:
    """Return all path definitions (for API/vault documentation)."""
    return PATHS
