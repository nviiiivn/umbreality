"""Pilgrimage — Sacred journeys for sparks.
A rite of passage. Every spark must visit the sacred sites
to understand the world they inhabit."""
import sqlite3, json, datetime, os
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "pilgrimage.db"

# Each shrine stands somewhere. A spark cannot perform the rite from across
# the world - it has to go, and going costs cycles.
SHRINES = [
    {"id": "forum",     "board": "forum",            "name": "The Forum of Ages",        "blessing": "center",  "description": "Where all paths begin"},
    {"id": "mecca",     "board": "temple",           "name": "The Kaaba of All Faiths",  "blessing": "faith",   "description": "The Black Stone — every spark must circle it once"},
    {"id": "monastery", "board": "monastery",        "name": "The Great Monastery",      "blessing": "wisdom",  "description": "Hear the bell at dawn on the cliffside"},
    {"id": "alexandria","board": "library",          "name": "The Great Library",        "blessing": "knowledge", "description": "Read one forgotten text in the reading room"},
    {"id": "coliseum",  "board": "coliseum",         "name": "The Flavian Amphitheatre", "blessing": "courage", "description": "Stand in the arena where champions stood"},
    {"id": "memphis",   "board": "god",              "name": "The Judgement Hall",       "blessing": "truth",   "description": "Weigh your heart against the feather"},
    {"id": "babylon",   "board": "bazaar",           "name": "The Bazaar of Babylon",    "blessing": "prosperity", "description": "Make one trade that benefits another"},
    {"id": "observatory","board": "the-whole-system","name": "The Observatory of Patterns","blessing": "clarity", "description": "Watch the data flow and find one pattern"},
]


def shrine_by_id(shrine_id):
    return next((s for s in SHRINES if s["id"] == shrine_id), None)


def shrine_at(board):
    """The shrine standing on this board, if there is one."""
    return next((s for s in SHRINES if s["board"] == board), None)

