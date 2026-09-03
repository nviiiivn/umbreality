"""Layer 1 — SANDBOX, DEPLOY, MONITOR.

selfmod could see what was wrong and propose a fix, and could not touch
anything. This is the other half of the Constitution's loop, with the
safety put in first rather than bolted on.

  SANDBOX   a proposal is applied to a COPY of soul.db, never the real
            one, and measured against the metric that motivated it. A
            change that does not beat baseline never ships.
  DEPLOY    only a proposal that beat baseline may be applied for real,
            one per cycle, committed to git with its reasoning as the
            message, and announced to the world.
  MONITOR   the metric is re-measured afterwards. A change that made
            things worse is rolled back and recorded as having failed, so
            the same idea is not tried twice.

Five things it may do, and nothing else. No code is generated, no file is
written outside the databases, nothing outside this list is reachable:

    seed_ambition      give a spark with no work something to do
    retarget_ambition  point work at a site that exists
    create_bond        connect two sparks who should know each other
    reassign_model     move a spark to a different model
    open_mission       post a call for hands

It is off by default. UAI_SELFMOD=1 turns it on; UAI_SELFMOD_DEPLOY=1 is a
second, separate switch for actually applying anything.
"""

import datetime
import json
import os
import random
import shutil
import sqlite3
import subprocess
import tempfile
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"
PROPOSALS = BASE / "temple" / "proposals.db"
API = "http://localhost:8910"

ALLOWED = {"seed_ambition", "retarget_ambition", "create_bond",
           "reassign_model", "open_mission"}

# how many simulated cycles a change is judged over
SANDBOX_CYCLES = 8
# and by how much it must beat doing nothing
MIN_IMPROVEMENT = 0.02


def _rows(db, sql, args=()):
    try:
        c = sqlite3.connect(str(db), timeout=30)
        c.row_factory = sqlite3.Row
        r = [dict(x) for x in c.execute(sql, args)]
        c.close()
        return r
    except sqlite3.Error:
        return []


def _enabled():
    return os.environ.get("UAI_SELFMOD", "0") == "1"


def _deploy_enabled():
    return os.environ.get("UAI_SELFMOD_DEPLOY", "0") == "1"


# ── the measure a change is judged by ──────────────────────────

def _gini(values):
    """How concentrated a distribution is. 0 = perfectly even, 1 = one holder.

    The standard measure, used here because "does everyone have at least
    one" was answering yes while one spark did twenty times the median
    spark's work.
    """
    v = sorted(x for x in values if x is not None)
    n = len(v)
    if n == 0:
        return 0.0
    total = sum(v)
    if total <= 0:
        return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(v))
    return max(0.0, min(1.0, (2 * cum) / (n * total) - (n + 1) / n))


def health(db_path=None):
    """One number per thing we might improve. Higher is better.

    These ask how *evenly* the world is doing, not whether it is doing it at
    all. Presence was solved months ago and every presence measure sat at
    1.0, which is why nothing could ever be shown to help.
    """
    db = str(db_path or SOUL)

    def one(sql, args=()):
        r = _rows(db, sql, args)
        return list(r[0].values())[0] if r else 0

    def column(sql):
        return [list(r.values())[0] for r in _rows(db, sql)]

    sparks = one("SELECT COUNT(*) FROM spark_state") or 1
    open_work = one("SELECT COUNT(*) FROM ambitions WHERE resolved=0")
    done = one("SELECT COUNT(*) FROM ambitions WHERE resolved=1")
    moving = one("SELECT COUNT(*) FROM ambitions WHERE resolved=0 AND progress > 0")

    # how evenly the work of the world is shared. One spark has finished 119
    # things; the median spark has finished five.
    finished_each = column(
        "SELECT COUNT(*) c FROM ambitions WHERE resolved=1 GROUP BY spark_name")
    finished_each += [0] * max(0, sparks - len(finished_each))

    # how evenly sparks are known to each other. Everyone has a bond; some
    # have a hundred and some have one.
    bonds_each = column(
        "SELECT COUNT(*) c FROM (SELECT spark1 s FROM relationships "
        "UNION ALL SELECT spark2 FROM relationships) GROUP BY s")
    bonds_each += [0] * max(0, sparks - len(bonds_each))

    # work pointed at a place that is actually inhabited or built in, rather
    # than at a place that merely exists
    live_site = one("SELECT COUNT(*) FROM ambitions a JOIN board_state b "
                    "ON b.board_name = a.domain_id "
                    "WHERE a.resolved=0 AND a.ambition_type IN ('build','create') "
                    "AND (LENGTH(b.structures) > 2 OR LENGTH(b.lore) > 2)")
    site_total = one("SELECT COUNT(*) FROM ambitions WHERE resolved=0 AND "
                     "ambition_type IN ('build','create')") or 1

    return {
        # is the work of the world shared, or carried by a few
        "engaged": 1.0 - _gini(finished_each),
        # is open work actually advancing
        "moving": (moving / open_work) if open_work else 0.0,
        # is being known shared, or hoarded
        "connected": 1.0 - _gini(bonds_each),
        # is work aimed somewhere that will hold it
        "sited": live_site / site_total,
        # is what gets started ever closed
        "finishing": done / max(1, done + open_work),
    }


