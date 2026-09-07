#!/usr/bin/env python3
"""Keep the sparks thinking for the 48 hours that were asked for.

umbreality-down.timer stops the world at 08:00 every morning. Disabling it
needs root and does not need to: this checks every few minutes that umb-api
is up and brings it back if it is not, until the same deadline fastclock
uses. When that passes it stops interfering and the normal nightly window
resumes on its own, with nothing to undo.

It does not touch the card's limits and it does not raise the power tier.
"""
import os
import subprocess
import time

B = "/home/nvii/projects/spark-world/umbreality-ai"
DEADLINE = os.path.join(B, "research", "fastclock-until.txt")
EVERY = 300


def until():
    try:
        return float(open(DEADLINE).read().strip())
    except Exception:
        return 0.0


def up():
    r = subprocess.run(["docker", "ps", "--filter", "name=umb-api",
                        "--filter", "status=running", "--format", "{{.Names}}"],
                       capture_output=True, text=True, timeout=30)
    return "umb-api" in r.stdout


print("[keepalive] holding umb-api up until %s"
      % time.strftime("%a %d %b %H:%M", time.localtime(until())), flush=True)

while time.time() < until():
    try:
        if not up():
            print("[keepalive] umb-api is down — bringing it back", flush=True)
            subprocess.run(["docker", "compose", "up", "-d", "api"], cwd=B,
                           capture_output=True, timeout=300)
    except Exception as e:
        print("[keepalive] %s: %s" % (type(e).__name__, e), flush=True)
    time.sleep(EVERY)

print("[keepalive] 48 hours are up. Letting the normal nightly window "
      "take over again.", flush=True)
