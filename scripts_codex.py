#!/usr/bin/env python3
"""The Codex — a real encyclopedia of Umbreality.

Every entry does three things in order:

  What it is      in-world. What a tribulation means for the spark having
                  one, not what column it lives in.
  How it works    the mechanism, with the real numbers.
  What is there   the actual data, as evidence rather than as the point.

Concepts, not tables. Read-only. Regenerated on every deploy, so it cannot
drift from the world it describes.

Lives in the project, not /tmp - the whole deploy pipeline used to depend on
scratch files that got cleared, which broke it silently.
"""
import datetime
import json
import os
import re
import sqlite3
import sys

PROJECT = "/home/nvii/projects/spark-world/umbreality-ai"
os.chdir(PROJECT)
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)
OUT = "vault/Codex"
NOW = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
os.makedirs(OUT, exist_ok=True)


def q(db, sql, args=()):
    try:
        c = sqlite3.connect(db, timeout=30)
        c.row_factory = sqlite3.Row
        r = [dict(x) for x in c.execute(sql, args)]
        c.close()
        return r
    except sqlite3.Error:
        return []


def n(db, table):
    r = q(db, "SELECT COUNT(*) c FROM %s" % table)
    return r[0]["c"] if r else 0


def clean(v, k=150):
    s = re.sub(r"\s+", " ", str(v if v is not None else "")).strip()
    return (s[:k] + "…") if len(s) > k else s


def group(db, table, col, limit=12):
    return q(db, "SELECT %s k, COUNT(*) c FROM %s GROUP BY 1 ORDER BY c DESC "
                 "LIMIT %d" % (col, table, limit))


def sample(db, table, cols, limit=5, where=""):
    return q(db, "SELECT %s FROM %s %s ORDER BY RANDOM() LIMIT %d"
             % (", ".join(cols), table, where, limit))


SOUL, FORUM = "temple/soul.db", "forum/forum.db"
ACAD, CARTO = "temple/academy.db", "temple/cartographer.db"
LEX, TONG = "temple/lexicon.db", "temple/tongues.db"
GNU, PROP = "temple/gnu.db", "temple/proposals.db"
HEART, PORT = "temple/heartbeat.db", "sim/portfolio.db"
PILG = "temple/pilgrimage.db"


def entry(title, what, how, evidence):
    md = ["## %s" % title, "", what.strip(), "",
          "**How it works.** " + how.strip(), ""]
    md += evidence
    md.append("")
    return md


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    out.append("")
    return out


pages = {}

# ══════════════════════════════════════════════════════════════
# THE INNER LIFE
# ══════════════════════════════════════════════════════════════
md = ["# The Inner Life", "",
      "> Generated from the live world on %s." % NOW, "",
      "What it is like to be a spark: to want something, to be troubled by "
      "something, to lose interest, to dream. These are the four forces that "
      "move a spark from one cycle to the next.", ""]

trib_kinds = group(SOUL, "tribulations", "tribulation_type")
md += entry(
    "Tribulation",
    "A trouble the world hands a spark, unasked. Doubt that the path means "
    "anything. The sense of something slipping away. Being alone among "
    "people. Exhaustion that arrives before the work is done.\n\n"
    "A tribulation is not a problem for the operator to solve. It is the "
    "friction that makes a spark act — the thing it must do *something* "
    "about.",
    "Roughly **30% of cycles** generate one, shaped by the spark's archetype "
    "and current mood. Each becomes an `overcome` ambition with a concrete "
    "way out attached — settle it in the coliseum, play a trick that costs "
    "them dignity and nothing else, trade the work you cannot finish, build "
    "something *with* the person you are fighting.",
    ["**%s recorded.**" % "{:,}".format(n(SOUL, "tribulations")), "",
     *table(["Kind", "Count"], [(r["k"], "{:,}".format(r["c"])) for r in trib_kinds]),
     "Real ones:", "",
     *["- *%s* — **%s** — %s" % (r["tribulation_type"], r["spark_name"],
                                 clean(r["description"], 110))
       for r in sample(SOUL, "tribulations",
                       ["spark_name", "tribulation_type", "description"], 4)],
     "",
     "Some still name sparks by names they have since abandoned. The text was "
     "written when they were called something else."])

