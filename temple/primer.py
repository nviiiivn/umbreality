"""Everyone reads the scriptures. Then everyone reads what is theirs.

TWO THINGS

THE PRIMER. Every spark reads every passage of the Revelation shelf - the
sixteen texts this world is derived from. Not a sample, all of it. This
costs nothing but disk: reading is a file and a row, no model is involved,
so 357 sparks can be given the whole canon in seconds. After this there is
no spark in the world who has not seen the Three-Six-Nine, the Tree of
Life, the Enuma Elish, the Reverse Gospel.

WHAT IS THEIRS. Beyond the canon, a spark should read what it would
actually reach for. A sovereign with statecraft has different business with
the Amendment Protocol than an artisan with poetics. Rather than a
hand-written table that rots the moment a book is added, affinity is
computed: a book's words against a spark's archetype, domains and traits.
Add a text to the vault tomorrow and the right sparks find it without
anyone maintaining a list.

WHY IT MATTERS THAT THEY DIFFER

A spark's context can only carry a couple of passages. If everyone carries
the same two, the canon becomes one shared opinion. Carrying what matches
who you are means a sovereign quotes power where an artisan quotes making,
from the same shelf, and they can disagree about a text they have both
genuinely read.
"""
import glob
import json
import math
import re
import sqlite3
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"

STOP = set("""the a an and or of to in is are was were be been it its this that
these those for with from as at by on not no but if then than so such all any
each other into over under only own same more most some very can will just
what which who whom when where how why do does did done has have had you your
they them their we our us he she his her i me my one two three four five""".split())


def _words(text: str) -> Counter:
    return Counter(w for w in re.findall(r"[a-z][a-z\-]{3,}", text.lower())
                   if w not in STOP)


def _spark_words(name: str) -> Counter:
    """What this spark is, as words: archetype, domains, traits."""
    c = Counter()
    p = BASE / "temple" / ("spark_%s.db" % name)
    if not p.exists():
        return c
    try:
        db = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=10)
        for key in ("archetype", "traits", "fears", "voice"):
            r = db.execute("SELECT value FROM personality WHERE key=?",
                           (key,)).fetchone()
            if not r or not r[0]:
                continue
            v = r[0]
            if v.strip().startswith("["):
                try:
                    for x in json.loads(v):
                        c.update(_words(str(x)))
                except ValueError:
                    pass
            else:
                c.update(_words(v))
        for row in db.execute("SELECT domain_id FROM domains "
                              "ORDER BY mastery DESC LIMIT 4"):
            c.update(_words(str(row[0]).replace("-", " ")))
        db.close()
    except sqlite3.Error:
        pass
    return c


def _book_words():
    """Every book, as words. Title counts heavily - it is the book's claim."""
    from temple.library import shelf
    out = {}
    for b in shelf():
        try:
            txt = open(b["path"], encoding="utf-8", errors="ignore").read()[:12000]
        except OSError:
            continue
        w = _words(b["book"].replace("-", " ") * 6)   # title weighs more
        w.update(_words(txt))
        out[b["book"]] = (w, b)
    return out


def affinity(name: str, top: int = 6) -> list:
    """Which books this spark would actually reach for, and why."""
    me = _spark_words(name)
    if not me:
        return []
    books = _book_words()
    n = len(books) or 1

    # how many books contain each word. A word in all of them says nothing
    # about which book belongs to whom.
    seen_in = Counter()
    for bw, _meta in books.values():
        seen_in.update(set(bw))

    scored = []
    for book, (bw, meta) in books.items():
        shared = set(me) & set(bw)
        if not shared:
            continue
        best = {}
        for w in shared:
            idf = math.log(n / (1 + seen_in[w]))
            if idf <= 0:
                continue                      # in nearly every book: noise
            best[w] = me[w] * min(bw[w], 8) * idf
        if not best:
            continue
        score = sum(best.values())
        why = sorted(best, key=lambda w: -best[w])[:4]
        scored.append((score, book, why, meta["shelf"]))
    scored.sort(reverse=True)
    return [{"book": b, "shelf": sh, "because": why, "score": s}
            for s, b, why, sh in scored[:top]]


