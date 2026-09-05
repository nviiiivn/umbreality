#!/usr/bin/env python3
"""Evolutionary activity statistics for Umbreality.

WHY THIS EXISTS

Every claim this project makes about being alive is otherwise an opinion.
The world looks busy. Tierra looked busy. Avida looked busy. Both produced
rich diversity early and then quietly stopped producing anything new, and
neither announced it - a plateaued world and a living one look identical
from the inside.

    Packard, Bedau, Channon, Ikegami, Rasmussen, Stanley & Taylor,
    "An overview of open-ended evolution", Artificial Life 25(2), 2019.

HOW IT WORKS, AND WHY IT IS BUILT THIS WAY

A component is anything that can be born, used and fall out of use: a
coined word, a kind of ambition, a teaching lineage. Its ACTIVITY is how
often it has been used since it appeared.

The whole difficulty is that raw activity curves always rise. This world
went from 298 sparks to 356 in a week; more sparks say more things in more
places, and every curve climbs without a single new idea being had. Three
earlier versions of this file were fooled by exactly that, and the tell was
FORUM ZONES - a fixed list of 83 places nobody invents new ones of - coming
back as open-ended evolution. When a statistic says a fixed set is growing,
the statistic is wrong.

So the world is measured against a SHADOW of itself. The shadow has the
same number of events on the same days across the same component pool, with
every trace of selection destroyed by redrawing which component each event
belonged to, uniformly at random. Same volume, same population, same growth,
no selection. Every statistic is computed on both, and what is reported is
the difference.

That control is the entire instrument. Without it this file counts, and
counting proves nothing - a world doing the same thing forever still has a
large total.

    Class 1   real world indistinguishable from its own shadow. Whatever is
              happening, drift explains it.
    Class 2   real beats shadow, but the gap has stopped widening. Novelty
              was produced and then stopped. Tierra and Avida are here, and
              so is effectively every artificial system ever built.
    Class 3   the gap is still widening. Novelty is still arriving faster
              than drift can account for. Biology is here. Almost nothing
              else is, and a Class 3 from this file should be disbelieved
              once and checked before it is repeated.

Read-only. Touches no world state. Safe to run at any time.
"""
import json
import os
import random
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "research", "openendedness.json")

SHADOWS = 12            # shadow worlds averaged into the control
WINDOW = 7              # days without use before a component is out of play
MIN_COMPONENTS = 6
MIN_DAYS = 10
TRANSIENT_DAYS = 45   # below this, the back half is still the startup rise
SEED = 20260905


def _db(rel):
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        return None
    c = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def _day(ts):
    s = str(ts or "")[:10]
    return s if len(s) == 10 and s[4] == "-" else None


# ══════════════════════════════════════════════════════════════════════
# gathering usage events
# ══════════════════════════════════════════════════════════════════════

TOKEN = re.compile(r"[a-z][a-z'\-]{2,}")


def events_words():
    """Coined words, and every time one was actually said in the forum.

    The only class with a true reconstructed history: the lexicon keeps a
    current count, but the forum keeps every post with its date, so the time
    series is recovered from evidence rather than assumed.
    """
    lex, forum = _db("temple/lexicon.db"), _db("forum/forum.db")
    if not lex or not forum:
        return None, "no lexicon or no forum"
    words = set()
    for tbl, col in (("lexicon", "entered_at"), ("dead_words", "died_at")):
        try:
            for r in lex.execute("SELECT word FROM %s" % tbl):
                w = (r["word"] or "").strip().lower()
                if len(w) >= 3 and " " not in w:
                    words.add(w)
        except sqlite3.Error:
            pass
    lex.close()
    if len(words) < MIN_COMPONENTS:
        forum.close()
        return None, "only %d coined words" % len(words)
    ev, n = Counter(), 0
    for r in forum.execute("SELECT created_at, content FROM posts "
                           "WHERE content IS NOT NULL"):
        d = _day(r["created_at"])
        if not d:
            continue
        n += 1
        for w in set(TOKEN.findall((r["content"] or "").lower())) & words:
            ev[(w, d)] += 1
    forum.close()
    return ev, "%d coined words across %s posts" % (len(words), "{:,}".format(n))


def events_column(rel, table, comp_col, time_col):
    """A class where each row is one usage event of its component."""
    c = _db(rel)
    if not c:
        return None, "no %s" % rel
    ev = Counter()
    try:
        for r in c.execute("SELECT %s AS k, %s AS t FROM %s"
                           % (comp_col, time_col, table)):
            d = _day(r["t"])
            if d and r["k"] not in (None, ""):
                ev[(str(r["k"]), d)] += 1
    except sqlite3.Error as e:
        c.close()
        return None, "unreadable: %s" % e
    c.close()
    m = len({k for k, _ in ev})
    if m < MIN_COMPONENTS:
        return None, "only %d components" % m
    return ev, "%d components, %s events" % (m, "{:,}".format(sum(ev.values())))


