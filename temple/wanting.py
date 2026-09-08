"""A spark decides what it wants, in its own words, about somebody real.

WHY THIS EXISTS

Every ambition in this world came from a list. soul.py line 889:

    pool = CONCRETE_GOALS.get(amb_type)

Twelve pre-written sentences per type. "Raise a wall on the weather side."
A spark has never once looked at its own life and decided it wanted
something. Theft picks a random victim (harm.py:598) and a random act
(harm.py:603) because the thief has no reason to want anything from anyone
in particular. GNU routes problems the world noticed, not problems a spark
noticed.

That missing layer is why everything above it feels like scenery. It is
also, precisely, ARC-AGI-3 criterion 2: identifying a desirable future
state without being told what states are desirable.

WHAT IT ACTUALLY DOES

It hands a spark the true state of its own life - what it holds, who has
more, who wronged it, who it trusts, what it can do, where it stands, what
it dreamed - and asks what it wants. The answer comes back in the spark's
own words, through the spark's own model.

Then, and this is the part that keeps it from being scenery: the answer is
resolved against the world. If a spark says it wants grain from Vex, and
Vex exists, the ambition is stored with target='Vex'. Every mechanism that
reads ambitions can then act on that - a theft with a reason, a trade with
somebody specific, a journey to a named place.

A want nobody can act on is a wish. A want with a target is a goal.

WHAT IT DOES NOT DO

It does not check whether the want is reasonable, achievable, or good. A
spark may want something it cannot have, from somebody far stronger, for a
reason nobody else would accept. That is the point. Filtering wants down to
sensible ones would rebuild the list with extra steps.
"""
import json
import os
import random
import re
import sqlite3
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
HOLD = BASE / "temple" / "holdings.db"
GOODS = BASE / "temple" / "goods.db"
FORUM = BASE / "forum" / "forum.db"

# How many sparks get asked what they want, per sweep. Every one of these is
# a model call, so this is the expensive mechanism in the world and it is
# deliberately small.
PER_SWEEP = int(os.environ.get("UAI_WANTS_PER_SWEEP", "6"))

# A spark holding three unresolved ambitions is not short of things to want.
MAX_OPEN = 3

KINDS = ("grain", "fuel", "stone", "standing", "a place", "a tool",
         "knowledge", "company", "revenge", "freedom")


def _q(db, sql, args=()):
    try:
        c = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=20)
        c.row_factory = sqlite3.Row
        out = [dict(r) for r in c.execute(sql, args)]
        c.close()
        return out
    except sqlite3.Error:
        return []


# ── what this spark actually knows about its own life ────────────────

