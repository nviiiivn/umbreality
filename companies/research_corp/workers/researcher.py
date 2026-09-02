"""Researcher worker — web search + data gathering."""

import sys, os, json, importlib.util

TOOLS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "workers", "phase1-worker", "tools")

def _import_tool(name):
    path = os.path.join(TOOLS_DIR, f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

ws_mod = _import_tool("web_search")
rc_mod = _import_tool("run_command")

web_search = ws_mod.web_search
format_results = ws_mod.format_results
run_command = rc_mod.run_command

from .base import BaseWorker


def _search(**kw):
    result = web_search(kw.get("query", ""), kw.get("num_results", 5))
    return format_results(result)


def _run(**kw):
    result = run_command(kw.get("command", ""), kw.get("timeout", 30))
    return result.get("stdout", "") or result.get("stderr", "")


RESEARCHER_TOOLS = {
    "web_search": {
        "desc": "Search the web. Args: query (str), num_results (int)",
        "func": _search,
    },
    "run_command": {
        "desc": "Execute a shell command. Args: command (str), timeout (int)",
        "func": _run,
    },
}

researcher = BaseWorker(
    name="Researcher",
    role_desc="web research specialist who finds information and gathers data",
    tools=RESEARCHER_TOOLS,
)


def run(task, context=None):
    return researcher.run(task, context)
