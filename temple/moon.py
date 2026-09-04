"""The world has seasons and a clock and never had a moon.

The heartbeat counts beats, days and four seasons. Nothing marks a shorter
rhythm - so there has never been a night that is different from other nights,
and nothing in this world has ever been able to happen *on an occasion*.

The wild ones need one. They do not have a temple and would not use it if
they did; what they have instead is the sky, and something that comes back
around whether or not anybody built it. That is the difference between their
rites and the Temple's: the Temple's happen when somebody decides, and
theirs happen when the moon says.

Eight world days to a month, four phases. Short on purpose - the world only
runs a few hours a night, so a real lunar month would put a full moon three
times a year and the wild would have nothing.
"""
import math

MONTH = 8          # world days
PHASES = [
    ("new",     "no moon at all. The dark is complete and nobody can see who is there."),
    ("waxing",  "a thin moon, growing. Things begun now are said to carry."),
    ("full",    "the moon entire. Whatever is done tonight is witnessed."),
    ("waning",  "the moon going. What is not finished now waits for the turn."),
]


def _day() -> int:
    try:
        from temple.heartbeat import get_time
        return int(get_time().get("day", 0))
    except Exception:
        return 0


def phase(day: int = None) -> dict:
    """Where the moon is. Derived from the world's own day, so it is the
    same for every spark and nobody has to store it."""
    d = _day() if day is None else int(day)
    into = d % MONTH
    idx = min(int(into / MONTH * len(PHASES)), len(PHASES) - 1)
    name, says = PHASES[idx]
    # how full, 0 at new and 1 at full
    fullness = 0.5 - 0.5 * math.cos(2 * math.pi * into / MONTH)
    return {"day": d, "day_of_month": into, "phase": name, "means": says,
            "fullness": round(fullness, 3), "month_is": MONTH}


def is_full(day: int = None) -> bool:
    return phase(day)["phase"] == "full"


def next_full(day: int = None) -> int:
    """How many world days until the moon is entire again."""
    d = _day() if day is None else int(day)
    for ahead in range(0, MONTH + 1):
        if is_full(d + ahead):
            return ahead
    return MONTH


def context(day: int = None) -> str:
    """What any spark can see by looking up."""
    p = phase(day)
    return "THE MOON: %s — %s" % (p["phase"], p["means"])