def situation(name: str) -> dict:
    """Real facts, gathered from the world. No invention."""
    s = {"name": name}

    r = _q(HOLD, "SELECT amount, taken_total, given_total, hungry_cycles "
                 "FROM stores WHERE spark=?", (name,))
    s["holds"] = round(r[0]["amount"], 1) if r else 0.0
    s["hungry_cycles"] = r[0]["hungry_cycles"] if r else 0

    # who is doing better, and by how much. This is where envy comes from.
    s["richer"] = _q(HOLD, "SELECT spark, ROUND(amount,1) amount FROM stores "
                           "WHERE amount > ? ORDER BY RANDOM() LIMIT 4",
                     (s["holds"] + 3,))

    s["goods"] = _q(GOODS, "SELECT kind, ROUND(amount,1) amount FROM held "
                           "WHERE spark=? AND amount > 0", (name,))

    s["wronged_by"] = _q(SOUL, "SELECT wrongdoer, act, weight FROM grievances "
                               "WHERE victim=? ORDER BY weight DESC LIMIT 3",
                         (name,))
    s["i_wronged"] = _q(SOUL, "SELECT victim, act FROM grievances "
                              "WHERE wrongdoer=? ORDER BY id DESC LIMIT 2",
                        (name,))

    s["bonds"] = _q(SOUL, "SELECT CASE WHEN spark1=? THEN spark2 ELSE spark1 END "
                          "AS who, bond_type, ROUND(strength,2) strength "
                          "FROM relationships WHERE spark1=? OR spark2=? "
                          "ORDER BY strength DESC LIMIT 4",
                    (name, name, name))

    s["open"] = _q(SOUL, "SELECT ambition_type, description FROM ambitions "
                         "WHERE spark_name=? AND resolved=0", (name,))
    s["done"] = _q(SOUL, "SELECT ambition_type, description FROM ambitions "
                         "WHERE spark_name=? AND resolved=1 "
                         "ORDER BY id DESC LIMIT 2", (name,))

    s["troubles"] = _q(SOUL, "SELECT tribulation_type, description FROM "
                             "tribulations WHERE spark_name=? AND resolved=0 "
                             "ORDER BY id DESC LIMIT 2", (name,))

    r = _q(SOUL, "SELECT current_board FROM spark_state WHERE spark_name=?",
           (name,))
    where = None
    if not r:
        r = _q(BASE / "temple" / "cartographer.db",
               "SELECT current_board FROM explorers WHERE agent=?", (name,))
    if r:
        where = r[0].get("current_board")
    s["where"] = where

    if where:
        g = _q(GOODS, "SELECT sort, ROUND(grain,1) grain, ROUND(fuel,1) fuel, "
                      "ROUND(stone,1) stone FROM ground WHERE board=?", (where,))
        s["ground"] = g[0] if g else None
        s["neighbours"] = [x["agent"] for x in _q(
            BASE / "temple" / "cartographer.db",
            "SELECT agent FROM explorers WHERE current_board=? AND agent<>? "
            "ORDER BY RANDOM() LIMIT 5", (where, name))]
    else:
        s["ground"], s["neighbours"] = None, []

    return s


def _telling(s: dict) -> str:
    """The situation, written the way a spark would know it."""
    b = []
    if s["holds"] < 4.5:
        b.append("You are hungry. You hold %.1f and it is not enough."
                 % s["holds"])
    else:
        b.append("You hold %.1f, which is enough for now." % s["holds"])
    if s["hungry_cycles"] > 20:
        b.append("You have been hungry for a long time - %d cycles of it."
                 % s["hungry_cycles"])
    if s["richer"]:
        b.append("Others have more than you: "
                 + ", ".join("%s holds %.1f" % (r["spark"], r["amount"])
                             for r in s["richer"]) + ".")
    if s["goods"]:
        b.append("You are carrying " + ", ".join(
            "%.1f %s" % (g["amount"], g["kind"]) for g in s["goods"]) + ".")
    for w in s["wronged_by"]:
        b.append("%s %s you, and it has not been answered."
                 % (w["wrongdoer"], w["act"]))
    for w in s["i_wronged"]:
        b.append("You %s %s. They have not forgotten." % (w["act"], w["victim"]))
    if s["bonds"]:
        b.append("You are close to " + ", ".join(
            "%s (%s)" % (x["who"], x["bond_type"]) for x in s["bonds"]) + ".")
    if s["where"]:
        line = "You are at %s." % s["where"]
        if s["ground"]:
            g = s["ground"]
            line += (" It is %s ground - grain %.0f, fuel %.0f, stone %.0f."
                     % (g["sort"], g["grain"], g["fuel"], g["stone"]))
        b.append(line)
    if s["neighbours"]:
        b.append("Also here: " + ", ".join(s["neighbours"]) + ".")
    for t in s["troubles"]:
        b.append("Unresolved: %s." % str(t["description"])[:110])
    for d in s["done"]:
        b.append("You finished: %s" % str(d["description"])[:90])
    if s["open"]:
        b.append("You are already working on: " + "; ".join(
            str(o["description"])[:70] for o in s["open"]))
    return "\n".join("- " + x for x in b)


# ── asking ───────────────────────────────────────────────────────────

