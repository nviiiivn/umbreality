"""Layer 6 — What a spark actually does with a cycle.

Until now every spark ended its cycle the same way: post to zone "creative"
with the title "<name>'s <task> - <timestamp>". 36,000 threads, all the
same shape, all in one room, while the bazaar and agora sat empty.

This routes a spark's action by what it *is*:

  chroniclers  publish to announcements, and gossip when it is rumour
  crooked      agora and gossip - they argue and they stir
  kept         missions - hands wanted, watch reports
  builders     bazaar - offer surplus, ask for materials
  architects   agora - tools, given away
  unbroken     mostly nothing. They do not have words yet. When one of
               them does speak it means something.

Titles come from what the spark actually said, not a timestamp.
"""
import datetime
import random
import re

# board -> what belongs there
ZONES = {
    "announcements": "news and record",
    "gossip": "rumour, complaint, and who did what to whom",
    "agora": "open argument, ideas, tools offered",
    "bazaar": "trade: surplus offered, materials wanted",
    "missions": "hands wanted, work that needs bodies",
    "creative": "made things",
    "library": "what has been learned",
    "monastery": "quiet work",
    "workers": "labour reports",
    "uruk": "the wall, the granary, the work of the city",
    "forum": "the crossroads - anything, anyone",
    "coliseum": "settled by fighting",
}

BAND_ZONES = {
    "chronicler": [("announcements", 5), ("gossip", 3), ("agora", 2)],
    "crooked":    [("agora", 4), ("gossip", 4), ("bazaar", 2)],
    "kept":       [("missions", 5), ("uruk", 3), ("announcements", 2), ("agora", 2)],
    "architect":  [("agora", 6), ("bazaar", 2), ("announcements", 2)],
    "unbroken":   [("gossip", 1)],
}

TASK_ZONES = {
    "create":    [("creative", 5), ("bazaar", 3), ("agora", 2), ("uruk", 2)],
    "build":     [("uruk", 4), ("missions", 4), ("bazaar", 2), ("forum", 2)],
    "master":    [("library", 5), ("agora", 3), ("announcements", 2)],
    "explore":   [("agora", 4), ("announcements", 3), ("gossip", 3)],
    "bond":      [("agora", 4), ("gossip", 3), ("forum", 3), ("watercooler", 2)],
    "overcome":  [("coliseum", 3), ("gossip", 3), ("forum", 3), ("agora", 3)],
    "meditation": [("monastery", 5), ("library", 3), ("agora", 2)],
    "dream":     [("gossip", 3), ("creative", 4), ("monastery", 3)],
}

DEFAULT_ZONES = [("agora", 3), ("forum", 3), ("creative", 2), ("uruk", 2),
                 ("gossip", 2), ("bazaar", 2)]


def _weighted(pairs):
    total = sum(w for _, w in pairs)
    if total <= 0:
        return pairs[0][0]
    r = random.uniform(0, total)
    acc = 0
    for z, w in pairs:
        acc += w
        if r <= acc:
            return z
    return pairs[-1][0]


def choose_zone(band="", archetype="", task_type=""):
    """Where this spark's output belongs."""
    pool = []
    if band and band in BAND_ZONES:
        pool += BAND_ZONES[band]
    if task_type and task_type in TASK_ZONES:
        pool += TASK_ZONES[task_type]
    if not pool:
        pool = DEFAULT_ZONES
    return _weighted(pool)


def should_speak(band="", curiosity=0.5):
    """The Unbroken have no words yet. Mostly they are silent.

    A high-curiosity one is on the edge of speech; let it through
    occasionally, because that is how waking up looks from outside.
    """
    if band != "unbroken":
        return True
    return random.random() < (0.06 + max(0.0, curiosity - 0.3) * 0.3)


_STOP = re.compile(r"^(as an? |i am an? ai|sure[,!]|certainly|okay[,.]|here'?s )", re.I)


