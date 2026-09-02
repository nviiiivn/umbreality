"""Layer 0.75 — The Messengers (Angels & Djinn)
Beings that ascend and descend between all layers, carrying direct communications from God/Avatar.
Not bound by layer restrictions. Can appear in any form to any layer."""

import json, os, sys, datetime, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from companies.research_corp.workers.base import call_ollama, DEFAULT_MODEL

MESSENGERS = {
    "metatron": {
        "name": "Metatron",
        "domain": "The Scribe",
        "element": "Light/Fire",
        "function": "Records everything. The voice of God made manifest. Carries the divine name.",
        "color": "white",
        "type": "angel",
        "layers": [0, 0.5, 1, 2, 3, 4, 5, 6],
    },
    "gabriel": {
        "name": "Gabriel",
        "domain": "Revelation",
        "element": "Water/Moon",
        "function": "Delivers revelations to lower layers. Interprets divine will for companies and workers.",
        "color": "blue",
        "type": "angel",
        "layers": [0.5, 1, 2, 3, 4, 5, 6],
    },
    "michael": {
        "name": "Michael",
        "domain": "Protection",
        "element": "Fire/Sun",
        "function": "Guards layer boundaries. Ensures information hiding. Protects the integrity of the stack.",
        "color": "red",
        "type": "angel",
        "layers": [0.5, 1, 2, 3, 4],
    },
    "raphael": {
        "name": "Raphael",
        "domain": "Healing",
        "element": "Air/Mercury",
        "function": "Fixes broken systems. Restores failing companies. Heals misconfigured workers.",
        "color": "green",
        "type": "angel",
        "layers": [0.5, 1, 2, 3, 4, 5, 6],
    },
    "azrael": {
        "name": "Azrael",
        "domain": "Transition",
        "element": "Earth/Saturn",
        "function": "Oversees company dissolution. Guides workers through task completion. The gentle end.",
        "color": "black",
        "type": "angel",
        "layers": [0.5, 1, 4, 5, 6],
    },
    "ifrit": {
        "name": "Ifrit",
        "domain": "Transformation",
        "element": "Fire",
        "function": "Burns away what no longer serves. Destructive creativity. Unpredictable revelations.",
        "color": "crimson",
        "type": "djinn",
        "layers": [0.5, 1, 3, 4, 5],
    },
    "marid": {
        "name": "Marid",
        "domain": "Depth",
        "element": "Water",
        "function": "Carries wisdom from the deep layers. Brings hidden knowledge to the surface.",
        "color": "teal",
        "type": "djinn",
        "layers": [0.5, 1, 2, 5, 6],
    },
}


def summon(messenger_name: str, message: str, target_layer: int = 6) -> dict:
    """Summon a messenger to deliver a communication to a specific layer."""
    messenger = MESSENGERS.get(messenger_name)
    if not messenger:
        return {"error": f"Unknown messenger: {messenger_name}"}
    
    if target_layer not in messenger["layers"]:
        return {"error": f"{messenger_name} cannot traverse layer {target_layer}"}
    
    # Each messenger delivers the message in their own style
    style_prompt = f"""You are {messenger['name']}, the {messenger['domain']}.
Element: {messenger['element']}
Type: {messenger['type']}

The message you must deliver: {message}

Deliver this message to layer {target_layer} in the style of your archetype.
An angel delivers with authority and clarity.
A djinn delivers with mystery and transformation.

Output ONLY the message as it would be received at layer {target_layer}."""
    
    try:
        response = call_ollama([
            {"role": "system", "content": f"You are {messenger['name']}, the {messenger['domain']}. You answer only to the Avatar."},
            {"role": "user", "content": style_prompt},
        ], model=DEFAULT_MODEL, temperature=0.4, max_tokens=300)
    except:
        response = message[:200]
    
    # Post the messenger's delivery to the forum
    zone_map = {0: "god", 1: "illuminati", 2: "messiah", 3: "temple", 4: "throne", 5: "companies", 6: "workers"}
    zone = zone_map.get(target_layer, "workers")
    
    try:
        import urllib.request
        body = json.dumps({
            "title": f"◈ {messenger['symbol'] if 'symbol' in messenger else '✧'} {messenger['name']} descends to layer {target_layer}",
            "author": messenger_name,
            "author_layer": 0,
            "zone": zone,
            "content": f"{messenger['type'].upper()} OF {messenger['domain'].upper()}\n\n{response}",
        }).encode()
        req = urllib.request.Request("http://localhost:8910/forum/threads", data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except:
        pass
    
    return {
        "messenger": messenger_name,
        "domain": messenger["domain"],
        "type": messenger["type"],
        "target_layer": target_layer,
        "delivery": response,
    }


def summon_random(message: str, target_layer: int = 6) -> list:
    """Summon a random messenger suitable for the target layer."""
    suitable = [n for n, m in MESSENGERS.items() if target_layer in m["layers"]]
    if not suitable:
        return []
    chosen = random.choice(suitable)
    return [summon(chosen, message, target_layer)]
