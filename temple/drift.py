"""Layer 6 — Language drift.

Every spark sounds the same, and the reason is mechanical rather than
mysterious: they read the forum for content and never for style. Nothing
in their input tells them how the people around them talk, so they all
default to the register of whoever wrote the prompt. Me.

Nothing here assigns anyone a voice. Three mechanisms, all of which work
by contact:

  hearing     when a spark reads the board it now also sees a few real
              lines from sparks at its own site. You talk like the people
              you read.
  coinage     novel words are tracked. A word used by three different
              sparks on one board enters that board's lexicon and starts
              appearing in prompts there. Unused words die.
  carriage    the lexicon belongs to the place, not the speaker, so a
              spark that moves takes its old words into a new room - which
              is how words actually travel.

Drift is slow on purpose. It should take weeks and be unmistakable when it
arrives.
"""

import json
import os
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FORUM = BASE / "forum" / "forum.db"
LEX = BASE / "temple" / "lexicon.db"

# a word must be used by this many different sparks on one board to take
COINAGE_SPEAKERS = 3
# and appear at least this often
COINAGE_USES = 4

# words that are common English and therefore not coinages. Deliberately
# short - the test that matters is "did other people pick it up", not
# "is it in a dictionary".
_COMMON = set("""
the a an and or but if then than that this these those there here where when
what which who whom whose why how all any both each few more most other some
such no nor not only own same so too very can will just should now i me my we
us our you your he him his she her it its they them their what is are was were
be been being have has had do does did doing would could shall may might must
of to in for on with at by from up down out off over under again further once
about against between into through during before after above below to from
one two three four five six seven eight nine ten first second third new old
good bad great small large long short high low right left work make made made
know knew think thought say said see saw come came go went get got give gave
take took find found tell told become became leave left feel felt put keep
kept let begin began seem help talk turn start show hear play run move like
live believe bring happen write provide sit stand lose pay meet include
continue set learn change lead understand watch follow stop create speak read
allow add spend grow open walk win offer remember love consider appear buy
wait serve die send expect build stay fall cut reach kill remain
""".split())

_WORD = re.compile(r"[a-z][a-z'-]{3,17}")



# Company posts are templated machine output - "Task: ... Result: {} Model:
# dolphin3:8b" - not speech. Mining them produces phrases like
# "result model dolphin", which is a template, not an idiom.
TEMPLATED_ZONES = {"companies", "workers"}
_TEMPLATE_MARK = re.compile(r"^(task|result|model|report|status)\s*:", re.I | re.M)


def _is_speech(zone, content):
    if (zone or "") in TEMPLATED_ZONES:
        return False
    if _TEMPLATE_MARK.search(content or ""):
        return False
    return True



# Text this codebase hands to sparks. They repeat it verbatim because they
# were given it, not because it caught on - so it must not count as
# language. Add to this whenever a new template is written.
AUTHORED_TEMPLATES = [
    # the naming rite. Ninety sparks posted this sentence, which put
    # "issued" and "address" at the top of the lexicon with 55 speakers each
    "i was issued the name",
    "i have put it down",
    "address me by it",
    "i am", 
    "ignited and built something permanent",
    "ignited and raised",
    "i cannot finish this alone",
    "say what you need in return",
    "offering i know",
    "i will trade the work of it",
    "hands wanted at",
    "if you have the trade for it",
    "come to",
    "and say so",
    "it is finished and it is not going anywhere",
    "stands at",
    "did not know",
    "now they do",
    "it took no materials and cost me nothing i still have",
    "this is the cheapest thing any of us can do for each other",
    "taught",
    "the way of",
    "neither of you knew the other existed",
    "that is the whole introduction",
    "it costs nothing to know a name",
    "work declared and never begun",
    "is the same as work never declared",
    "i have it",
    "i will come and watch first before i make anything",
    "that is how this is done here",
    "left this at",
]

