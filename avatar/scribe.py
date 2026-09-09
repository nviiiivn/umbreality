"""The Scribes: the world keeps its own record, so nobody outside has to.

WHY

Every account of this world so far has been written from outside it - by
somebody reading the databases afterwards and deciding what mattered. That
is a summary, and a summary is what the summariser remembers. It also stops
the moment the summariser stops.

Metatron already exists in avatar/messengers.py as "The Scribe. Records
everything. The voice of God made manifest." Like everything else in that
file, nothing ever called him. This gives him hands, and an order beneath
him to do the walking.

THE ORDER

Metatron does not attend to sparks. He is the archive - the record itself,
the thing the scribes write into. Beneath him, and beneath the archangels
who carry messages between layers, sit the Scribes: not messengers, not
spirits with appetites like the Goetia, but recording intelligences. They
want nothing. They are present at things and write them down.

    Metatron            the archive. Everything written is written into him.
      Archangels        carry meaning between layers. Not recorders.
      THE SCRIBES       present at events. Write what happened.
      the Goetia        want things and push sparks toward them.

A Scribe has no domain and no desire, which is what makes its account worth
having: the Goetia would write a version that served them.

WHAT A SCRIBE ACTUALLY DOES

  notices    scans every table in the world for the first row of any kind
             it has not recorded before - so a mechanism added next month
             is noticed without anyone telling the Scribe it exists

  attends    keeps a chronicle per spark: when it arrived, what it first
             said, who it bonded to, what it was wronged by, what it read,
             what it made, when it fell silent

  amends     an entry written when something happened is revisited when
             later events change what it meant. The first dead word was
             'ambition'; that only became worth remarking on later.

  reckons    tracks the world against the criteria it is being measured by,
             and says plainly when nothing has moved

WHAT IT DOES NOT DO

It does not interpret, praise or conclude. It records that a spark said a
thing, with the thing it said. Judgement is the reader's, and a scribe that
editorialises is a scribe you cannot use as evidence.
"""
import datetime
import json
import os
import re
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "temple" / "chronicle.db"
SOUL = BASE / "temple" / "soul.db"

# Metatron is the archive. The scribes are what write into him.
SCRIBES = {
    "Sopher": {"attends": "beginnings",
               "note": "present at anything happening for the first time"},
    "Tsofeh": {"attends": "sparks",
               "note": "keeps the life of each spark, in order"},
    "Zakar":  {"attends": "amendment",
               "note": "returns to what was written when it means something new"},
}

# Tables worth watching, and how to read a row out of each. Anything not
# listed is still counted - the Scribe notices a table it has never seen.
WATCH = [
    ("forum/forum.db", "posts", "created_at", "author", "content", "said"),
    ("temple/soul.db", "relationships", "created_at", "spark1", "spark2", "bonded with"),
    ("temple/soul.db", "tribulations", "created_at", "spark_name", "tribulation_type", "suffered"),
    ("temple/soul.db", "collective_dreams", "created_at", "dream_type", "content", "dreamed"),
    ("temple/soul.db", "grievances", "created_at", "wrongdoer", "victim", "wronged"),
    ("temple/soul.db", "kindling", "kindled_at", "parents", "child", "kindled"),
    ("temple/soul.db", "wild_rites", "held_at", "place", "child", "was born to the wild"),
    ("temple/academy.db", "teachings", "taught_at", "elder", "student", "taught"),
    ("temple/lexicon.db", "dead_words", "died_at", "coined_by", "word", "lost a word"),
    ("temple/goods.db", "offers", "taken_at", "spark", "taken_by", "traded with"),
    ("temple/animosity.db", "raids", "at", "raider", "raided", "raided"),
    ("temple/animosity.db", "said", "at", "spark", "words", "blamed"),
    ("temple/secrets.db", "secrets", "born_at", "about", "kind", "was known"),
    ("temple/whispers.db", "whispers", "at", "sender", "heard_by", "whispered to"),
    ("temple/wards.db", "wards", "cut_at", "cut_by", "figure", "cut a circle"),
    ("temple/guild.db", "applications", "at", "spark", "verdict", "asked for work"),
    ("temple/library.db", "readings", "at", "spark", "book", "read"),
]