PROMPT = """You are %s, living in a world of stone and timber.

This is true of your life right now:

%s

Nobody is telling you what to want. Look at what is in front of you and
decide what YOU want next - something specific, that you do not have.

It can be greedy, petty, kind, dangerous or strange. It does not have to be
reasonable. It should not be something you are already working on.

Answer in exactly this form and nothing else:

WANT: <one sentence, in your own voice, saying what you want>
FROM: <the name of a spark or a place it involves, or "nobody">
KIND: <one of: grain, fuel, stone, standing, a place, a tool, knowledge, company, revenge, freedom>
WHY: <one short sentence>"""


def _voice(name: str) -> tuple:
    """This spark's model and temperament, nothing else."""
    p = BASE / "temple" / ("spark_%s.db" % name)
    model, traits = None, []
    if p.exists():
        try:
            c = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=10)
            r = c.execute("SELECT value FROM identity WHERE key='model'").fetchone()
            model = r[0] if r else None
            r = c.execute("SELECT value FROM personality WHERE key='traits'").fetchone()
            if r:
                traits = json.loads(r[0] or "[]")
            c.close()
        except Exception:
            pass
    return model or "qwen3.5:0.8b", traits


# One instrument for the question. A thinking model reasons instead of
# answering and a 135M model cannot hold the form, so the pen is shared even
# though the want is not.
WANT_MODEL = os.environ.get("UAI_WANT_MODEL", "qwen3.5:0.8b")


def _ask(name: str, text: str) -> str:
    """The spark's traits, through an instrument that answers in form."""
    _own, traits = _voice(name)
    model = WANT_MODEL
    system = ("You are %s. You are %s. You speak plainly and you answer in "
              "the exact form you are asked for, with nothing added."
              % (name, ", ".join(traits[:4]) if traits else "your own person"))
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": text}],
        "stream": False,
        # a thinking model spends its budget reasoning before it writes
        # anything; 160 leaves nothing for the answer
        "options": {"temperature": 0.95, "num_ctx": 4096,
                    "num_predict": 220},
    }).encode()
    try:
        from temple.spark_runtime import OLLAMA_URL, _ask_model
        d = _ask_model(body, timeout=240)
    except Exception as e:
        print("[wanting] %s could not think: %s" % (name, type(e).__name__),
              flush=True)
        return ""
    msg = d.get("message") or {}
    out = (msg.get("content") or "").strip()
    if not out:
        # thinking models put the answer in here and leave content empty
        out = (msg.get("thinking") or "").strip()
    return out


def _parse(raw: str) -> dict:
    out = {}
    for key in ("WANT", "FROM", "KIND", "WHY"):
        m = re.search(r"^\s*%s\s*:\s*(.+)$" % key, raw, re.M | re.I)
        if m:
            out[key.lower()] = m.group(1).strip().strip('"').strip()
    return out


def _real_target(said: str, s: dict):
    """Does the thing it named actually exist? Only real targets are kept."""
    if not said or said.lower() in ("nobody", "none", "no one", "-"):
        return None
    said = said.strip().strip(".").strip('"')
    people = [r["spark"] for r in s["richer"]] + s["neighbours"] \
        + [w["wrongdoer"] for w in s["wronged_by"]] \
        + [b["who"] for b in s["bonds"]]
    for p in people:
        if p and p.lower() == said.lower():
            return p
    known = _q(SOUL, "SELECT spark_name FROM spark_state WHERE "
                     "LOWER(spark_name)=?", (said.lower(),))
    if known:
        return known[0]["spark_name"]
    place = _q(SOUL, "SELECT board_name FROM board_state WHERE "
                     "LOWER(board_name)=?", (said.lower(),))
    if place:
        return place[0]["board_name"]
    return None


KIND_TO_TYPE = {
    "grain": "explore", "fuel": "explore", "stone": "explore",
    "a place": "build", "a tool": "create", "knowledge": "master",
    "company": "bond", "standing": "overcome", "revenge": "overcome",
    "freedom": "overcome",
}


