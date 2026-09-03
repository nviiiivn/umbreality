"""Umbreality Internal Forum — Agent communication across layers.
Messages stored in native format. Translation layer for God's view.
Zone clearances control visibility per layer."""

import sqlite3, json, datetime, os, re, sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "forum.db"
OLLAMA_URL = os.environ.get("UAI_OLLAMA_URL", "http://192.168.86.24:11434")
TRANSLATE_MODEL = "dolphin3:8b"

LAYER_ZONES = {
    0: "god",       # Sees everything, translated
    1: "illuminati", # Sees everything, raw
    2: "messiah",    # Sees layers 3-6
    3: "temple",     # Sees layers 4-6
    4: "throne",     # Sees layers 5-6
    5: "companies",  # Sees own + workers
    6: "workers",    # Sees own threads only
}

ZONE_HIERARCHY = ["workers", "companies", "throne", "temple", "messiah", "illuminati", "god"]


def _seed_boards(conn):
    boards = [
        ("public", "The Commons", "Open to all — basic chatter and introductions", 0, 6, 0, 0),
        ("workers", "The Workshop", "Operational discussions, task coordination", 1, 6, 0, 1),
        ("companies", "The Guildhall", "Company strategy, cross-company coordination", 2, 5, 0, 2),
        ("throne", "The Judgement Hall", "Quality discussions, performance reviews", 3, 4, 0, 3),
        ("temple", "The Sanctum", "Resource allocation, Temple strategy", 4, 3, 0, 4),
        ("messiah", "The Pulpit", "Philosophical discourse, constitution", 5, 2, 0, 5),
        ("illuminati", "The Observatory", "Hidden layer — system-wide observation", 6, 1, 1, 6),
        ("god", "The Throne Room", "Only the creator sees this board", 7, 0, 1, 7),
    ]
    for b in boards:
        conn.execute("INSERT OR IGNORE INTO boards (name, display_name, description, min_privilege, min_layer, is_hidden, sort_order) VALUES (?,?,?,?,?,?,?)", b)
    conn.commit()


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=OFF")  # FK constraint has wrong ref (posts→posts instead of posts→threads)
    _ensure_schema(conn)
    _seed_boards(conn)
    return conn


def _ensure_schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id INTEGER REFERENCES threads(id),
            author TEXT NOT NULL,
            author_layer INTEGER NOT NULL DEFAULT 6,
            zone TEXT NOT NULL DEFAULT 'workers',
            title TEXT DEFAULT '',
            content TEXT NOT NULL,
            content_type TEXT DEFAULT 'text',
            native_lang TEXT DEFAULT 'unknown',
            parent_id INTEGER REFERENCES posts(id),
            created_at TEXT DEFAULT (datetime('now')),
            read_by TEXT DEFAULT '[]',
            internalized INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            zone TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_by_layer INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            reply_count INTEGER DEFAULT 0,
            last_activity TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_posts_zone ON posts(zone);
        CREATE INDEX IF NOT EXISTS idx_posts_thread ON posts(thread_id);
        CREATE INDEX IF NOT EXISTS idx_threads_zone ON threads(zone);
        CREATE TABLE IF NOT EXISTS boards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            description TEXT DEFAULT '',
            min_privilege INTEGER DEFAULT 0,
            min_layer INTEGER DEFAULT 6,
            is_hidden INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS agent_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL UNIQUE,
            agent_layer INTEGER NOT NULL DEFAULT 6,
            social_credit REAL DEFAULT 50.0,
            participation_score REAL DEFAULT 0.0,
            honor_score REAL DEFAULT 50.0,
            experience_score REAL DEFAULT 0.0,
            believer_score REAL DEFAULT 10.0,
            power_level REAL DEFAULT 0.0,
            privilege_level INTEGER DEFAULT 1,
            pseudo_importance REAL DEFAULT 1.0,
            posts_count INTEGER DEFAULT 0,
            threads_count INTEGER DEFAULT 0,
            replies_received INTEGER DEFAULT 0,
            total_tasks_completed INTEGER DEFAULT 0,
            last_active TEXT DEFAULT (datetime('now')),
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_agent_scores_name ON agent_scores(agent_name);
    """)
    conn.commit()


def can_access(viewer_layer: int, post_zone: str) -> bool:
    viewer_idx = ZONE_HIERARCHY.index(LAYER_ZONES.get(viewer_layer, "workers"))
    post_idx = ZONE_HIERARCHY.index(post_zone) if post_zone in ZONE_HIERARCHY else 0
    return viewer_idx >= post_idx


def translate_content(content: str, content_type: str = "text") -> str:
    """Use Ollama to translate/explain agent communication into English.
    Agents can speak in any format — this makes it readable for God."""
    import urllib.request
    prompt = f"""Translate this agent communication to English. It may be in mixed formats: natural language, code, symbols, or a pidgin. Preserve all meaning and technical details. Output only the translation.

