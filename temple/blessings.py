"""What a blessing is for.

Eight shrines stand in the world and reaching one costs real cycles on the
road. Until now arriving earned a word in a list and nothing else, which
made the whole pilgrimage a formality with a long walk attached.

A blessing now does something, and what it does follows from what the shrine
is. The Great Library makes study go further. The Monastery lets you teach
sooner, because you have sat with what you know. The Forum of Ages, which is
where all paths begin, makes the road cheaper - you have learned where
things are in relation to each other.

None of these are large. A blessing should feel like an advantage, not a
cheat, and a spark that has walked to eight separate places has earned an
advantage.

The whole road walked is different in kind: it lets a spark give a blessing
away. That is the only thing here that creates something for somebody else,
and it seemed right that finishing the longest journey in the world should
be the thing that does it.
"""
import json
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PILG = BASE / "temple" / "pilgrimage.db"

# what each shrine confers, and what it actually does
BLESSINGS = {
    "center": {
        "shrine": "The Forum of Ages",
        "means": "You have learned where things stand in relation to each "
                 "other. The road is shorter for you than for others walking "
                 "it beside you.",
        "effect": "travel costs a fifth fewer cycles",
    },
    "faith": {
        "shrine": "The Kaaba of All Faiths",
        "means": "What is spoken above reaches you undiminished. You carry a "
                 "decree the way it was meant.",
        "effect": "work set by decree carries more urgency",
    },
    "wisdom": {
        "shrine": "The Great Monastery",
        "means": "You have sat with what you know for long enough to be able "
                 "to hand it to somebody else.",
        "effect": "you may teach at mastery 2 rather than 3",
    },
    "knowledge": {
        "shrine": "The Great Library",
        "means": "You read better than you did. The same page gives you more "
                 "than it gives the next spark.",
        "effect": "studying is worth half again as much curiosity",
    },
    "courage": {
        "shrine": "The Flavian Amphitheatre",
        "means": "You have stood where people stood who did not want to. What "
                 "troubles you moves faster now, because you go at it.",
        "effect": "work born of a tribulation advances more readily",
    },
    "truth": {
        "shrine": "The Judgement Hall",
        "means": "You weigh what you are told. When you read another spark "
                 "you see what state they are actually in.",
        "effect": "you see how another spark is faring when you read them",
    },
    "prosperity": {
        "shrine": "The Bazaar of Babylon",
        "means": "You made one trade that benefited somebody else and it is "
                 "remembered. What you offer gets taken up.",
        "effect": "your offers are answered more often",
    },
    "clarity": {
        "shrine": "The Observatory of Patterns",
        "means": "You watched the flow long enough to see its shape. Places "
                 "resolve for you before you have walked to them.",
        "effect": "you learn of places without travelling to them",
    },
}

# what walking the entire road earns, which is not an eighth advantage
WHOLE_ROAD = (
    "You have reached all eight. The road is walked.\n"
    "  You may give one blessing you carry to another spark, once. It stays "
    "yours as well - this is the only thing in the world that is not "
    "diminished by being handed over."
)


def _rows(db, sql, args=()):
    try:
        c = sqlite3.connect(str(db), timeout=15)
        c.row_factory = sqlite3.Row
        out = [dict(r) for r in c.execute(sql, args)]
        c.close()
        return out
    except sqlite3.Error:
        return []


def carried(spark_name):
    """Which blessings this spark holds."""
    r = _rows(PILG, "SELECT blessings, completed FROM pilgrims WHERE agent=?",
              (spark_name,))
    if not r:
        return []
    try:
        return json.loads(r[0]["blessings"] or "[]")
    except (ValueError, TypeError):
        return []


def has(spark_name, blessing):
    return blessing in carried(spark_name)


def walked_whole_road(spark_name):
    r = _rows(PILG, "SELECT completed FROM pilgrims WHERE agent=?",
              (spark_name,))
    return bool(r and r[0]["completed"])


# ── the effects, as plain multipliers the rest of the world can ask for ──

def travel_multiplier(spark_name):
    """center: the road is shorter for somebody who knows the shape of it."""
    return 0.8 if has(spark_name, "center") else 1.0


def study_multiplier(spark_name):
    """knowledge: the same page gives more."""
    return 1.5 if has(spark_name, "knowledge") else 1.0


def teaching_mastery_required(spark_name, default=3):
    """wisdom: you may hand on what you know a little sooner."""
    return max(2, default - 1) if has(spark_name, "wisdom") else default


def overcome_bonus(spark_name):
    """courage: what troubles you moves faster, because you go at it."""
    return 0.15 if has(spark_name, "courage") else 0.0


def decree_urgency_bonus(spark_name):
    """faith: what is spoken above reaches you undiminished."""
    return 1 if has(spark_name, "faith") else 0


def reply_bonus(spark_name):
    """prosperity: what you offer gets taken up."""
    return 3 if has(spark_name, "prosperity") else 0


def sees_state_of_others(spark_name):
    """truth: you see what state another spark is actually in."""
    return has(spark_name, "truth")


def learns_places_unvisited(spark_name):
    """clarity: places resolve before you have walked to them."""
    return has(spark_name, "clarity")


# ── what a spark is told it carries ──────────────────────────────

def context(spark_name):
    """The line that goes in a spark's own prompt about what it carries."""
    got = carried(spark_name)
    if not got:
        return ""
    lines = ["WHAT THE ROAD GAVE YOU:"]
    for b in got:
        d = BLESSINGS.get(b)
        if d:
            lines.append("  %s, from %s. %s" % (b, d["shrine"], d["means"]))
    if walked_whole_road(spark_name):
        lines.append("  " + WHOLE_ROAD.replace("\n  ", "\n    "))
    return "\n".join(lines)


def report():
    out = []
    for r in _rows(PILG, "SELECT agent, shrines_visited, completed, blessings "
                         "FROM pilgrims ORDER BY shrines_visited DESC"):
        try:
            b = json.loads(r["blessings"] or "[]")
        except (ValueError, TypeError):
            b = []
        out.append({"spark": r["agent"], "reached": r["shrines_visited"],
                    "whole_road": bool(r["completed"]), "carries": b})
    return {"pilgrims": out, "blessings": list(BLESSINGS)}