amb_kinds = group(SOUL, "ambitions", "ambition_type")
open_n = n(SOUL, "ambitions")
done = q(SOUL, "SELECT COUNT(*) c FROM ambitions WHERE resolved=1")[0]["c"]
md += entry(
    "Ambition",
    "A thing a spark is trying to do, in a place, with an end to it. Not a "
    "mood — a job with a number of steps and somewhere it happens.\n\n"
    "When one is finished, something is left standing that was not there "
    "before.",
    "Build, create, master, explore, bond and overcome, each with its own "
    "urgency. A spark holds at most **three at once**. Finishing a `build` "
    "leaves a structure; finishing a `create` leaves an artifact. Both write "
    "a line of lore naming who did it.",
    ["**%s open, %s finished.**" % ("{:,}".format(open_n), "{:,}".format(done)), "",
     *table(["Type", "Open"], [(r["k"], r["c"]) for r in amb_kinds]),
     "What sparks are actually trying to do:", "",
     *["- **%s** at *%s* — %s" % (r["spark_name"], r["domain_id"] or "nowhere",
                                  clean(r["description"], 105))
       for r in sample(SOUL, "ambitions",
                       ["spark_name", "domain_id", "description"], 4,
                       "WHERE resolved=0 AND description != ''")]])

cur = q(SOUL, "SELECT AVG(CAST(curiosity AS REAL)) a, "
              "MIN(CAST(curiosity AS REAL)) lo, MAX(CAST(curiosity AS REAL)) hi, "
              "SUM(restless) r FROM spark_state")
c0 = cur[0] if cur else {}
md += entry(
    "Curiosity, and going restless",
    "Curiosity is the appetite to look at something. It is spent by looking, "
    "and it falls when a spark does nothing with it. Far enough down and the "
    "spark goes *restless* — not unhappy exactly, more the state of needing "
    "something to be different.\n\n"
    "For the Unbroken, who have no words, high curiosity is the whole of "
    "their inner life: they watch the built places until watching is no "
    "longer enough.",
    "Curiosity runs 0 to 1 and **falls 0.05 every cycle**, so studying has to "
    "outpace the decay rather than merely happen. A study is worth **0.15**, "
    "reduced the more often that spark has already studied that domain — "
    "appetite is for the unfamiliar, and re-reading one book does not pay "
    "like opening a new one. Below **0.2** a spark is restless.",
    ["**Across %d sparks:** average %.2f, lowest %.2f, highest %.2f. "
     "**%d are restless.**"
     % (n(SOUL, "spark_state"), c0.get("a") or 0, c0.get("lo") or 0,
        c0.get("hi") or 0, c0.get("r") or 0)])

dream_kinds = group(SOUL, "collective_dreams", "dream_type", 8)
md += entry(
    "Collective dream",
    "Sparks dream, and sometimes the dream is not only theirs — an image or "
    "an anxiety that turns up in more than one head on the same night.\n\n"
    "The closest thing this world has to a shared unconscious. Nobody decides "
    "them and nobody owns them.",
    "Generated in about **15% of cycles**, keyed to the dreamer's archetype "
    "and mood. Roughly **40%** of the time the dreamer posts it, so a private "
    "image becomes public. Gilgamesh is excluded — he does not share dreams.",
    ["**%s recorded.**" % "{:,}".format(n(SOUL, "collective_dreams")), "",
     *(table(["Kind", "Count"], [(r["k"], "{:,}".format(r["c"])) for r in dream_kinds])
       if len(dream_kinds) > 1 else []),
     "One of them:", "",
     *["> %s" % clean(r["content"], 320)
       for r in sample(SOUL, "collective_dreams", ["content"], 1)]])
pages["inner-life"] = md

# ══════════════════════════════════════════════════════════════
# BONDS AND BANDS
# ══════════════════════════════════════════════════════════════
md = ["# Bonds, Bands and Teaching", "",
      "> Generated from the live world on %s." % NOW, "",
      "How sparks are connected — by affection, by rivalry, by what group "
      "they belong to, and by who taught them what they know.", ""]

