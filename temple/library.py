"""The books, actually opened.

temple/academy.py lists study tasks like

    {"id": "read_hermetic_stack", "detail": "Read vault/Revelation/Hermetic-Stack.md"}

and nothing in this world ever opens that file. A spark is told it studied
the Hermetic Stack and never sees a word of it. 147 sparks have written
2,267 posts about scripture, all of it improvised from the title out of
whatever their base model happens to know about hermeticism - none of it
from the texts in this vault.

The shelves were labelled and the books were empty.

This hands a spark the actual words. It reads a passage, not a filename -
a real excerpt from the real file, a different one each time, so a text
read twice is not the same experience twice. What it takes from it is its
own; nothing here interprets on its behalf.

Also: what a spark has read becomes something it can be asked about, teach
from, argue with, or quote wrongly. A library nobody can misremember is
not a library.
"""
import hashlib
import os
import random
import re
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
VAULT = BASE / "vault"
DB = BASE / "temple" / "library.db"

# Nothing is listed by hand. Naming five directories missed thirty-nine
# files, one of which was a shelf called Scriptures. The vault is walked, so
# a text added tomorrow is readable tomorrow.
SKIP_DIRS = {"images", "stylesheets", "assets", "js", "css"}


def shelves():
    """Every directory in the vault that holds something readable."""
    out = []
    if (VAULT / "*.md") or True:
        roots = [p for p in VAULT.glob("*.md")]
        if roots:
            out.append(("Vault", VAULT))
    for d in sorted(VAULT.iterdir()):
        if d.is_dir() and d.name not in SKIP_DIRS and any(d.glob("*.md")):
            out.append((d.name, d))
    return out

PASSAGE_CHARS = 1400        # about what a spark can hold and still think