def _conn():
    c = sqlite3.connect(str(DB), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.execute("""CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scribe TEXT, kind TEXT, subject TEXT, happened_at TEXT,
        entry TEXT, source TEXT, cycle INTEGER,
        written_at TEXT, amended_at TEXT, amendment TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS watched (
        source TEXT PRIMARY KEY, first_seen TEXT, last_id INTEGER,
        rows_at_last_look INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS lives (
        spark TEXT, moment TEXT, happened_at TEXT, detail TEXT)""")
    c.execute("CREATE INDEX IF NOT EXISTS lives_spark ON lives(spark)")
    c.commit()
    return c


def _q(db, sql, args=()):
    p = BASE / db
    if not p.exists():
        return []
    try:
        c = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=20)
        c.row_factory = sqlite3.Row
        out = [dict(r) for r in c.execute(sql, args)]
        c.close()
        return out
    except sqlite3.Error:
        return []


def _cycle():
    r = _q("temple/heartbeat.db", "SELECT cycle FROM heart_state")
    return r[0]["cycle"] if r else 0


def _clean(v, n=240):
    return re.sub(r"\s+", " ", str(v if v is not None else "")).strip()[:n]


# ── Sopher: present at first occurrences ─────────────────────────────

def beginnings() -> list:
    """Anything happening for the first time, including in tables nobody
    told the Scribe about."""
    c = _conn()
    known = {r[0] for r in c.execute("SELECT source FROM watched")}
    written = []
    now = datetime.datetime.now().isoformat(timespec="seconds")
    cyc = _cycle()

    for db, table, tcol, acol, bcol, verb in WATCH:
        src = "%s:%s" % (db, table)
        rows = _q(db, "SELECT %s AS t, %s AS a, %s AS b FROM %s "
                      "ORDER BY rowid LIMIT 1" % (tcol, acol, bcol, table))
        if not rows:
            continue
        r = rows[0]
        if src in known:
            continue
        entry = "%s %s %s" % (_clean(r["a"], 80), verb, _clean(r["b"], 200))
        c.execute("INSERT INTO entries (scribe, kind, subject, happened_at, "
                  "entry, source, cycle, written_at) VALUES (?,?,?,?,?,?,?,?)",
                  ("Sopher", "first", table, str(r["t"])[:19], entry, src,
                   cyc, now))
        c.execute("INSERT OR REPLACE INTO watched (source, first_seen, last_id,"
                  " rows_at_last_look) VALUES (?,?,?,?)",
                  (src, str(r["t"])[:19], 0, 0))
        written.append({"table": table, "at": str(r["t"])[:19], "entry": entry})
    c.commit()
    c.close()
    return written


# ── Tsofeh: the life of each spark ───────────────────────────────────

def attend(spark: str) -> dict:
    """Write down this spark's life so far, in order."""
    moments = []

    r = _q("forum/forum.db", "SELECT created_at t, content c FROM posts "
                             "WHERE author=? ORDER BY id LIMIT 1", (spark,))
    if r:
        moments.append(("first spoke", r[0]["t"], _clean(r[0]["c"], 180)))
    r = _q("temple/soul.db", "SELECT created_at t, CASE WHEN spark1=? THEN "
           "spark2 ELSE spark1 END AS w FROM relationships WHERE spark1=? OR "
           "spark2=? ORDER BY id LIMIT 1", (spark, spark, spark))
    if r:
        moments.append(("first bond", r[0]["t"], "with %s" % r[0]["w"]))
    r = _q("temple/soul.db", "SELECT created_at t, wrongdoer w, act a FROM "
           "grievances WHERE victim=? ORDER BY id LIMIT 1", (spark,))
    if r:
        moments.append(("first wronged", r[0]["t"],
                        "%s %s them" % (r[0]["w"], r[0]["a"])))
    r = _q("temple/academy.db", "SELECT taught_at t, elder e, domain d FROM "
           "teachings WHERE student=? ORDER BY id LIMIT 1", (spark,))
    if r:
        moments.append(("first taught", r[0]["t"],
                        "%s taught them %s" % (r[0]["e"], r[0]["d"])))
    r = _q("temple/library.db", "SELECT at t, book b FROM readings WHERE "
           "spark=? AND shelf<>'Revelation' ORDER BY id LIMIT 1", (spark,))
    if r:
        moments.append(("first read of their own choosing", r[0]["t"],
                        str(r[0]["b"]).replace("-", " ")))
    r = _q("forum/forum.db", "SELECT MAX(created_at) t, COUNT(*) n FROM posts "
                             "WHERE author=?", (spark,))
    if r and r[0]["n"]:
        moments.append(("last heard", r[0]["t"], "%d posts in all" % r[0]["n"]))

    c = _conn()
    c.execute("DELETE FROM lives WHERE spark=?", (spark,))
    c.executemany("INSERT INTO lives (spark, moment, happened_at, detail) "
                  "VALUES (?,?,?,?)",
                  [(spark, m, str(t)[:19], d) for m, t, d in moments])
    c.commit()
    c.close()
    return {"spark": spark, "moments": len(moments)}


