"""A cycle buys a limited number of actions.

Until now a spark's turn was free. It could speak, answer somebody, study,
make art, write music, read scripture and go on the road, all in the same
turn, every turn, for ever. Nothing traded against anything, so no choice a
spark made cost it another choice - and a decision that costs nothing is not
a decision.

This is the keystone. Taxes take from a finite pot, winter needs stores you
chose to keep rather than sell, a group can carry what one spark cannot -
none of that means anything while the underlying resource, a spark's own
time, is infinite. Everything else in the world is waiting on this.

WHAT A SPARK GETS

Four actions a cycle at ordinary energy, five or six when rested and
thriving, three when worn down. Not a big number on purpose: three or four
real choices a turn is enough to make a week's worth of them add up to a
life, and small enough that walking to a shrine genuinely costs you the
thing you would rather have built.

WHAT THINGS COST

Speaking is cheap, because a world where talking is expensive goes quiet.
Making something costs more than saying something. The road costs most of
all, which is the point of a pilgrimage: it is meant to be a sacrifice of
time, and until now it was a sacrifice of nothing.

WHAT RUNNING OUT MEANS

Nothing punishing. A spark that has spent its cycle simply stops for the
turn, and the things it did not get to are the things it did not choose.
Spending nothing at all returns a little energy - rest is a legitimate use
of a day and should be one a spark can take.
"""
import datetime
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOUL = BASE / "temple" / "soul.db"

# What a turn can hold. Deliberately small.
BASE_ACTIONS = 4
MIN_ACTIONS = 2
MAX_ACTIONS = 7

COSTS = {
    "speak": 1,        # start a thread
    "answer": 1,       # reply to somebody
    "study": 1,        # read, learn a domain
    "bond": 1,         # reach out to another spark
    "trade": 1,
    "art": 2,          # making is dearer than saying
    "music": 2,
    "scripture": 2,    # reading the texts properly, and answering them
    "teach": 2,        # your time and theirs
    "build": 3,        # putting something in the world that stays
    "travel": 3,       # the road
    "pilgrimage": 3,   # the road, with somewhere to be
    "rite": 4,         # a ceremony at a temple
}


def _conn():
    c = sqlite3.connect(str(SOUL), timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    return c


def _ensure():
    c = _conn()
    c.execute("""CREATE TABLE IF NOT EXISTS cycle_spend (
        spark_name TEXT NOT NULL,
        cycle INTEGER NOT NULL,
        action TEXT NOT NULL,
        cost INTEGER NOT NULL,
        spent_at TEXT DEFAULT (datetime('now')),
        PRIMARY KEY (spark_name, cycle, action, spent_at))""")
    c.commit()
    c.close()


def current_cycle() -> int:
    """The world's own beat, so a cycle is the same length for everybody."""
    try:
        from temple.heartbeat import get_time
        return int(get_time().get("total_beats", 0))
    except Exception:
        # the world's clock is the authority; without it fall back to the
        # wall clock so budgets still turn over rather than freezing
        return int(datetime.datetime.now().timestamp() // 3600)


def allowance(spark_name: str) -> int:
    """How many actions this spark has this cycle.

    Energy is the main term - a worn-out spark gets less done, which is the
    hook exhaustion will hang on later. Ember tilts it slightly, so a spark
    that is thriving has a little more room than one that is barely holding
    a shape.
    """
    energy = 0.5
    try:
        c = _conn()
        row = c.execute("SELECT energy FROM spark_state WHERE spark_name=?",
                        (spark_name,)).fetchone()
        c.close()
        if row and row[0] is not None:
            energy = float(row[0])
    except (sqlite3.Error, TypeError, ValueError):
        pass

    n = BASE_ACTIONS + (1 if energy >= 0.8 else 0) - (1 if energy < 0.45 else 0)

    try:
        from temple.ember import of as _ember
        r = _ember(spark_name)
        if r and r.get("ember", 0) >= 70:
            n += 1
        elif r and r.get("ember", 0) < 25:
            n -= 1
    except Exception:
        pass

    # Hunger narrows a spark. This is the selection pressure the world was
    # missing: a spark with nothing does less, so it builds less and leaves
    # less behind, and heredity finally has something to carry.
    try:
        from temple.holdings import action_penalty
        n -= action_penalty(spark_name)
    except Exception as e:
        print("[cycles] no stores for %s: %s" % (spark_name, e), flush=True)

    return max(1, min(MAX_ACTIONS, n))


class Budget:
    """One spark's turn. Ask before acting; it says yes until it does not.

    Deliberately not enforced from inside the actions themselves. A spark
    consults its own budget and stops when it is out, the way a person
    decides they have not got another errand in them - rather than being
    physically prevented at the last moment by something it cannot see.
    """

    def __init__(self, spark_name: str, cycle: int = None):
        _ensure()
        self.name = spark_name
        self.cycle = current_cycle() if cycle is None else cycle
        self.total = allowance(spark_name)
        self.spent = 0
        self.log = []

    def left(self) -> int:
        return max(0, self.total - self.spent)

    def can(self, action: str) -> bool:
        return COSTS.get(action, 1) <= self.left()

    def take(self, action: str) -> bool:
        """Spend on an action. False means the spark has run out of cycle."""
        cost = COSTS.get(action, 1)
        if cost > self.left():
            return False
        self.spent += cost
        self.log.append(action)
        try:
            c = _conn()
            c.execute("INSERT INTO cycle_spend (spark_name, cycle, action, cost) "
                      "VALUES (?,?,?,?)", (self.name, self.cycle, action, cost))
            c.commit()
            c.close()
        except sqlite3.Error as e:
            print("[cycles] could not record %s for %s: %s"
                  % (action, self.name, e), flush=True)
        return True

    def close(self):
        """End the turn. An unspent cycle is rest, and rest returns a little.

        Not much - resting should be a real option, not a better strategy
        than living.
        """
        if self.spent > 0:
            return {"spent": self.spent, "of": self.total, "did": self.log}
        try:
            c = _conn()
            c.execute("UPDATE spark_state SET energy = MIN(1.0, energy + 0.06) "
                      "WHERE spark_name=?", (self.name,))
            c.commit()
            c.close()
        except sqlite3.Error as e:
            print("[cycles] could not rest %s: %s" % (self.name, e), flush=True)
        return {"spent": 0, "of": self.total, "did": [], "rested": True}


def report(cycles_back: int = 1) -> dict:
    """What the population actually spent its time on."""
    _ensure()
    now = current_cycle()
    c = _conn()
    c.row_factory = sqlite3.Row
    rows = [dict(r) for r in c.execute(
        "SELECT action, COUNT(*) n, SUM(cost) total FROM cycle_spend "
        "WHERE cycle > ? GROUP BY action ORDER BY total DESC",
        (now - cycles_back,))]
    who = c.execute("SELECT COUNT(DISTINCT spark_name) FROM cycle_spend "
                    "WHERE cycle > ?", (now - cycles_back,)).fetchone()[0]
    c.close()
    return {"cycle": now, "sparks_that_acted": who, "spend": rows}