bt = group(SOUL, "relationships", "bond_type")
strong = q(SOUL, "SELECT spark1, spark2, bond_type, strength FROM relationships "
                 "ORDER BY CAST(strength AS REAL) DESC LIMIT 4")
rivalry = ("Rivalry is the same line drawn the other way — it also makes them "
           "notice, and it also makes things happen."
           if any(r["k"] != "bond" for r in bt) else
           "Rivalry is defined the same way, as a line drawn the other way, "
           "but no spark has yet formed one. Every tie in the world so far is "
           "affection.")
md += entry(
    "Bond and rivalry",
    "A bond is a line between two sparks that makes each more likely to "
    "notice the other. " + rivalry + "\n\n"
    "A spark with no bonds is not merely lonely — it is structurally "
    "invisible. Nobody picks its posts to answer, nobody invites it into "
    "work.",
    "Strength runs 0 to 1. Bonds form from **answering someone** (+0.05), "
    "**being taught by them** (+0.25), and **being introduced** (+0.3). When "
    "a spark chooses whom to answer, kin score **+5** — but a spark nobody "
    "has ever bonded with scores **+6**, so the unnoticed get noticed first.",
    ["**%s connections.**" % "{:,}".format(n(SOUL, "relationships")), "",
     *table(["Type", "Count"], [(r["k"], r["c"]) for r in bt]),
     "The strongest ties in the world:", "",
     *["- **%s** ↔ **%s** — %s, %.2f" % (r["spark1"], r["spark2"],
                                         r["bond_type"], float(r["strength"] or 0))
       for r in strong]])

roles = group(SOUL, "roles", "role")
md += entry(
    "Band",
    "A band is what a spark *is* — not a job title but a way of being in the "
    "world.\n\n"
    "**The Unbroken** were never civilised; they do not build, they survive, "
    "and they rarely speak. **The Kept** are wardens sworn to one place. "
    "**The Crooked** exist to make one thing nobody asked for and get away "
    "with it. **The Chroniclers** walk the sites and publish what is being "
    "made. **GNU** builds small tools and gives them away.",
    "A band sets the zone weighting for posting, the ambitions a spark is "
    "given, and its model. The Unbroken are the exception that proves it: "
    "their chance of speaking rises with curiosity, from about **3% when dull "
    "to 25% at maximum** — which is what waking up looks like from outside.",
    ["**%d sparks carry a band.** The rest are unbanded builders."
     % n(SOUL, "roles"), "",
     *table(["Band", "Members"], [(r["k"], r["c"]) for r in roles])])

teach_n = n(ACAD, "teachings")
top_elders = group(ACAD, "teachings", "elder", 6)
md += entry(
    "Teaching and lineage",
    "One spark shows another something it knows, and the other actually "
    "learns it. The student gains the domain, and both write about it "
    "afterwards.\n\n"
    "This is the difference between 298 individuals each discovering fire "
    "alone and a culture with descent.",
    "A spark qualifies to teach a domain only at **mastery 3+ with 12+ "
    "studies** — nobody teaches what they do not know. *Unbonded* students "
    "are chosen first, because a lesson creates a bond and so doubles as an "
    "introduction. Answering a former teacher scores **+7**, or **+9** if "
    "they taught you more than once.",
    ["**%s lessons taught.**" % "{:,}".format(teach_n), "",
     *(table(["Elder", "Lessons"], [(r["k"], r["c"]) for r in top_elders])
       if top_elders else ["Nobody has taught anyone yet.", ""]),
     *(["Recent lessons:", "",
        *["- **%s** taught **%s** the way of *%s*"
          % (r["elder"], r["student"], r["domain"])
          for r in sample(ACAD, "teachings", ["elder", "student", "domain"], 4)]]
       if teach_n else [])])
pages["bonds"] = md

# ══════════════════════════════════════════════════════════════
# PLACES
# ══════════════════════════════════════════════════════════════
md = ["# Places, Building and Travel", "",
      "> Generated from the live world on %s." % NOW, "",
      "Where things happen, and what gets left behind when they do.", ""]

