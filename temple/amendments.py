"""Ratification — the step where the world has to ask.

The Amendment Protocol in Alexandria already sets out how this world is
supposed to change itself: a proposal with its rationale, then review, then
ratification, then versioning, with core changes needing God's approval and
every version preserved so it can be rolled back. It has been written down
since June and never implemented.

The self-modification loop implemented three of the four steps without
knowing it. selfmod.observe and selfmod.hypothesize are Step 1, Proposal:
they measure the world against ten questions and write up what is wrong,
with evidence. sandbox.sandbox is Step 2, Review: it runs the change on a
copy of the world against an untouched control with the same turns and the
same seed, and reports whether it actually helped. sandbox.deploy is Step 4,
Versioning: it backs up first, commits with the reasoning in the message,
and rolls back if anything fails.

Step 3 was missing. A proposal that passed review was deployed immediately,
with nobody asked. This is Step 3.

A proposal that survives review now waits at `awaiting_ratification` until a
person says yes. Ratifying is a deliberate act and works whether or not
auto-deploy is switched on - a human saying yes is the authority the switch
was standing in for. Rejecting keeps the proposal and the reason, because a
world that is told no should be able to see that it was told no.

When the loop has been watched long enough to be trusted, set
UAI_SELFMOD_RATIFY=0 and Step 3 goes away: review passing becomes reason
enough. That is the whole training-wheels arrangement, and it is one
environment variable.
"""
import datetime
import json
import os
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROPOSALS = BASE / "temple" / "proposals.db"

# Ratification is required unless explicitly switched off. Defaulting the
# other way would mean a missing variable quietly grants the world consent.
RATIFY_DEFAULT = "1"

AWAITING = "awaiting_ratification"


def ratify_required() -> bool:
    return os.environ.get("UAI_SELFMOD_RATIFY", RATIFY_DEFAULT) == "1"


def _conn():
    c = sqlite3.connect(str(PROPOSALS), timeout=30)
    c.row_factory = sqlite3.Row
    return c


def _ensure_columns():
    """Room to record the review, the decision, and who made it."""
    c = _conn()
    have = {r[1] for r in c.execute("PRAGMA table_info(proposals)")}
    for col, decl in (("sandbox_result", "TEXT"),
                      ("decided_at", "TEXT"),
                      ("decided_by", "TEXT"),
                      ("decision_note", "TEXT")):
        if col not in have:
            c.execute("ALTER TABLE proposals ADD COLUMN %s %s" % (col, decl))
    c.commit()
    c.close()


def hold_for_ratification(proposal_id: int, sandbox_result: dict) -> dict:
    """Park a proposal that passed review, with the review attached.

    The result is stored rather than recomputed, so the page shows the
    numbers the decision was actually made on.
    """
    _ensure_columns()
    c = _conn()
    c.execute("UPDATE proposals SET status=?, sandbox_result=? WHERE id=?",
              (AWAITING, json.dumps(sandbox_result), proposal_id))
    c.commit()
    c.close()
    return {"ok": True, "id": proposal_id, "status": AWAITING}


def _load(proposal_id: int):
    c = _conn()
    row = c.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
    c.close()
    return dict(row) if row else None


def _decide(proposal_id: int, status: str, who: str, note: str = ""):
    c = _conn()
    c.execute("UPDATE proposals SET status=?, decided_at=?, decided_by=?, "
              "decision_note=? WHERE id=?",
              (status, datetime.datetime.now().isoformat(timespec="seconds"),
               who or "the Source", note or "", proposal_id))
    c.commit()
    c.close()


def ratify(proposal_id: int, who: str = "the Source") -> dict:
    """Say yes, and let the change through.

    Deploy normally refuses unless UAI_SELFMOD_DEPLOY is set. That switch
    exists to stop the world changing itself unwatched; a person saying yes
    is the thing it was standing in for, so ratification passes through it.
    The review requirement is not waived - a proposal that never passed the
    sandbox cannot be ratified, however much anybody wants it.
    """
    _ensure_columns()
    p = _load(proposal_id)
    if not p:
        return {"ok": False, "error": "no proposal %s" % proposal_id}
    if p["status"] not in (AWAITING, "proposed", "sandboxed:improves"):
        return {"ok": False, "error": "proposal is %s, not awaiting a decision"
                                      % p["status"]}
    try:
        result = json.loads(p["sandbox_result"] or "null")
    except (ValueError, TypeError):
        result = None
    if not result:
        return {"ok": False,
                "error": "this has not been through review yet - it has to "
                         "pass the sandbox before it can be ratified"}

    from temple.sandbox import deploy
    prev = os.environ.get("UAI_SELFMOD_DEPLOY")
    os.environ["UAI_SELFMOD_DEPLOY"] = "1"      # the human is the authority
    try:
        d = deploy(p, result)
    finally:
        if prev is None:
            os.environ.pop("UAI_SELFMOD_DEPLOY", None)
        else:
            os.environ["UAI_SELFMOD_DEPLOY"] = prev

    if d.get("ok"):
        _decide(proposal_id, "ratified", who)
    else:
        _decide(proposal_id, "ratification_failed", who, str(d.get("error")))
    return {"ok": d.get("ok"), "id": proposal_id, "deploy": d}