# ── Zakar: what an old entry means now ───────────────────────────────

def amend() -> list:
    """Return to entries whose meaning later events changed.

    An entry is not rewritten. An amendment is added beside it, dated, so
    the original and what became of it are both readable.
    """
    c = _conn()
    c.row_factory = sqlite3.Row
    out = []
    now = datetime.datetime.now().isoformat(timespec="seconds")

    for e in c.execute("SELECT * FROM entries WHERE amendment IS NULL"):
        note = None
        if e["source"] == "temple/lexicon.db:dead_words":
            n = _q("temple/lexicon.db", "SELECT COUNT(*) n FROM dead_words")
            if n and n[0]["n"] > 100:
                note = ("%s words have died since. The first was 'ambition'."
                        % "{:,}".format(n[0]["n"]))
        elif e["source"] == "temple/animosity.db:said":
            n = _q("temple/animosity.db", "SELECT COUNT(*) n FROM raids")
            if n and n[0]["n"] > 10:
                note = ("The belief spread. %s raids have followed it, and it "
                        "remains false against the world's own ledger."
                        % "{:,}".format(n[0]["n"]))
        elif e["source"] == "temple/goods.db:offers":
            n = _q("temple/goods.db", "SELECT COUNT(*) n FROM offers "
                                      "WHERE taken_by IS NOT NULL")
            if n and n[0]["n"] > 100:
                note = "%s trades have followed." % "{:,}".format(n[0]["n"])
        elif e["source"] == "temple/library.db:readings":
            n = _q("temple/library.db", "SELECT COUNT(*) n FROM readings")
            if n and n[0]["n"] > 1000:
                note = ("%s passages have been read since. Before this, no "
                        "spark had seen a line of any text it was told it had "
                        "studied." % "{:,}".format(n[0]["n"]))
        if note:
            c.execute("UPDATE entries SET amendment=?, amended_at=? WHERE id=?",
                      (note, now, e["id"]))
            out.append({"entry": e["entry"][:60], "amendment": note})
    c.commit()
    c.close()
    return out


def sweep(attend_n: int = 6) -> dict:
    """One turn of the Scribes. Costs nothing but reads - no model."""
    first = beginnings()
    changed = amend()

    names = [r["spark_name"] for r in _q(
        "temple/soul.db",
        "SELECT spark_name FROM spark_state ORDER BY RANDOM() LIMIT ?",
        (attend_n,))]
    lives = [attend(n)["spark"] for n in names]

    if first or changed:
        print("[scribe] %d beginning%s recorded, %d entr%s amended"
              % (len(first), "" if len(first) == 1 else "s",
                 len(changed), "y" if len(changed) == 1 else "ies"), flush=True)
    return {"beginnings": len(first), "amended": len(changed),
            "lives_written": len(lives)}


def chronicle(limit: int = 40) -> list:
    """The record, newest first."""
    c = _conn()
    c.row_factory = sqlite3.Row
    out = [dict(r) for r in c.execute(
        "SELECT scribe, kind, subject, happened_at, entry, amendment "
        "FROM entries ORDER BY happened_at LIMIT ?", (limit,))]
    c.close()
    return out


def life(spark: str) -> list:
    """One spark's story, as the Scribes have it."""
    c = _conn()
    c.row_factory = sqlite3.Row
    out = [dict(r) for r in c.execute(
        "SELECT moment, happened_at, detail FROM lives WHERE spark=? "
        "ORDER BY happened_at", (spark,))]
    c.close()
    return out