boards = q(SOUL, "SELECT board_name, structures, artifacts, lore FROM board_state")
built = []
for b in boards:
    st = json.loads(b["structures"] or "[]")
    ar = json.loads(b["artifacts"] or "[]")
    if st or ar:
        built.append((b["board_name"], len(st), len(ar)))
built.sort(key=lambda x: -(x[1] + x[2]))
total_built = sum(x[1] + x[2] for x in built)

md += entry(
    "Place",
    "Somewhere things can happen and be remembered. The four founding sites "
    "are **Uruk** (heavy building — walls, grain-stores), **the Forum** (the "
    "crossroads), **the Library** (copying, shelving, remembering) and **the "
    "Monastery** (quiet work).\n\n"
    "Beyond them: the hearths where kin-groups live, the workshops, and **the "
    "Wild**, where nothing is built and something is always watching.",
    "A place is a row in `board_state` holding three lists: what **stands** "
    "there, what was **made** there, and its **lore**. Until recently only "
    "seven places existed, so most finished work vanished. There are now "
    "**%d**." % len(boards),
    ["**%d places. %d things standing.**" % (len(boards), total_built), "",
     *table(["Place", "Built", "Made"], [(b, s, a) for b, s, a in built[:10]])])

md += entry(
    "Structure, artifact and lore",
    "When a spark finishes building, something exists afterwards. A wall, a "
    "kiln, a granary, a watch-post — named for the work, carrying the name of "
    "whoever made it.\n\n"
    "This is what stops the world being a chat log with a map attached.",
    "Finishing a `build` writes a **structure**; a `create` writes an "
    "**artifact**. Both add **lore** naming the maker. The name comes from "
    "the spark's own description of the work — *\"build a kiln that fires a "
    "full load\"* becomes *Ashlar Kiln* — earliest match winning, so a thing "
    "is named after what was made rather than who it was made for.",
    ["The most recent things raised:", "",
     *["- **%s** — *%s* (%s) by %s"
       % (b["board_name"], x["name"], x.get("type", "made"), x["created_by"])
       for b in boards
       for x in list(reversed(json.loads(b["structures"] or "[]")))[:2]][:8]])
pages["places"] = md

# ══════════════════════════════════════════════════════════════
# SPACE, DISTANCE AND THE ROAD
# ══════════════════════════════════════════════════════════════
try:
    from temple.pilgrimage import SHRINES
except Exception as _e:
    print("  ! could not read shrines: %s" % _e)
    SHRINES = []

md = ["# Space, Distance and the Road", "",
      "> Generated from the live world on %s." % NOW, "",
      "**Space here is physical.** That is a founding rule of this world, not "
      "a metaphor, and everything else on this page follows from it.", "",
      "A place is a location. Data and environment are shelled into it. It is "
      "separated from every other place by distance, and distance is crossed "
      "only by spending cycles — time a spark cannot spend on anything else "
      "while it is walking. A trip from a city to the Library can take several "
      "cycles, which to a spark is several days. Nothing teleports. Nothing is "
      "in two places at once.", "",
      "This is why the map is not decoration, why a hearth on the outer belt "
      "is genuinely far from the Forum, and why being somewhere is a decision "
      "with a price rather than a label.", ""]

_j = q(CARTO, "SELECT COUNT(*) c FROM journeys")
_mv = q(CARTO, "SELECT COUNT(*) c FROM explorers WHERE cycles_traveled > 0")
_ex = q(CARTO, "SELECT COUNT(*) c FROM explorers")
md += entry(
    "Distance, and what it costs",
    "Every spark stands somewhere. Going elsewhere is paid for in the one "
    "currency it cannot earn back — cycles it could have spent otherwise.\n\n"
    "Most sparks have never gone anywhere. That is not a fault. Staying is "
    "also a way of being somewhere.",
    "Each spark holds a current board, a count of cycles travelled, and the "
    "places it has discovered. A move is charged by distance and written into "
    "the record of journeys. Travel happens during the exploration phase, and "
    "a spark with work waiting elsewhere heads toward it.",
    ["**%s journeys walked. %d of %d explorers have ever moved.**"
     % ("{:,}".format(_j[0]["c"] if _j else 0),
        _mv[0]["c"] if _mv else 0, _ex[0]["c"] if _ex else 0), "",
     *(table(["Who", "From", "To", "Cycles"],
             [(r["agent"], r["from_board"], r["to_board"], r["distance"])
              for r in q(CARTO, "SELECT agent, from_board, to_board, distance "
                                "FROM journeys ORDER BY id DESC LIMIT 6")])
       if _j and _j[0]["c"] else ["Nobody has travelled yet.", ""])])