def reject(proposal_id: int, reason: str = "", who: str = "the Source") -> dict:
    """Say no, and keep the reason.

    The proposal is not deleted. A world that was told no should be able to
    see that it was told no, and why.
    """
    _ensure_columns()
    p = _load(proposal_id)
    if not p:
        return {"ok": False, "error": "no proposal %s" % proposal_id}
    _decide(proposal_id, "rejected", who, reason)
    return {"ok": True, "id": proposal_id, "status": "rejected"}


def send_to_review(proposal_id: int) -> dict:
    """Convene the review for one proposal, now.

    Review used to happen only inside the nightly loop, which is off, so
    proposals sat at `proposed` forever and nothing ever reached
    ratification. This runs Step Two on demand.

    It is cheap and safe: two copies of soul.db in a temporary directory,
    the change applied to one, the same turns from the same seed on both,
    then thrown away. No model call, so the world does not need to be awake.
    """
    _ensure_columns()
    p = _load(proposal_id)
    if not p:
        return {"ok": False, "error": "no proposal %s" % proposal_id}
    if p["status"] in ("ratified", "rejected"):
        return {"ok": False, "error": "already decided: %s" % p["status"]}

    from temple.sandbox import sandbox
    try:
        result = sandbox(p)
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, e)}

    if not result.get("ok"):
        c = _conn()
        c.execute("UPDATE proposals SET status=? WHERE id=?",
                  ("sandboxed:error", proposal_id))
        c.commit()
        c.close()
        return {"ok": False, "error": result.get("error"), "id": proposal_id}

    verdict = result.get("verdict")
    # Only a change that actually beat the control goes to a person. The
    # rest are recorded and stop there - there is nothing to decide about a
    # change that does nothing.
    status = AWAITING if verdict == "improves" else "sandboxed:%s" % verdict

    c = _conn()
    c.execute("UPDATE proposals SET status=?, sandbox_result=? WHERE id=?",
              (status, json.dumps(result), proposal_id))
    c.commit()
    c.close()
    return {"ok": True, "id": proposal_id, "verdict": verdict,
            "status": status, "review": result}


# ── what the page needs, in one call ─────────────────────────────

METRIC_MEANING = {
    "population": "how many sparks are alive",
    "open_ambitions": "work declared and not yet finished",
    "resolved_ambitions": "work carried through to the end",
    "stalled_ambitions": "work declared and never moved",
    "frozen_sparks": "sparks whose state has not changed",
    "idle_sparks": "sparks doing nothing at all",
    "unbonded_sparks": "sparks tied to nobody in either direction",
    "silent_sparks": "sparks that have not spoken",
    "quiet_boards": "places nobody has posted in",
    "orphan_sites": "places with nothing and nobody",
}

STATE_MEANING = {
    "proposed": "written up, not yet reviewed",
    "sandboxed:improves": "passed review, waiting to be held",
    "sandboxed:no effect": "review found it changed nothing",
    "sandboxed:worsens": "review found it made things worse",
    "awaiting_ratification": "passed review, waiting on you",
    "ratified": "you said yes; applied to the world",
    "rejected": "you said no",
    "ratification_failed": "you said yes but applying it failed",
    "stale": "the condition it described no longer holds",
}


def _latest_observations(conn):
    """The most recent reading of each of the ten metrics."""
    rows = conn.execute(
        "SELECT o.* FROM observations o JOIN (SELECT metric, MAX(id) mid "
        "FROM observations GROUP BY metric) m ON o.id = m.mid").fetchall()
    out = []
    for r in rows:
        try:
            detail = json.loads(r["detail"] or "[]")
        except (ValueError, TypeError):
            detail = []
        out.append({
            "metric": r["metric"],
            "means": METRIC_MEANING.get(r["metric"], ""),
            "value": r["value"],
            "names": detail if isinstance(detail, list) else [],
            "observed_at": r["observed_at"],
        })
    out.sort(key=lambda x: x["metric"])
    return out


def board() -> dict:
    """Everything the amendments page shows."""
    _ensure_columns()
    c = _conn()

    proposals = []
    for r in c.execute("SELECT * FROM proposals ORDER BY id DESC"):
        d = dict(r)
        for k in ("params", "evidence", "sandbox_result"):
            try:
                d[k] = json.loads(d.get(k) or "null")
            except (ValueError, TypeError):
                pass
        d["state_means"] = STATE_MEANING.get(d.get("status"), "")
        d["decidable"] = d.get("status") in (AWAITING, "sandboxed:improves")
        # what a person can actually do with this one, right now
        d["reviewable"] = d.get("status") in ("proposed", "stale",
                                              "sandboxed:error")
        d["settled"] = d.get("status") in ("ratified", "rejected",
                                           "sandboxed:no effect",
                                           "sandboxed:worsens")
        proposals.append(d)

    observations = _latest_observations(c)
    total_obs = c.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    c.close()

    waiting = [p for p in proposals if p["decidable"]]
    unreviewed = [p for p in proposals if p["reviewable"]]
    return {
        "ratification_required": ratify_required(),
        "watching": observations,
        "observations_total": total_obs,
        "proposals": proposals,
        "waiting_on_you": len(waiting),
        "never_reviewed": len(unreviewed),
        "counts": {
            "ratified": sum(1 for p in proposals if p["status"] == "ratified"),
            "rejected": sum(1 for p in proposals if p["status"] == "rejected"),
            "stale": sum(1 for p in proposals if p["status"] == "stale"),
            "total": len(proposals),
        },
    }
