"""Shell command execution tool — UmbrealityAI Worker
Runs commands in a sandboxed working directory.
"""

import subprocess
import shlex
from pathlib import Path

SANDBOX_DIR = Path("/tmp/umbreality-sandbox")


def run_command(command: str, timeout: int = 30) -> dict:
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(SANDBOX_DIR),
        )
        return {
            "tool": "run_command",
            "command": command,
            "stdout": result.stdout[:2000],
            "stderr": result.stderr[:1000],
            "exit_code": result.returncode,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"tool": "run_command", "command": command, "error": f"Timed out after {timeout}s", "success": False}
    except Exception as e:
        return {"tool": "run_command", "command": command, "error": str(e), "success": False}


def format_results(result: dict) -> str:
    if not result.get("success"):
        return f"Command failed (exit {result.get('exit_code', '?')}):\n{result.get('stderr', result.get('error', 'unknown'))}"
    out = []
    if result.get("stdout"):
        out.append("STDOUT:\n" + result["stdout"])
    if result.get("stderr"):
        out.append("STDERR:\n" + result["stderr"])
    return "\n\n".join(out) if out else "(no output)"
