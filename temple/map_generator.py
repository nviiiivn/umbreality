"""Map Generator — Creates SVG maps of the known world from actual exploration data.
Discovered boards show in color. Undiscovered boards are fog of war.
Built from cartographer data — the map grows as agents explore."""

import os
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "vault" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REGION_COLORS = {
    "center": "#ffd700", "commons": "#00d4ff", "admin": "#00ff88",
    "academy": "#8888ff", "arts": "#ff6600", "faith": "#ff4444",
    "commerce": "#ffd700", "contests": "#ff3355", "hidden": "#8800ff",
}

REGION_NAMES = {
    "center": "Center", "commons": "Commons", "admin": "Admin",
    "academy": "Academy", "arts": "Arts", "faith": "Faith",
    "commerce": "Commerce", "contests": "Coliseum", "hidden": "Hidden",
}


def generate_map(discovered_boards: list = None) -> str:
    """Generate an SVG map showing discovered vs undiscovered territory."""
    from temple.cartographer import GEOGRAPHY
    
    if discovered_boards is None:
        discovered_boards = []
    
    svg = []
    svg.append('<svg width="800" height="650" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 650">')
    svg.append('<rect width="800" height="650" fill="#0a0a0a"/>')
    
    # Title
    svg.append('<text x="400" y="30" text-anchor="middle" fill="#ffd700" font-family="serif" font-size="14" font-weight="bold" letter-spacing="3">THE EXPLORED WORLD</text>')
    svg.append(f'<text x="400" y="45" text-anchor="middle" fill="#555" font-family="monospace" font-size="6">{len(discovered_boards)} of {len(GEOGRAPHY)} boards discovered</text>')
    
    # Grid lines
    for i in range(-6, 7):
        x = 400 + i * 60
        svg.append(f'<line x1="{x}" y1="60" x2="{x}" y2="580" stroke="#111" stroke-width="0.5"/>')
    for i in range(-4, 5):
        y = 320 + i * 60
        svg.append(f'<line x1="40" y1="{y}" x2="760" y2="{y}" stroke="#111" stroke-width="0.5"/>')
    
    # Draw boards
    for board, info in GEOGRAPHY.items():
        x = 400 + info["x"] * 60
        y = 320 + info["y"] * 30  # Stretch Y for readability
        discovered = board in discovered_boards or info.get("discovered", False)
        region = info["region"]
        color = REGION_COLORS.get(region, "#555")
        
        if region == "hidden":
            y += 200  # Hidden realm is far below
        
        if discovered:
            opacity = "1.0"
            stroke_w = "0.8"
            label_fill = color
        else:
            opacity = "0.15"
            stroke_w = "0.3"
            label_fill = "#333"
        
        # Board marker
        svg.append(f'<circle cx="{x}" cy="{y}" r="4" fill="none" stroke="{color}" stroke-width="{stroke_w}" opacity="{opacity}"/>')
        
        # Board label
        display = board.replace("-", " ").title()
        svg.append(f'<text x="{x}" y="{y+12}" text-anchor="middle" fill="{label_fill}" font-family="monospace" font-size="5" opacity="{opacity}">{display}</text>')
        
        # Region label for first board in each region
        if board == list(GEOGRAPHY.keys())[list(GEOGRAPHY.values()).index(info) if list(GEOGRAPHY.values()).count(info) == 1 else 0]:
            pass  # Will add region labels separately
    
    # Region labels (rough positioning)
    region_positions = [
        ("center", 400, 200, "ffd700"),
        ("commons", 400, 140, "00d4ff"),
        ("admin", 280, 220, "00ff88"),
        ("academy", 250, 370, "8888ff"),
        ("arts", 160, 160, "ff6600"),
        ("faith", 580, 150, "ff4444"),
        ("commerce", 160, 400, "ffd700"),
        ("contests", 640, 400, "ff3355"),
        ("hidden", 400, 580, "8800ff"),
    ]
    
    for region, rx, ry, color in region_positions:
        discovered_count = sum(1 for b, i in GEOGRAPHY.items() if i["region"] == region and (b in discovered_boards or i.get("discovered", False)))
        total_count = sum(1 for i in GEOGRAPHY.values() if i["region"] == region)
        name = REGION_NAMES.get(region, region)
        svg.append(f'<text x="{rx}" y="{ry}" text-anchor="middle" fill="#{color}" font-family="serif" font-size="7" font-weight="bold" opacity="0.6">{name.upper()}</text>')
        svg.append(f'<text x="{rx}" y="{ry+10}" text-anchor="middle" fill="#555" font-family="monospace" font-size="4">{discovered_count}/{total_count} discovered</text>')
    
    # Legend
    svg.append('<g transform="translate(600, 560)">')
    svg.append('<text x="0" y="0" fill="#ffd700" font-family="serif" font-size="7" font-weight="bold">MAP LEGEND</text>')
    svg.append(f'<circle cx="6" cy="14" r="3" fill="none" stroke="#ffd700" stroke-width="0.8"/>')
    svg.append(f'<text x="14" y="17" fill="#888" font-family="monospace" font-size="5">Discovered</text>')
    svg.append(f'<circle cx="6" cy="26" r="3" fill="none" stroke="#333" stroke-width="0.3" opacity="0.3"/>')
    svg.append(f'<text x="14" y="29" fill="#444" font-family="monospace" font-size="5">Undiscovered</text>')
    svg.append(f'<text x="0" y="44" fill="#555" font-family="monospace" font-size="4">Send explorers to reveal</text>')
    svg.append(f'<text x="0" y="52" fill="#555" font-family="monospace" font-size="4">the fog of war</text>')
    svg.append('</g>')
    
    # Footer
    svg.append(f'<text x="400" y="635" text-anchor="middle" fill="#333" font-family="monospace" font-size="4">Map generated from explorer journeys · {len(discovered_boards)}/{len(GEOGRAPHY)} boards · UmbrealityAI</text>')
    
    svg.append('</svg>')
    
    return "\n".join(svg)


def write_map():
    """Generate and write the current exploration map."""
    from temple.cartographer import get_discovered_world
    world = get_discovered_world()
    discovered = [board for board, info in world.items() if info["discovered"]]
    
    svg = generate_map(discovered)
    path = OUTPUT_DIR / "explored-world.svg"
    with open(path, "w") as f:
        f.write(svg)
    return str(path)
