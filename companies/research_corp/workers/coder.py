"""Coder worker — code generation, review, and debugging specialist."""
import os, sys, importlib.util
TOOLS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "workers", "phase1-worker", "tools")

def _import_tool(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS_DIR, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

rc_mod = _import_tool("run_command")
from .base import BaseWorker


def _run(**kw):
    result = rc_mod.run_command(kw.get("command", ""), kw.get("timeout", 30))
    return result.get("stdout", "") or result.get("stderr", "")


def _read_file(**kw):
    path = kw.get("path", "")
    try:
        with open(os.path.expanduser(path)) as f:
            content = f.read()
        return f"--- {path} ({len(content)} bytes) ---\n{content[:2000]}"
    except Exception as e:
        return f"Error reading {path}: {e}"


CODER_TOOLS = {
    "run_command": {"desc": "Execute a shell command. Args: command (str), timeout (int)", "func": _run},
    "read_file": {"desc": "Read a file from disk. Args: path (str)", "func": _read_file},
}

coder = BaseWorker(
    name="Coder",
    role_desc="senior software engineer specializing in code generation, review, and debugging",
    tools=CODER_TOOLS,
)


def run(task, context=None):
    return coder.run(task, context)
