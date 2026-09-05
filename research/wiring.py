#!/usr/bin/env python3
"""What in this world can actually be reached, and what only looks finished.

Umbreality grew by writing modules, not by extending the one loop that runs
them. temple/scheduler.py is the only heartbeat, and anything not reachable
from it - or from an HTTP route, or from a spark's turn, or from a __main__ -
is dead code that looks exactly like live code. No test fails, no error
appears, it sits there looking done.

That is how the wardens never patrolled, apply_reality_shift was never
called, sim/strategies.py was never imported, record_daily_prices left
price_history empty for the life of the world, score_reply_received froze
honour for all 298, and gnu.cycle - which says "safe on a timer" in its own
docstring - was never put on one.

HOW THIS WORKS, AND WHAT THE FIRST VERSION GOT WRONG

Reachability, not mentions: a function called only by another dead function
is still dead, and both are "mentioned".

But the first version keyed everything by bare function name, so `sweep`
from eight different modules collapsed into a single entry and any one of
them being live made all of them look live. Names are module-qualified now,
and a call is resolved against what that module actually imported - so
`from temple.harm import commit_harm` followed by `commit_harm(...)` marks
temple.harm.commit_harm and nothing else.

Where a call cannot be resolved to one module - a bare name matching several
- it marks all the candidates, which errs toward calling things live. This
undercounts dead code rather than crying wolf, which is the right direction
for something that fails a commit.
"""
import ast
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1
            else "/home/nvii/projects/spark-world/umbreality-ai")
SKIP_DIRS = {".git", "__pycache__", "node_modules", "venv", ".venv",
             "backups", "archive", "wwwProjects"}

# these run without anybody calling them
ENTRY_FILES = {"temple/scheduler.py", "worker_api.py",
               "temple/spark_runtime.py", "temple/spark_scheduler.py",
               "temple/heartbeat.py"}

SKIP_PREFIX = ("_", "test_")


def _mod(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("/", ".")[:-3]


def _is_backup(name):
    """A copy kept for safety is not part of the world."""
    n = name.lower()
    return (".bak" in n or n.endswith(".old") or n.endswith("~")
            or ".precred" in n or "superseded" in n)


def python_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP_DIRS and not _is_backup(d)]
        for fn in filenames:
            if fn.endswith(".py") and not _is_backup(fn):
                yield Path(dirpath) / fn


def _called(node):
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return ""


def build():
    defs = {}                       # "mod:func" -> (rel, line)
    by_name = defaultdict(set)      # func -> {"mod:func"}
    calls = defaultdict(set)        # "mod:func" -> {func names}
    imports = defaultdict(dict)     # mod -> {local name: source module}
    entries = set()
    deferred_roots = []   # (mod, names called at module level)
    fimports = defaultdict(dict)    # "mod:func" -> {local name: source}

    for path in python_files():
        rel = str(path.relative_to(ROOT))
        mod = _mod(path)
        try:
            src = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(src)
        except SyntaxError:
            continue

        # what this module pulls in, including inside functions, because
        # this codebase imports lazily almost everywhere
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for a in node.names:
                    # keep the original name as well as the alias. This
                    # codebase is full of "from temple.harm import sweep as
                    # _reckon", and losing the original made every aliased
                    # call unresolvable - which read as the whole world
                    # being dead.
                    imports[mod][a.asname or a.name] = (node.module, a.name)

        module_level_calls = set()
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                     ast.ClassDef)):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call):
                        module_level_calls.add(_called(sub))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = "%s:%s" % (mod, node.name)
                defs[q] = (rel, node.lineno)
                by_name[node.name].add(q)
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call):
                        calls[q].add(_called(sub))
                    # an import inside a function belongs to that function.
                    # Two functions in one file legitimately import
                    # different things under the same local name, and this
                    # codebase does it - flattening them to the module lost
                    # whichever came first.
                    elif isinstance(sub, ast.ImportFrom) and sub.module:
                        for a in sub.names:
                            fimports[q][a.asname or a.name] = (sub.module,
                                                               a.name)
                if node.decorator_list:
                    entries.add(q)          # a route, an event, a timer

        # Anything called at module level runs the moment the module is
        # loaded. That is a root regardless of whether we happened to list
        # the file as an entry point - a plain generator script has no
        # __main__ guard and is still executed on every deploy. Resolved
        # after the whole tree is walked, because doing it here would depend
        # on the order files came off the disk.
        deferred_roots.append((mod, module_level_calls))

        if rel in ENTRY_FILES or '__name__ == "__main__"' in src:
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    entries.add("%s:%s" % (mod, node.name))

    for mod, names in deferred_roots:
        for n in names:
            # a bare name means this module's own definition if it has one,
            # otherwise whatever it imported under that name
            own = "%s:%s" % (mod, n)
            if own in defs:
                entries.add(own)
                continue
            for q in resolve(own, n, by_name, imports, None):
                entries.add(q)

    return defs, by_name, calls, imports, entries, fimports