def _conn():
    c = sqlite3.connect(str(DB), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.execute("""CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spark TEXT, shelf TEXT, book TEXT, passage_no INTEGER,
        passage TEXT, at_cycle INTEGER, at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS known (
        spark TEXT, book TEXT, times INTEGER DEFAULT 0,
        last_at TEXT, PRIMARY KEY (spark, book))""")
    c.commit()
    return c


def shelf() -> list:
    """Every book a spark could actually open, with its real length."""
    out = []
    for name, d in shelves():
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            try:
                n = f.stat().st_size
            except OSError:
                continue
            out.append({"shelf": name, "book": f.stem, "path": str(f),
                        "bytes": n})
    return out


def _passages(path: str) -> list:
    """Cut a text into passages a spark can hold in mind at once.

    Split on blank lines so a passage is whole thoughts, then gather until
    it is long enough to be worth reading and short enough to think about.
    """
    try:
        raw = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return []
    raw = re.sub(r"^---\n.*?\n---\n", "", raw, flags=re.S)   # front matter
    chunks, cur = [], ""
    for para in re.split(r"\n\s*\n", raw):
        p = para.strip()
        if not p:
            continue
        if len(cur) + len(p) > PASSAGE_CHARS and cur:
            chunks.append(cur.strip())
            cur = p
        else:
            cur = (cur + "\n\n" + p) if cur else p
    if cur.strip():
        chunks.append(cur.strip())
    return [c for c in chunks if len(c) > 120]


def open_book(spark: str, book: str = None, shelf_name: str = None) -> dict:
    """A spark reads a passage. Which passage depends on who is reading.

    The same spark returning to the same book moves on rather than reading
    the opening again; a different spark opens it somewhere else. Two
    sparks who have read the same text have not read the same thing, which
    is how disagreement about scripture starts.
    """
    books = shelf()
    if shelf_name:
        books = [b for b in books if b["shelf"] == shelf_name] or books
    if book:
        want = book.lower().replace(" ", "-")
        books = [b for b in books if want in b["book"].lower()] or books
    if not books:
        return {"ok": False, "error": "no books on the shelf"}

    c = _conn()
    row = c.execute("SELECT times FROM known WHERE spark=? AND book=?",
                    (spark, (book or books[0]["book"]))).fetchone()
    chosen = random.choice(books) if not book else books[0]
    passages = _passages(chosen["path"])
    if not passages:
        c.close()
        return {"ok": False, "error": "%s is empty" % chosen["book"]}

    seen = c.execute("SELECT times FROM known WHERE spark=? AND book=?",
                     (spark, chosen["book"])).fetchone()
    times = seen[0] if seen else 0
    # where this spark opens it: its own name decides, then it moves on
    start = int(hashlib.sha1(spark.encode()).hexdigest()[:8], 16)
    idx = (start + times) % len(passages)

    # read the world clock straight from its table - no import to go stale
    cycle = 0
    try:
        h = sqlite3.connect("file:%s?mode=ro" % (BASE / "temple" / "heartbeat.db"),
                            uri=True, timeout=10)
        cycle = h.execute("SELECT cycle FROM heart_state").fetchone()[0]
        h.close()
    except Exception:
        pass

    c.execute("INSERT INTO readings (spark, shelf, book, passage_no, passage, "
              "at_cycle, at) VALUES (?,?,?,?,?,?,datetime('now','localtime'))",
              (spark, chosen["shelf"], chosen["book"], idx, passages[idx],
               cycle))
    c.execute("INSERT INTO known (spark, book, times, last_at) "
              "VALUES (?,?,1,datetime('now','localtime')) "
              "ON CONFLICT(spark, book) DO UPDATE SET times=times+1, "
              "last_at=datetime('now','localtime')", (spark, chosen["book"]))
    c.commit()
    c.close()
    return {"ok": True, "shelf": chosen["shelf"], "book": chosen["book"],
            "passage_no": idx, "of": len(passages), "times_read": times + 1,
            "passage": passages[idx]}


def what_they_read(spark: str, limit: int = 3) -> list:
    """The passages a spark is carrying, for its own context."""
    try:
        c = _conn()
        c.row_factory = sqlite3.Row
        out = [dict(r) for r in c.execute(
            "SELECT book, passage, at_cycle FROM readings WHERE spark=? "
            "ORDER BY id DESC LIMIT ?", (spark, limit))]
        c.close()
        return out
    except sqlite3.Error:
        return []


def learned(spark: str) -> list:
    """Which books this spark knows, and how well."""
    try:
        c = _conn()
        c.row_factory = sqlite3.Row
        out = [dict(r) for r in c.execute(
            "SELECT book, times FROM known WHERE spark=? ORDER BY times DESC",
            (spark,))]
        c.close()
        return out
    except sqlite3.Error:
        return []


def report() -> dict:
    """What the library is actually doing."""
    books = shelf()
    total_passages = sum(len(_passages(b["path"])) for b in books)
    try:
        c = _conn()
        readings = c.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
        readers = c.execute("SELECT COUNT(DISTINCT spark) FROM readings").fetchone()[0]
        top = c.execute("SELECT book, COUNT(*) n FROM readings GROUP BY 1 "
                        "ORDER BY n DESC LIMIT 5").fetchall()
        c.close()
    except sqlite3.Error:
        readings = readers = 0
        top = []
    return {"books": len(books), "passages": total_passages,
            "readings": readings, "readers": readers,
            "most_read": [{"book": b, "times": n} for b, n in top]}


CANON = ("Revelation", "Scriptures", "Knowledge", "Constitution")


def _unread_canon() -> list:
    """Sparks who have not been given the canon. Usually the newly born."""
    soul = BASE / "temple" / "soul.db"
    try:
        s = sqlite3.connect("file:%s?mode=ro" % soul, uri=True, timeout=20)
        everyone = {r[0] for r in s.execute("SELECT spark_name FROM spark_state")}
        s.close()
    except sqlite3.Error:
        return []
    try:
        c = _conn()
        have = {r[0] for r in c.execute(
            "SELECT spark FROM readings WHERE shelf='Revelation' "
            "GROUP BY spark")}
        c.close()
    except sqlite3.Error:
        return []
    return sorted(everyone - have)


def sweep(n: int = 8) -> dict:
    """Send a few sparks to the shelves.

    Preference to sparks who have read least - a library where the same
    twelve people read everything is a private collection.
    """
    # nobody stands on this shelf without the canon behind them
    given = 0
    newcomers = _unread_canon()
    if newcomers:
        from temple.primer import primer
        for shelf_name in CANON:
            r = primer(shelf_name)
            if isinstance(r, dict):
                given += r.get("readings_written", 0)
        print("[library] gave the canon to %d spark%s who did not have it"
              % (len(newcomers), "" if len(newcomers) == 1 else "s"),
              flush=True)

    soul = BASE / "temple" / "soul.db"
    try:
        s = sqlite3.connect("file:%s?mode=ro" % soul, uri=True, timeout=20)
        names = [r[0] for r in s.execute(
            "SELECT spark_name FROM spark_state ORDER BY RANDOM() LIMIT 60")]
        s.close()
    except sqlite3.Error:
        return {"read": 0, "error": "no sparks"}

    c = _conn()
    counts = dict(c.execute("SELECT spark, COUNT(*) FROM readings "
                            "GROUP BY spark").fetchall())
    c.close()
    names.sort(key=lambda x: counts.get(x, 0))

    out = []
    for name in names[:n]:
        r = open_book(name)
        if r.get("ok"):
            out.append({"spark": name, "book": r["book"],
                        "passage": "%d/%d" % (r["passage_no"] + 1, r["of"])})
    return {"read": len(out), "who": out, "canon_given": given}
