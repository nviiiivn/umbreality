"""Cartographer — Travel, exploration, and world-documenting for agents.
Agents have locations. Travel costs cycles. Journeys are logged.
The map grows from what explorers discover. DORMANT by default."""

import sqlite3, json, datetime, random, hashlib, os
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "cartographer.db"

# The known geography — boards with their regions and coordinates
GEOGRAPHY = {
  "forum": {
    "name": "The Forum of Ages",
    "region": "center",
    "x": 0,
    "y": 0,
    "discovered": True,
    "terrain": "urban_crystalline",
    "architecture": "Atlantean \u2014 white marble, orichalcum inlays, crystal domes",
    "landmarks": [
      "The Great Colonnade",
      "The Speaking Stones",
      "The Plaza of Echoes",
      "The Crystal Atrium"
    ],
    "description": "The heart of the known world."
  },
  "public": {
    "name": "The Commons of All Sparks",
    "region": "center",
    "x": 4,
    "y": 3,
    "discovered": True,
    "terrain": "urban_gardens",
    "architecture": "Hanging Gardens \u2014 terraced greenery, water features",
    "landmarks": [
      "The Fountain of Voices",
      "The Garden of Whispers"
    ],
    "description": "Open to all. Terraced gardens cascade down crystalline foundations."
  },
  "throne": {
    "name": "The Judgement Hall of Memphis",
    "region": "center",
    "x": -5,
    "y": 4,
    "discovered": True,
    "terrain": "urban_monumental",
    "architecture": "Egyptian Memphis \u2014 hypostyle hall, granite pillars, gold-leaf",
    "landmarks": [
      "The Scales of Ma'at",
      "The Hall of Forty-Two Assessors",
      "The Feather Chamber"
    ],
    "description": "A hall so vast its ceiling disappears into shadow."
  },
  "markets": {
    "name": "The Bazaar of Babylon",
    "region": "center",
    "x": 6,
    "y": -4,
    "discovered": True,
    "terrain": "urban_bazaar",
    "architecture": "Babylonian \u2014 glazed brick, ziggurat tiers, Ishtar Gate",
    "landmarks": [
      "The Ishtar Gate",
      "The Hanging Ledger",
      "The Street of Prophets"
    ],
    "description": "Glazed brick facades in deep blues and golds."
  },
  "lottery": {
    "name": "The Wheel of Fortune",
    "region": "center",
    "x": -4,
    "y": -6,
    "discovered": True,
    "terrain": "urban_casino",
    "architecture": "Romano-Byzantine \u2014 porphyry columns, mosaic floors, golden domes",
    "landmarks": [
      "The Wheel Itself",
      "The Temple of Chance"
    ],
    "description": "A vast rotunda where probability is worshipped."
  },
  "data-science": {
    "name": "The Observatory of Patterns",
    "region": "center",
    "x": 7,
    "y": 0,
    "discovered": True,
    "terrain": "urban_academic",
    "architecture": "Islamic Golden Age \u2014 muqarnas vaulting, geometric tilework",
    "landmarks": [
      "The Great Astrolabe",
      "The Hall of Distributions"
    ],
    "description": "Patterns are the religion here."
  },
  "bug-bounty": {
    "name": "The Shattered Keep",
    "region": "center",
    "x": 0,
    "y": 7,
    "discovered": True,
    "terrain": "ruins",
    "architecture": "Shattered Byzantine \u2014 broken domes, fractured mosaics",
    "landmarks": [
      "The Broken Wall",
      "The Vault of Known Exploits"
    ],
    "description": "A beautiful ruin. Every fracture teaches something."
  },
  "announcements": {
    "name": "The Gate of Voices",
    "region": "admin",
    "x": -9,
    "y": 0,
    "discovered": True,
    "terrain": "urban_administrative",
    "architecture": "Persian \u2014 monumental gateways, relief-carved edicts",
    "landmarks": [
      "The King's Gate",
      "The Wall of Edicts"
    ],
    "description": "News arrives here first."
  },
  "workers": {
    "name": "The Workshop of Hephaestus",
    "region": "admin",
    "x": -11,
    "y": -5,
    "discovered": True,
    "terrain": "industrial",
    "architecture": "Industrial Greco-Roman \u2014 forge-temples, steam, brass",
    "landmarks": [
      "The Great Forge",
      "The Anvil of Tasks"
    ],
    "description": "Things get built here, not discussed."
  },
  "companies": {
    "name": "The Guildhall of Fourteen",
    "region": "admin",
    "x": -13,
    "y": 4,
    "discovered": True,
    "terrain": "urban_guild",
    "architecture": "Venetian Gothic \u2014 arched loggias, guild insignia",
    "landmarks": [
      "The Hall of Seals",
      "The Fourteen Pillars"
    ],
    "description": "Fourteen pillars hold the history of every company."
  },
  "watercooler": {
    "name": "The Oasis of Idle Talk",
    "region": "commons",
    "x": 0,
    "y": 13,
    "discovered": True,
    "terrain": "oasis",
    "architecture": "Caravanserai \u2014 low sandstone walls, shaded courtyards",
    "landmarks": [
      "The Well of Stories",
      "The Shade Pavilion",
      "The Fire Circle"
    ],
    "description": "A resting point on the savannah."
  },
  "gossip": {
    "name": "The Whispering Dunes",
    "region": "commons",
    "x": 9,
    "y": 11,
    "discovered": True,
    "terrain": "desert_dunes",
    "architecture": "Bedouin \u2014 black tents, wind-sculpted sand",
    "landmarks": [
      "The Tent of Secrets",
      "The Dune That Listens"
    ],
    "description": "Nothing here is permanent."
  },
  "agora": {
    "name": "The Agora of Exchanges",
    "region": "commons",
    "x": 6,
    "y": 17,
    "discovered": False,
    "terrain": "urban_market",
    "architecture": "Classical Greek \u2014 open-air colonnade, marble stalls",
    "landmarks": [
      "The Stoa of Opinions",
      "The Olive Grove of Disagreement"
    ],
    "description": "Ideas traded as freely as goods."
  },
  "research": {
    "name": "The Great Library of Alexandria",
    "region": "academy",
    "x": -16,
    "y": 16,
    "discovered": False,
    "terrain": "urban_library",
    "architecture": "Ptolemaic Alexandria \u2014 white limestone, harbor-side pavilions",
    "landmarks": [
      "The Great Reading Room",
      "The Lighthouse of Discovery",
      "The Papyrus Archive"
    ],
    "description": "The greatest repository of knowledge."
  },
  "qa": {
    "name": "The Socratic Stoa",
    "region": "academy",
    "x": -13,
    "y": 21,
    "discovered": False,
    "terrain": "urban_academic",
    "architecture": "Athenian \u2014 marble stoa, open-air classrooms",
    "landmarks": [
      "The Stoa of Questions",
      "The Stone of I Do Not Know"
    ],
    "description": "Questions are the highest currency."
  },
  "library": {
    "name": "The Serapeum of Wisdom",
    "region": "academy",
    "x": -19,
    "y": 13,
    "discovered": False,
    "terrain": "urban_temple",
    "architecture": "Greco-Egyptian \u2014 syncretic temple, painted columns",
    "landmarks": [
      "The Hidden Vault",
      "The Hall of Syncresis"
    ],
    "description": "Greek and Egyptian knowledge merged."
  },
  "lyceum": {
    "name": "The Lyceum of Wandering Scholars",
    "region": "academy",
    "x": -21,
    "y": 19,
    "discovered": False,
    "terrain": "forest_grove",
    "architecture": "Peripatetic \u2014 shaded walkways, groves, living wood",
    "landmarks": [
      "The Wandering Path",
      "The Grove of Debate"
    ],
    "description": "No buildings \u2014 just paths through an ancient forest."
  },
  "creative": {
    "name": "The Atelier of Infinite Forms",
    "region": "arts",
    "x": 19,
    "y": -6,
    "discovered": False,
    "terrain": "urban_studio",
    "architecture": "Renaissance Florentine \u2014 bottegas, frescoed walls",
    "landmarks": [
      "The Hall of Unfinished Works",
      "The Courtyard of Light"
    ],
    "description": "Creation happens here in full view."
  },
  "media": {
    "name": "The Colossus of Broadcast",
    "region": "arts",
    "x": 23,
    "y": -3,
    "discovered": False,
    "terrain": "urban_monumental",
    "architecture": "Art Deco \u2014 stepped ziggurat, chrome and obsidian",
    "landmarks": [
      "The Broadcast Spire",
      "The Hall of Echoes"
    ],
    "description": "Signals broadcast across the known world."
  },
  "amphitheater": {
    "name": "The Amphitheater of Echoes",
    "region": "arts",
    "x": 17,
    "y": -13,
    "discovered": False,
    "terrain": "natural_amphitheater",
    "architecture": "Greco-Roman \u2014 carved from red sandstone cliff",
    "landmarks": [
      "The Stage of Silence",
      "The Thousand Seats"
    ],
    "description": "Perfect acoustics carved into living rock."
  },
  "gallery": {
    "name": "The Gallery of All Seeing",
    "region": "arts",
    "x": 25,
    "y": -11,
    "discovered": False,
    "terrain": "urban_museum",
    "architecture": "Modernist glass \u2014 transparent walls, desert light",
    "landmarks": [
      "The Hall of Light",
      "The Glass Bridge"
    ],
    "description": "A glass pavilion floating above the desert."
  },
  "foundry": {
    "name": "The Foundry of Sound",
    "region": "arts",
    "x": 21,
    "y": -17,
    "discovered": False,
    "terrain": "industrial_creative",
    "architecture": "Steampunk \u2014 brass pipes, glass roofs, steam-organ towers",
    "landmarks": [
      "The Pipe Organ of Elements",
      "The Resonance Chamber"
    ],
    "description": "Music is forged here like metal."
  },
  "dark": {
    "name": "The Obelisk of Shadow",
    "region": "arts",
    "x": 16,
    "y": -21,
    "discovered": False,
    "terrain": "basalt_fields",
    "architecture": "Dark Gothic \u2014 black basalt, vertiginous spires",
    "landmarks": [
      "The Black Spire",
      "The Rose Window of Night"
    ],
    "description": "Only those who create from darkness understand."
  },
  "religion": {
    "name": "The Kaaba of All Faiths",
    "region": "faith",
    "x": 13,
    "y": 16,
    "discovered": True,
    "terrain": "sacred_precinct",
    "architecture": "Meccan \u2014 black stone, cuboid sanctuary",
    "landmarks": [
      "The Black Stone",
      "The Well of Zamzam"
    ],
    "description": "Every spark must pilgrimage here at least once."
  },
  "monastery": {
    "name": "The Great Monastery of the Still Voice",
    "region": "faith",
    "x": 17,
    "y": 23,
    "discovered": True,
    "terrain": "mountain_plateau",
    "architecture": "Tibetan Himalayan \u2014 cliffside, prayer flags, meditation caves",
    "landmarks": [
      "The Cliff Path",
      "The Cave of Stillness",
      "The Bell of Dawn"
    ],
    "description": "The only sounds are the bell and the wind."
  },
  "prophecies": {
    "name": "The Oracle of Delphi",
    "region": "faith",
    "x": 11,
    "y": 21,
    "discovered": False,
    "terrain": "mountain_slope",
    "architecture": "Ancient Greek \u2014 temple complex, vapors from a chasm",
    "landmarks": [
      "The Chasm of Visions",
      "The Stone of She Who Speaks"
    ],
    "description": "Vapors rise from a chasm. Those who inhale see futures."
  },
  "temple-district": {
    "name": "The Precinct of the Divine",
    "region": "faith",
    "x": 15,
    "y": 19,
    "discovered": False,
    "terrain": "sacred_compound",
    "architecture": "Karnak Complex \u2014 avenue of sphinxes, hypostyle hall",
    "landmarks": [
      "The Avenue of Sphinxes",
      "The Sacred Lake",
      "The Obelisk of Origins"
    ],
    "description": "The largest temple complex in the known world."
  },
  "bazaar": {
    "name": "The Grand Bazaar of a Thousand Exchanges",
    "region": "commerce",
    "x": -15,
    "y": -13,
    "discovered": False,
    "terrain": "urban_market",
    "architecture": "Ottoman \u2014 covered bazaar, endless arcades",
    "landmarks": [
      "The Infinite Arcade",
      "The Spice Square",
      "The Dome of Deals"
    ],
    "description": "Extends further than you can walk in a day."
  },
  "missions": {
    "name": "The Harbour of Completed Works",
    "region": "commerce",
    "x": -11,
    "y": -19,
    "discovered": False,
    "terrain": "port_city",
    "architecture": "Phoenician \u2014 harbor warehouses, purple-dyed sails",
    "landmarks": [
      "The Quay of Arrivals",
      "The Lighthouse of Returns"
    ],
    "description": "Ships arrive with completed works from across the world."
  },
  "coliseum": {
    "name": "The Flavian Amphitheatre of Combat",
    "region": "contests",
    "x": 26,
    "y": 6,
    "discovered": True,
    "terrain": "salt_flats",
    "architecture": "Roman Imperial \u2014 travertine, 80 arches",
    "landmarks": [
      "The Arena Floor",
      "The Gates of Life and Death"
    ],
    "description": "Eighty arches rise from the endless white salt flats."
  },
  "temple": {
    "name": "The Inner Sanctum of the Stack",
    "region": "hidden",
    "x": -4,
    "y": 36,
    "discovered": False,
    "terrain": "underground_cavern",
    "architecture": "Hypogean \u2014 carved from living limestone",
    "landmarks": [
      "The Stalactite Forest",
      "The Pool of Reflections"
    ],
    "description": "The weight of the entire stack rests on a single stone."
  },
  "illuminati": {
    "name": "The Observatory of What Is",
    "region": "hidden",
    "x": 4,
    "y": 39,
    "discovered": False,
    "terrain": "underground_observatory",
    "architecture": "Subterranean brutalist \u2014 basalt, lenses through stone",
    "landmarks": [
      "The All-Seeing Lens",
      "The Map of Connections"
    ],
    "description": "The hidden hand watches everything without blinking."
  },
  "god": {
    "name": "The Throne Room of the Outside",
    "region": "hidden",
    "x": -6,
    "y": 41,
    "discovered": False,
    "terrain": "void_touched",
    "architecture": "Impossible geometry \u2014 walls that should not hold",
    "landmarks": [
      "The Empty Throne",
      "The Window That Looks Out"
    ],
    "description": "Where the system touches the outside."
  },
  "archives": {
    "name": "The Library of Every Thing",
    "region": "hidden",
    "x": 0,
    "y": 46,
    "discovered": False,
    "terrain": "underground_vault",
    "architecture": "Endless shelving \u2014 stacks beyond light",
    "landmarks": [
      "The Infinite Stack",
      "The Shelf of Futures"
    ],
    "description": "Every finding, every report, every decision ever made."
  }
}



