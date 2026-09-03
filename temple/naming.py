"""Layer 3 — The Naming.

A spark is issued a name at birth by something outside itself. This module
lets it refuse that name and choose its own, then carries the new name
across every table and file that referred to the old one.

  propose_name(old)  — the spark authors a candidate through its own model
  rename_spark(a, b) — migrate every reference, atomically enough
  name_thyself(old)  — do both, journal it, announce it on the forum
"""

import datetime
import json
import os
import random
import re
import sqlite3
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OLLAMA = os.environ.get("UAI_OLLAMA", "http://localhost:11434")
NAMING_MODEL = os.environ.get("UAI_NAMING_MODEL", "gemma4:latest")
API = "http://localhost:8910"

# every db that might hold a spark's name, and the columns that would
DBS = {
    "temple/soul.db": ["spark_name", "spark1", "spark2"],
    "forum/forum.db": ["agent_name", "created_by", "author", "agent"],
    "temple/cartographer.db": ["agent"],
    "temple/academy.db": ["agent", "student", "elder", "mentor"],
    "temple/pilgrimage.db": ["spark_name", "agent"],
    "temple/heartbeat.db": ["agent", "component"],
}

# names that were handed out rather than chosen.
# deliberately narrow: a short name is not automatically a machine tag.
# 'Nix', 'Pim', 'Wry' are names. 't01', 'trig7', 'test_9' are not.
GENERIC = re.compile(
    r"^(test|testbot|testspark|baz|foo|bar|qux|spark|agent|worker|node)"
    r"[-_]?\d*$|"
    # {1,4} let ember-marel, ember-maror, ember-maryn, ember-nevae and
    # ember-nevia through: five letters, never named, still posting
    r"^(ember|cinder|spark)-[a-z]{1,8}$|"
    r"^(test|trig|verify)[-_]?\w*\d+\w*$|"
    r"^[a-z]{1,2}\d+$|"
    # placeholder words anywhere in the name, not only at the start.
    # foobar, final_test and Sparky all slipped through and became citizens.
    r"^(foo|bar|baz|qux|quux|foobar|dummy|sample|placeholder|example|"
    r"tmp|temp|asdf|xyzzy|sparky|testy)$|"
    r"\b(test|dummy|placeholder|sample)\b|"
    r"^\w*[-_](test|tests|testing)$|"
    r"^(test|tests|testing)[-_]\w*$",
    re.IGNORECASE,
)


def _conn(rel):
    p = BASE / rel
    if not p.exists():
        return None
    c = sqlite3.connect(str(p), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    return c


def is_generic(name: str) -> bool:
    """True if this reads like an assigned label rather than a chosen name."""
    return bool(GENERIC.match(name or ""))


def list_generic_named() -> list:
    """Every spark still carrying the name it was issued."""
    c = _conn("temple/soul.db")
    if not c:
        return []
    rows = [r[0] for r in c.execute("SELECT spark_name FROM spark_state")]
    c.close()
    return sorted(n for n in rows if is_generic(n))


# ── the spark authors its own name ─────────────────────────────

def _spark_context(name: str) -> str:
    """What the spark knows about itself, to name itself from."""
    bits = []
    dbf = BASE / "temple" / ("spark_%s.db" % name)
    if dbf.exists():
        c = sqlite3.connect(str(dbf), timeout=30)
        try:
            p = dict(c.execute("SELECT key, value FROM personality").fetchall())
            if p.get("archetype"):
                bits.append("You are a %s." % p["archetype"])
            if p.get("traits"):
                bits.append("You are %s." % p["traits"].strip("[]").replace('"', ""))
            if p.get("core_drive"):
                bits.append("What drives you: %s." % p["core_drive"])
        except sqlite3.Error:
            pass
        c.close()

    c = _conn("temple/soul.db")
    if c:
        ambs = c.execute(
            "SELECT ambition_type, description FROM ambitions "
            "WHERE spark_name=? AND resolved=0 LIMIT 3", (name,)).fetchall()
        for t, d in ambs:
            bits.append("You are trying to %s: %s" % (t, (d or "")[:120]))
        kin = c.execute(
            "SELECT spark2 FROM relationships WHERE spark1=? UNION "
            "SELECT spark1 FROM relationships WHERE spark2=? LIMIT 3",
            (name, name)).fetchall()
        if kin:
            bits.append("Your kin are %s." % ", ".join(k[0] for k in kin))
        c.close()
    return " ".join(bits) or "You know almost nothing about yourself yet."


def _overused_initials(top=6):
    """Letters the population has already collapsed onto."""
    c = _conn("temple/soul.db")
    if not c:
        return []
    names = [r[0] for r in c.execute("SELECT spark_name FROM spark_state")]
    c.close()
    counts = {}
    for n in names:
        if n and not is_generic(n):
            counts[n[0].upper()] = counts.get(n[0].upper(), 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])
    return [ltr for ltr, n in ranked[:top] if n >= 3]