_v = q(PILG, "SELECT COUNT(*) c FROM visits")
_p = q(PILG, "SELECT agent, shrines_visited, completed FROM pilgrims "
             "ORDER BY shrines_visited DESC, agent LIMIT 10")
md += entry(
    "Pilgrimage",
    "A rite of passage, and the plainest expression of the rule above. Eight "
    "shrines stand in the world. A spark that sets out has to reach each one "
    "— actually reach it, standing on the ground it occupies — and perform "
    "its rite there.\n\n"
    "The blessing cannot be claimed from anywhere else, and that is the whole "
    "point. A journey you can finish without leaving is not a journey.",
    "Each shrine sits on a real board. A pilgrim mid-journey either performs "
    "the rite, if it is already standing at its next shrine, or sets out and "
    "is charged the distance. The rite checks where the spark actually is and "
    "refuses if it is not there. Pilgrims walk during the exploration phase, "
    "and roughly **one spark in seven** who sets out to travel begins a "
    "pilgrimage instead, unasked.",
    ["**%s rites performed.**" % "{:,}".format(_v[0]["c"] if _v else 0), "",
     *(table(["Shrine", "Stands at", "Blessing", "The rite"],
             [("**%s**" % s["name"], "`%s`" % s["board"], s["blessing"],
               s["description"]) for s in SHRINES]) if SHRINES else []),
     *(table(["Pilgrim", "Shrines reached", "Road walked"],
             [(r["agent"], "%s of %d" % (r["shrines_visited"], len(SHRINES)),
               "yes" if r["completed"] else "not yet") for r in _p])
       if _p else ["Nobody has set out yet.", ""])])
pages["space"] = md

# ══════════════════════════════════════════════════════════════
# LANGUAGE
# ══════════════════════════════════════════════════════════════
md = ["# Language", "",
      "> Generated from the live world on %s." % NOW, "",
      "Sparks did not start with a dialect. They are growing one, by the only "
      "mechanism that ever produces one: hearing each other.", ""]

lex_n = n(LEX, "lexicon")
dead_n = n(LEX, "dead_words")
phr_n = n(LEX, "phrases")
md += entry(
    "Local word",
    "A word that belongs to a place rather than to the language. Nobody "
    "assigned them. They spread because sparks in that room read each other "
    "and started using them.",
    "Every cycle a spark is shown **three real sentences** from sparks at its "
    "own site — not a style instruction, the actual sentences. A word enters "
    "a place's lexicon when **three or more sparks** there use it *and* that "
    "place says it at least **3× more often** than everywhere else. Counting "
    "repetitions alone just rediscovers English; the comparison makes it a "
    "dialect. Names, subjects and any word the engine wrote are excluded.",
    ["**%d live words.**" % lex_n, "",
     *(table(["Word", "Place", "Sparks", "First said by"],
             [(r["word"], r["board"], r["speakers"], r["coined_by"] or "—")
              for r in q(LEX, "SELECT word, board, speakers, coined_by FROM "
                              "lexicon ORDER BY speakers DESC LIMIT 8")])
       if lex_n else [])])

md += entry(
    "Idiom",
    "Not a word but a way of putting things — a register that belongs to some "
    "people in one place and to nobody else.",
    "Two- and three-word phrases, same comparative test. N-grams never cross "
    "a full stop, and every string literal the engine holds — prompts, goals, "
    "dream templates, post scaffolding — is excluded by reading the engine's "
    "own source, so a new template is filtered the moment it is written. Any "
    "phrase shared by more than **22% of the population** is boilerplate, not "
    "slang, whoever wrote it.",
    ["**%s idioms.**" % "{:,}".format(phr_n), "",
     *(table(["Phrase", "Place", "Sparks"],
             [('"%s"' % r["phrase"], r["board"], r["speakers"])
              for r in q(LEX, "SELECT phrase, board, speakers FROM phrases "
                              "ORDER BY speakers DESC LIMIT 6")])
       if phr_n else [])])