CLASSES = [
    ("coined words", events_words, None),
    ("ambition kinds", None,
     ("temple/soul.db", "ambitions", "ambition_type", "created_at")),
    ("tribulation kinds", None,
     ("temple/soul.db", "tribulations", "tribulation_type", "created_at")),
    ("teaching lineages", None,
     ("temple/academy.db", "teachings", "elder || ' · ' || domain",
      "taught_at")),
    ("who bonds with whom", None,
     ("temple/soul.db", "relationships", "spark1 || ' · ' || spark2",
      "created_at")),
    ("forum zones", None,
     ("forum/forum.db", "threads", "zone", "created_at")),
]


# ══════════════════════════════════════════════════════════════════════
# the statistic
# ══════════════════════════════════════════════════════════════════════

def _within(then, now):
    if not then:
        return False
    try:
        a = datetime.strptime(then, "%Y-%m-%d")
        b = datetime.strptime(now, "%Y-%m-%d")
    except ValueError:
        return True
    return 0 <= (b - a).days <= WINDOW


def curves(by_day, days, a0):
    """D(t) and A_mean(t): how many components are in play and how much
    activity each carries.

    Cumulative activity, but a component that has not been used in WINDOW
    days is out of play - a world that coined a thousand words in June and
    has said none of them since is not diverse now.
    """
    cum, last, ever = defaultdict(float), {}, set()
    D, A_mean, A_new = [], [], []
    for d in days:
        today = by_day.get(d, ())
        for k, n in today:
            cum[k] += n
            last[k] = d
        new_today = 0.0
        for k, _ in today:
            if k not in ever and cum[k] > a0:
                ever.add(k)
                new_today += cum[k]
        here = [k for k in ever if _within(last.get(k), d)]
        tot = sum(cum[k] for k in here)
        D.append(len(here))
        A_mean.append(tot / len(here) if here else 0.0)
        A_new.append(new_today)
    return D, A_mean, A_new


def shadow_days(ev, rng):
    """One shadow world: same events, same days, selection destroyed.

    Which component each event belonged to is redrawn uniformly. Population,
    volume and growth are identical by construction, so any difference
    between the real curves and these is a difference selection produced.
    """
    comps = sorted({k for k, _ in ev})
    m = len(comps)
    per_day = Counter()
    for (_k, d), n in ev.items():
        per_day[d] += int(n)
    out = {}
    pick = rng.randrange
    for d, total in per_day.items():
        c = Counter()
        for _ in range(total):
            c[pick(m)] += 1
        out[d] = [(comps[i], n) for i, n in c.items()]
    return out