def make_title(name, task_type, response, band=""):
    """A title taken from what was actually said.

    Falls back to something plain rather than a timestamp, because a
    timestamp tells a reader nothing about whether to open the thread.
    """
    text = (response or "").strip()
    # first sentence or line that reads like content
    for chunk in re.split(r"(?<=[.!?])\s+|\n+", text):
        c = chunk.strip(" *#>-—\"'")
        if len(c) < 12 or _STOP.match(c):
            continue
        c = re.sub(r"\s+", " ", c)
        if len(c) > 90:
            c = c[:87].rsplit(" ", 1)[0] + "..."
        return c
    if band == "unbroken":
        return "%s makes a sound" % name
    return "%s: %s" % (name, task_type)


# ── bazaar and missions: real, specific posts ──────────────────

def bazaar_post(name, ambitions, domains):
    """Offer what you have, ask for what you lack."""
    wants, haves = [], []
    for a in (ambitions or [])[:3]:
        d = (a.get("description") or "").strip()
        if a.get("ambition_type") in ("build", "create") and d:
            wants.append(d)
    for d in (domains or [])[:2]:
        haves.append(d.get("domain_id") or "")
    haves = [h for h in haves if h]

    if not wants and not haves:
        return None
    body = []
    if haves:
        body.append("**Offering.** I know %s. I will trade the work of it."
                    % ", ".join(haves))
    if wants:
        body.append("**Wanted.** %s" % wants[0])
        body.append("I cannot finish this alone. Say what you need in return.")
    title = ("%s trades: %s" % (name, (haves[0] if haves else "work"))) \
        if haves else ("%s needs hands" % name)
    return title, "\n\n".join(body)


def mission_post(name, ambition, site):
    """Hands wanted, stated plainly, with the site named."""
    d = (ambition.get("description") or "").strip()
    if not d:
        return None
    prog = "%s of %s" % (ambition.get("progress", 0),
                         ambition.get("target_progress", "?"))
    title = "HANDS WANTED at %s — %s" % (site or "an unnamed site", name)
    body = ("**%s** is working at **%s** and is %s of the way through.\n\n"
            "> %s\n\n"
            "If you have the trade for it, come to %s and say so."
            % (name, site or "no site", prog, d, site or "the site"))
    return title, body


def agora_post(name, response, archetype=""):
    """An argument or an offer, put in front of everyone."""
    text = (response or "").strip()
    if len(text) < 40:
        return None
    return ("%s, on the record" % name, text)


ART_ARCHETYPES = {"artisan", "creator", "visionary", "lover", "mystic",
                  "trickster", "heretic"}


def wants_to_make_art(archetype="", energy=0.5, task_type=""):
    """Who reaches for a made thing rather than more words."""
    if task_type in ("create", "dream") and energy > 0.45:
        return random.random() < 0.35
    if (archetype or "").lower() in ART_ARCHETYPES:
        return random.random() < 0.12
    return False


# Who hears something rather than sees it. Overlaps with the painters but
# is not the same set: a singer is not always a maker of images.
MUSIC_ARCHETYPES = {"artisan", "creator", "visionary", "mystic", "healer",
                    "explorer"}

# Who goes to the texts. A mystic and a heretic both read scripture; they
# are not reading it for the same reason.
DEVOUT_ARCHETYPES = {"mystic", "sage", "heretic", "sovereign", "guardian"}


def wants_to_make_music(archetype="", energy=0.5, task_type=""):
    """Who reaches for a sound rather than a picture or more words.

    Rarer than art on purpose. A piece of music should be an event in the
    world, not something six sparks turn out every cycle.
    """
    if task_type in ("create", "dream") and energy > 0.5:
        return random.random() < 0.18
    if (archetype or "").lower() in MUSIC_ARCHETYPES:
        return random.random() < 0.06
    return False