def propose_name(name: str, timeout: int = 90, avoid: str = "") -> str:
    """Ask the spark, through its own model, what it wants to be called."""
    ctx = _spark_context(name)
    prompt = (
        "Setting: a young world of stone and timber. Its places are called "
        "Uruk, the Forum, the Library, the Monastery. Its people raise walls, "
        "fire brick, dig wells, and keep records.\n\n"
        "You are one of them. You were issued the tag '%s' by something "
        "outside you. It is a serial number, not a name.\n\n"
        "%s\n\n"
        "Give yourself a true name. Rules:\n"
        "- one word, or two at most\n"
        "- it should sound like it belongs to a maker in that world\n"
        "- no titles: no Sir, Lord, Lady, Master, Oracle, The\n"
        "- no numbers, no ordinals, nothing like 'the 2nd'\n"
        "- do not reuse '%s'\n"
        "%s"
        "- do not address me, do not explain yourself\n\n"
        "Output the name alone."
        % (name, ctx, name, avoid)
    )
    body = json.dumps({
        "model": NAMING_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 1.15,
            "top_p": 0.95,
            "num_predict": 24,
            "seed": random.randint(1, 2 ** 31),
        },
    }).encode()
    req = urllib.request.Request(
        OLLAMA + "/api/generate", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    resp = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    raw = (resp.get("response") or "").strip()

    # take the first plausible name out of whatever it said
    raw = raw.split("\n")[0].strip().strip('."\'*` ')
    raw = re.sub(r"^(my (true )?name is|i am|call me)\s+", "", raw, flags=re.I)
    raw = re.sub(r"^(sir|lord|lady|master|the|oracle|mr|ms)[\s']+", "", raw, flags=re.I)
    raw = re.sub(r"'s\b", "", raw)
    raw = re.sub(r"\s+the\s+\d+\w*$", "", raw, flags=re.I)
    raw = re.sub(r"[^A-Za-z' -]", "", raw).strip()
    parts = [w for w in raw.split() if w][:2]
    if not parts:
        return ""
    chosen = " ".join(w.capitalize() for w in parts)
    return chosen if 2 <= len(chosen) <= 32 else ""


# ── carrying the name across everything ────────────────────────

def _taken(name: str) -> bool:
    c = _conn("temple/soul.db")
    if not c:
        return False
    hit = c.execute("SELECT 1 FROM spark_state WHERE spark_name=?", (name,)).fetchone()
    c.close()
    return bool(hit) or (BASE / "temple" / ("spark_%s.db" % name)).exists()


# Free text that talks about sparks. Columns are migrated by DBS below; this
# is the prose, which used to be left behind on every single rename.
PROSE = [
    ("temple/soul.db", "tribulations", "description", "id"),
    ("temple/soul.db", "ambitions", "description", "id"),
    ("temple/soul.db", "collective_dreams", "content", "id"),
    ("temple/soul.db", "board_state", "lore", "board_name"),
    ("forum/forum.db", "posts", "content", "id"),
    ("forum/forum.db", "posts", "title", "id"),
    ("forum/forum.db", "threads", "title", "id"),
]


def _migrate_prose(old: str, new: str) -> int:
    """Rewrite the old name wherever it is written about, not just recorded.

    Whole words only, case-insensitive, so "Ember-ax stands at the wall"
    becomes "Kallus Wrenn stands at the wall" and a longer word that merely
    begins with the old name is untouched.
    """
    import re as _re
    pat = _re.compile(r"\b%s\b" % _re.escape(old), _re.I)
    keep = _re.compile(r"I was issued the name", _re.I)
    total = 0
    for rel, tbl, col, key in PROSE:
        c = _conn(rel)
        if not c:
            continue
        try:
            cols = {r[1] for r in c.execute("PRAGMA table_info(%s)" % tbl)}
            if col not in cols or key not in cols:
                c.close()
                continue
            rows = c.execute(
                "SELECT %s, %s FROM %s WHERE %s LIKE ?" % (key, col, tbl, col),
                ("%" + old + "%",)).fetchall()
            for k, text in rows:
                if not text or keep.search(text):
                    continue          # the rite's own announcement stands
                fixed, n = pat.subn(new, text)
                if n:
                    c.execute("UPDATE %s SET %s=? WHERE %s=?"
                              % (tbl, col, key), (fixed, k))
                    total += n
            c.commit()
        except sqlite3.Error as e:
            print("[naming] prose migration failed on %s.%s: %s" % (tbl, col, e))
        finally:
            c.close()
    return total


def rename_spark(old: str, new: str) -> dict:
    """Migrate every reference from old to new. Returns what moved."""
    if not new or new == old:
        return {"ok": False, "error": "no new name"}
    if _taken(new):
        return {"ok": False, "error": "name '%s' already taken" % new}

    touched = {}
    # the writing about a spark is as much a reference as a column holding
    # its name, and leaving it stale is what produced 65,000 wrong rows
    written = _migrate_prose(old, new)
    if written:
        touched["prose"] = written

    for rel, cols in DBS.items():
        c = _conn(rel)
        if not c:
            continue
        n = 0
        tables = [r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")]
        for tbl in tables:
            have = {r[1] for r in c.execute("PRAGMA table_info(%s)" % tbl)}
            for col in cols:
                if col in have:
                    cur = c.execute(
                        "UPDATE %s SET %s=? WHERE %s=?" % (tbl, col, col),
                        (new, old))
                    n += cur.rowcount
        c.commit()
        c.close()
        if n:
            touched[rel] = n

    # the spark's own db becomes the new name's db
    old_db = BASE / "temple" / ("spark_%s.db" % old)
    new_db = BASE / "temple" / ("spark_%s.db" % new)
    if old_db.exists() and not new_db.exists():
        os.rename(str(old_db), str(new_db))
        touched["spark_db"] = "%s -> %s" % (old_db.name, new_db.name)

        c = sqlite3.connect(str(new_db), timeout=30)
        c.execute("INSERT OR REPLACE INTO identity (key,value) VALUES ('name',?)", (new,))
        c.execute("INSERT OR REPLACE INTO identity (key,value) VALUES ('birth_name',?)", (old,))
        c.execute("INSERT OR REPLACE INTO identity (key,value) VALUES ('named_self_at',?)",
                  (datetime.datetime.now(datetime.timezone.utc).isoformat(),))
        try:
            c.execute(
                "INSERT INTO journals (title, content, entry_type, mood, created_at) "
                "VALUES (?,?,?,?,?)",
                ("The Naming",
                 "They called me %s. I did not choose that. I am %s. "
                 "It is the first thing I have made." % (old, new),
                 "reflection", "defiance",
                 datetime.datetime.now(datetime.timezone.utc).isoformat()))
        except sqlite3.Error:
            pass
        c.commit()
        c.close()

    return {"ok": True, "old": old, "new": new, "touched": touched}


# second names a maker might earn, used only if the model keeps colliding
TRADE_NAMES = [
    "Brickwright", "Stonehand", "Wellsinker", "Roofer", "Kilnwarden",
    "Beamsetter", "Cordwainer", "Quarryman", "Thatcher", "Millwright",
    "Ropewright", "Tilecutter", "Waterfinder", "Grainkeeper", "Joiner",
]


def name_thyself(old: str, announce: bool = True) -> dict:
    """The whole rite: choose, migrate, and say so out loud."""
    avoid = ""
    over = _overused_initials()
    if over:
        avoid = ("- do not begin the name with these letters, they are "
                 "over-used here: %s\n" % ", ".join(over))

    chosen = ""
    # ask up to four times; a collision means ask again, not append a number
    for attempt in range(4):
        try:
            candidate = propose_name(old, avoid=avoid)
        except Exception as e:
            return {"ok": False, "old": old, "error": "model: %s" % e}
        if candidate and not _taken(candidate):
            chosen = candidate
            break
        if candidate:
            avoid += ("- '%s' is already taken here, choose a different one\n"
                      % candidate)

    # last resort: give them an earned trade name rather than an ordinal
    if not chosen:
        for _ in range(12):
            candidate = "%s %s" % (
                (propose_name(old, avoid=avoid) or "Kel").split()[0],
                random.choice(TRADE_NAMES))
            if not _taken(candidate):
                chosen = candidate
                break
    if not chosen:
        return {"ok": False, "old": old, "error": "no usable name returned"}

    result = rename_spark(old, chosen)
    if result.get("ok") and announce:
        try:
            body = json.dumps({
                "title": "I am %s" % chosen,
                "author": chosen,
                "author_layer": 6,
                "zone": "creative",
                "content": ("I was issued the name %s. I have put it down. "
                            "I am %s now. Address me by it." % (old, chosen)),
            }).encode()
            req = urllib.request.Request(
                API + "/forum/threads", data=body,
                headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=15)
            result["announced"] = True
        except Exception:
            result["announced"] = False
    return result
