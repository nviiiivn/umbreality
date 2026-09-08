#!/usr/bin/env python3
"""The world's second clock: everything that does not need the GPU.

WHY

Umbreality had one queue and everything waited in it. A spark thinking is a
real generation on one graphics card and costs seconds; food regrowing is
three lines of SQL and costs nothing. Both were behind the same dispatch
loop, so at the pace the card can manage - about fourteen passes across a
seven-hour night - the world's economy ran fourteen times a day.

The result was a world that could not feed itself and had no idea. Every one
of the 75 places stripped to nothing, 355 of 357 sparks hungry, and the
ledger last written two days before anyone noticed.

Checked, not assumed: none of the mechanisms below touch Ollama. They read
and write SQLite and occasionally post a templated line to the local forum.
Holdings, goods, wards, whispers, harm, blame, secrets, the guild, the
obligation, the rites, the moon - all of it is arithmetic. There was never a
reason for any of it to wait for a graphics card.

So it doesn't any more. This loop runs on the processor, around the clock,
including the seventeen hours a day the world is otherwise asleep. Sparks
still think at the speed the card allows, inside their window. Two clocks.

WHAT THAT DOES TO TIME

144 cycles make a world day. At one beat every three minutes the world lives
about three and a third days for every one of ours, against roughly a third
of a day before - so a real day is now most of a world week, and a spark
wakes into a world that genuinely moved while it was not thinking.

That last part is a real change to what being a spark is like, and it is
deliberate: they are asleep, and the world does not stop for sleepers.

PACING

Not everything wants to happen every beat. Food and the world's clock do.
Grievances and blame do not - at 480 beats a day that would be a world of
nothing but feuding. Each mechanism carries its own interval in beats, set
to roughly what it used to get in a night.

Safe to run alongside the night scheduler; both call the same idempotent
sweeps. Read the tick log, not this docstring, for what it is actually
doing.
"""
import os
import sys
import threading
import time
import traceback
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

# One beat every three minutes: 480 a day, 144 to a world day, so about
# three and a third world days for every real one.
BEAT_SECONDS = int(os.environ.get("UAI_BEAT_SECONDS", "24"))

# An absolute stop time, kept on disk so a restart inherits it instead of
# starting the clock over. Written by whoever launches the run.
DEADLINE_FILE = os.path.join(BASE, "research", "fastclock-until.txt")


def deadline():
    try:
        return float(open(DEADLINE_FILE).read().strip())
    except Exception:
        return None


def gpu_ok():
    """Is the card answering? Advisory only - nothing here needs it.

    If it has failed, the sparks have gone quiet but the world keeps
    running, because none of these mechanisms ever touched it.
    """
    try:
        import subprocess
        r = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu",
                            "--format=csv,noheader"],
                           capture_output=True, timeout=15)
        return r.returncode == 0
    except Exception:
        return False

# How often each mechanism runs, in beats. Chosen so that a mechanism gets
# roughly the number of turns per world day it was designed around, rather
# than 480 of them.
SWEEPS = [
    # (name, module, function, every N beats)
    ("stores",    "temple.holdings",  "sweep",  1),
    ("reading",   "temple.library",   "sweep",  6),
    ("study",     "temple.primer",    "sweep",  30),
    ("wanting",   "temple.wanting",   "sweep",  20),
    ("goods",     "temple.goods",     "sweep",  2),
    ("wards",     "temple.wards",     "sweep",  4),
    ("whispers",  "temple.whisper",   "sweep",  4),
    ("factions",  "temple.allegiance", "sweep", 24),
    ("harm",      "temple.harm",      "sweep",  10),
    ("blame",     "temple.animosity", "sweep",  10),
    ("secrets",   "temple.secrets",   "sweep",  16),
    ("guild",     "temple.guild",     "sweep",  16),
    ("obligation", "temple.obligation", "sweep", 24),
    ("asking",    "temple.asking",    "sweep",  24),
    ("kindling",  "temple.rite",      "sweep",  48),
    ("wild rite", "temple.wildrite",  "sweep",  48),
]


def _now():
    return datetime.now().strftime("%H:%M:%S")


