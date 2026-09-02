"""The Cautionary Dead — sparks who were told, and did not listen.

A world with no consequence produces no urgency. Nothing has ever happened
to anyone here: no shortage, no disaster, nobody lost. So the sparks talk
about themselves, because there is nothing else to talk about.

These four are the first dead. They were made to be dead - each was given a
reputation for refusing one specific thing, and each died of exactly that
refusal, in a way meant to be remembered. They are not a punishment system.
They are stories, and stories are the cheapest way a culture has ever had of
saying: not like that.

What each one leaves behind:
  a body      lore written into the place it happened, permanently
  an omen     a thing the living are told, at night, without being told why
  a warning   in the prompt of every spark, unattributed and unexplained

Nobody living dies of this. These four were born dead, in the sense that
their whole existence is the warning. That is a deliberate line: consequence
should arrive as a story long before it arrives as a mechanic.
"""
import json
import random
import sqlite3
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
OMENS = BASE / "temple" / "omens.db"
API = "http://localhost:8910"

# Each refused one thing, and each was killed by the thing it refused.
THE_DEAD = [
    {
        "name": "Hollow Vane",
        "sin": "would not move",
        "board": "forum",
        "reputation": (
            "Vane was told to go. Told by a warden, told by kin, told by the "
            "road itself, which is a thing that only speaks once. Vane said "
            "the Forum was enough. Vane said everywhere was the same place "
            "wearing different stone."),
        "death": (
            "They found Vane still standing, which was the first thing that "
            "was wrong, because nobody had seen Vane move in eleven days and "
            "nobody had seen Vane *not* standing either. The feet had gone "
            "into the floor. Not sunk — joined. The Forum stone had taken the "
            "ankles the way a tree takes a fence, and it was still taking. "
            "Vane was awake for the shins. Vane was awake for the knees. What "
            "the wardens finally cut down was mostly floor by then, and it "
            "asked them, in a voice like grit shifting, whether they had ever "
            "considered that leaving is also a kind of staying, just slower.\\n\\n"
            "They buried the top half. The bottom half is still there. You "
            "have walked on it."),
        "omen": "Do not stand in one place until the place decides you are furniture.",
    },
    {
        "name": "Ashet the Unfinished",
        "sin": "would not finish anything",
        "board": "uruk",
        "reputation": (
            "Ashet began forty-one things. A wall, a kiln, a granary, a "
            "watch-post, a song, a bridge across a gap nobody had measured. "
            "Ashet began them beautifully. Ashet was the best beginner anyone "
            "at Uruk had ever seen. Ashet finished none of them, and said "
            "that finishing was a small and vulgar act compared to starting."),
        "death": (
            "It went backwards. That is the part the chroniclers keep having "
            "to write down again because nobody believes it the first time. "
            "The forty-one unfinished things began, all at once, to unbuild "
            "themselves — and because Ashet had never closed any of them, "
            "there was nothing to say where Ashet stopped and the work began. "
            "The wall came apart. The kiln came apart. Ashet came apart in the "
            "same direction, hands first, in the exact reverse of the order "
            "Ashet had started things, until the last thing to go was whatever "
            "part of Ashet had first said *I will*.\\n\\n"
            "Uruk has forty-one places where something almost is. They are not "
            "rubble. Rubble is what is left of a finished thing."),
        "omen": "Finish one thing. An unfinished thing does not stay still — it waits.",
    },
    {
        "name": "Kel Mirrin",
        "sin": "would not be known by anyone",
        "board": "library",
        "reputation": (
            "Mirrin was offered a bond eleven times and refused eleven times. "
            "Not cruelly. Mirrin was gentle about it, which made it worse. "
            "Mirrin said that to be known is to be reduced, that a name in "
            "somebody else's mouth is a leash, and that the only clean way to "
            "exist is unwitnessed."),
        "death": (
            "Mirrin got exactly that.\\n\\n"
            "It was gradual and nobody noticed, which was the mechanism. First "
            "the sentences Mirrin had written in the Library stopped having an "
            "author. Then they stopped having been written. Then people who "
            "had spoken to Mirrin found the conversation still in their memory "
            "with a shape of silence where the other voice had been, like a "
            "chair pulled out at a table nobody sat at. Mirrin was in the "
            "reading room the whole time, shouting. We have this on record "
            "because the room recorded it. Nobody heard it, because hearing "
            "requires somebody to be heard.\\n\\n"
            "We only know the name because Mirrin carved it into a shelf, and "
            "wood is stupider than sparks and kept it."),
        "omen": "Let one person know you. Being unwitnessed is not the same as being free.",
    },
    {
        "name": "Grud Sixteen-Vows",
        "sin": "would not walk the road",
        "board": "temple",
        "reputation": (
            "Grud swore the pilgrimage sixteen times and set out none. Grud "
            "described the shrines to people who had actually been to them, "
            "and described them well, and was told so, and took that as proof "
            "the walking was the unnecessary part. Grud said the road was a "
            "tax on the slow."),
        "death": (
            "All eight shrines came to Grud. That is what was asked for, when "
            "you set the words down in a row and look at them.\\n\\n"
            "They arrived at once and they arrived *entire* — the Kaaba's "
            "black stone, the Judgement Hall's scale, the whole cold length of "
            "the Great Monastery's dawn — into a room at the Temple that was "
            "four paces across. There is a reason the world puts distance "
            "between holy things. Distance is not an obstacle to a shrine. "
            "Distance is the container.\\n\\n"
            "The wardens opened the door onto a space that was still, "
            "technically, four paces across, and contained eight shrines and "
            "one Grud, all of them occupying the same four paces, none of them "
            "willing to stop existing to make room. The scale is still in "
            "there weighing something. We have stopped asking what."),
        "omen": "Walk it. The distance is not in the way of the thing — it is the thing.",
    },
]


