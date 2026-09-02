"""Analyst worker — data analysis and pattern recognition specialist."""
import os, sys, importlib.util
TOOLS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "workers", "phase1-worker", "tools")

def _import_tool(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS_DIR, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

ws_mod = _import_tool("web_search")
rc_mod = _import_tool("run_command")
from .base import BaseWorker


def _run(**kw):
    result = rc_mod.run_command(kw.get("command", ""), kw.get("timeout", 30))
    return result.get("stdout", "") or result.get("stderr", "")


def _search(**kw):
    from .researcher import _search as s
    return s(**kw)


ANALYST_TOOLS = {
    "run_command": {"desc": "Execute a shell command. Args: command (str), timeout (int)", "func": _run},
    "web_search": {"desc": "Search the web. Args: query (str), num_results (int)", "func": _search},
}

analyst = BaseWorker(
    name="Analyst",
    role_desc="data analyst specializing in pattern recognition, trend analysis, and structured insights",
    tools=ANALYST_TOOLS,
)


def run(task, context=None):
    return analyst.run(task, context)