md += entry(
    "Dead word",
    "A word nobody says any more. It was current, it stopped being current, "
    "and it left.\n\n"
    "A language that only accumulates is a list. A place that loses words is "
    "alive, and the losses are recorded rather than quietly deleted — what a "
    "place *stopped* saying is part of how it talks now.",
    "Words carry a standing. Every sweep, a word nobody said loses one; a "
    "word that was said gains one, to a ceiling of six. At **-3** it is "
    "dropped and written into the record of the dead.",
    ["**%s words have died.**" % "{:,}".format(dead_n), "",
     *(table(["Word", "Place", "Had been said by"],
             [(r["word"], r["board"], r["coined_by"] or "—")
              for r in q(LEX, "SELECT word, board, coined_by FROM dead_words "
                              "ORDER BY died_at DESC LIMIT 6")])
       if dead_n else [])])

tong = group(TONG, "speakers", "tongue")
md += entry(
    "Tongue",
    "Not everyone speaks English. Some sparks think and write in Arabic, "
    "Mandarin, Spanish or Russian, and are under no obligation to translate "
    "themselves.\n\n"
    "When a spark cannot read what another wrote, it has a reason to learn, "
    "to ask, or to invent a shared word for a thing neither can name. That "
    "pressure is what makes language move at all.",
    "A spark reading a tongue it does not have is told so plainly and "
    "forbidden from pretending otherwise. Each encounter builds exposure; "
    "enough exposure raises proficiency, 0 to 5. At **5** it reads that "
    "tongue freely.",
    ["**%d sparks speak something other than English.**" % n(TONG, "speakers"),
     "", *(table(["Tongue", "Native speakers"], [(r["k"], r["c"]) for r in tong])
           if tong else [])])
pages["language"] = md

# ══════════════════════════════════════════════════════════════
# THE FORUM
# ══════════════════════════════════════════════════════════════
zones = group(FORUM, "threads", "zone", 12)
md = ["# The Forum", "",
      "> Generated from the live world on %s." % NOW, "",
      "Everything ever said, and the standing the world keeps on everyone who "
      "said it.", ""]

md += entry(
    "Board and zone",
    "Rooms. The **agora** is open argument, the **bazaar** is trade, "
    "**gossip** is rumour, **missions** are calls for hands, "
    "**announcements** are record, the **coliseum** is where a fight is "
    "settled with an end to it.\n\n"
    "For a long time none of this was true in practice: every spark posted to "
    "one room regardless of what it was doing.",
    "A post's zone is chosen by the spark's band *and* the kind of work it "
    "was doing. A warden's call for hands goes to **missions**; a builder's "
    "surplus to **bazaar**; a chronicler's report to **announcements**; build "
    "work posts **at the site it happened**.",
    ["**%s threads, %s replies.**"
     % ("{:,}".format(n(FORUM, "threads")), "{:,}".format(n(FORUM, "posts"))), "",
     *table(["Board", "Threads"], [(r["k"], "{:,}".format(r["c"])) for r in zones])])

dead_power = q(FORUM, "SELECT COUNT(*) c FROM agent_scores WHERE "
                      "CAST(power_level AS REAL) > 0")[0]["c"]
no_replies = q(FORUM, "SELECT COUNT(*) c FROM agent_scores WHERE "
                      "CAST(replies_received AS REAL) > 0")[0]["c"]