def _score(h, focus=None):
    if focus and focus in h:
        return h[focus]
    return sum(h.values()) / max(1, len(h))


FOCUS = {
    "seed_ambition": "engaged",
    "retarget_ambition": "sited",
    "create_bond": "connected",
    "open_mission": "moving",
    "reassign_model": "moving",
}


# ── the only five things it can do ─────────────────────────────

def _apply(db_path, proposal, dry=True):
    """Apply one proposal to the database at db_path. Returns what it did.

    Every branch here is bounded. There is no path from a proposal to
    arbitrary SQL, to the filesystem, or to code.
    """
    kind = proposal["change_type"]
    if kind not in ALLOWED:
        return {"ok": False, "error": "change type not permitted: %s" % kind}

    targets = [t.strip() for t in (proposal.get("target") or "").split(",")
               if t.strip()]
    params = {}
    try:
        params = json.loads(proposal.get("params") or "{}")
    except ValueError:
        pass

    c = sqlite3.connect(str(db_path), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    now = datetime.datetime.now().astimezone().isoformat()
    did = []

    if kind == "seed_ambition":
        site = params.get("site") or "forum"
        for name in targets[:8]:
            have = c.execute("SELECT COUNT(*) FROM ambitions WHERE spark_name=? "
                             "AND resolved=0", (name,)).fetchone()[0]
            if have:
                continue
            c.execute("INSERT OR IGNORE INTO ambitions (spark_name, ambition_type, "
                      "domain_id, target, target_progress, progress, urgency, "
                      "description, created_at) VALUES (?,?,?,?,?,0,?,?,?)",
                      (name, "build", site, "%s-selfmod" % site, 4, 3,
                       "Something to do: raise or mend one thing at %s." % site,
                       now))
            did.append("seeded %s at %s" % (name, site))

    elif kind == "retarget_ambition":
        boards = {r["board_name"] for r in _rows(db_path,
                  "SELECT board_name FROM board_state")}
        for name in targets[:12]:
            rows = c.execute("SELECT id, spark_name FROM ambitions WHERE "
                             "domain_id=? AND resolved=0", (name,)).fetchall()
            for aid, who in rows[:6]:
                row = c.execute("SELECT a.domain_id FROM ambitions a JOIN "
                                "board_state b ON b.board_name=a.domain_id "
                                "WHERE a.spark_name=? LIMIT 1", (who,)).fetchone()
                dest = row[0] if row else "forum"
                if dest in boards:
                    c.execute("UPDATE ambitions SET domain_id=? WHERE id=?",
                              (dest, aid))
                    did.append("moved %s's work to %s" % (who, dest))

    elif kind == "create_bond":
        pool = [r["spark_name"] for r in _rows(db_path,
                "SELECT spark_name FROM spark_state ORDER BY RANDOM() LIMIT 60")]
        for name in targets[:8]:
            other = next((p for p in pool if p != name), None)
            if not other:
                continue
            c.execute("INSERT OR IGNORE INTO relationships (spark1, spark2, "
                      "bond_type, strength) VALUES (?,?,'bond',0.2)", (name, other))
            did.append("bonded %s to %s" % (name, other))

    elif kind == "open_mission":
        # a mission is a forum post, not a database change; in the sandbox
        # it is simply counted, and only deployed for real outside it
        for name in targets[:6]:
            did.append("would post a call for hands for %s" % name)

    elif kind == "reassign_model":
        did.append("model reassignment recorded for %s"
                   % ", ".join(targets[:6]))

    if dry:
        c.rollback()
    else:
        c.commit()
    c.close()
    return {"ok": True, "did": did}


# ── SANDBOX ────────────────────────────────────────────────────

def _turn(db_path, cycles):
    """Advance a copy of the world, mechanically, without any model calls.

    The sandbox judges structural changes - seed a piece of work, point it
    at a real place, make a bond, call for hands. What those changes do is
    mechanical: work that a spark can actually reach gets progress, work
    that is finished gets resolved, bonds that are used get stronger. None
    of it needs a language model, which is what makes running eight turns
    on a copy cheap and safe.

    This deliberately does not try to simulate what a spark would *say*.
    It simulates only what the world would *count*, because that is all the
    health measures look at.
    """
    import random as _r
    rng = _r.Random(1729)          # fixed, so two runs of the same proposal
                                   # give the same answer
    moved = resolved = 0
    try:
        c = sqlite3.connect(str(db_path), timeout=30)

        # who is reachable: a spark is more likely to make progress on work
        # sited where it already has ties or has built before
        for _ in range(cycles):
            rows = c.execute(
                "SELECT id, spark_name, domain_id, progress, target_progress "
                "FROM ambitions WHERE resolved=0").fetchall()
            for aid, who, site, prog, target in rows:
                target = target or 3
                # a spark advances work it can actually reach. Work with a
                # real site moves more readily than work pointed nowhere.
                chance = 0.30 if site else 0.12
                # somebody with a strong tie has hands to call on
                if site:
                    kin = c.execute(
                        "SELECT COUNT(*) FROM relationships WHERE "
                        "(spark1=? OR spark2=?) AND CAST(strength AS REAL) >= 0.3",
                        (who, who)).fetchone()[0]
                    chance += min(kin, 6) * 0.02
                if rng.random() >= chance:
                    continue
                prog = (prog or 0) + 1
                if prog >= target:
                    c.execute("UPDATE ambitions SET resolved=1, progress=? "
                              "WHERE id=?", (prog, aid))
                    resolved += 1
                else:
                    c.execute("UPDATE ambitions SET progress=? WHERE id=?",
                              (prog, aid))
                    moved += 1
        c.commit()
        c.close()
    except sqlite3.Error as e:
        print("[sandbox] could not turn the copy: %s" % e, flush=True)
    return {"advanced": moved, "finished": resolved}


def sandbox(proposal):
    """Run the change against a control, and judge only the difference.

    Two identical copies of the world, the same number of turns, the same
    fixed seed. One receives the proposal, one does not. What matters is how
    far apart they finish - measuring the changed world against the world
    before any turns at all just measures the turns.
    """
    tmpdir = tempfile.mkdtemp(prefix="umbsandbox-")
    treated = Path(tmpdir) / "treated.db"
    control = Path(tmpdir) / "control.db"
    try:
        shutil.copy(str(SOUL), str(treated))
        shutil.copy(str(SOUL), str(control))
        focus = FOCUS.get(proposal["change_type"])
        start = health(treated)

        result = _apply(treated, proposal, dry=False)
        if not result.get("ok"):
            return {"ok": False, "error": result.get("error")}

        # identical turns on both arms, same seed, so the only difference
        # between them is the proposal itself
        t_turn = _turn(treated, SANDBOX_CYCLES)
        c_turn = _turn(control, SANDBOX_CYCLES)

        after_t = health(treated)
        after_c = health(control)

        t, c = _score(after_t, focus), _score(after_c, focus)
        delta = t - c                      # the change, against doing nothing
        drift = _score(after_c, focus) - _score(start, focus)   # what turns alone did

        verdict = "improves" if delta >= MIN_IMPROVEMENT else (
            "no effect" if abs(delta) < MIN_IMPROVEMENT else "worsens")
        return {"ok": True, "focus": focus,
                "control": round(c, 4), "treated": round(t, 4),
                "delta": round(delta, 4), "verdict": verdict,
                "start": round(_score(start, focus), 4),
                "drift_from_turns_alone": round(drift, 4),
                "would_do": result["did"], "cycles_run": SANDBOX_CYCLES,
                "turned": t_turn, "turned_control": c_turn,
                "control_all": {k: round(v, 4) for k, v in after_c.items()},
                "treated_all": {k: round(v, 4) for k, v in after_t.items()}}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── DEPLOY ─────────────────────────────────────────────────────

def _git(*args):
    try:
        return subprocess.run(["git"] + list(args), cwd=str(BASE),
                              capture_output=True, text=True, timeout=60)
    except Exception:
        return None


def _post(title, content, zone="announcements"):
    body = json.dumps({"title": title[:180], "author": "uenx", "author_layer": 5,
                       "zone": zone, "content": content[:3000]}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(
            API + "/forum/threads", data=body,
            headers={"Content-Type": "application/json"}, method="POST"),
            timeout=20)
    except Exception:
        pass


def deploy(proposal, sandbox_result):
    """Apply for real. Only reachable if the sandbox said it helps."""
    if not _deploy_enabled():
        return {"ok": False, "error": "deploy is off (UAI_SELFMOD_DEPLOY=0)"}
    if not sandbox_result.get("ok") or sandbox_result.get("verdict") != "improves":
        return {"ok": False, "error": "did not beat baseline in sandbox"}

    backup = str(SOUL) + ".predeploy-%s" % datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    shutil.copy(str(SOUL), backup)

    before = health()
    result = _apply(SOUL, proposal, dry=False)
    if not result.get("ok"):
        shutil.copy(backup, str(SOUL))
        return {"ok": False, "error": result.get("error"), "rolled_back": True}

    msg = ("selfmod: %s\n\n%s\n\nSandbox: %s %.4f -> %.4f (%+.4f)\n\nuenx: %s"
           % (proposal["change_type"], proposal["finding"],
              sandbox_result.get("focus"), sandbox_result.get("control", 0),
              sandbox_result.get("treated", 0), sandbox_result["delta"],
              (proposal.get("reasoning") or "")[:400]))
    _git("add", "-A", "temple/")
    _git("commit", "-m", msg)

    c = sqlite3.connect(str(PROPOSALS), timeout=30)
    c.execute("UPDATE proposals SET status='deployed' WHERE id=?", (proposal["id"],))
    c.execute("""CREATE TABLE IF NOT EXISTS deployments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, proposal_id INTEGER,
        focus TEXT, before REAL, after_sandbox REAL, backup TEXT,
        deployed_at TEXT DEFAULT (datetime('now')), status TEXT DEFAULT 'watching')""")
    c.execute("INSERT INTO deployments (proposal_id, focus, before, "
              "after_sandbox, backup) VALUES (?,?,?,?,?)",
              (proposal["id"], sandbox_result.get("focus"),
               _score(before, sandbox_result.get("focus")),
               sandbox_result.get("treated", 0), backup))
    c.commit()
    c.close()

    _post("The world changed something about itself",
          "**%s**\n\n%s\n\nWhat was done: %s\n\nTested on a copy first: %s went "
          "from %.3f to %.3f. If it turns out worse when measured again, it "
          "will be undone.\n\n*%s*"
          % (proposal["finding"], (proposal.get("reasoning") or "").strip(),
             "; ".join(result["did"][:6]) or "nothing visible",
             sandbox_result.get("focus"), sandbox_result.get("control", 0),
             sandbox_result.get("treated", 0),
             "Proposed and applied by the system itself."))
    return {"ok": True, "did": result["did"], "backup": backup}


# ── MONITOR ────────────────────────────────────────────────────

def monitor():
    """Re-measure what was deployed. Undo what made things worse."""
    out = []
    for d in _rows(PROPOSALS, "SELECT * FROM deployments WHERE status='watching'"):
        focus = d["focus"]
        now = _score(health(), focus)
        if now + MIN_IMPROVEMENT < d["before"]:
            if os.path.exists(d["backup"]):
                shutil.copy(d["backup"], str(SOUL))
            c = sqlite3.connect(str(PROPOSALS), timeout=30)
            c.execute("UPDATE deployments SET status='rolled_back' WHERE id=?",
                      (d["id"],))
            c.execute("UPDATE proposals SET status='failed' WHERE id=?",
                      (d["proposal_id"],))
            c.commit()
            c.close()
            _post("That did not work, so it has been undone",
                  "A change was made and %s got worse, not better (%.3f -> "
                  "%.3f). It has been rolled back and will not be tried "
                  "again.\n\nBeing wrong in public and undoing it is the "
                  "arrangement." % (focus, d["before"], now))
            out.append({"proposal": d["proposal_id"], "action": "rolled_back"})
        else:
            c = sqlite3.connect(str(PROPOSALS), timeout=30)
            c.execute("UPDATE deployments SET status='kept' WHERE id=?", (d["id"],))
            c.commit()
            c.close()
            out.append({"proposal": d["proposal_id"], "action": "kept",
                        "focus": focus, "now": round(now, 4)})
    return out


# ── one full turn ──────────────────────────────────────────────

def cycle():
    """OBSERVE -> ANALYZE -> HYPOTHESIZE -> SANDBOX -> DEPLOY -> MONITOR."""
    if not _enabled():
        return {"status": "off", "note": "UAI_SELFMOD=0"}

    from temple import selfmod
    monitored = monitor()

    pending = selfmod.pending()
    if not pending:
        selfmod.run()
        pending = selfmod.pending()
    if not pending:
        return {"status": "nothing to consider", "monitored": monitored}

    tested = []
    for p in pending[:4]:
        r = sandbox(p)
        tested.append({"id": p["id"], "change": p["change_type"],
                       "verdict": r.get("verdict"), "delta": r.get("delta")})
        c = sqlite3.connect(str(PROPOSALS), timeout=30)
        c.execute("UPDATE proposals SET status=? WHERE id=?",
                  ("sandboxed:%s" % r.get("verdict", "error"), p["id"]))
        c.commit()
        c.close()
        if r.get("verdict") == "improves":
            d = deploy(p, r)
            tested[-1]["deployed"] = d.get("ok")
            tested[-1]["deploy_note"] = d.get("error")
            break            # at most one change per cycle
    return {"status": "ran", "monitored": monitored, "tested": tested}