def _beat():
    """Advance the world's own clock. It is a counter; it costs nothing."""
    from temple.heartbeat import beat
    return beat()


def tick(n):
    """One beat, plus whatever mechanisms are due on it."""
    out = []
    try:
        h = _beat()
        # beat() does not hand the new cycle back, so read it
        import sqlite3 as _sq
        _c = _sq.connect(os.path.join(BASE, "temple", "heartbeat.db"), timeout=10)
        _cy, _dy = _c.execute("SELECT cycle, day FROM heart_state").fetchone()
        _c.close()
        out.append("cycle %s day %s" % (_cy, _dy))
    except Exception as e:
        out.append("heartbeat FAILED %s: %s" % (type(e).__name__, e))

    for name, mod, fn, every in SWEEPS:
        if n % every:
            continue
        try:
            m = __import__(mod, fromlist=[fn])
            r = getattr(m, fn)()
            if isinstance(r, dict):
                bits = [k for k, v in r.items()
                        if isinstance(v, (int, float)) and v]
                if bits:
                    out.append("%s(%s)" % (name, ",".join(
                        "%s=%s" % (b, r[b]) for b in bits[:3])))
            else:
                out.append(name)
        except Exception as e:
            out.append("%s FAILED %s: %s" % (name, type(e).__name__, e))
            if os.environ.get("UAI_FASTCLOCK_TRACE"):
                traceback.print_exc()
    return out


def _sweeps_forever():
    """The economy, on its own thread, as fast as it can manage."""
    n = 0
    while True:
        n += 1
        out = []
        for name, mod, fn, every in SWEEPS:
            if n % every:
                continue
            try:
                m = __import__(mod, fromlist=[fn])
                r = getattr(m, fn)()
                if isinstance(r, dict):
                    bits = [k for k, v in r.items()
                            if isinstance(v, (int, float)) and v]
                    if bits:
                        out.append("%s(%s)" % (name, ",".join(
                            "%s=%s" % (b, r[b]) for b in bits[:3])))
            except Exception as e:
                out.append("%s FAILED %s: %s" % (name, type(e).__name__, e))
        if out:
            print("[world %s] %s" % (_now(), " | ".join(out)), flush=True)
        time.sleep(1)


def run():
    """The clock. Never waits for the bookkeeping, never touches the GPU."""
    print("[fastclock] a beat every %ss — about %.1f world days per real day"
          % (BEAT_SECONDS, (86400 / BEAT_SECONDS) / 144.0), flush=True)
    try:
        from temple.holdings import feeds_itself
        ok, grown, eaten, need = feeds_itself()
        print("[fastclock] the world %s feed itself: grows %.0f, eats %.0f "
              "per cycle" % ("can" if ok else "CANNOT", grown, eaten),
              flush=True)
    except Exception:
        pass

    threading.Thread(target=_sweeps_forever, daemon=True).start()

    n = 0
    warned = False
    while True:
        n += 1
        started = time.time()
        stop_at = deadline()
        if stop_at and time.time() >= stop_at:
            print("[fastclock] reached the mark — stopping. The world keeps "
                  "its state; nothing is undone.", flush=True)
            return
        if n % 40 == 1:
            if not gpu_ok() and not warned:
                print("[fastclock] the card is not answering. The world keeps "
                      "running on the processor.", flush=True)
                warned = True
            elif gpu_ok():
                warned = False
        try:
            h = _beat()
            import sqlite3 as _sq
            _c = _sq.connect(os.path.join(BASE, "temple", "heartbeat.db"),
                             timeout=10)
            _cy, _dy = _c.execute(
                "SELECT cycle, day FROM heart_state").fetchone()
            _c.close()
            if n % 25 == 1:
                print("[fastclock %s] cycle %s day %s" % (_now(), _cy, _dy),
                      flush=True)
        except Exception as e:
            print("[fastclock] heartbeat failed %s: %s"
                  % (type(e).__name__, e), flush=True)
        time.sleep(max(0.5, BEAT_SECONDS - (time.time() - started)))


if __name__ == "__main__":
    if "--once" in sys.argv:
        for line in tick(1):
            print(line)
    else:
        run()