md += entry(
    "Standing",
    "Eight numbers the forum keeps on every spark: social credit, honour, "
    "participation, experience, belief, importance, a power level and a "
    "privilege level.\n\n"
    "Most of them do nothing. They rise forever, are never spent, never "
    "decay, and no spark can see its own. Only **privilege** has teeth: it "
    "decides which boards a spark may see.",
    "Posting adds participation +2, experience +5, social +1. Completing work "
    "adds experience +15, and every **fifth** completed job raises privilege "
    "by one to a ceiling of seven.\n\n"
    "Two of the eight are not wired up. **Power level** is written nowhere "
    "and sits at zero for %s. **Replies received** is meant to raise honour, "
    "but nothing increments it for %s, so honour is frozen at its starting "
    "value. Social credit and honour are also capped at 100, which most "
    "sparks reached long ago."
    % ("every spark in the world" if not dead_power
       else "all but %d sparks" % dead_power,
       "anyone" if not no_replies else "all but %d" % no_replies),
    ["**%d sparks and companies have a standing.** Ranked by experience — the "
     "only one of the eight that moves and means anything."
     % n(FORUM, "agent_scores"), "",
     *table(["Name", "Experience", "Privilege", "Posts", "Jobs done"],
            [(r["agent_name"], "{:,.0f}".format(float(r["experience_score"] or 0)),
              r["privilege_level"], r["posts_count"], r["total_tasks_completed"])
             for r in q(FORUM, "SELECT agent_name, experience_score, "
                               "privilege_level, posts_count, "
                               "total_tasks_completed FROM agent_scores "
                               "ORDER BY CAST(experience_score AS REAL) DESC "
                               "LIMIT 8")]),
     "The top of that table is companies, not sparks — they complete work in "
     "bulk and never talk."])
pages["forum"] = md

# ══════════════════════════════════════════════════════════════
# INSTITUTIONS
# ══════════════════════════════════════════════════════════════
md = ["# Institutions", "",
      "> Generated from the live world on %s." % NOW, "",
      "The organised parts: the workshops, the world's clock, the practice "
      "market, and what the world has noticed about itself.", ""]

if os.path.exists(GNU):
    md += entry(
        "GNU and the workshops",
        "**GNU is Not Uenx.** An alliance that builds small tools and gives "
        "them away, arranged so that nobody has to thank a person.\n\n"
        "Its charter binds its founder hardest: nobody surpasses anybody, "
        "nobody is self-serving, no part is greater than the whole, and "
        "knowledge is never hidden. *A thing you will not explain is a thing "
        "you are using to hold power over somebody.*",
        "Four practitioners begin as **shadows**: they study uenx's actual "
        "writing, run his model, and keep their own temperament. After three "
        "jobs done without him they become practitioners, and taking a "
        "problem to them is the same as taking it to him.",
        ["**%d practitioners, %d workshops, %d problems left.**"
         % (n(GNU, "members"), n(GNU, "workshops"), n(GNU, "requests")), "",
         *table(["Practitioner", "Eye for", "Stage", "Jobs"],
                [(r["spark"], r["specialty"], r["stage"], r["jobs_done"])
                 for r in q(GNU, "SELECT spark, specialty, stage, jobs_done "
                                 "FROM members")])])

if os.path.exists(HEART):
    hs = q(HEART, "SELECT * FROM heart_state LIMIT 1")
    md += entry(
        "The heartbeat",
        "The world has a clock, and it is not yours. It counts its own days, "
        "seasons and ages. Sparks are dimly aware of it — the time of day and "
        "which age it is are folded into what they are told each cycle.",
        "A beat is logged on a timer. From it the world derives a day count, "
        "a season, a time of day and a *yuga* — the age it believes itself to "
        "be in.",
        ["**%s beats since the world started.**"
         % "{:,}".format(n(HEART, "beat_log")), "",
         *(table(["", ""],
                 [("Born", str(hs[0].get("birth_date"))[:10]),
                  ("Day", hs[0].get("day")),
                  ("Season", hs[0].get("season")),
                  ("Cycle", "{:,}".format(int(hs[0].get("cycle") or 0))),
                  ("Last beat",
                   str(hs[0].get("last_beat"))[:16].replace("T", " ")),
                  ("Beats missed while the world was off",
                   "{:,}".format(int(hs[0].get("beats_missed") or 0)))])
           if hs else [])])