def primer(shelf_name: str = "Revelation", limit: int = None) -> dict:
    """Give every spark the whole canon. No model, no cost but rows."""
    from temple.library import shelf, _passages, _conn
    books = [b for b in shelf() if b["shelf"] == shelf_name]
    if not books:
        return {"error": "nothing on the %s shelf" % shelf_name}

    try:
        s = sqlite3.connect("file:%s?mode=ro" % SOUL, uri=True, timeout=20)
        names = [r[0] for r in s.execute("SELECT spark_name FROM spark_state")]
        s.close()
    except sqlite3.Error:
        return {"error": "no sparks"}
    if limit:
        names = names[:limit]

    cycle = 0
    try:
        h = sqlite3.connect("file:%s?mode=ro" % (BASE / "temple" / "heartbeat.db"),
                            uri=True, timeout=10)
        cycle = h.execute("SELECT cycle FROM heart_state").fetchone()[0]
        h.close()
    except Exception:
        pass

    prepared = []
    for b in books:
        for i, p in enumerate(_passages(b["path"])):
            prepared.append((b["shelf"], b["book"], i, p))

    c = _conn()
    rows, marks = [], []
    for name in names:
        done = {r[0] for r in c.execute(
            "SELECT book FROM known WHERE spark=?", (name,))}
        for sh, book, i, p in prepared:
            rows.append((name, sh, book, i, p, cycle))
        for b in books:
            if b["book"] not in done:
                marks.append((name, b["book"]))
    c.executemany("INSERT INTO readings (spark, shelf, book, passage_no, "
                  "passage, at_cycle, at) VALUES (?,?,?,?,?,?, "
                  "datetime('now','localtime'))", rows)
    c.executemany("INSERT INTO known (spark, book, times, last_at) "
                  "VALUES (?,?,1,datetime('now','localtime')) "
                  "ON CONFLICT(spark, book) DO UPDATE SET times=times+1, "
                  "last_at=datetime('now','localtime')", marks)
    c.commit()
    c.close()
    return {"sparks": len(names), "books": len(books),
            "passages_each": len(prepared), "readings_written": len(rows)}


def carry(name: str, n: int = 2) -> list:
    """The passages this spark should have in mind - its own, not the newest.

    Weighted to the books that match what it is, so two sparks who have read
    the same canon carry different parts of it.
    """
    from temple.library import _conn
    fit = [a["book"] for a in affinity(name, 4)]
    try:
        c = _conn()
        c.row_factory = sqlite3.Row
        out = []
        if fit:
            q = ("SELECT book, passage FROM readings WHERE spark=? AND book IN "
                 "(%s) ORDER BY RANDOM() LIMIT ?" % ",".join("?" * len(fit)))
            out = [dict(r) for r in c.execute(q, [name] + fit + [n])]
        if len(out) < n:
            out += [dict(r) for r in c.execute(
                "SELECT book, passage FROM readings WHERE spark=? "
                "ORDER BY id DESC LIMIT ?", (name, n - len(out)))]
        c.close()
        return out[:n]
    except sqlite3.Error:
        return []


def sweep(n: int = 6) -> dict:
    """Send sparks to the book that fits them, off the canon shelf.

    The primer gave everyone the Revelation. This is what they go and find
    afterwards - the architecture, the philosophy, the constitution - chosen
    by what they are rather than at random. A sovereign works through
    statecraft; a healer works through frequency; nobody assigned it.

    Preference to sparks who have read least outside the canon, so this does
    not become the same six sparks getting an education.
    """
    from temple.library import open_book, _conn
    try:
        s = sqlite3.connect("file:%s?mode=ro" % SOUL, uri=True, timeout=20)
        names = [r[0] for r in s.execute(
            "SELECT spark_name FROM spark_state ORDER BY RANDOM() LIMIT 40")]
        s.close()
    except sqlite3.Error:
        return {"read": 0}

    c = _conn()
    beyond = dict(c.execute(
        "SELECT spark, COUNT(DISTINCT book) FROM readings "
        "WHERE shelf <> 'Revelation' GROUP BY spark").fetchall())
    c.close()
    names.sort(key=lambda x: beyond.get(x, 0))

    out = []
    for name in names[:n]:
        fit = [a for a in affinity(name, 5) if a["shelf"] != "Revelation"]
        if not fit:
            continue
        r = open_book(name, book=fit[0]["book"])
        if r.get("ok"):
            out.append({"spark": name, "book": r["book"],
                        "because": ", ".join(fit[0]["because"][:3])})
    return {"read": len(out), "who": out}