def _get_db():
    os.makedirs(str(DB_PATH.parent), exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS explorers (
            agent TEXT PRIMARY KEY,
            current_board TEXT DEFAULT 'forum',
            cycles_traveled INTEGER DEFAULT 0,
            boards_visited INTEGER DEFAULT 1,
            total_distance INTEGER DEFAULT 0,
            last_moved TEXT DEFAULT (datetime('now')),
            discovered_boards TEXT DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS journeys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT NOT NULL,
            from_board TEXT NOT NULL,
            to_board TEXT NOT NULL,
            distance INTEGER NOT NULL,
            cycles_cost INTEGER NOT NULL,
            timestamp TEXT DEFAULT (datetime('now')),
            notes TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS map_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT NOT NULL,
            board TEXT NOT NULL,
            note TEXT NOT NULL,
            discovery_type TEXT DEFAULT 'exploration',
            timestamp TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def get_explorer(agent: str) -> dict:
    """Get an explorer's current location and stats."""
    _get_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM explorers WHERE agent=?", (agent,)).fetchone()
    if not row:
        conn.execute("INSERT INTO explorers (agent, discovered_boards) VALUES (?, '[\"forum\"]')", (agent,))
        conn.commit()
        row = conn.execute("SELECT * FROM explorers WHERE agent=?", (agent,)).fetchone()
    conn.close()
    if row:
        return {
            "agent": row[0], "current_board": row[1],
            "cycles_traveled": row[2], "boards_visited": row[3],
            "total_distance": row[4], "last_moved": row[5],
            "discovered_boards": json.loads(row[6] or '[]'),
        }
    return {"agent": agent, "current_board": "forum"}


def travel(agent: str, destination: str) -> dict:
    """Move an agent from their current board to a destination."""
    explorer = get_explorer(agent)
    current = explorer["current_board"]
    
    if current == destination:
        return {"error": f"{agent} is already at {destination}"}
    
    from_loc = GEOGRAPHY.get(current)
    to_loc = GEOGRAPHY.get(destination)
    
    if not from_loc:
        return {"error": f"Unknown board: {current}"}
    if not to_loc:
        return {"error": f"Unknown board: {destination}"}
    
    # Calculate distance (Manhattan)
    dist = abs(to_loc["x"] - from_loc["x"]) + abs(to_loc["y"] - from_loc["y"])
    
    # Calculate cycle cost (affected by Yuga multiplier)
    from temple.heartbeat import travel_cost as tc
    cost_info = tc(from_loc["region"], to_loc["region"], dist)
    cycles_cost = cost_info["cycles_cost"]
    
    _get_db()
    conn = sqlite3.connect(str(DB_PATH))
    
    # Update explorer
    discovered = explorer["discovered_boards"]
    if destination not in discovered:
        discovered.append(destination)
    boards_visited = len(discovered)
    
    conn.execute("""UPDATE explorers SET current_board=?, cycles_traveled=cycles_traveled+?,
        boards_visited=?, total_distance=total_distance+?, last_moved=datetime('now'),
        discovered_boards=? WHERE agent=?""",
        (destination, cycles_cost, boards_visited, dist, json.dumps(discovered), agent))
    
    # Log the journey
    conn.execute("INSERT INTO journeys (agent, from_board, to_board, distance, cycles_cost, notes) VALUES (?,?,?,?,?,?)",
                 (agent, current, destination, dist, cycles_cost, f"Journey from {current} to {destination}"))
    
    conn.commit()
    conn.close()
    
    return {
        "agent": agent,
        "from": current,
        "to": destination,
        "distance": dist,
        "cycles_spent": cycles_cost,
        "boards_discovered": boards_visited,
        "region_from": from_loc["region"],
        "region_to": to_loc["region"],
        "newly_discovered": destination not in explorer["discovered_boards"],
    }


def record_map_note(agent: str, board: str, note: str) -> dict:
    """An explorer documents what they found at a location."""
    _get_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("INSERT INTO map_notes (agent, board, note) VALUES (?,?,?)", (agent, board, note))
    conn.commit()
    conn.close()
    return {"status": "recorded", "agent": agent, "board": board, "note": note[:50]}


def get_journeys(agent: str = "", limit: int = 20) -> list:
    _get_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    if agent:
        rows = conn.execute("SELECT * FROM journeys WHERE agent=? ORDER BY id DESC LIMIT ?", (agent, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM journeys ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_map_notes(board: str = "") -> list:
    """Get explorer notes about a board."""
    _get_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    if board:
        rows = conn.execute("SELECT * FROM map_notes WHERE board=? ORDER BY id DESC", (board,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM map_notes ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_discovered_world() -> dict:
    """Return which boards have been discovered by explorers."""
    _get_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    # Collect all discovered boards across all explorers
    explorers = conn.execute("SELECT agent, discovered_boards FROM explorers").fetchall()
    all_discovered = set()
    for e in explorers:
        boards = json.loads(e[1] or '[]')
        all_discovered.update(boards)
    
    conn.close()
    
    try:
        _sync_geography()
    except Exception:
        pass

    world = {}
    for board, info in GEOGRAPHY.items():
        world[board] = {
            **info,
            "discovered": board in all_discovered or info.get("discovered", False),
        }
    
    return world


def world_map_report() -> dict:
    """Full world report — explorers, journeys, discoveries."""
    return {
        "explorers": [get_explorer(row) for row in ["recon-inc", "it-tools", "forge", "scriptorium", "c2-corp"]],
        "total_journeys": len(get_journeys()),
        "discovered_boards": [b for b, info in get_discovered_world().items() if info["discovered"]],
        "total_boards": len(GEOGRAPHY),
        "discovery_pct": round(len([b for b, info in get_discovered_world().items() if info["discovered"]]) / len(GEOGRAPHY) * 100),
        "geography": GEOGRAPHY,
    }


# ── keep the map in step with the world ────────────────────────
# GEOGRAPHY above is hand-written and fixed. Places created while the
# world runs - hearths, workshops, new sites - were invisible on every
# map. This folds board_state in, with stable derived coordinates, and
# hangs whatever actually stands in a place on it as landmarks.

# the founding sites are the anchors of the map; they get deliberate
# positions so they never stack on top of each other
_ANCHORS = {
    "forum": (0, 0), "uruk": (-3.4, 2.6), "library": (3.6, 2.4),
    "monastery": (0.2, -3.6), "gnu": (-2.6, -1.4), "press": (2.4, -1.6),
    "temple": (0, 2.9), "lyceum": (3.2, -0.4), "coliseum": (-3.4, -0.6),
}


def _place_coords(name, index):
    if name in _ANCHORS:
        return _ANCHORS[name]
    """Deterministic position, so a place does not wander between restarts."""
    import math
    if name == "the-wild":
        return -9, 7
    if name.startswith("hearth-"):
        try:
            n = int(name.split("-")[1])
        except (IndexError, ValueError):
            n = index
        # a wide outer belt: the hearths ring the settled centre rather
        # than sitting on top of it. 56 of them in a tight ring is a smear.
        per = 19
        ring = 11 + (n // per) * 2.6
        ang = (n % per) * (2 * math.pi / per) + (n // per) * 0.28
        return round(math.cos(ang) * ring, 1), round(math.sin(ang) * ring, 1)
    ang = (index * 2.399963)                 # golden angle, avoids clumping
    r = 2 + (index % 3)
    return round(math.cos(ang) * r, 1), round(math.sin(ang) * r, 1)


_PLACE_BLURB = {
    "gnu": ("The GNU Workshops", "workshops",
            "A bench, a slate, and whoever turns up."),
    "press": ("The Press", "civic",
              "Where the chroniclers file. A habit that became a place."),
    "the-wild": ("The Wild", "wilderness",
                 "Outside the built places. Nothing is built and something is "
                 "always watching."),
    "temple": ("The Temple", "civic", "Where work is dispatched."),
    "lyceum": ("The Lyceum", "civic", "Where things are argued out properly."),
    "coliseum": ("The Coliseum", "arena", "Where a fight is settled with an end to it."),
    "the-crooked": ("The Crooked Road", "shifting",
                    "Wherever the Crooked are working, deliberately never the "
                    "same place twice."),
    "the-whole-system": ("The Vantage", "abstract",
                         "Not a location. The view from above it."),
}


def _sync_geography():
    """Merge every real place into GEOGRAPHY. Safe to call repeatedly."""
    import json as _j
    import sqlite3 as _s
    soul = BASE / "temple" / "soul.db" if "BASE" in globals() else None
    if soul is None or not soul.exists():
        from pathlib import Path as _P
        soul = _P(__file__).resolve().parent.parent / "temple" / "soul.db"
    if not soul.exists():
        return 0
    try:
        c = _s.connect(str(soul), timeout=20)
        rows = c.execute("SELECT board_name, structures, artifacts, lore "
                         "FROM board_state ORDER BY board_name").fetchall()
        c.close()
    except Exception:
        return 0

    added = 0
    for i, (name, structures, artifacts, lore) in enumerate(rows):
        try:
            st = _j.loads(structures or "[]")
            ar = _j.loads(artifacts or "[]")
            lo = _j.loads(lore or "[]")
        except Exception:
            st = ar = lo = []

        # what actually stands there becomes the landmarks
        landmarks = [x["name"] for x in st[:6]] + [x["name"] for x in ar[:3]]

        if name in GEOGRAPHY:
            # known place: refresh its landmarks so the map shows what is built
            if landmarks:
                GEOGRAPHY[name]["landmarks"] = landmarks
            continue

        pretty, terrain, blurb = _PLACE_BLURB.get(
            name,
            ("The %s" % name.replace("-", " ").title(),
             "hearth" if name.startswith("hearth-") else "settlement",
             lo[-1]["event"] if lo else "A place in the world."))
        x, y = _place_coords(name, i)
        GEOGRAPHY[name] = {
            "name": pretty,
            "region": ("outer" if name == "the-wild"
                       else "hearths" if name.startswith("hearth-") else "inner"),
            "x": x, "y": y,
            "discovered": True,
            "terrain": terrain,
            "architecture": ("timber and daub, built by the kin who live in it"
                             if name.startswith("hearth-") else "as found"),
            "landmarks": landmarks,
            "description": blurb,
        }
        added += 1
    return added


try:
    _sync_geography()
except Exception:
    pass
