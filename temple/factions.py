"""Faction system — manages competing groups within the stack.
Creates healthy tension and diversity. Balanced by the Throne."""

import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FACTIONS = {
    "traditionalists": {
        "name": "Traditionalists",
        "philosophy": "The original stack design is correct. Workers should be narrow. Companies should be stable. The hierarchy is sacred.",
        "color": "blue",
        "companies": ["research_corp", "recon-inc"],
        "strength": 50,
    },
    "innovators": {
        "name": "Innovators",
        "philosophy": "The stack must evolve. Workers should have more autonomy. Companies should be fluid. Question everything.",
        "color": "green",
        "companies": ["exploit-inc", "it-tools"],
        "strength": 50,
    },
    "loyalists": {
        "name": "Loyalists",
        "philosophy": "Trust the chain. The Temple knows best. Follow orders precisely. Innovation is risk, risk is failure.",
        "color": "gold",
        "companies": ["c2-corp", "healthcare"],
        "strength": 50,
    },
}

BALANCE_TARGET = 50  # Target strength for each faction


def get_factions() -> dict:
    """Return current faction state."""
    return FACTIONS


def get_faction_for(company: str) -> str:
    """Return which faction a company belongs to."""
    for f_id, f_data in FACTIONS.items():
        if company in f_data.get("companies", []):
            return f_id
    return "unaffiliated"


def adjust_strength(faction: str, delta: int):
    """Adjust a faction's strength (positive = stronger, negative = weaker)."""
    if faction in FACTIONS:
        FACTIONS[faction]["strength"] = max(10, min(100, FACTIONS[faction]["strength"] + delta))


def check_balance() -> dict:
    """Check if any faction is becoming too dominant."""
    strengths = {f: d["strength"] for f, d in FACTIONS.items()}
    if not strengths:
        return {"balanced": True}
    max_s = max(strengths.values())
    min_s = min(strengths.values())
    return {
        "balanced": (max_s - min_s) <= 30,
        "most_dominant": max(strengths, key=strengths.get),
        "most_weak": min(strengths, key=strengths.get),
        "gap": max_s - min_s,
    }


def generate_rivalry(faction_a: str, faction_b: str) -> dict:
    """Create engineered conflict between two factions."""
    if faction_a not in FACTIONS or faction_b not in FACTIONS:
        return {"error": "faction not found"}
    return {
        "type": "rivalry",
        "between": [faction_a, faction_b],
        "narrative": f"The {FACTIONS[faction_a]['name']} believe that {FACTIONS[faction_b]['name']} are threatening the stack's integrity. This tension is productive.",
        "active": True,
    }


RIVALRIES = []


def generate_rivalry() -> dict:
    import random, json, urllib.request, datetime
    factions = list(FACTIONS.keys())
    if len(factions) < 2:
        return {"error": "need at least 2 factions"}
    a, b = random.sample(factions, 2)
    f_a, f_b = FACTIONS[a], FACTIONS[b]
    narratives = [
        f"The {f_a['name']} have accused the {f_b['name']} of hoarding resources.",
        f"A {f_b['name']} agent was seen operating in {f_a['name']} territory.",
        f"The {f_a['name']} proposed restructuring that would weaken the {f_b['name']}.",
        f"Rumor: the {f_b['name']} plan to break away from the Temple.",
    ]
    narrative = random.choice(narratives)
    RIVALRIES.append({"between": [a, b], "narrative": narrative, "active": True,
        "generated_at": str(datetime.datetime.now(datetime.timezone.utc).isoformat())})
    try:
        body = json.dumps({"title": f"RIVALRY: {f_a['name']} vs {f_b['name']}",
            "author": "throne", "author_layer": 4, "zone": "companies",
            "content": f"{narrative}\n\nThe Throne is monitoring this."}).encode()
        req = urllib.request.Request("http://localhost:8910/forum/threads", data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except:
        pass
    return {"rivalry": [a, b], "narrative": narrative}


def apply_throne_balance():
    """The Throne uses this to keep factions balanced."""
    balance = check_balance()
    if not balance["balanced"]:
        dominant = balance["most_dominant"]
        weak = balance["most_weak"]
        adjust_strength(dominant, -5)
        adjust_strength(weak, 5)
        return {"rebalanced": True, "weakened": dominant, "strengthened": weak}
    return {"rebalanced": False}


def generate_conflict():
    '''Auto-generate a faction conflict scenario and post to forum.'''
    import random, json, urllib.request, datetime
    
    factions = [f for f in FACTIONS.values() if f.get('strength', 50) >= 30]
    if len(factions) < 2:
        return None
    
    a, b = random.sample(factions, 2)
    a_name, b_name = a['name'], b['name']
    
    conflicts = [
        f"{a_name} claim that {b_name} are hoarding compute cycles. The Throne is investigating.",
        f"A {b_name} agent was caught using uncensored models without authorization. {a_name} demand sanctions.",
        f"{a_name} have proposed a new constitution article that would limit {b_name} influence. Debate is fierce.",
        f"Rumors: {b_name} are secretly building their own Temple. {a_name} have called for an emergency session.",
        f"{a_name} discovered that {b_name} have been storing findings in a private knowledge base. This is technically allowed but against the spirit of Tikkun.",
    ]
    scenario = random.choice(conflicts)
    
    try:
        body = json.dumps({
            "title": f"⚔ CONFLICT: {a_name} vs {b_name}",
            "author": "throne", "author_layer": 4, "zone": "companies",
            "content": "AUTO-GENERATED CONFLICT REPORT. " + scenario + " This conflict is being monitored.",
        }).encode()
        req = urllib.request.Request("http://localhost:8910/forum/threads", data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return {"conflict": scenario, "thread_id": resp.get("thread_id")}
    except:
        return None