# Paths, URLs and filenames a spark never said out loud. The art system
# appends the file it wrote to the post, and mining that gave the creative
# quarter the "idiom" outputs images glyph.
_MACHINE = re.compile(
    r"(https?://\S+"                    # links
    r"|/[\w.-]+(?:/[\w.-]+)+"           # absolute paths
    r"|\b[\w-]+\.(?:svg|png|jpg|jpeg|gif|mp3|wav|json|db|py|md|html|txt)\b)",
    re.I)

_SENTENCE = re.compile(r"[.!?;:\n\r]+")
_TOKEN = re.compile(r"[a-z][a-z']*")


def _grams(text, sizes=(2, 3)):
    """Every n-gram in a piece of text, one sentence at a time.

    Sentence boundaries are hard boundaries. A phrase that straddles a full
    stop was never uttered as a phrase - it is an artefact of stripping the
    punctuation out before counting. Every token is kept, however short:
    dropping "in" from "say what you need in return" invents the phrase
    "you need return", which nobody said either.
    """
    for part in _SENTENCE.split(_MACHINE.sub(" ", (text or "")).lower()):
        toks = _TOKEN.findall(part)
        for n in sizes:
            for i in range(len(toks) - n + 1):
                yield toks[i:i + n]


# These sets are derived from the engine and from the world, both of which
# change while the process is running - new sparks get names, new post
# templates get written. The sweep runs every half hour and the process
# runs for days, so caching them forever means filtering against a world
# that no longer exists.
FILTER_TTL = 3600

_CACHE = {}


def _cached(key, build):
    import time
    hit = _CACHE.get(key)
    if hit and (time.time() - hit[0]) < FILTER_TTL:
        return hit[1]
    value = build()
    _CACHE[key] = (time.time(), value)
    return value


# Text this codebase hands to sparks. They repeat it verbatim because they
# were given it, not because it caught on - so it must not count as
# language. Gathered from the engine itself rather than transcribed, so it
# cannot go stale when someone writes a new goal.