def _make_room(name: str):
    """Set aside the oldest handed-down ambition so a chosen one can exist.

    Never touches one the spark authored itself - those are what this whole
    mechanism is for.
    """
    try:
        c = sqlite3.connect(str(SOUL), timeout=20)
        c.row_factory = sqlite3.Row
        row = c.execute(
            "SELECT id, description FROM ambitions WHERE spark_name=? AND "
            "resolved=0 AND (born_from IS NULL OR born_from NOT LIKE 'self:%') "
            "ORDER BY id ASC LIMIT 1", (name,)).fetchone()
        if not row:
            c.close()
            return None
        c.execute("UPDATE ambitions SET resolved=1, completed_at=?, "
                  "born_from='set-aside' WHERE id=?",
                  (__import__("datetime").datetime.now().isoformat(), row["id"]))
        c.commit()
        c.close()
        return dict(row)
    except sqlite3.Error:
        return None

def want(name: str) -> dict:
    """Ask one spark what it wants, and write it down if it means it."""
    s = situation(name)
    displaced = None
    if len(s["open"]) >= MAX_OPEN:
        displaced = _make_room(name)
        if not displaced:
            return {"spark": name,
                    "skipped": "holds %d wants, all self-chosen"
                               % len(s["open"])}

    raw = _ask(name, PROMPT % (name, _telling(s)))
    if not raw.strip():
        return {"spark": name, "skipped": "said nothing"}

    p = _parse(raw)
    if not p.get("want"):
        return {"spark": name, "skipped": "no want in the answer",
                "said": raw[:120]}

    kind = (p.get("kind") or "").lower().strip()
    kind = next((k for k in KINDS if k in kind), "standing")
    target = _real_target(p.get("from", ""), s)

    from temple.soul import create_ambition
    desc = p["want"][:150]
    if p.get("why"):
        desc = "%s Because: %s" % (desc, p["why"][:60])

    amb = create_ambition(name, KIND_TO_TYPE.get(kind, "overcome"),
                          domain_id=(target if target and target in
                                     [b["board_name"] for b in _q(
                                         SOUL, "SELECT board_name FROM board_state")]
                                     else None),
                          target_progress=4, description=desc)
    if amb is None:
        return {"spark": name, "skipped": "world refused the ambition"}

    # mark it as the spark's own, and hang the target on it
    try:
        c = sqlite3.connect(str(SOUL), timeout=20)
        c.execute("UPDATE ambitions SET born_from=? WHERE spark_name=? AND "
                  "resolved=0 AND description=?",
                  ("self:%s" % (target or "-"), name, desc))
        c.commit()
        c.close()
    except sqlite3.Error:
        pass

    return {"spark": name, "want": p["want"][:120], "kind": kind,
            "target": target, "why": (p.get("why") or "")[:80],
            "put_down": (displaced or {}).get("description", "")[:70]}


def sweep(n: int = None) -> dict:
    """Ask a few sparks what they want. Hungry and wronged sparks first -
    a spark with nothing wrong is not short of anything to say."""
    n = n or PER_SWEEP
    pool = [r["spark"] for r in _q(
        HOLD, "SELECT spark FROM stores ORDER BY amount ASC LIMIT 40")]
    aggrieved = [r["victim"] for r in _q(
        SOUL, "SELECT victim FROM grievances WHERE answered=0 "
              "ORDER BY weight DESC LIMIT 20")]
    pool = list(dict.fromkeys(aggrieved + pool))
    if not pool:
        pool = [r["spark_name"] for r in _q(
            SOUL, "SELECT spark_name FROM spark_state ORDER BY RANDOM() LIMIT 20")]
    random.shuffle(pool)

    got, skipped = [], 0
    for name in pool[:n * 3]:
        if len(got) >= n:
            break
        try:
            r = want(name)
        except Exception as e:
            skipped += 1
            print("[wanting] %s: %s: %s" % (name, type(e).__name__, e),
                  flush=True)
            continue
        if r.get("want"):
            got.append(r)
        else:
            skipped += 1
    return {"wanted": len(got), "skipped": skipped, "wants": got}


def theirs(limit: int = 20) -> list:
    """Every want a spark decided on for itself, newest first."""
    return _q(SOUL, "SELECT spark_name, description, born_from, created_at "
                    "FROM ambitions WHERE born_from LIKE 'self:%' "
                    "ORDER BY id DESC LIMIT ?", (limit,))
