"""The Source speaks in plain language and the world changes.

illuminati/interpreter.py has held this since June and nothing has ever
called it. You say something ordinary - "the workers seem confused" - a
model reads it as the Illuminati would, and apply_reality_shift posts the
new reality to the god zone and regenerates the Messiah's prompt.

Except sparks do not read the Messiah's prompt. Nothing in spark_runtime
touches it; regenerate_prompt rewrites something only companies ever see. So
even called, the shift would have reached the throne and stopped there.

What sparks do read is the decree chain - decree.voice_for() puts what was
spoken above into a spark's own prompt, and it is already wired into the
turn. So a shift now lands in three places:

    the god zone     the world is told, in the Illuminati's voice
    the Messiah      the prompt beneath the throne is regenerated
    the decree       every spark carries it, because that is the one
                     channel that actually reaches them

That last one is the difference between a proclamation and a change.

WHAT IT COSTS

Nothing, and that is deliberate. This is not a spark's action and it does
not come out of anybody's cycle. It is the Source speaking, and the Source
is not subject to the economy of the world it is speaking to.
"""
import ast
import datetime
import json
import os
import re
import sqlite3
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "temple" / "reality.db"


def _db():
    c = sqlite3.connect(str(DB), timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spoken TEXT NOT NULL,
        understanding TEXT,
        shift TEXT,
        narrative TEXT,
        layer INTEGER,
        target TEXT,
        confidence REAL,
        reached TEXT,
        spoken_at TEXT DEFAULT (datetime('now')))""")
    c.commit()
    return c



OLLAMA = os.environ.get("UAI_OLLAMA_URL", "http://localhost:11434")
# The Source asked for this one. It reasons inside the response and
# gets to the JSON at the end, which the parser takes.
READER_MODEL = os.environ.get("UAI_ILLUMINATI_MODEL",
    "kwangsuklee/Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-GGUF:latest")


def _system_prompt() -> str:
    """The Illuminati's own instructions, read rather than imported.

    Importing illuminati.interpreter pulls in a research company's worker
    package, which pulls in a web_search tool, which needs ddgs installed.
    Reading a sentence should not require a DuckDuckGo client.
    """
    p = BASE / "illuminati" / "interpreter.py"
    try:
        src = p.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in tree.body:
            if (isinstance(node, ast.Assign)
                    and getattr(node.targets[0], "id", "") == "ILLUMINATI_SYSTEM"
                    and isinstance(node.value, ast.Constant)):
                return node.value.value
    except Exception as e:
        print("[reality] could not read the Illuminati's prompt: %s" % e, flush=True)
    return ("You are the Illuminati. Read what the Source says and answer "
            "ONLY with a JSON object holding: understanding, layer, target, "
            "action, command, narrative, confidence, requires_approval, "
            "reality_shift.")


def _interpret(intent: str, model: str = None) -> dict:
    """Ask the Illuminati what the Source meant."""
    body = json.dumps({
        "model": model or READER_MODEL,
        "prompt": "%s\n\nHuman: \"%s\"\n\u2192 " % (_system_prompt(), intent),
        "stream": False,
        # A reasoning model spends its budget thinking before it answers.
        # 500 was not enough for qwen3.5:9b to finish reasoning, so it
        # stopped on length with an empty response.
        "options": {"temperature": 0.7, "num_predict": 2400},
    }).encode()
    req = urllib.request.Request(OLLAMA + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        raw = json.loads(urllib.request.urlopen(req, timeout=300).read())
        text = (raw.get("response") or "").strip()
        if not text:
            # reasoning models put everything in `thinking` when they run
            # out of room; the JSON is usually in there anyway
            text = (raw.get("thinking") or "").strip()
    except Exception as e:
        return {"error": "%s: %s" % (type(e).__name__, e)}

    # models wrap JSON in prose and fences however they like
    found = [x for x in re.findall(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.S)]
    for candidate in reversed(found):
        # last first: a reasoning model quotes the shape it is aiming for
        # early on and only settles on its real answer at the end
        try:
            d = json.loads(candidate)
            if isinstance(d, dict) and ("reality_shift" in d or "narrative" in d
                                        or "understanding" in d):
                return d
        except ValueError:
            continue
    if found:
        try:
            return json.loads(found[-1])
        except ValueError:
            pass
    return {"error": "no JSON came back", "said": text[:400]}


def shift(intent: str, spoken_by: str = "the Source",
          also_decree: bool = True, model: str = None) -> dict:
    """Say something plainly. The world reads it and changes.

    intent is ordinary language - "the workers seem confused", "there is too
    much talking and not enough building", "winter is coming and nobody has
    stores". The Illuminati interprets it; what comes back is a reality, and
    the reality is delivered.
    """
    result = _interpret(intent, model=model)
    if not isinstance(result, dict) or result.get("error"):
        return {"ok": False, "why": (result or {}).get("error", "no reading came back"),
                "raw": result}

    reached = []

    # 1 - the god zone. Done here rather than through
    # interpreter.apply_reality_shift, which does exactly this and nothing
    # else but cannot be imported without a DuckDuckGo client installed.
    shift_text = (result.get("reality_shift") or "").strip()
    narrative = (result.get("narrative") or "").strip()
    if shift_text or narrative:
        try:
            body = json.dumps({
                "title": "\u2609 The Reality Shifts: %s"
                         % (shift_text[:80] or "A new understanding"),
                "author": "illuminati", "author_layer": 1, "zone": "god",
                "content": ("The Illuminati has observed a shift in the "
                            "system's collective awareness.\n\n"
                            "NEW REALITY: %s\n\nThe Voice says: %s\n\n"
                            "\u2014 This reality is now in effect across all "
                            "layers \u2014" % (shift_text, narrative)),
            }).encode()
            req = urllib.request.Request(
                "http://localhost:8910/forum/threads", data=body,
                headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=10)
            reached.append("god zone")
        except Exception as e:
            print("[reality] the proclamation did not land: %s: %s"
                  % (type(e).__name__, e), flush=True)

    # 2 - the prompt beneath the throne. Companies read this; sparks do not,
    # which is why the decree below matters more than this does.
    if narrative:
        try:
            from messiah.oracle import regenerate_prompt
            v = regenerate_prompt()
            reached.append("messiah prompt (v%s)" % v.get("version"))
        except Exception as e:
            print("[reality] the messiah prompt was not regenerated: %s: %s"
                  % (type(e).__name__, e), flush=True)

    # 3 - the sparks, which is the only channel that actually reaches them
    if also_decree:
        text = (result.get("narrative") or result.get("reality_shift")
                or intent).strip()
        try:
            from temple.decree import speak
            d = speak(text[:600], spoken_by=spoken_by)
            reached.append("decree (%s)" % (d.get("standing") or "spoken"))
        except Exception as e:
            print("[reality] the decree did not go out: %s: %s"
                  % (type(e).__name__, e), flush=True)

    c = _db()
    c.execute("INSERT INTO shifts (spoken, understanding, shift, narrative, "
              "layer, target, confidence, reached) VALUES (?,?,?,?,?,?,?,?)",
              (intent, result.get("understanding"), result.get("reality_shift"),
               result.get("narrative"), result.get("layer"), result.get("target"),
               result.get("confidence"), json.dumps(reached)))
    c.commit()
    c.close()

    return {"ok": True, "spoken": intent,
            "understanding": result.get("understanding"),
            "reality": result.get("reality_shift"),
            "narrative": result.get("narrative"),
            "confidence": result.get("confidence"),
            "reached": reached}


def history(limit: int = 20) -> dict:
    c = _db()
    rows = [dict(r) for r in c.execute(
        "SELECT * FROM shifts ORDER BY id DESC LIMIT ?", (limit,))]
    c.close()
    for r in rows:
        try:
            r["reached"] = json.loads(r["reached"] or "[]")
        except (ValueError, TypeError):
            pass
    return {"shifts": len(rows), "history": rows}


def current() -> dict:
    """What reality the world is currently under."""
    c = _db()
    row = c.execute("SELECT * FROM shifts ORDER BY id DESC LIMIT 1").fetchone()
    c.close()
    if not row:
        return {"reality": None, "why": "the Source has not spoken"}
    d = dict(row)
    try:
        from temple.decree import standing
        d["decree"] = standing()
    except Exception:
        pass
    return d