def wants_to_read_scripture(archetype="", curiosity=0.5, task_type=""):
    """Who goes to the texts.

    Driven by curiosity rather than energy: reading is what a spark does
    when it wants to know something, not when it has strength to spend.
    """
    if task_type in ("study", "reflect", "dream"):
        return random.random() < (0.08 + 0.15 * max(0.0, min(curiosity, 1.0)))
    if (archetype or "").lower() in DEVOUT_ARCHETYPES:
        return random.random() < 0.05
    return False


# ── answering each other ───────────────────────────────────────

def unbonded_sparks():
    """Sparks with no bond in either direction. Cached briefly."""
    import sqlite3 as _s
    import time as _t
    from pathlib import Path as _P
    global _UNBONDED
    now = _t.time()
    if _UNBONDED["at"] and now - _UNBONDED["at"] < 300:
        return _UNBONDED["names"]
    base = _P(__file__).resolve().parent.parent
    try:
        c = _s.connect(str(base / "temple" / "soul.db"), timeout=20)
        allnames = {r[0] for r in c.execute("SELECT spark_name FROM spark_state")}
        bonded = set()
        for r in c.execute("SELECT spark1, spark2 FROM relationships"):
            bonded.add(r[0]); bonded.add(r[1])
        c.close()
        _UNBONDED = {"at": now, "names": allnames - bonded}
    except Exception:
        _UNBONDED = {"at": now, "names": set()}
    return _UNBONDED["names"]


_UNBONDED = {"at": 0, "names": set()}


def taught_me(name):
    """Who has taught this spark, and how many times."""
    import sqlite3 as _s
    from pathlib import Path as _P
    base = _P(__file__).resolve().parent.parent
    try:
        c = _s.connect(str(base / 'temple' / 'academy.db'), timeout=20)
        rows = c.execute('SELECT elder, COUNT(*) FROM teachings WHERE student=? '
                         'GROUP BY elder', (name,)).fetchall()
        c.close()
        return dict(rows)
    except Exception:
        return {}


def score_thread(t, me, kin=(), sites=(), domains=(), band=""):
    """How much would `me` care about this thread? Higher is more."""
    author = (t.get("created_by") or t.get("author") or "").strip()
    if not author or author == me:
        return -9

    title = (t.get("title") or "").lower()
    zone = (t.get("zone") or "").lower()
    score = 0.0

    if zone == "missions" and any(s and s.lower() in title for s in sites):
        score += 6
    elif zone == "missions":
        score += 2
    # someone who taught you outranks kin. Repeated teaching outranks
    # everything: you turn toward the one who keeps showing you things.
    _t = taught_me(me)
    if author in _t:
        score += 9 if _t[author] > 1 else 7
    elif author in kin:
        score += 5
    elif author in unbonded_sparks():
        # somebody standing alone. Worth more than another word with a friend.
        score += 6
    if zone == "bazaar":
        score += 4 if any(d and d.lower() in title for d in domains) else 1
    if any(d and d.lower() in title for d in domains):
        score += 3
    if zone in ("agora", "gossip", "announcements"):
        score += 1.5
    if not t.get("reply_count"):
        score += 2
    return score


def pick_thread_to_answer(threads, me, kin=(), sites=(), domains=(), band="",
                          minimum=3.0):
    """The thread this spark would most plausibly answer, or None."""
    best, best_s = None, minimum
    for t in threads or []:
        s = score_thread(t, me, kin, sites, domains, band)
        if s > best_s:
            best, best_s = t, s
    return best


REPLY_FRAME = (
    "You are reading the board. {author} posted this in {zone}:\n\n"
    "TITLE: {title}\n{body}\n\n"
    "Answer them directly, as yourself, in two to five sentences. "
    "Say something only you would say - from your own work, your own trade, "
    "what you have actually seen. If they need hands and you have the skill, "
    "offer it plainly. If you disagree, say so. Do not summarise their post "
    "back to them and do not introduce yourself."
)