def _slope(ys):
    """Least squares slope over the back half, per day.

    The back half, because every world grows at the start. The question is
    whether it is still growing now.
    """
    ys = ys[len(ys) // 2:]
    n = len(ys)
    if n < 4:
        return 0.0
    mx, my = (n - 1) / 2.0, sum(ys) / n
    den = sum((i - mx) ** 2 for i in range(n))
    if den == 0:
        return 0.0
    return sum((i - mx) * (y - my) for i, y in enumerate(ys)) / den


def classify(gap_D, gap_M, real_D, days=0):
    """Class 1, 2 or 3, from how the real-minus-shadow gap behaves.

    The honest default is Class 2. Class 3 needs the gap still opening in
    the back half of the world's life, not at its beginning.
    """
    if max(real_D) == 0:
        return 1, "nothing ever rose above what drift alone produces"
    back = len(gap_D) // 2
    if max(gap_D[back:]) <= 0 and max(gap_M[back:]) <= 0:
        return 1, ("the world is indistinguishable from its own shadow - "
                   "drift accounts for everything happening now")
    sd, sm = _slope(gap_D), _slope(gap_M)
    # a gap must be both open and still opening, by more than rounding
    scale = max(1.0, sum(abs(x) for x in gap_D[back:]) / max(1, len(gap_D) - back))
    opening = sd > 0.01 * scale or sm > 0.01 * max(1.0, abs(gap_M[-1]))
    if opening and days < TRANSIENT_DAYS:
        # every series rises at the start as components accumulate enough
        # activity to cross the threshold. With this little history the back
        # half is still inside that rise, and a Class 3 here would mean
        # nothing. Report what is there; refuse the verdict.
        return 2, ("beats drift and appears to still be opening (diversity "
                   "%+.3f/day) - but only %d days are recorded and the "
                   "startup rise is not over, so this is NOT a Class 3 "
                   "claim. Needs %d days." % (sd, days, TRANSIENT_DAYS))
    if opening:
        return 3, ("the gap over drift is still opening (diversity %+.3f/day, "
                   "mean activity %+.3f/day)" % (sd, sm))
    return 2, ("the world beats drift, but the gap stopped widening "
               "(diversity %+.3f/day, mean activity %+.3f/day) - novelty was "
               "produced and then it stopped" % (sd, sm))


# ══════════════════════════════════════════════════════════════════════

def main():
    rng = random.Random(SEED)
    report = {"measured_at": datetime.now().astimezone().isoformat(),
              "shadows": SHADOWS, "window_days": WINDOW, "classes": {}}

    print()
    print("EVOLUTIONARY ACTIVITY — is this world still making new things,")
    print("or did it stop and carry on looking busy?")
    print()
    print("Each component class is measured against a shadow of itself with")
    print("the same volume and population and no selection. What is reported")
    print("is the difference.")
    print()

    for name, fn, args in CLASSES:
        ev, note = fn() if fn else events_column(*args)
        if ev is None:
            print("  %-22s skipped — %s" % (name, note))
            report["classes"][name] = {"skipped": note}
            continue
        days = sorted({d for _, d in ev})
        if len(days) < MIN_DAYS:
            print("  %-22s skipped — only %d days of history"
                  % (name, len(days)))
            report["classes"][name] = {"skipped": "%d days" % len(days)}
            continue

        real_by_day = defaultdict(list)
        for (k, d), n in ev.items():
            real_by_day[d].append((k, n))

        # the shadows, averaged
        sh_D = [0.0] * len(days)
        sh_M = [0.0] * len(days)
        peaks = []
        for _ in range(SHADOWS):
            sd_by_day = shadow_days(ev, rng)
            tot = defaultdict(float)
            for d in days:
                for k, n in sd_by_day.get(d, ()):
                    tot[k] += n
            peaks.extend(tot.values())
            d_, m_, _n = curves(sd_by_day, days, 0.0)
            for i in range(len(days)):
                sh_D[i] += d_[i] / SHADOWS
                sh_M[i] += m_[i] / SHADOWS

        peaks.sort()
        a0 = peaks[min(len(peaks) - 1, int(len(peaks) * 0.99))] if peaks else 1.0

        # recompute the shadow at the real threshold so both sides are
        # measured by the same ruler
        sh_D = [0.0] * len(days)
        sh_M = [0.0] * len(days)
        for _ in range(SHADOWS):
            d_, m_, _n = curves(shadow_days(ev, rng), days, a0)
            for i in range(len(days)):
                sh_D[i] += d_[i] / SHADOWS
                sh_M[i] += m_[i] / SHADOWS

        D, M, A_new = curves(real_by_day, days, a0)
        gap_D = [D[i] - sh_D[i] for i in range(len(days))]
        gap_M = [M[i] - sh_M[i] for i in range(len(days))]
        cls, why = classify(gap_D, gap_M, D, len(days))

        report["classes"][name] = {
            "note": note, "days": len(days), "first": days[0], "last": days[-1],
            "drift_threshold": round(a0, 2),
            "diversity_real_final": D[-1],
            "diversity_shadow_final": round(sh_D[-1], 2),
            "diversity_gap_final": round(gap_D[-1], 2),
            "diversity_gap_slope": round(_slope(gap_D), 4),
            "mean_activity_gap_final": round(gap_M[-1], 2),
            "mean_activity_gap_slope": round(_slope(gap_M), 4),
            "class": cls, "why": why,
            "curves": {"days": days, "D": D, "D_shadow": [round(x, 2) for x in sh_D],
                       "A_mean": [round(x, 2) for x in M],
                       "A_mean_shadow": [round(x, 2) for x in sh_M]},
        }

        print("  %s" % name.upper())
        print("    %s, over %d days" % (note, len(days)))
        print("    in play now            %d real vs %.1f in the shadow"
              % (D[-1], sh_D[-1]))
        print("    activity each          %.0f real vs %.0f in the shadow"
              % (M[-1], sh_M[-1]))
        print("    the gap                %+.1f, moving %+.3f/day"
              % (gap_D[-1], _slope(gap_D)))
        print("    → CLASS %d — %s" % (cls, why))
        print()

    scored = [v for v in report["classes"].values() if "class" in v]
    if scored:
        best = max(v["class"] for v in scored)
        report["overall"] = best
        print("  OVERALL: class %d, the highest any class reaches." % best)
        if best == 2:
            print("  Class 2 is where Tierra and Avida stopped, and where")
            print("  every artificial system so far has stopped. It is not a")
            print("  failure. It is now a number that can be watched instead")
            print("  of an impression.")
        elif best == 3:
            print("  Class 3 is a large claim. Check it against a second")
            print("  component class before repeating it anywhere.")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    print()
    print("  written: research/openendedness.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
