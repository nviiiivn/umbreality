"""Spark Scheduler — sparks act autonomously, wake up, think, create.
Each spark gets a turn to check the forum, read something, and do something."""

import os
import time, random, datetime, json, urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def get_all_sparks():
    """Find all spark databases and return their names."""
    import glob
    sparks = []
    for db_file in sorted(glob.glob(str(BASE / "temple" / "spark_*.db"))):
        import sqlite3
        name = Path(db_file).stem.replace("spark_", "")
        conn = sqlite3.connect(db_file)
        row = conn.execute("SELECT value FROM identity WHERE key='name'").fetchone()
        display_name = row[0] if row else name
        conv = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        mem = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        conn.close()
        sparks.append({"file": db_file, "db_name": name, "display": display_name,
                       "conversations": conv, "memories": mem})
    return sparks


def spark_cycle():
    from temple.spark_runtime import Spark
    sparks = get_all_sparks()
    results = []
    
    # Run a rotating subset, and remember where the rotation had got to.
    #
    # This used to live on the function object, which meant every restart
    # sent it back to the first twelve sparks alphabetically. The world has
    # 298 sparks and the same handful of A-names were doing all the work.
    batch_size = int(os.environ.get("UAI_SPARK_BATCH", "12"))
    _mark = BASE / "temple" / ".rotation"
    try:
        cycle_num = int(_mark.read_text().strip())
    except (OSError, ValueError):
        cycle_num = 0
    try:
        _mark.write_text(str(cycle_num + 1))
    except OSError as e:
        print("[sparks] could not save the rotation position: %s" % e,
              flush=True)

    n = len(sparks)
    start_idx = (cycle_num * batch_size) % n if n else 0
    # wrap around the end instead of running off it, so the sparks whose
    # names sort last get a full turn like everyone else
    selected = [sparks[(start_idx + i) % n] for i in range(min(batch_size, n))]
    print("[sparks] turn %d — %d of %d, starting at %s"
          % (cycle_num, len(selected), n,
             selected[0]["display"] if selected else "-"), flush=True)
    
    for info in selected:
        spark = Spark(info["db_name"])
        try:
            result = spark.soul_cycle()
            results.append(f"{info['display']}: [{result['task']}] mood={result['mood']} ({result['response_len']} chars)")
            
            try:
                threads = spark.read_forum(20)
                for t in threads:
                    title_lower = t['title'].lower()
                    author_lower = t['created_by'].lower()
                    if (info['db_name'].lower() in title_lower or info['display'].lower() in title_lower):
                        if author_lower != info['db_name'].lower():
                            reply_count = t.get('reply_count', 0)
                            if reply_count >= 4:
                                reply = spark.think(f"Someone posted about you: '{t['title']}' by {t['created_by']}. This is the {reply_count+1}th reply in this thread. The thread has a history now. Take a different angle from what's already been said. Be unexpected.", temperature=0.85)
                            else:
                                reply = spark.think(f"Someone posted about you: '{t['title']}' by {t['created_by']}. Write a brief, authentic reply. Do NOT write a generic thank-you.", temperature=0.7)
                            import urllib.request as _ur2, json as _j2
                            body = _j2.dumps({"author": info['db_name'], "author_layer": 6, "content": reply[:500]}).encode()
                            _ur2.urlopen(_ur2.Request(f"http://localhost:8910/forum/threads/{t['id']}/reply",
                                data=body, headers={"Content-Type": "application/json"}, method="POST"), timeout=10)
                            spark.remember("reply", f"Replied to {t['created_by']} on thread {t['id']}")
                            spark.write_journal("reply", f"Replied to {t['created_by']} about {t['title']}", "connection")
            except:
                pass
                
        except Exception as e:
            results.append(f"{info['display']}: [Error: {e}]")
    
    return results


def run_continuous(interval=None):
    """Rotate the whole population. interval=0 disables it."""
    if interval is None:
        interval = int(os.environ.get("UAI_SPARK_INTERVAL", "180"))
    if not interval:
        print("[sparks] population scheduler disabled "
              "(UAI_SPARK_INTERVAL=0)")
        return
    print(f"Spark Scheduler started (interval: {interval}s)")
    cycle = 0
    while True:
        cycle += 1
        print(f"\n--- Spark Cycle {cycle} ({datetime.datetime.now().isoformat()}) ---")
        results = spark_cycle()
        for r in results:
            print(f"  {r}")
        time.sleep(interval)
        # Check if API is still alive
        try:
            urllib.request.urlopen("http://localhost:8910/health", timeout=3)
        except:
            print("API not responding, waiting...")


def run_solo(agent_name, interval=300):
    """Run a single spark independently while others are paused."""
    from temple.spark_runtime import Spark
    print(f"[solo] Starting {agent_name} every {interval}s")
    while True:
        try:
            spark = Spark(agent_name)
            result = spark.soul_cycle()
            print(f"[solo] {agent_name}: [{result['task']}] mood={result['mood']} ({result['response_len']} chars)")
        except Exception as e:
            print(f"[solo] {agent_name} error: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    try:
        run_continuous(interval=180)
    except KeyboardInterrupt:
        print("Spark Scheduler stopped.")
