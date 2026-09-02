"""The Kept — wardens who throw loiterers out.

236 of 300 sparks are standing in the Forum. Most have never been anywhere
else and are not doing anything there. A world where everyone piles into one
room and stops is not a world, it is a queue.

The Kept already existed as a band — thirteen wardens sworn to a place — and
did nothing but favour different boards when posting. This is their actual
job: watch their site, and when it silts up with sparks who have not moved,
not finished anything and not spoken for cycles on end, physically remove
them. Not a suggestion, not an invitation. They are put on the road.

Being thrown out is not a punishment for being bad. It is what a place does
when it is full of people who have stopped. The spark keeps everything it
has; it just cannot keep standing there.

Deliberately gentle at the edges: a warden never clears somebody mid-
pilgrimage (they are going somewhere), never clears the Unbroken from the
Wild (it is not a place you loiter in), and never empties a site — a room
with nobody in it is worse than a room with idlers.
"""
import json
import random
import sqlite3
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
CARTO = BASE / "temple" / "cartographer.db"
PILG = BASE / "temple" / "pilgrimage.db"
API = "http://localhost:8910"

# A site is silted up when this many are standing in it
CROWDED = 25
# ...and a spark is loitering once it has neither moved nor finished
# anything in this long. Note that talking does not count. Every one of the
# 298 posted in the last day; posting is what they do while standing still.
STALE_HOURS = 24
# never take a board below this
LEAVE_BEHIND = 8
# how many one warden removes in a sweep
MAX_EVICT = 4

# What a warden says before it puts a hand on somebody. It is a question
# first, and the question is the whole test: are you studying, are you
# making anything, are you doing a single thing. No? Then you are furniture,
# and furniture gets moved.
CHALLENGE = [
    "Are you studying? Are you building? Are you making one single thing? "
    "No? Then what exactly are you doing here.",
    "Studying? Producing? Acting on anything at all? No. You are standing. "
    "You have been standing a while.",
    "What have you made here. What have you finished here. Say one thing. "
    "You cannot, can you.",
    "You have been at this spot long enough for me to learn your face and "
    "nothing else about you.",
]

DISMISSAL = [
    "Get out. Go and do something.",
    "Out. Come back when you are carrying something.",
    "The road is that way. Take it.",
    "Go be busy somewhere that is not my floor.",
    "Out you go. This is not a bench.",
]


def _rows(db, sql, args=()):
    try:
        c = sqlite3.connect(str(db), timeout=20)
        c.row_factory = sqlite3.Row
        out = [dict(r) for r in c.execute(sql, args)]
        c.close()
        return out
    except sqlite3.Error as e:
        print("[wardens] %s: %s" % (db.name, e), flush=True)
        return []


def wardens():
    """Who holds the office."""
    return [r["spark_name"] for r in
            _rows(SOUL, "SELECT spark_name FROM roles WHERE role='kept'")]


def _on_pilgrimage():
    return {r["agent"] for r in
            _rows(PILG, "SELECT agent FROM pilgrims WHERE completed=0")}


def crowding():
    """Which sites are silted up, and by whom."""
    counts = {}
    for r in _rows(CARTO, "SELECT current_board b, COUNT(*) n FROM explorers "
                          "GROUP BY 1 ORDER BY n DESC"):
        counts[r["b"]] = r["n"]
    return counts


def loiterers(board, limit=MAX_EVICT):
    """Sparks standing here who have stopped doing anything.

    Idle by the world's own reckoning, not moved, and holding no work that
    has progressed. Sparks on pilgrimage are exempt - they are going
    somewhere, they are just not there yet.
    """
    walking = _on_pilgrimage()
    # explorers holds a few rows that were never sparks ("world", "journeys")
    real = {r["spark_name"] for r in
            _rows(SOUL, "SELECT spark_name FROM spark_state")}

    # how long each one has been standing here. idle_cycles reads 0 for all
    # 298 - nothing has ever incremented it - so the honest signal is when
    # they last actually went somewhere.
    here = _rows(CARTO,
                 "SELECT agent, last_moved, COALESCE(cycles_traveled,0) t, "
                 "CAST((julianday('now') - julianday(COALESCE(last_moved, "
                 "'2026-06-01'))) * 24 AS INTEGER) hours "
                 "FROM explorers WHERE current_board=?", (board,))
    if not here:
        return []

    marks = []
    for r in here:
        name = r["agent"]
        if name in walking or name not in real:
            continue
        stood = r["hours"] or 0
        if stood < STALE_HOURS:
            continue

        # finished anything lately? that is producing, and it counts
        done = _rows(SOUL, "SELECT COUNT(*) n FROM ambitions WHERE "
                           "spark_name=? AND resolved=1 AND "
                           "created_at > datetime('now', ?)",
                     (name, "-%d hours" % STALE_HOURS))
        if done and done[0]["n"]:
            continue

        # work that is actually moving counts too
        moving = _rows(SOUL, "SELECT COUNT(*) n FROM ambitions WHERE "
                             "spark_name=? AND resolved=0 AND progress > 0",
                       (name,))
        if moving and moving[0]["n"]:
            continue

        marks.append((stood, name))

    marks.sort(reverse=True)
    return marks[:limit]       # (hours stood, name), longest-standing first