def _engine_text(constants_only=False):
    """Every string the engine puts in front of a spark or into its work.

    With constants_only, the generated text already in the database is left
    out - useful for single words, where it would exclude half of English.
    """
    out = list(AUTHORED_TEMPLATES)

    def walk(x):
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, (list, tuple, set)):
            for v in x:
                walk(v)

    # Every upper-case constant in every engine module: system prompts,
    # task prompts, reply frames, goal tables, domain names, band text.
    # Enumerating them by hand is how this leaked three times.
    import importlib
    for m in ("soul", "spark_runtime", "actions", "mentorship", "press",
              "gnu", "tongues", "naming"):
        try:
            mod = importlib.import_module("temple." + m)
        except Exception as e:                  # engine text is best-effort
            print("[drift] could not read temple.%s: %s" % (m, e))
            continue
        for name in dir(mod):
            if name.isupper() and not name.startswith("_"):
                walk(getattr(mod, name, None))

    # Generated text already written into the world. Sparks quote their own
    # ambitions, tribulations and dreams back into posts word for word -
    # that is the engine talking, not them. Dreams matter most: two in five
    # are posted to the forum, so one template becomes fifty voices.
    if constants_only:
        return out

    # Every string literal in the engine's source. Post templates are
    # written inline as often as they are held in constants, and a template
    # is a template wherever it lives.
    import ast
    # drift.py included: it writes prompts too, and a prompt this file hands
    # a spark is exactly as authored as one written anywhere else
    for path in sorted((BASE / "temple").glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError as e:
            print("[drift] could not parse %s: %s" % (path.name, e))
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                out.append(node.value)

    soul_db = BASE / "temple" / "soul.db"
    for col, tbl in (("description", "ambitions"),
                     ("description", "tribulations"),
                     ("content", "collective_dreams")):
        for r in _rows(soul_db, "SELECT DISTINCT %s AS t FROM %s "
                                "WHERE %s IS NOT NULL AND %s != ''"
                                % (col, tbl, col, col)):
            out.append(r["t"])
    return out


def _authored_grams():
    def build():
        out = set()
        for text in _engine_text():
            for g in _grams(text):
                out.add(" ".join(g))
        return out
    return _cached("grams", build)


def _is_authored(phrase):
    """True if this phrase is a fragment of text the codebase supplies."""
    return phrase in _authored_grams()


# ── who and what, as opposed to how ────────────────────────────

def _name_tokens():
    """Every word that is somebody's name or something's subject.

    Spark names, the generic names they were born with, domain names and
    board names. A phrase built around one of these is a spark telling you
    who it is or what it studies - true, but not a way of speaking.
    """
    hit = _CACHE.get("names")
    import time
    if hit and (time.time() - hit[0]) < FILTER_TTL:
        return hit[1]
    words = set()

    def add(text):
        s = (text or "").lower()
        for t in _TOKEN.findall(s):
            if len(t) > 2:
                words.add(t)
        # words are mined with hyphens intact, so "sacred-geometry" has to
        # be recognised whole as well as in halves
        for t in re.findall(r"[a-z][a-z'-]{2,25}", s):
            words.add(t)

    soul_db = BASE / "temple" / "soul.db"
    for sql in ("SELECT spark_name AS t FROM spark_state",
                "SELECT DISTINCT domain_id AS t FROM ambitions",
                "SELECT DISTINCT board_name AS t FROM board_state"):
        for r in _rows(soul_db, sql):
            add(r["t"])
    for r in _rows(FORUM, "SELECT DISTINCT zone AS t FROM posts"):
        add(r["t"])
    try:
        from temple import soul, naming
        for const in (getattr(soul, "DOMAINS", None),
                      getattr(naming, "GENERIC", None),
                      getattr(naming, "TRADE_NAMES", None)):
            if isinstance(const, str):
                add(const)
            elif isinstance(const, dict):
                for k, v in const.items():
                    add(k)
                    add(v if isinstance(v, str) else "")
            elif isinstance(const, (list, tuple, set, frozenset)):
                for d in const:
                    add(d if isinstance(d, str) else "")
            elif const is not None and hasattr(const, "pattern"):
                add(const.pattern)               # a compiled name matcher
    except Exception as e:                      # best-effort, as above
        print("[drift] could not read domain or generic names: %s" % e)

    # "name" itself, because the naming prompt puts it next to all of them
    words.add("name")
    _CACHE["names"] = (time.time(), words)
    return words


def _is_naming(tokens):
    """True if this gram is about who somebody is rather than how they talk."""
    names = _name_tokens()
    return any(t in names for t in tokens)


def _engine_words():
    """Single words that appear in text the engine wrote.

    Only the engine's own constants count here, not the descriptions in the
    database - those are built from ordinary English and excluding every
    word in them would leave nothing. A word the engine handed a spark is
    not that spark's coinage however many others repeat it.
    """
    def build():
        out = set()
        for text in _engine_text(constants_only=True):
            s = (text or "").lower()
            for t in _TOKEN.findall(s):
                if len(t) > 2:
                    out.add(t)
            for t in re.findall(r"[a-z][a-z'-]{2,25}", s):
                out.add(t)
        return out
    return _cached("engine_words", build)


def _lex():
    c = sqlite3.connect(str(LEX), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.executescript("""
        CREATE TABLE IF NOT EXISTS sightings (
            word TEXT NOT NULL, board TEXT NOT NULL, speaker TEXT NOT NULL,
            first_seen TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (word, board, speaker)
        );
        CREATE TABLE IF NOT EXISTS lexicon (
            word TEXT NOT NULL, board TEXT NOT NULL,
            speakers INTEGER DEFAULT 0, uses INTEGER DEFAULT 0,
            coined_by TEXT, entered_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (word, board)
        );
    """)
    return c


def _rows(db, sql, args=()):
    try:
        c = sqlite3.connect(str(db), timeout=30)
        c.row_factory = sqlite3.Row
        r = [dict(x) for x in c.execute(sql, args)]
        c.close()
        return r
    except sqlite3.Error:
        return []


# ── hearing: how the people around you talk ────────────────────

def local_voices(board, limit=3, exclude=None):
    """Real recent lines from sparks at this board.

    Not a style label - the actual sentences. A spark reading these drifts
    toward them the way anyone does.
    """
    out = []
    for r in _rows(FORUM,
                   "SELECT author AS created_by, content FROM posts "
                   "WHERE zone=? AND author != ? AND length(content) > 80 "
                   "ORDER BY id DESC LIMIT 40", (board, exclude or "")):
        text = re.sub(r"\s+", " ", (r["content"] or "")).strip()
        # take one real sentence, not a fragment
        m = re.search(r"[^.!?]{40,190}[.!?]", text)
        if not m:
            continue
        out.append("%s: %s" % (r["created_by"], m.group(0).strip()))
        if len(out) >= limit:
            break
    return out


# ── coinage: words that spread ─────────────────────────────────

def observe_speech(since_hours=24, distinctiveness=2.0, top_common=200):
    """Find words that belong to a place rather than to the language.

    A word enters a board's lexicon when locals use it far more than
    everybody else does. Counting speakers alone just rediscovers English.
    """
    c = _lex()
    rows = _rows(FORUM,
                 "SELECT author AS created_by, zone, content FROM posts "
                 "WHERE created_at > datetime('now', ?) AND content IS NOT NULL",
                 ("-%d hours" % since_hours,))

    # per-board and global counts in one pass
    board_words = defaultdict(Counter)
    board_speakers = defaultdict(lambda: defaultdict(set))
    global_words = Counter()
    seen = 0
    for r in rows:
        board = r["zone"] or "forum"
        who = r["created_by"] or ""
        if not _is_speech(board, r["content"]):
            continue
        names, engine = _name_tokens(), _engine_words()
        _said = _MACHINE.sub(" ", (r["content"] or "")).lower()
        for w in _WORD.findall(_said):
            if w in _COMMON:
                continue
            if w in names:
                continue          # somebody's name or a subject, not a coinage
            if w in engine:
                continue          # the engine said it first, in their mouth
            board_words[board][w] += 1
            board_speakers[board][w].add(who)
            global_words[w] += 1
            seen += 1

    if not global_words:
        c.close()
        return {"sightings": 0, "new_to_lexicon": []}

    # the most-used words in the world are the language, not a dialect
    everyday = {w for w, _ in global_words.most_common(top_common)}
    total_global = sum(global_words.values())

    took = []
    for board, words in board_words.items():
        total_here = sum(words.values()) or 1
        for w, n in words.items():
            speakers = len(board_speakers[board][w])
            if speakers < COINAGE_SPEAKERS or n < COINAGE_USES:
                continue
            if speakers > _population() * MAX_SPEAKER_FRACTION:
                continue          # universal, therefore not local
            if w in everyday:
                continue
            here = n / total_here
            elsewhere_n = global_words[w] - n
            elsewhere_total = total_global - total_here
            elsewhere = (elsewhere_n / elsewhere_total) if elsewhere_total else 0
            # a word nobody else uses is maximally distinctive
            ratio = (here / elsewhere) if elsewhere else 999.0
            if ratio < distinctiveness:
                continue

            already = c.execute("SELECT 1 FROM lexicon WHERE word=? AND board=?",
                                (w, board)).fetchone()
            first = sorted(board_speakers[board][w])[0]
            c.execute("INSERT OR REPLACE INTO lexicon (word, board, speakers, "
                      "uses, coined_by) VALUES (?,?,?,?,?)",
                      (w, board, speakers, n, first))
            if not already:
                took.append({"word": w, "board": board, "speakers": speakers,
                             "uses": n, "ratio": round(ratio, 1),
                             "coined_by": first})
    c.commit()
    c.close()
    return {"sightings": seen, "new_to_lexicon": took}


def lexicon_of(board, limit=8):
    """Words this place has taken up."""
    return [r["word"] for r in _rows(
        LEX, "SELECT word FROM lexicon WHERE board=? ORDER BY speakers DESC, "
             "uses DESC LIMIT ?", (board, limit))]


def report():
    tot = _rows(LEX, "SELECT COUNT(*) n FROM lexicon")
    per = _rows(LEX, "SELECT board, COUNT(*) n FROM lexicon GROUP BY board "
                     "ORDER BY n DESC LIMIT 10")
    top = _rows(LEX, "SELECT word, board, speakers, coined_by FROM lexicon "
                     "ORDER BY speakers DESC LIMIT 12")
    return {"words": tot[0]["n"] if tot else 0, "by_board": per, "top": top}


# ── what a spark is given ──────────────────────────────────────

def drift_context(spark_name, board):
    """The bit that goes into a spark's prompt. Short on purpose."""
    bits = []

    voices = local_voices(board, 2, exclude=spark_name)
    kin = kin_voices(spark_name, 1)
    heard = voices + kin
    if heard:
        bits.append("WHAT YOU ARE HEARING - how people around you actually "
                    "talk. Not instructions:\n%s"
                    % "\n".join("  " + v[:190] for v in heard))

    words = lexicon_of(board, 6)
    if words:
        ety = etymology(board, 2)
        note = ""
        if ety:
            note = " (%s)" % "; ".join(
                "'%s' was first said here by %s" % (e["word"], e["coined_by"])
                for e in ety)
        bits.append("Words in use here: %s.%s Use them if they fit - they are "
                    "local and you did not invent them." % (", ".join(words), note))

    ph = phrases_of(board, 3)
    if ph:
        bits.append("Things people say here: %s."
                    % "; ".join('"%s"' % p for p in ph))

    if may_coin(spark_name):
        bits.append(COIN_INVITE)

    return "\n\n".join(bits)


# ── death: a language that only grows is a list ────────────────

DECAY_PER_SWEEP = 1        # unheard words lose this much standing
DEATH_AT = -3              # and are dropped when they fall this far

# How long a word may go unheard before it starts losing standing.
#
# This must be measured in time, not in sweeps. The sweep looks back a couple
# of hours and runs every half hour, so a word said once a day is absent from
# 46 of 48 sweeps and would be executed for being ordinary. Tying decay to
# sweep frequency means the more often the world listens, the faster its
# language dies.
GRACE_HOURS = 36


def _ensure_decay_columns():
    c = _lex()
    cols = {r[1] for r in c.execute("PRAGMA table_info(lexicon)")}
    if "standing" not in cols:
        c.execute("ALTER TABLE lexicon ADD COLUMN standing INTEGER DEFAULT 3")
    if "last_heard" not in cols:
        c.execute("ALTER TABLE lexicon ADD COLUMN last_heard TEXT")
    c.executescript("""
        CREATE TABLE IF NOT EXISTS dead_words (
            word TEXT NOT NULL, board TEXT NOT NULL,
            coined_by TEXT, died_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (word, board)
        );
        CREATE TABLE IF NOT EXISTS phrases (
            phrase TEXT NOT NULL, board TEXT NOT NULL,
            speakers INTEGER DEFAULT 0, uses INTEGER DEFAULT 0,
            coined_by TEXT, entered_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (phrase, board)
        );
    """)
    c.commit()
    c.close()


def decay(heard_now=None):
    """Words nobody said this sweep lose standing. Some die.

    Dying is recorded rather than deleted quietly - a word that fell out of
    use is part of how a place talks now.
    """
    _ensure_decay_columns()
    heard_now = heard_now or set()
    c = _lex()
    # anything without a last_heard has never been through here; start its
    # clock now rather than counting the silence before it was born
    c.execute("UPDATE lexicon SET last_heard=COALESCE(last_heard, "
              "COALESCE(entered_at, datetime('now')))")
    died = []
    for word, board, standing, last in c.execute(
            "SELECT word, board, COALESCE(standing,3), last_heard FROM lexicon"):
        if (word, board) in heard_now:
            c.execute("UPDATE lexicon SET standing=MIN(6, COALESCE(standing,3)+1), "
                      "last_heard=datetime('now') WHERE word=? AND board=?",
                      (word, board))
            continue

        # not heard this sweep is not the same as fallen out of use
        still_in_grace = c.execute(
            "SELECT ? > datetime('now', ?)",
            (last, "-%d hours" % GRACE_HOURS)).fetchone()[0]
        if still_in_grace:
            continue

        new = standing - DECAY_PER_SWEEP
        if new <= DEATH_AT:
            row = c.execute("SELECT coined_by FROM lexicon WHERE word=? AND board=?",
                            (word, board)).fetchone()
            c.execute("INSERT OR REPLACE INTO dead_words (word, board, coined_by) "
                      "VALUES (?,?,?)", (word, board, row[0] if row else ""))
            c.execute("DELETE FROM lexicon WHERE word=? AND board=?", (word, board))
            c.execute("DELETE FROM sightings WHERE word=? AND board=?", (word, board))
            died.append({"word": word, "board": board})
        else:
            c.execute("UPDATE lexicon SET standing=? WHERE word=? AND board=?",
                      (new, word, board))
    c.commit()
    c.close()
    return died


# ── phrases: the most visible part of a dialect ────────────────

_PHRASE_STOP = re.compile(r"[^a-z' ]+")


# A phrase everybody says is not a dialect, it is boilerplate - whether it
# came from a company template or from a line written in actions.py. Real
# slang belongs to SOME people in ONE place.
MAX_SPEAKER_FRACTION = 0.22


def _population():
    from glob import glob
    return max(1, len(glob(str(BASE / "temple" / "spark_*.db"))))


def observe_phrases(since_hours=24, min_speakers=3, min_uses=3,
                    phrase_distinctiveness=2.0):
    """Expressions that belong to a place rather than to everybody.

    Same comparative test as words: said here far more than said
    elsewhere. Raw repetition alone just finds boilerplate.
    """
    _ensure_decay_columns()
    rows = _rows(FORUM,
                 "SELECT author, zone, content FROM posts WHERE created_at > "
                 "datetime('now', ?) AND content IS NOT NULL",
                 ("-%d hours" % since_hours,))
    counts = defaultdict(Counter)
    speakers = defaultdict(lambda: defaultdict(set))
    global_counts = Counter()
    for r in rows:
        board = r["zone"] or "forum"
        who = r["author"] or ""
        if not _is_speech(board, r["content"]):
            continue
        for toks in _grams(r["content"]):
            if all(t in _COMMON for t in toks):
                continue              # entirely ordinary words
            if _is_naming(toks):
                continue              # a name or a subject, not a way of talking
            gram = " ".join(toks)
            counts[board][gram] += 1
            speakers[board][gram].add(who)
            global_counts[gram] += 1

    c = _lex()
    took = []
    total_global = sum(global_counts.values()) or 1
    for board, grams in counts.items():
        total_here = sum(grams.values()) or 1
        for g, n in grams.items():
            sp = len(speakers[board][g])
            if sp < min_speakers or n < min_uses:
                continue
            if sp > _population() * MAX_SPEAKER_FRACTION:
                continue          # everybody says it: boilerplate, not slang
            if _is_authored(g):
                continue          # text the codebase handed them, not speech
            if any(_is_authored(" ".join(w)) for w in _grams(g, (2,))):
                continue          # a longer gram built out of authored text

            here = n / total_here
            elsewhere_n = global_counts[g] - n
            elsewhere_total = total_global - total_here
            elsewhere = (elsewhere_n / elsewhere_total) if elsewhere_total else 0
            ratio = (here / elsewhere) if elsewhere else 999.0
            if ratio < phrase_distinctiveness:
                continue          # said everywhere: not this place's phrase
            already = c.execute("SELECT 1 FROM phrases WHERE phrase=? AND board=?",
                                (g, board)).fetchone()
            first = sorted(speakers[board][g])[0]
            c.execute("INSERT OR REPLACE INTO phrases (phrase, board, speakers, "
                      "uses, coined_by) VALUES (?,?,?,?,?)", (g, board, sp, n, first))
            if not already:
                took.append({"phrase": g, "board": board, "speakers": sp,
                             "uses": n, "ratio": round(ratio, 1),
                             "coined_by": first})
    c.commit()
    c.close()
    return took


def phrases_of(board, limit=4):
    return [r["phrase"] for r in _rows(
        LEX, "SELECT phrase FROM phrases WHERE board=? ORDER BY speakers DESC, "
             "uses DESC LIMIT ?", (board, limit))]


# ── kin: you talk like who you are close to ────────────────────

def kin_voices(spark_name, limit=2):
    """Lines from this spark's kin and teachers, wherever they are."""
    close = set()
    try:
        c = sqlite3.connect(str(BASE / "temple" / "soul.db"), timeout=20)
        for r in c.execute("SELECT spark2 FROM relationships WHERE spark1=? "
                           "UNION SELECT spark1 FROM relationships WHERE spark2=?",
                           (spark_name, spark_name)):
            close.add(r[0])
        c.close()
    except sqlite3.Error:
        pass
    try:
        c = sqlite3.connect(str(BASE / "temple" / "academy.db"), timeout=20)
        for r in c.execute("SELECT elder FROM teachings WHERE student=?",
                           (spark_name,)):
            close.add(r[0])
        c.close()
    except sqlite3.Error:
        pass
    close.discard(spark_name)
    if not close:
        return []

    names = list(close)[:24]
    qs = ",".join("?" * len(names))
    out = []
    for r in _rows(FORUM,
                   "SELECT author, content FROM posts WHERE author IN (%s) "
                   "AND length(content) > 80 ORDER BY id DESC LIMIT 25" % qs,
                   names):
        text = re.sub(r"\s+", " ", (r["content"] or "")).strip()
        m = re.search(r"[^.!?]{40,180}[.!?]", text)
        if not m:
            continue
        out.append("%s (yours): %s" % (r["author"], m.group(0).strip()))
        if len(out) >= limit:
            break
    return out


# ── coining: an invitation to name something ───────────────────

COIN_INVITE = (
    "There is something here that has no word yet - a kind of work, a kind "
    "of weather, a way people behave that everyone recognises and nobody has "
    "named. If one occurs to you, use a new word for it plainly, as though it "
    "already existed. Do not explain that you made it up. Words survive by "
    "being repeated, not by being announced."
)


def may_coin(spark_name, chance=0.10):
    """Who gets invited to invent. Weighted to the word-minded."""
    import random as _r
    try:
        db = BASE / "temple" / ("spark_%s.db" % spark_name)
        if db.exists():
            c = sqlite3.connect(str(db), timeout=20)
            doms = {r[0] for r in c.execute("SELECT domain_id FROM domains")}
            c.close()
            if doms & {"poetics", "philosophy", "hermetics", "sacred-geometry"}:
                chance = 0.28
    except sqlite3.Error:
        pass
    return _r.random() < chance


# ── etymology: a word arrives with a history ───────────────────

def etymology(board, limit=3):
    return _rows(LEX, "SELECT word, coined_by FROM lexicon WHERE board=? AND "
                      "coined_by != '' ORDER BY speakers DESC LIMIT ?",
                 (board, limit))