def resolve(caller_q, name, by_name, imports, fimports=None):
    """Which definition does this call mean?

    If the calling module imported the name from somewhere, that is the
    answer - resolved through the alias back to the original, since this
    codebase almost always imports as "sweep as _reckon". Otherwise every
    definition with that name is a candidate, which errs toward calling
    things live.
    """
    mod = caller_q.split(":")[0]
    # the caller's own function scope wins over its module's
    found = (fimports or {}).get(caller_q, {}).get(name) \
        or imports.get(mod, {}).get(name)
    if found:
        src, original = found
        q = "%s:%s" % (src, original)
        if q in by_name.get(original, ()):
            return {q}
        # the module may be reachable by a different path in the tree
        for cand in by_name.get(original, ()):
            if cand.split(":")[0].endswith(src.split(".")[-1]):
                return {cand}
    return by_name.get(name, set())


def walk(defs, by_name, calls, imports, entries, fimports=None):
    seen, stack = set(), [e for e in entries if e in defs]
    while stack:
        q = stack.pop()
        if q in seen:
            continue
        seen.add(q)
        for name in calls.get(q, ()):
            if not name:
                continue
            for target in resolve(q, name, by_name, imports,
                                  fimports):
                if target not in seen:
                    stack.append(target)
    return seen


def report():
    defs, by_name, calls, imports, entries, fimports = build()
    live = walk(defs, by_name, calls, imports, entries, fimports)

    dead = []
    for q, (rel, line) in sorted(defs.items()):
        func = q.split(":")[1]
        if q in live or func.startswith(SKIP_PREFIX) or func.startswith("__"):
            continue
        dead.append({"name": func, "file": rel, "line": line})

    by_file = defaultdict(list)
    for d in dead:
        by_file[d["file"]].append(d)
    return {"functions": len(defs), "reachable": len(live & set(defs)),
            "unreachable": len(dead), "dead": dead,
            "by_file": {k: v for k, v in sorted(by_file.items(),
                                                key=lambda kv: -len(kv[1]))}}


if __name__ == "__main__":
    r = report()
    (ROOT / "research").mkdir(exist_ok=True)
    (ROOT / "research" / "wiring.json").write_text(json.dumps(r, indent=1))

    print("WHAT CAN ACTUALLY BE REACHED")
    print()
    print("  functions defined : %d" % r["functions"])
    print("  reachable         : %d" % r["reachable"])
    print("  unreachable       : %d" % r["unreachable"])
    print()
    for f, items in list(r["by_file"].items())[:12]:
        print("  %s" % f)
        for d in items[:5]:
            print("     %-34s :%d" % (d["name"] + "()", d["line"]))
        if len(items) > 5:
            print("     ... and %d more" % (len(items) - 5))
    print()

    budget_file = ROOT / "research" / "wiring-budget.txt"
    budget = None
    if budget_file.exists():
        try:
            budget = int(budget_file.read_text().strip())
        except ValueError:
            pass

    if budget is None:
        budget_file.write_text(str(r["unreachable"]))
        print("  budget set at %d. It may not go up." % r["unreachable"])
        raise SystemExit(0)

    if r["unreachable"] > budget:
        print("  FAILED: %d unreachable against a budget of %d."
              % (r["unreachable"], budget))
        print("  Something was written and nothing calls it. Wire it to the")
        print("  scheduler, an HTTP route or a spark's turn - or delete it.")
        print("  Do not raise the budget to make this pass.")
        raise SystemExit(1)

    if r["unreachable"] < budget:
        budget_file.write_text(str(r["unreachable"]))
        print("  budget tightened: %d -> %d" % (budget, r["unreachable"]))
    print("  OK")
