"""Let the world see its own wiring, and say what is wrong with it.

The self-modification loop has watched ten things since it was written:
population, open ambitions, resolved ambitions, stalled ambitions, frozen
sparks, idle sparks, unbonded sparks, silent sparks, quiet boards, orphan
sites. Every one is a row count. It can notice that sparks are lonely and it
has never been able to notice that the wardens never ran, because there is
no observation in it for a thing that was built and connected to nothing -
which is the fault that has actually shaped this world.

So it gets two more eyes:

    unreachable_code   functions nothing in the world can reach
    dead_modules       whole files where nothing is reachable

And it can now say so. The existing change types all write database rows -
open a mission, make a bond, seed an ambition - so even seeing the problem
it had no way to describe the fix. A proposal of type `wire` names a
function and the loop that should call it. It changes nothing by itself.

WHAT THIS DELIBERATELY DOES NOT DO

It does not edit code. sandbox._apply writes rows and only rows, and that
stays true: a world that can rewrite its own source while nobody is watching
is a different proposition from one that can rearrange its own furniture,
and that threshold is the Source's to cross rather than mine.

What it can do is see the fault, name it precisely, and put it before the
Congress with evidence - which is the difference between a world that cannot
know it is broken and one that can tell you where.
"""
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROPOSALS = BASE / "temple" / "proposals.db"
WIRING = BASE / "research" / "wiring.json"

# a file with this many unreachable functions is not a gap, it is a module
# nobody connected
DEAD_MODULE_AT = 4


def _conn():
    c = sqlite3.connect(str(PROPOSALS), timeout=30)
    c.row_factory = sqlite3.Row
    return c


def _cycle():
    try:
        from temple.cycles import current_cycle
        return current_cycle()
    except Exception:
        return 0


def look() -> dict:
    """Read the wiring report, computing it if it is stale or missing."""
    if not WIRING.exists():
        try:
            subprocess.run([sys.executable, str(BASE / "research" / "wiring.py")],
                           capture_output=True, timeout=240)
        except Exception as e:
            return {"error": "%s: %s" % (type(e).__name__, e)}
    try:
        return json.loads(WIRING.read_text())
    except (OSError, ValueError) as e:
        return {"error": str(e)}


def observe() -> dict:
    """Record what the world can now see about itself.

    Written into the same observations table the other ten metrics use, so
    it sits alongside them and nothing has to treat it specially.
    """
    r = look()
    if r.get("error"):
        return {"ok": False, "why": r["error"]}

    dead_modules = {f: v for f, v in (r.get("by_file") or {}).items()
                    if len(v) >= DEAD_MODULE_AT}

    c = _conn()
    c.execute("""CREATE TABLE IF NOT EXISTS observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        observed_at TEXT DEFAULT (datetime('now')),
        metric TEXT, value REAL, detail TEXT)""")
    c.execute("INSERT INTO observations (metric, value, detail) VALUES (?,?,?)",
              ("unreachable_code", float(r["unreachable"]),
               json.dumps([d["name"] for d in r.get("dead", [])][:60])))
    c.execute("INSERT INTO observations (metric, value, detail) VALUES (?,?,?)",
              ("dead_modules", float(len(dead_modules)),
               json.dumps(sorted(dead_modules))))
    c.commit()
    c.close()
    return {"ok": True, "unreachable": r["unreachable"],
            "reachable": r["reachable"],
            "dead_modules": sorted(dead_modules),
            "worst": [(f, len(v)) for f, v in list(dead_modules.items())[:5]]}


def propose() -> dict:
    """Say what is wrong, precisely, with evidence.

    A proposal of type `wire` names functions nothing reaches and the loop
    that ought to call them. It applies nothing - the Congress reviews it and
    the Source decides, the same as every other amendment.
    """
    r = look()
    if r.get("error"):
        return {"ok": False, "why": r["error"]}

    by_file = r.get("by_file") or {}
    worst = [(f, v) for f, v in by_file.items() if len(v) >= DEAD_MODULE_AT]
    if not worst:
        return {"ok": False, "why": "nothing is badly enough disconnected"}

    c = _conn()
    made = []
    for path, items in worst[:3]:
        names = [i["name"] for i in items]
        already = c.execute(
            "SELECT id FROM proposals WHERE change_type='wire' AND target=? "
            "AND status IN ('proposed','awaiting_ratification')",
            (path,)).fetchone()
        if already:
            continue

        finding = ("%d functions in %s that nothing in the world reaches"
                   % (len(names), path))
        reasoning = (
            "These were written and connected to nothing. No test fails and "
            "no error appears - a function only runs if something calls it, "
            "and temple/scheduler.py is the only heartbeat here. Every one of "
            "these is either work that should be running and is not, or work "
            "that should be deleted. I cannot tell which from here; that is a "
            "judgement, and judgements go to the Congress.\n\n"
            "What would fix it: call them from the maintenance round, give "
            "them an HTTP route, call them from a spark's turn, or remove "
            "them.")
        cur = c.execute(
            "INSERT INTO proposals (finding, reasoning, change_type, target, "
            "params, evidence, status) VALUES (?,?,?,?,?,?,?)",
            (finding, reasoning, "wire", path,
             json.dumps({"functions": names[:20],
                         "fix": "call from scheduler, route, or spark turn, "
                                "or delete"}),
             json.dumps(names[:20]), "proposed"))
        made.append({"id": cur.lastrowid, "file": path, "count": len(names)})
    c.commit()
    c.close()
    return {"ok": True, "raised": made}


def cycle() -> dict:
    """One turn of the world looking at itself."""
    seen = observe()
    said = propose() if seen.get("ok") else {"ok": False}
    return {"observed": seen, "proposed": said}