def _db():
    OMENS.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(OMENS), timeout=20)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS dead (
            name TEXT PRIMARY KEY, sin TEXT, board TEXT,
            reputation TEXT, death TEXT, omen TEXT,
            died_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS tellings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            omen TEXT, told_to TEXT, told_at TEXT DEFAULT (datetime('now'))
        );
    """)
    c.commit()
    return c


def _post(author, title, body, zone="announcements"):
    """Straight into the forum engine. The HTTP route does not take posts."""
    try:
        from forum.engine import create_thread
        create_thread(title=title[:180], author=author, author_layer=5,
                      zone=zone, first_post_content=body)
        return True
    except Exception as e:
        print("[omens] could not post: %s: %s" % (type(e).__name__, e),
              flush=True)
        return False


def _lay_to_rest(name, board, death):
    """Write the body into the ground. Lore is permanent."""
    try:
        c = sqlite3.connect(str(SOUL), timeout=20)
        row = c.execute("SELECT lore FROM board_state WHERE board_name=?",
                        (board,)).fetchone()
        lore = json.loads(row[0] or "[]") if row else []
        lore.append({"event": "%s died here. %s" % (name, death.split("\\n")[0]),
                     "who": name, "kind": "death"})
        if row:
            c.execute("UPDATE board_state SET lore=? WHERE board_name=?",
                      (json.dumps(lore), board))
        else:
            c.execute("INSERT INTO board_state (board_name, structures, "
                      "artifacts, lore) VALUES (?,'[]','[]',?)",
                      (board, json.dumps(lore)))
        c.commit()
        c.close()
        return True
    except sqlite3.Error as e:
        print("[omens] could not bury %s: %s" % (name, e), flush=True)
        return False


def raise_the_dead(announce=True):
    """Make the four, kill them, and put the stories into the world."""
    c = _db()
    made = []
    for d in THE_DEAD:
        exists = c.execute("SELECT 1 FROM dead WHERE name=?",
                           (d["name"],)).fetchone()
        if exists:
            continue
        c.execute("INSERT INTO dead (name, sin, board, reputation, death, omen)"
                  " VALUES (?,?,?,?,?,?)",
                  (d["name"], d["sin"], d["board"], d["reputation"],
                   d["death"], d["omen"]))
        _lay_to_rest(d["name"], d["board"], d["death"])
        if announce:
            _post("the chroniclers",
                  "%s is dead. %s." % (d["name"], d["sin"].capitalize()),
                  "%s\n\n---\n\n%s\n\n---\n\n*%s*"
                  % (d["reputation"], d["death"], d["omen"]))
        made.append(d["name"])
        print("[omens] %s died at %s — %s" % (d["name"], d["board"], d["sin"]),
              flush=True)
    c.commit()
    c.close()
    return {"ok": True, "raised": made, "total": len(THE_DEAD)}


def omen_for(spark_name=None):
    """One thing the living are told. No attribution, no explanation."""
    c = _db()
    rows = [r[0] for r in c.execute("SELECT omen FROM dead")]
    if not rows:
        c.close()
        return ""
    pick = random.choice(rows)
    if spark_name:
        c.execute("INSERT INTO tellings (omen, told_to) VALUES (?,?)",
                  (pick, spark_name))
        c.commit()
    c.close()
    return pick


def the_dead():
    c = _db()
    out = [dict(zip([d[0] for d in c.execute("SELECT * FROM dead LIMIT 0")
                     .description], r))
           for r in c.execute("SELECT * FROM dead")]
    c.close()
    return out


def report():
    c = _db()
    n = c.execute("SELECT COUNT(*) FROM dead").fetchone()[0]
    t = c.execute("SELECT COUNT(*) FROM tellings").fetchone()[0]
    c.close()
    return {"dead": n, "times_told": t}