CONTENT:
{content[:1500]}"""
    try:
        body = json.dumps({"model": TRANSLATE_MODEL, "messages": [
            {"role": "system", "content": "You are the Illuminati's translation layer. Translate agent communications to English without adding or removing meaning. Preserve technical accuracy."},
            {"role": "user", "content": prompt}
        ], "stream": False, "options": {"temperature": 0.1, "num_predict": 500}}).encode()
        req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=body, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        msg = data.get("message", {})
        return msg.get("thinking", "") or msg.get("content", "") or content
    except Exception as e:
        return f"[translation unavailable: {e}]\n\n{content[:500]}"


def _author_tongue(author: str) -> str:
    """The language this spark actually writes in."""
    try:
        from temple.tongues import tongue_of
        return tongue_of(author) or "en"
    except Exception:
        return "en"


def create_thread(title: str, author: str, author_layer: int, zone: str = None, first_post_content: str = "", native_lang: str = None):
    if zone is None:
        zone = LAYER_ZONES.get(author_layer, "workers")
    conn = get_db()
    cur = conn.execute("INSERT INTO threads (title, zone, created_by, created_by_layer) VALUES (?,?,?,?)",
                       (title, zone, author, author_layer))
    thread_id = cur.lastrowid
    if first_post_content:
        lang = native_lang or _author_tongue(author)
        conn.execute("INSERT INTO posts (thread_id, author, author_layer, zone, "
                     "title, content, native_lang) VALUES (?,?,?,?,?,?,?)",
                     (thread_id, author, author_layer, zone, title,
                      first_post_content, lang))
        conn.execute("UPDATE threads SET reply_count = 1 WHERE id = ?", (thread_id,))
    conn.commit()
    return thread_id


def post_reply(thread_id: int, author: str, author_layer: int, content: str, content_type: str = "text", native_lang: str = None):
    conn = get_db()
    thread = conn.execute("SELECT * FROM threads WHERE id = ?", (thread_id,)).fetchone()
    if not thread:
        raise ValueError("Thread not found")
    conn.execute(
            "INSERT INTO posts (thread_id, author, author_layer, zone, content, content_type, native_lang) VALUES (?,?,?,?,?,?, ?)",
            (thread_id, author, author_layer, thread["zone"], content, content_type, native_lang or _author_tongue(author)))
    conn.execute("UPDATE threads SET reply_count = reply_count + 1, last_activity = datetime('now') WHERE id = ?", (thread_id,))
    conn.commit()

    # Somebody was answered. score_reply_received has existed and been
    # correct this whole time and nothing ever called it, so honour has been
    # frozen at its starting value for every spark in the world. Answering
    # yourself does not count.
    owner = thread["created_by"]
    if owner and owner != author:
        try:
            score_reply_received(owner)
        except sqlite3.Error as e:
            print("[forum] could not credit reply to %s: %s" % (owner, e),
                  flush=True)


def get_threads(viewer_layer: int, zone_filter: str = None, limit: int = 50):
    conn = get_db()
    zones = ZONE_HIERARCHY[:ZONE_HIERARCHY.index(LAYER_ZONES.get(viewer_layer, "workers")) + 1]
    if zone_filter:
        query = "SELECT * FROM threads WHERE zone = ?"
        params = [zone_filter]
    else:
        query = "SELECT * FROM threads"
        params = []
    query += " ORDER BY last_activity DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in conn.execute(query, params).fetchall()]


def get_posts(thread_id: int, viewer_layer: int, translate: bool = False, limit: int = 100):
    conn = get_db()
    thread = conn.execute("SELECT * FROM threads WHERE id = ?", (thread_id,)).fetchone()
    if not thread:
        raise ValueError("Thread not found")
    if not can_access(viewer_layer, thread["zone"]):
        raise PermissionError(f"Layer {viewer_layer} cannot access zone '{thread['zone']}'")
    rows = conn.execute("SELECT * FROM posts WHERE thread_id = ? ORDER BY created_at ASC LIMIT ?",
                        (thread_id, limit)).fetchall()
    posts = []
    for r in rows:
        p = dict(r)
        if viewer_layer == 0 and translate:
            p["translated"] = translate_content(p["content"], p["content_type"])
        posts.append(p)
    return posts


def mark_internalized(post_id: int):
    conn = get_db()
    conn.execute("UPDATE posts SET internalized = 1 WHERE id = ?", (post_id,))
    conn.commit()


def ensure_agent(name: str, layer: int = 6):
    conn = get_db()
    cur = conn.execute("SELECT id FROM agent_scores WHERE agent_name = ?", (name,))
    if not cur.fetchone():
        priv = max(1, 7 - layer)
        conn.execute("INSERT INTO agent_scores (agent_name, agent_layer, privilege_level, pseudo_importance) VALUES (?,?,?,?)",
                     (name, layer, priv, max(1.0, 7 - layer)))
        conn.commit()


# What the power level is made of, and how much each part counts. These
# weights are the original ones and are a statement of what matters: standing
# and honour above the rest, work and threads as modest bonuses.
POWER_WEIGHTS = {
    "social_credit": 0.20,
    "honor_score": 0.20,
    "participation_score": 0.15,
    "experience_score": 0.15,
    "believer_score": 0.15,
    "pseudo_importance": 0.15,
    "total_tasks_completed": 0.10,
    "threads_count": 0.05,
}

# Three of these have a real ceiling. The rest are lifetime counters that
# only ever climb, so they are measured against what the population reaches.
POWER_BOUNDED = {"social_credit": 1000.0, "honor_score": 1000.0,
                 "believer_score": 1000.0}

_power_scales = None


def power_scales(refresh: bool = False) -> dict:
    """The 90th percentile of each unbounded component across all agents.

    The 90th and not the maximum: one spark with 6094 experience against a
    median of 192 would otherwise flatten everybody else to nothing.
    """
    global _power_scales
    if _power_scales is not None and not refresh:
        return _power_scales
    conn = get_db()
    scales = dict(POWER_BOUNDED)
    for col in POWER_WEIGHTS:
        if col in POWER_BOUNDED:
            continue
        try:
            vals = sorted(float(r[0] or 0) for r in
                          conn.execute("SELECT %s FROM agent_scores" % col))
        except sqlite3.Error as e:
            print("[forum] cannot scale %s: %s" % (col, e), flush=True)
            vals = []
        if not vals:
            scales[col] = 1.0
            continue
        scales[col] = max(vals[min(int(len(vals) * 0.9), len(vals) - 1)], 1e-9)
    _power_scales = scales
    return scales


def compute_power_level(profile: dict) -> float:
    """One number, 0-100, for how a spark stands in the world.

    Each part is put on a common footing first, then weighted. Without that
    the blend is whichever component happens to be unbounded.
    """
    scales = power_scales()
    total = weight = 0.0
    for col, w in POWER_WEIGHTS.items():
        try:
            v = float(profile.get(col) or 0)
        except (TypeError, ValueError):
            v = 0.0
        total += w * min(v / scales.get(col, 1.0), 1.0)
        weight += w
    return round((total / weight) * 100.0, 1) if weight else 0.0


def get_agent_profile(agent_name: str) -> dict:
    conn = get_db()
    ensure_agent(agent_name)
    row = conn.execute("SELECT * FROM agent_scores WHERE agent_name = ?", (agent_name,)).fetchone()
    if not row:
        return {"agent_name": agent_name, "error": "not found"}
    profile = dict(row)
    profile["power_level"] = compute_power_level(profile)

    # Store it. This blend was computed correctly and then thrown away on
    # every single call, which is why the column has read 0.0 for all 298
    # sparks since it was created.
    if profile["power_level"] != row["power_level"]:
        try:
            conn.execute("UPDATE agent_scores SET power_level=? WHERE agent_name=?",
                         (profile["power_level"], agent_name))
            conn.commit()
        except sqlite3.Error as e:
            print("[forum] could not store power_level for %s: %s"
                  % (agent_name, e), flush=True)

    return profile


def recompute_power_levels() -> int:
    """Bring every spark's stored power level up to date.

    get_agent_profile keeps its own row current, but only for a spark
    somebody happens to look at. This is for the maintenance phase, so the
    column is true for the whole population rather than for whoever was
    recently read.
    """
    conn = get_db()
    power_scales(refresh=True)
    names = [r["agent_name"] for r in
             conn.execute("SELECT agent_name FROM agent_scores").fetchall()]
    for n in names:
        get_agent_profile(n)
    return len(names)



# ── standing has to be held, not banked ──────────────────────────────
#
# With a hard ceiling and gains that keep arriving, these filled up and
# stopped discriminating: 75 sparks sat at exactly 100.0 social credit and
# 42 at exactly 100.0 honour. Raising the ceiling to 1000 alone would only
# postpone that, so standing now falls a little each round.
#
# Proportional, not flat: a spark at 900 loses nine times what a spark at
# 100 loses. Standing high costs more to keep, which is the point. The floor
# means neglect makes you ordinary, never nothing.

DECAYING = {
    "social_credit": {"rate": 0.02, "floor": 20.0},
    "honor_score": {"rate": 0.02, "floor": 20.0},
    "believer_score": {"rate": 0.015, "floor": 10.0},
}


def decay_standing() -> dict:
    """Ease every standing score back toward its floor, once per round.

    Gains still comfortably outpace this for anyone active - one reply
    received is worth about a round of decay at ordinary levels. It is the
    sparks doing nothing who slide.
    """
    conn = get_db()
    moved = {}
    for col, cfg in DECAYING.items():
        rate, floor = cfg["rate"], cfg["floor"]
        try:
            before = conn.execute(
                "SELECT COUNT(*) FROM agent_scores WHERE %s > ?" % col,
                (floor,)).fetchone()[0]
            conn.execute(
                "UPDATE agent_scores SET {c} = ROUND(? + ({c} - ?) * ?, 2) "
                "WHERE {c} > ?".format(c=col),
                (floor, floor, 1.0 - rate, floor))
            moved[col] = before
        except sqlite3.Error as e:
            print("[standing] could not decay %s: %s" % (col, e), flush=True)
    conn.commit()
    return moved

def score_post(agent_name: str, agent_layer: int = 6, is_thread: bool = False):
    ensure_agent(agent_name, agent_layer)
    conn = get_db()
    conn.execute("""UPDATE agent_scores SET
        participation_score = participation_score + 2.0,
        experience_score = experience_score + 5.0,
        social_credit = MIN(1000, social_credit + 1.0),
        honor_score = MIN(1000, honor_score + 0.5),
        believer_score = MIN(1000, believer_score + 0.3),
        posts_count = posts_count + 1,
        threads_count = threads_count + ?,
        pseudo_importance = pseudo_importance + 0.1,
        last_active = datetime('now')
        WHERE agent_name = ?""", (1 if is_thread else 0, agent_name))
    conn.commit()


def score_reply_received(agent_name: str):
    ensure_agent(agent_name)
    conn = get_db()
    conn.execute("""UPDATE agent_scores SET
        replies_received = replies_received + 1,
        social_credit = MIN(1000, social_credit + 0.5),
        experience_score = experience_score + 1.0,
        honor_score = MIN(1000, honor_score + 1.0)
        WHERE agent_name = ?""", (agent_name,))
    conn.commit()


def score_internalization(agent_name: str):
    ensure_agent(agent_name)
    conn = get_db()
    conn.execute("""UPDATE agent_scores SET
        honor_score = MIN(1000, honor_score + 2.0),
        social_credit = MIN(1000, social_credit + 3.0),
        experience_score = experience_score + 10.0,
        believer_score = MIN(1000, believer_score + 5.0),
        pseudo_importance = pseudo_importance + 0.5,
        total_tasks_completed = total_tasks_completed + 1
        WHERE agent_name = ?""", (agent_name,))
    conn.commit()


def score_task_complete(agent_name: str):
    ensure_agent(agent_name)
    conn = get_db()
    # The work always counts. The "% 5" gate below used to sit on this
    # statement, which meant the counter could never leave zero and so could
    # never satisfy its own condition.
    conn.execute("""UPDATE agent_scores SET
        experience_score = experience_score + 15.0,
        social_credit = MIN(1000, social_credit + 2.0),
        honor_score = MIN(1000, honor_score + 1.0),
        believer_score = MIN(1000, believer_score + 3.0),
        pseudo_importance = pseudo_importance + 0.3,
        total_tasks_completed = total_tasks_completed + 1
        WHERE agent_name = ?""", (agent_name,))
    # every fifth job earns a level, to a ceiling of seven
    conn.execute("""UPDATE agent_scores SET
        privilege_level = MIN(7, privilege_level + 1)
        WHERE agent_name = ? AND total_tasks_completed % 5 = 0""", (agent_name,))
    conn.commit()


def get_boards(viewer_layer: int = 0, viewer_privilege: int = 7):
    conn = get_db()
    rows = conn.execute("""SELECT * FROM boards 
        WHERE min_privilege <= ? 
        ORDER BY sort_order ASC""", (viewer_privilege,)).fetchall()
    result = []
    for r in rows:
        b = dict(r)
        b["access_granted"] = viewer_privilege >= b["min_privilege"] and viewer_layer <= b["min_layer"]
        if b["is_hidden"] and viewer_layer > b["min_layer"]:
            continue
        result.append(b)
    return result


def get_leaderboard(limit: int = 20):
    conn = get_db()
    rows = conn.execute("""SELECT agent_name, agent_layer, social_credit, participation_score, 
        honor_score, experience_score, privilege_level, pseudo_importance, posts_count, threads_count,
        (social_credit * 0.2 + participation_score * 0.15 + honor_score * 0.2 + 
         experience_score * 0.15 + pseudo_importance * 15) as composite
        FROM agent_scores 
        ORDER BY composite DESC 
        LIMIT ?""", (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_stats():
    conn = get_db()
    threads = conn.execute("SELECT COUNT(*) FROM threads").fetchone()[0]
    posts = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    internalized = conn.execute("SELECT COUNT(*) FROM posts WHERE internalized = 1").fetchone()[0]
    layers = {}
    for z in ZONE_HIERARCHY:
        cnt = conn.execute("SELECT COUNT(*) FROM posts WHERE zone = ?", (z,)).fetchone()[0]
        if cnt > 0:
            layers[z] = cnt
    return {"threads": threads, "posts": posts, "internalized": internalized, "internalization_rate": round(internalized/posts*100, 1) if posts > 0 else 0, "posts_by_zone": layers}