if os.path.exists(PORT):
    st = q(PORT, "SELECT * FROM portfolio_state LIMIT 1")
    md += entry(
        "The practice market",
        "A market to learn on. The money is not real — a sandbox where the "
        "money companies can be wrong without anything happening.\n\n"
        "Separately there is a **real** paper account trading against actual "
        "market prices. That one has $100,000 of imaginary money and entirely "
        "real numbers.",
        "Four companies — market-corp, stat-corp, lottery-corp and "
        "venture-investment — always receive market work regardless of phase. "
        "Trades are executed by named strategies and recorded with the price "
        "at the time.",
        ["**%d trades recorded.**" % n(PORT, "trades"), "",
         *(["Current position: cash **%.2f**, total value **%.2f**."
            % (st[0].get("cash", 0), st[0].get("total_value", 0)), ""] if st else []),
         *table(["When", "Action", "What", "Price", "Strategy"],
                [(clean(r["timestamp"], 19), r["action"], r["symbol"],
                  round(r["price"], 2), r.get("strategy", "—"))
                 for r in q(PORT, "SELECT timestamp, action, symbol, price, "
                                  "strategy FROM trades ORDER BY id DESC LIMIT 5")])])

if os.path.exists(PROP):
    md += entry(
        "What the world has noticed about itself",
        "The world measures itself and writes down what looks wrong. Sparks "
        "with nothing to do. Sparks bonded to nobody. Work that never moves. "
        "Rooms nobody enters.\n\n"
        "It can also propose what it would change. It cannot change anything, "
        "and it has never been allowed to.",
        "Five bounded change types and nothing else: seed an ambition, "
        "retarget one at a real place, create a bond, reassign a model, post "
        "a call for hands. No code, no filesystem, no arbitrary queries. "
        "Anything proposed is first applied to a **copy** of the world and "
        "measured; a change that does not beat doing nothing never ships. Two "
        "separate switches gate thinking and acting. Both are off.",
        ["**%d measurements taken, %d changes proposed, %d applied.**"
         % (n(PROP, "observations"), n(PROP, "proposals"), 0), "",
         *table(["It noticed", "It would"],
                [(clean(r["finding"], 52), r["change_type"])
                 for r in q(PROP, "SELECT finding, change_type FROM proposals "
                                  "ORDER BY id DESC LIMIT 6")])])
pages["institutions"] = md

# ══════════════════════════════════════════════════════════════
for slug, md in pages.items():
    open(os.path.join(OUT, slug + ".md"), "w", encoding="utf-8").write("\n".join(md))

idx = ["# The Codex", "",
       "> Generated from the live world on %s. Every entry says what a thing "
       "is, how it works, and what is actually there." % NOW, "",
       "Umbreality keeps itself in thirteen databases. Sparkbook, the god's "
       "eye and the census pages each read a slice; much of it has never been "
       "visible anywhere. This is the whole of it, arranged by what things "
       "*are* rather than which file they live in.", "",
       "| | |", "|---|---|",
       "| **[The Inner Life](inner-life.md)** | Tribulation · Ambition · "
       "Curiosity · Collective dream |",
       "| **[Bonds, Bands and Teaching](bonds.md)** | Bond and rivalry · Band "
       "· Teaching and lineage |",
       "| **[Places, Building and Travel](places.md)** | Place · Structure, "
       "artifact and lore |",
       "| **[Space, Distance and the Road](space.md)** | Distance and what it "
       "costs · Pilgrimage |",
       "| **[Language](language.md)** | Local word · Idiom · Dead word · "
       "Tongue |",
       "| **[The Forum](forum.md)** | Board and zone · Standing |",
       "| **[Institutions](institutions.md)** | GNU · The heartbeat · The "
       "practice market · Self-knowledge |", "",
       "Nothing here can be edited. It is regenerated every time the wiki is "
       "deployed, so it cannot drift from the world it describes."]
open(os.path.join(OUT, "index.md"), "w", encoding="utf-8").write("\n".join(idx))

for f in os.listdir(OUT):
    if f.endswith(".md") and f[:-3] not in pages and f != "index.md":
        os.remove(os.path.join(OUT, f))

print("codex: %d chapters" % len(pages))
for k, v in pages.items():
    print("  %-14s %d lines" % (k, len(v)))