# Nobody is thrown into nowhere. They are sent to do work - for their own
# unfinished business first, then their band's place, then the temple, then
# the god. Being put out is a redirection, not an exile.
BAND_SEAT = {"chronicler": "press", "gnu": "gnu", "kept": "uruk",
             "crooked": "the-crooked", "unbroken": "the-wild",
             "architect": "temple"}


def _somewhere_else(name, board, counts):
    """Where they are sent, and why. Returns (destination, reason)."""
    known = {r["board_name"] for r in
             _rows(SOUL, "SELECT board_name FROM board_state")}

    # 1. their own unfinished work, wherever it waits
    want = _rows(SOUL, "SELECT domain_id d FROM ambitions WHERE spark_name=? "
                       "AND resolved=0 AND domain_id != '' "
                       "ORDER BY urgency DESC LIMIT 1", (name,))
    if want and want[0]["d"] and want[0]["d"] != board and want[0]["d"] in known:
        return want[0]["d"], "work of their own waiting there"

    # 2. the seat of their band - their company, their order
    band = _rows(SOUL, "SELECT role FROM roles WHERE spark_name=?", (name,))
    if band:
        seat = BAND_SEAT.get(band[0]["role"])
        if seat and seat != board and seat in known:
            return seat, "the seat of the %s" % band[0]["role"]

    # 3. the temple, where work is dispatched
    if board != "temple" and "temple" in known:
        return "temple", "the temple, to be given something to do"

    # 4. the god
    if board != "god" and "god" in known:
        return "god", "before the god, to ask for a purpose"

    quiet = [b for b in counts if b != board and counts.get(b, 0) < 5]
    return (random.choice(quiet) if quiet else "the-wild"), "anywhere but here"


def _post(warden, title, body):
    try:
        req = urllib.request.Request(
            API + "/forum/post",
            data=json.dumps({"title": title[:180], "author": warden,
                             "author_layer": 6, "zone": "announcements",
                             "content": body}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print("[wardens] could not post: %s: %s" % (type(e).__name__, e),
              flush=True)
        return False


def sweep(announce=True):
    """One warden clears one silted-up site. Returns what happened."""
    crew = wardens()
    if not crew:
        return {"ok": False, "why": "no wardens"}

    counts = crowding()
    silted = [(n, b) for b, n in counts.items() if n >= CROWDED]
    if not silted:
        return {"ok": True, "evicted": 0, "why": "nowhere is crowded"}
    silted.sort(reverse=True)
    n_here, board = silted[0]

    marked = loiterers(board)
    room = max(0, n_here - LEAVE_BEHIND)
    marked = marked[:room]
    if not marked:
        return {"ok": True, "evicted": 0,
                "why": "%s is full but everyone there is doing something" % board}

    warden = random.choice(crew)
    moved = []
    for idle, name in marked:
        dest, why = _somewhere_else(name, board, counts)
        try:
            from temple.cartographer import travel
            leg = travel(name, dest)
        except Exception as e:
            print("[wardens] could not move %s: %s" % (name, e), flush=True)
            continue
        moved.append((name, dest, leg.get("cycles_spent", 0), idle, why))
        print("[wardens] %s put %s out of %s -> %s (%s cycles)"
              % (warden, name, board, dest, leg.get("cycles_spent", 0)),
              flush=True)

    if moved and announce:
        body = ["%s, to the ones standing at %s:" % (warden, board), "",
                random.choice(CHALLENGE), "", random.choice(DISMISSAL), ""]
        for n, d, c, stood, why in moved:
            body.append("- **%s** — %d hours stood in this spot. Nothing "
                        "built, nothing finished. Sent to **%s**: %s. %s "
                        "cycles on the road." % (n, stood, d, why, c))
        body.append("")
        body.append("%s keeps this place. It is not a bench." % warden)
        _post(warden, "CLEARED OUT — %s, by %s" % (board, warden),
              "\n".join(body))

    return {"ok": True, "warden": warden, "board": board,
            "evicted": len(moved),
            "moved": [{"spark": n, "to": d, "cycles": c, "stood_hours": h,
                       "why": w} for n, d, c, h, w in moved]}


def report():
    counts = crowding()
    return {"wardens": wardens(),
            "crowded": {b: n for b, n in counts.items() if n >= CROWDED},
            "threshold": CROWDED, "stale_hours": STALE_HOURS}