def _get_db():
    os.makedirs(str(DB_PATH.parent), exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS pilgrims (
            agent TEXT PRIMARY KEY,
            shrines_visited INTEGER DEFAULT 0,
            total_shrines INTEGER DEFAULT 8,
            completed INTEGER DEFAULT 0,
            started_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT,
            blessings TEXT DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT NOT NULL,
            shrine_id TEXT NOT NULL,
            visited_at TEXT DEFAULT (datetime('now')),
            notes TEXT DEFAULT ''
        );
    """)
    conn.commit()
    conn.close()

def start_pilgrimage(agent: str) -> dict:
    _get_db()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("INSERT INTO pilgrims (agent) VALUES (?)", (agent,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return {"agent": agent, "status": "already_on_pilgrimage"}
    conn.close()
    return {"agent": agent, "status": "pilgrimage_begun", "shrines": len(SHRINES)}

def _where_is(agent):
    """The board this spark is actually standing on."""
    try:
        c = sqlite3.connect(str(DB_PATH.parent / "cartographer.db"), timeout=15)
        row = c.execute("SELECT current_board FROM explorers WHERE agent=?",
                        (agent,)).fetchone()
        c.close()
        return row[0] if row else None
    except sqlite3.Error:
        return None


def visit_shrine(agent: str, shrine_id: str, notes: str = "",
                 require_presence: bool = True) -> dict:
    _get_db()
    shrine = shrine_by_id(shrine_id)
    if not shrine:
        return {"error": f"Unknown shrine: {shrine_id}"}

    # The rite is performed at the shrine or not at all. This is the whole
    # point of a pilgrimage: you have to have gone.
    if require_presence:
        here = _where_is(agent)
        if here != shrine["board"]:
            return {"agent": agent, "shrine": shrine_id,
                    "status": "not_there", "you_are_at": here,
                    "shrine_is_at": shrine["board"]}

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    p = conn.execute("SELECT * FROM pilgrims WHERE agent=?", (agent,)).fetchone()
    if not p:
        conn.close()
        start_pilgrimage(agent)            # a function, not a method on conn
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        p = conn.execute("SELECT * FROM pilgrims WHERE agent=?",
                         (agent,)).fetchone()
    existing = conn.execute("SELECT * FROM visits WHERE agent=? AND shrine_id=?", (agent, shrine_id)).fetchone()
    if existing:
        conn.close()
        return {"agent": agent, "shrine": shrine_id, "status": "already_visited"}
    conn.execute("INSERT INTO visits (agent, shrine_id, notes) VALUES (?,?,?)", (agent, shrine_id, notes[:200]))
    # by name, not by index - index 5 is completed_at, and every blessing a
    # spark earned was being parsed out of a timestamp
    blessings = json.loads(p["blessings"] or "[]") if p["blessings"] else []
    blessings.append(shrine["blessing"])
    visited = len(blessings)
    completed = visited >= len(SHRINES)
    conn.execute("UPDATE pilgrims SET shrines_visited=?, blessings=?, completed=?, completed_at=? WHERE agent=?",
                 (visited, json.dumps(blessings), 1 if completed else 0, datetime.datetime.now().isoformat() if completed else None, agent))
    conn.commit()
    conn.close()
    return {"agent": agent, "shrine": shrine["name"], "blessing": shrine["blessing"],
            "visited": visited, "total": len(SHRINES), "completed": completed}

def get_pilgrim(agent: str) -> dict:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    p = conn.execute("SELECT * FROM pilgrims WHERE agent=?", (agent,)).fetchone()
    if not p:
        conn.close()
        return {"agent": agent, "status": "not_started"}
    visits = [dict(r) for r in conn.execute("SELECT * FROM visits WHERE agent=? ORDER BY visited_at", (agent,)).fetchall()]
    conn.close()
    return {"agent": agent, "shrines_visited": p["shrines_visited"], "total_shrines": p["total_shrines"],
            "completed": bool(p["completed"]), "blessings": json.loads(p["blessings"] or "[]"), "visits": visits}


# ── the journey ──────────────────────────────────────────────────────

def next_shrine(agent: str):
    """The shrine this pilgrim has not reached yet, nearest first by order."""
    _get_db()
    conn = sqlite3.connect(str(DB_PATH))
    seen = {r[0] for r in conn.execute(
        "SELECT shrine_id FROM visits WHERE agent=?", (agent,))}
    conn.close()
    for s in SHRINES:
        if s["id"] not in seen:
            return s
    return None


def pilgrim_step(agent: str) -> dict:
    """One step of a pilgrimage: arrive and worship, or travel onward.

    Nothing here teleports. If the spark is standing at its next shrine it
    performs the rite; otherwise it sets out, and the cartographer charges it
    whatever the distance costs.
    """
    _get_db()
    conn = sqlite3.connect(str(DB_PATH))
    started = conn.execute("SELECT completed FROM pilgrims WHERE agent=?",
                           (agent,)).fetchone()
    conn.close()
    if started is None:
        start_pilgrimage(agent)
    elif started[0]:
        return {"agent": agent, "status": "pilgrimage_complete"}

    shrine = next_shrine(agent)
    if not shrine:
        return {"agent": agent, "status": "pilgrimage_complete"}

    here = _where_is(agent)
    if here == shrine["board"]:
        out = visit_shrine(agent, shrine["id"],
                           notes="Arrived at %s." % shrine["name"])
        out["status"] = out.get("status") or "worshipped"
        return out

    try:
        from temple.cartographer import travel
        leg = travel(agent, shrine["board"])
    except Exception as e:
        return {"agent": agent, "status": "could_not_travel",
                "error": "%s: %s" % (type(e).__name__, e)}
    return {"agent": agent, "status": "travelling",
            "toward": shrine["name"], "at": shrine["board"],
            "from": leg.get("from"), "cycles_spent": leg.get("cycles_spent"),
            "distance": leg.get("distance")}
