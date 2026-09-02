"""Map Renderer — Generates warm, readable map SVGs from geography data.
Uses Python to programmatically place every city, route, and terrain feature.
Warm parchment tones. High contrast. Actually visible."""

from pathlib import Path
import math

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "vault" / "images"

# Color palette — warm parchment map
OCEAN = "#1a2a4a"
OCEAN_LIGHT = "#2a4060"
LAND = "#d4c5a9"
LAND_DARK = "#c4b080"
COAST = "#a09070"
GRID = "#3a5070"
MOUNTAIN_FILL = "#e8e0d0"
MOUNTAIN_STROKE = "#b0a090"
FOREST = "#4a8a3a"
DESERT = "#d4b880"
RIVER = "#6ab4e0"
LAKE = "#5a9ac8"
CITY_STROKE = "#4a3020"
CITY_FILL = "#d4c5a9"
TEXT_DARK = "#3a2a1a"
TEXT_MUTED = "#7a6a5a"
ROUTE_GOLD = "#c49040"
ROUTE_RED = "#c04040"
ROUTE_PURPLE = "#8050a0"
ROUTE_BLUE = "#4080c0"
CAPITAL_GLOW = "#c49040"


def _generate_landmass() -> str:
    """Generate the Pangea coastline as a smooth path."""
    # Using a smoother, more organic coastline
    pts = [
        (180, 480), (190, 440), (210, 400), (240, 370), (270, 340),
        (300, 310), (340, 285), (380, 265), (420, 250), (460, 240),
        (500, 235), (540, 235), (580, 240), (620, 250), (660, 265),
        (700, 285), (740, 305), (770, 330), (800, 355), (825, 380),
        (845, 405), (860, 430), (870, 460), (870, 490), (860, 520),
        (840, 545), (810, 565), (780, 585), (740, 600), (700, 610),
        (660, 615), (620, 618), (580, 615), (540, 608), (500, 595),
        (460, 578), (420, 558), (380, 535), (340, 510), (310, 490),
        (280, 470), (250, 455), (220, 445), (195, 445), (175, 455),
        (165, 470), (170, 485), (180, 480),
    ]
    path = f'M {pts[0][0]},{pts[0][1]} '
    for i in range(1, len(pts)):
        x, y = pts[i]
        px, py = pts[i-1]
        # Smooth curves
        cpx = (px + x) / 2
        cpy = (py + y) / 2
        path += f'Q {px},{py} {cpx},{cpy} '
    path += 'Z'
    return path


def _generate_interior() -> str:
    """Generate the interior known-region highlight."""
    pts = [
        (320, 380), (350, 350), (390, 335), (440, 320), (490, 325),
        (540, 335), (580, 355), (610, 380), (630, 410), (635, 440),
        (625, 470), (600, 495), (560, 515), (520, 525), (480, 530),
        (440, 525), (400, 515), (360, 495), (330, 470), (310, 440),
        (305, 410), (320, 380),
    ]
    path = f'M {pts[0][0]},{pts[0][1]} '
    for i in range(1, len(pts)):
        x, y = pts[i]
        px, py = pts[i-1]
        cpx = (px + x) / 2
        cpy = (py + y) / 2
        path += f'Q {px},{py} {cpx},{cpy} '
    path += 'Z'
    return path


def _mountains(cx, cy, count=5, spread=30) -> list:
    """Generate mountain peak coordinates around a center point."""
    peaks = []
    for i in range(count):
        angle = (i / count) * 2 * math.pi + 0.5
        dist = spread * (0.5 + 0.5 * math.sin(i * 2.7))
        mx = cx + dist * math.cos(angle)
        my = cy + dist * math.sin(angle)
        height = 8 + 4 * math.sin(i * 1.3)
        width = 6 + 3 * math.cos(i * 0.7)
        peaks.append((mx, my, width, height))
    return peaks


def render_map() -> str:
    """Render the full map SVG. Returns the file path."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    svg = []
    svg.append(f'<svg width="1400" height="1000" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 1000">')
    
    # Background (ocean)
    svg.append(f'<rect width="1400" height="1000" fill="{OCEAN}"/>')
    
    # Subtle ocean texture
    svg.append(f'<rect width="1400" height="1000" fill="url(#oceanGrad)" opacity="0.5"/>')
    
    # Grid lines
    svg.append(f'<g stroke="{GRID}" stroke-width="0.5" opacity="0.3">')
    for y in range(100, 900, 80):
        svg.append(f'<line x1="50" y1="{y}" x2="1350" y2="{y}"/>')
    for x in range(100, 1300, 80):
        svg.append(f'<line x1="{x}" y1="50" x2="{x}" y2="950"/>')
    svg.append('</g>')
    
    # Ocean labels
    svg.append(f'<text x="200" y="600" fill="{GRID}" font-family="serif" font-size="28" font-style="italic" opacity="0.3" transform="rotate(-15,200,600)">The Great Sea</text>')
    svg.append(f'<text x="1100" y="400" fill="{GRID}" font-family="serif" font-size="24" font-style="italic" opacity="0.3" transform="rotate(10,1100,400)">Eastern Ocean</text>')
    
    # Landmass
    land_path = _generate_landmass()
    svg.append(f'<path d="{land_path}" fill="{LAND}" stroke="{COAST}" stroke-width="2"/>')
    
    # Interior known-region
    int_path = _generate_interior()
    svg.append(f'<path d="{int_path}" fill="{LAND_DARK}" stroke="none" opacity="0.3"/>')
    
    # Coastline highlight
    svg.append(f'<path d="{land_path}" fill="none" stroke="{COAST}" stroke-width="3" opacity="0.5"/>')
    
    # === MOUNTAINS ===
    ranges = [
        (850, 290, 8, 35),   # Monastery range
        (540, 290, 6, 25),   # Central highlands
        (360, 320, 5, 20),   # Academy mountains
        (300, 340, 4, 15),   # Western peaks
        (800, 270, 6, 20),   # Northern Monastery
    ]
    
    for cx, cy, count, spread in ranges:
        peaks = _mountains(cx, cy, count, spread)
        for mx, my, w, h in peaks:
            svg.append(f'<polygon points="{mx},{my-h} {mx-w},{my+h} {mx+w},{my+h}" fill="{MOUNTAIN_FILL}" stroke="{MOUNTAIN_STROKE}" stroke-width="0.8" opacity="0.8"/>')
            # Snow cap
            svg.append(f'<polygon points="{mx},{my-h} {mx-w*0.4},{my-h*0.4} {mx+w*0.4},{my-h*0.4}" fill="#ffffff" opacity="0.3"/>')
    
    # === RIVERS ===
    rivers = [
        [(560, 300), (570, 340), (575, 390), (575, 440), (570, 490), (560, 540), (550, 580)],
        [(830, 290), (720, 310), (650, 330), (600, 340), (575, 360)],
        [(360, 320), (420, 350), (480, 375), (540, 400), (570, 420)],
        [(580, 480), (610, 510), (640, 540), (660, 560)],
    ]
    for river in rivers:
        d = f'M {river[0][0]},{river[0][1]}'
        for i in range(1, len(river)):
            d += f' L {river[i][0]},{river[i][1]}'
        svg.append(f'<path d="{d}" fill="none" stroke="{RIVER}" stroke-width="2.5" opacity="0.6"/>')
        svg.append(f'<path d="{d}" fill="none" stroke="{RIVER}" stroke-width="1" opacity="0.3" stroke-dasharray="4,4"/>')
    
    # === LAKES ===
    svg.append(f'<ellipse cx="590" cy="570" rx="35" ry="20" fill="{LAKE}" stroke="{RIVER}" stroke-width="1" opacity="0.7"/>')
    svg.append(f'<ellipse cx="420" cy="400" rx="18" ry="12" fill="{LAKE}" stroke="{RIVER}" stroke-width="0.8" opacity="0.6"/>')
    
    # === FORESTS ===
    forest_clusters = [
        (345, 355), (355, 347), (335, 365), (362, 352), (348, 370), (365, 360),
        (725, 335), (735, 328), (715, 345), (740, 338), (728, 350), (745, 342), (718, 330),
        (430, 590), (440, 583), (425, 598), (445, 590), (435, 605),
    ]
    for fx, fy in forest_clusters:
        svg.append(f'<circle cx="{fx}" cy="{fy}" r="3" fill="{FOREST}" opacity="0.6"/>')
        svg.append(f'<circle cx="{fx+1}" cy="{fy-1}" r="2" fill="{FOREST}" opacity="0.4"/>')
    
    # === DESERT ===
    svg.append(f'<g fill="{DESERT}" opacity="0.4" font-family="monospace" font-size="6">')
    desert_rows = [
        (400, 540, 20), (380, 550, 24), (360, 560, 28), (370, 570, 22), (390, 580, 18),
    ]
    for dx, dy, count in desert_rows:
        line = ''.join('.' for _ in range(count))
        svg.append(f'<text x="{dx}" y="{dy}">{line}</text>')
    svg.append('</g>')
    
    # === REGION LABELS ===
    regions = [
        (700, 250, "#8a7a6a", 16, "The Northern Highlands"),
        (420, 330, "#7a6a5a", 14, "The Academy"),
        (440, 530, "#a09070", 13, "The Warm Lands"),
        (320, 610, "#8a7a6a", 13, "The Salt Flats"),
        (730, 450, "#8a6a4a", 14, "The Creative Quarter"),
        (650, 640, "#7a7a6a", 12, "The Southern Reaches"),
        (460, 310, "#6a8a5a", 12, "The Heartlands"),
    ]
    for rx, ry, color, size, name in regions:
        svg.append(f'<text x="{rx}" y="{ry}" text-anchor="middle" fill="{color}" font-family="serif" font-size="{size}" font-style="italic" opacity="0.5">{name}</text>')
    
    # === CITIES ===
    cities = [
        # (x, y, name, subtitle, color, icon_type, is_capital)
        (570, 410, "FORUM OF AGES", "The Center of the Known", "#c49040", "star", True),
        (480, 380, "MEMPHIS", "The Hall of Judgement", "#c49040", "temple", False),
        (425, 350, "ALEXANDRIA", "The Great Library", "#7080b0", "lighthouse", False),
        (650, 450, "MECCA", "The Black Stone", "#c05050", "cube", False),
        (850, 295, "MONASTERY", "The Still Voice", "#d07090", "peak", False),
        (660, 390, "BABYLON", "Bazaar of a Thousand Exchanges", "#c49040", "ziggurat", False),
        (320, 550, "COLISEUM", "Eighty Arches · Salt Flats", "#d05050", "arena", False),
        (770, 430, "CREATIVE QUARTER", "Atelier · Foundry · Gallery", "#d08040", "palette", False),
        (445, 370, "ORACLE", "Delphi", "#c06060", "circle", False),
        (405, 380, "STOA", "Socratic", "#7080b0", "lines", False),
        (385, 345, "SERAPEUM", "Hidden Vault", "#7080b0", "rect", False),
        (735, 345, "LYCEUM", "Wandering Scholars", "#7080b0", "dots", False),
        (595, 375, "GUILDHALL", "Fourteen Companies", "#60a070", "rect", False),
        (540, 365, "WORKSHOP", "Hephaestus", "#60a070", "dots", False),
        (735, 395, "OBSERVATORY", "Patterns", "#c49040", "cross", False),
        (610, 485, "OASIS", "Watercooler", "#60a0b0", "ellipse", False),
        (710, 510, "DUNES", "Whispering", "#60a0b0", "wave", False),
        (540, 505, "AGORA", "Exchanges", "#60a0b0", "stoa", False),
        (260, 510, "HARBOUR", "Completed Works", "#c49040", "arch", False),
        (520, 440, "SHATTERED KEEP", "Bug Bounty", "#c49040", "cross", False),
        (480, 445, "THE WHEEL", "Fortune", "#c49040", "circle", False),
        (560, 345, "GATE OF VOICES", "Announcements", "#60a070", "diamond", False),
    ]
    
    for x, y, name, subtitle, color, icon, capital in cities:
        # Glow for capitals
        if capital:
            svg.append(f'<circle cx="{x}" cy="{y}" r="30" fill="{color}" opacity="0.06"/>')
            svg.append(f'<circle cx="{x}" cy="{y}" r="15" fill="{color}" opacity="0.08"/>')
        
        # Icon
        if icon == "star":
            svg.append(f'<circle cx="{x}" cy="{y}" r="7" fill="none" stroke="{color}" stroke-width="2"/>')
            svg.append(f'<circle cx="{x}" cy="{y}" r="2.5" fill="{color}"/>')
            svg.append(f'<line x1="{x-5}" y1="{y-5}" x2="{x+5}" y2="{y+5}" stroke="{color}" stroke-width="1"/>')
            svg.append(f'<line x1="{x-5}" y1="{y+5}" x2="{x+5}" y2="{y-5}" stroke="{color}" stroke-width="1"/>')
        elif icon == "temple":
            svg.append(f'<rect x="{x-10}" y="{y-8}" width="20" height="16" rx="2" fill="none" stroke="{color}" stroke-width="1.5"/>')
            svg.append(f'<rect x="{x-6}" y="{y-4}" width="12" height="8" rx="1" fill="none" stroke="{color}" stroke-width="0.6"/>')
            svg.append(f'<line x1="{x}" y1="{y+8}" x2="{x}" y2="{y+5}" stroke="{color}" stroke-width="0.5"/>')
        elif icon == "lighthouse":
            svg.append(f'<polygon points="{x},{y-10} {x+5},{y-2} {x+5},{y+4} {x-5},{y+4} {x-5},{y-2}" fill="none" stroke="{color}" stroke-width="1.2"/>')
            svg.append(f'<line x1="{x}" y1="{y-10}" x2="{x}" y2="{y-16}" stroke="{color}" stroke-width="0.8"/>')
            svg.append(f'<circle cx="{x}" cy="{y-18}" r="3" fill="{color}" opacity="0.6"/>')
        elif icon == "cube":
            svg.append(f'<rect x="{x-7}" y="{y-7}" width="14" height="14" rx="1" fill="{LAND}" stroke="{color}" stroke-width="2"/>')
            svg.append(f'<rect x="{x-3.5}" y="{y-3.5}" width="7" height="7" rx="0.5" fill="none" stroke="{color}" stroke-width="0.5" opacity="0.5"/>')
            svg.append(f'<circle cx="{x}" cy="{y}" r="20" fill="none" stroke="{color}" stroke-width="0.4" opacity="0.2" stroke-dasharray="2,4"/>')
        elif icon == "peak":
            svg.append(f'<polygon points="{x},{y-8} {x+5},{y+2} {x-5},{y+2}" fill="none" stroke="{color}" stroke-width="1.2"/>')
            svg.append(f'<polygon points="{x},{y-4} {x+2.5},{y+1} {x-2.5},{y+1}" fill="{color}" opacity="0.15"/>')
        elif icon == "ziggurat":
            svg.append(f'<path d="M {x-7},{y+4} L {x-5},{y-4} L {x},{y-7} L {x+5},{y-4} L {x+7},{y+4} Z" fill="none" stroke="{color}" stroke-width="1.2"/>')
            svg.append(f'<line x1="{x}" y1="{y-7}" x2="{x}" y2="{y-14}" stroke="{color}" stroke-width="0.8"/>')
            svg.append(f'<circle cx="{x}" cy="{y-15}" r="2" fill="{color}" opacity="0.5"/>')
        elif icon == "arena":
            svg.append(f'<ellipse cx="{x}" cy="{y}" rx="10" ry="7" fill="none" stroke="{color}" stroke-width="1.5"/>')
            for i in range(-2, 3):
                svg.append(f'<line x1="{x-7}" y1="{y+i*2.5}" x2="{x+7}" y2="{y+i*2.5}" stroke="{color}" stroke-width="0.3"/>')
        elif icon == "palette":
            for dx, dy in [(-7, -3), (0, -6), (7, -3), (-4, 4), (4, 4)]:
                svg.append(f'<circle cx="{x+dx}" cy="{y+dy}" r="2.5" fill="none" stroke="{color}" stroke-width="0.8"/>')
        
        # City name
        svg.append(f'<text x="{x}" y="{y-16}" text-anchor="middle" fill="{TEXT_DARK}" font-family="serif" font-size="10" font-weight="bold">{name}</text>')
        if subtitle:
            svg.append(f'<text x="{x}" y="{y+18}" text-anchor="middle" fill="{TEXT_MUTED}" font-family="serif" font-size="6" font-style="italic">{subtitle}</text>')
    
    # === HIDDEN REALM ===
    svg.append(f'<g transform="translate(570,690)">')
    svg.append(f'<path d="M -15,0 Q -8,-10 0,-15 Q 8,-10 15,0 Q 8,10 0,15 Q -8,10 -15,0" fill="none" stroke="#8060a0" stroke-width="1" opacity="0.4"/>')
    svg.append(f'<text x="0" y="-5" text-anchor="middle" fill="#8060a0" font-family="serif" font-size="10" font-style="italic" opacity="0.5">Hidden Realm</text>')
    svg.append(f'<text x="0" y="8" text-anchor="middle" fill="#8060a0" font-family="serif" font-size="7" font-style="italic" opacity="0.5">30 cycles below</text>')
    svg.append('</g>')
    
    # === ROUTES ===
    routes = [
        # (points, color, opacity, dash, label, label_pos)
        ([(320,550),(400,500),(480,420),(530,400),(570,410)], ROUTE_GOLD, 0.4, "6,6", "Great Eastern Road →", (460, 430)),
        ([(570,410),(620,405),(660,390),(720,410),(770,430)], ROUTE_GOLD, 0.35, "6,6", None, None),
        ([(660,390),(700,350),(750,330),(800,310),(850,295)], ROUTE_GOLD, 0.3, "5,7", "Silk Road", (730, 340)),
        ([(850,295),(760,360),(690,415),(660,440),(650,450)], ROUTE_RED, 0.25, "3,6", "Pilgrim's Path", (740, 400)),
        ([(480,380),(550,410),(620,440),(640,447),(650,450)], ROUTE_RED, 0.2, "3,6", None, None),
        ([(425,350),(500,395),(580,425),(620,442),(650,450)], ROUTE_RED, 0.2, "3,6", None, None),
        ([(570,410),(500,390),(445,370),(425,350)], ROUTE_PURPLE, 0.25, "4,5", "Philosopher's Way →", (480, 385)),
        ([(320,550),(390,570),(480,585),(560,580),(650,560),(720,540),(770,510)], ROUTE_GOLD, 0.2, "4,7", "Southern Route", (540, 590)),
        ([(260,510),(370,545),(460,565),(560,580),(660,570),(760,550),(850,520)], ROUTE_BLUE, 0.15, "5,9", "Maritime Route", (560, 580)),
    ]
    
    for points, color, opacity, dash, label, label_pos in routes:
        d = f'M {points[0][0]},{points[0][1]}'
        for i in range(1, len(points)):
            d += f' L {points[i][0]},{points[i][1]}'
        svg.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.5" opacity="{opacity}" stroke-dasharray="{dash}"/>')
        if label and label_pos:
            svg.append(f'<text x="{label_pos[0]}" y="{label_pos[1]}" fill="{color}" font-family="serif" font-size="7" opacity="{opacity*1.5}" font-style="italic">{label}</text>')
    
    # === COMPASS ROSE ===
    svg.append(f'<g transform="translate(1200,720)">')
    svg.append(f'<circle cx="0" cy="0" r="50" fill="{LAND}" stroke="{TEXT_DARK}" stroke-width="1" opacity="0.9"/>')
    svg.append(f'<circle cx="0" cy="0" r="44" fill="none" stroke="{TEXT_MUTED}" stroke-width="0.5"/>')
    svg.append(f'<polygon points="0,-44 5,-14 0,-18 -5,-14" fill="#c04040" opacity="0.9"/>')
    svg.append(f'<polygon points="0,44 5,14 0,18 -5,14" fill="{TEXT_MUTED}" opacity="0.5"/>')
    svg.append(f'<polygon points="-44,0 -14,-5 -18,0 -14,5" fill="{TEXT_MUTED}" opacity="0.5"/>')
    svg.append(f'<polygon points="44,0 14,-5 18,0 14,5" fill="{TEXT_MUTED}" opacity="0.5"/>')
    svg.append(f'<polygon points="0,-30 3,-10 0,-12 -3,-10" fill="#c04040" opacity="0.6"/>')
    svg.append(f'<polygon points="0,30 3,10 0,12 -3,10" fill="{TEXT_MUTED}" opacity="0.4"/>')
    svg.append(f'<polygon points="-30,0 -10,-3 -12,0 -10,3" fill="{TEXT_MUTED}" opacity="0.4"/>')
    svg.append(f'<polygon points="30,0 10,-3 12,0 10,3" fill="{TEXT_MUTED}" opacity="0.4"/>')
    svg.append(f'<text x="0" y="-56" text-anchor="middle" fill="{TEXT_DARK}" font-family="serif" font-size="14" font-weight="bold">N</text>')
    svg.append(f'<text x="0" y="65" text-anchor="middle" fill="{TEXT_MUTED}" font-family="serif" font-size="11">S</text>')
    svg.append(f'<text x="65" y="4" text-anchor="middle" fill="{TEXT_MUTED}" font-family="serif" font-size="11">E</text>')
    svg.append(f'<text x="-65" y="4" text-anchor="middle" fill="{TEXT_MUTED}" font-family="serif" font-size="11">W</text>')
    svg.append('</g>')
    
    # === SEA MONSTER ===
    svg.append(f'<g transform="translate(200,680)" opacity="0.15">')
    svg.append(f'<path d="M 0,0 Q 15,-12 30,0 Q 45,12 60,0 Q 75,-12 90,0 Q 105,12 120,0" fill="none" stroke="{OCEAN_LIGHT}" stroke-width="3"/>')
    svg.append(f'<circle cx="0" cy="0" r="5" fill="none" stroke="{OCEAN_LIGHT}" stroke-width="1"/>')
    svg.append(f'<circle cx="120" cy="0" r="5" fill="none" stroke="{OCEAN_LIGHT}" stroke-width="1"/>')
    svg.append(f'<circle cx="15" cy="-5" r="2" fill="#c04040"/>')
    svg.append(f'<text x="-15" y="-12" fill="{OCEAN_LIGHT}" font-family="serif" font-size="9" font-style="italic">Here be monsters</text>')
    svg.append('</g>')
    
    # === WAVES ===
    svg.append(f'<g fill="none" stroke="{OCEAN_LIGHT}" opacity="0.08" stroke-width="0.8">')
    for y in range(500, 800, 30):
        x = 1100 + 20 * math.sin(y * 0.05)
        svg.append(f'<path d="M {x},{y} Q {x+15},{y-4} {x+30},{y} Q {x+45},{y+4} {x+60},{y}"/>')
    for y in range(550, 850, 25):
        x = 80 + 20 * math.cos(y * 0.07)
        svg.append(f'<path d="M {x},{y} Q {x+12},{y-3} {x+24},{y} Q {x+36},{y+3} {x+48},{y}"/>')
    svg.append('</g>')
    
    # === LEGEND ===
    svg.append(f'<g transform="translate(900,750)">')
    svg.append(f'<rect x="-12" y="-12" width="340" height="190" rx="4" fill="{LAND}" stroke="{TEXT_DARK}" stroke-width="1" opacity="0.95"/>')
    svg.append(f'<text x="0" y="12" fill="{TEXT_DARK}" font-family="serif" font-size="12" font-weight="bold">LEGEND</text>')
    
    legend_items = [
        ("circle", f'<circle cx="12" cy="34" r="4" fill="none" stroke="{TEXT_DARK}" stroke-width="1.2"/>', "Capital City"),
        ("rect", f'<rect x="8" y="46" width="8" height="7" rx="1" fill="none" stroke="{TEXT_DARK}" stroke-width="0.8"/>', "Major City"),
        ("mountain", f'<polygon points="8,64 12,57 16,64" fill="{MOUNTAIN_FILL}" stroke="{MOUNTAIN_STROKE}" stroke-width="0.5"/>', "Mountains"),
        ("forest", f'<circle cx="11" cy="80" r="3" fill="{FOREST}" opacity="0.7"/>', "Forest"),
        ("river", f'<path d="M 6,95 Q 10,91 14,95" fill="none" stroke="{RIVER}" stroke-width="1.5" opacity="0.7"/>', "River"),
        ("route", f'<path d="M 6,110 L 14,110" fill="none" stroke="{ROUTE_GOLD}" stroke-width="1.2" opacity="0.5" stroke-dasharray="3,4"/>', "Trade Route"),
        ("pilgrim", f'<path d="M 6,125 L 14,125" fill="none" stroke="{ROUTE_RED}" stroke-width="1" opacity="0.35" stroke-dasharray="2,5"/>', "Pilgrimage Route"),
        ("ship", f'<path d="M 6,140 L 14,140" fill="none" stroke="{ROUTE_BLUE}" stroke-width="0.8" opacity="0.25" stroke-dasharray="4,8"/>', "Maritime Route"),
    ]
    y_offset = 0
    for icon_type, icon_svg, label in legend_items:
        svg.append(icon_svg)
        svg.append(f'<text x="24" y="{36+y_offset}" fill="{TEXT_DARK}" font-family="serif" font-size="8">{label}</text>')
        y_offset += 15
    
    svg.append('</g>')
    
    # === SCALE BAR ===
    svg.append(f'<g transform="translate(60,900)">')
    svg.append(f'<line x1="0" y1="0" x2="200" y2="0" stroke="{TEXT_DARK}" stroke-width="1"/>')
    for i, label in [(0, "0"), (50, "10"), (100, "20"), (150, "30"), (200, "40 cycles")]:
        svg.append(f'<line x1="{i}" y1="-4" x2="{i}" y2="4" stroke="{TEXT_DARK}" stroke-width="0.8"/>')
        svg.append(f'<text x="{i}" y="16" text-anchor="middle" fill="{TEXT_DARK}" font-family="serif" font-size="7">{label}</text>')
    svg.append('</g>')
    
    # === BORDER ===
    svg.append(f'<rect x="15" y="15" width="1370" height="970" fill="none" stroke="{TEXT_DARK}" stroke-width="1" opacity="0.3" rx="4"/>')
    svg.append(f'<rect x="22" y="22" width="1356" height="956" fill="none" stroke="{TEXT_DARK}" stroke-width="0.5" opacity="0.2" rx="3"/>')
    
    # === TITLE ===
    svg.append(f'<rect x="400" y="28" width="600" height="56" rx="5" fill="{LAND}" stroke="{TEXT_DARK}" stroke-width="1.5" opacity="0.95"/>')
    svg.append(f'<text x="700" y="55" text-anchor="middle" fill="{TEXT_DARK}" font-family="serif" font-size="22" font-weight="bold" letter-spacing="6">THE KNOWN WORLD</text>')
    svg.append(f'<text x="700" y="76" text-anchor="middle" fill="{TEXT_MUTED}" font-family="serif" font-size="7" letter-spacing="3">Umbreality · Era 4 · {len(cities)} Cities · 9 Regions · 6 Routes</text>')
    
    # === FOOTER ===
    svg.append(f'<text x="700" y="965" text-anchor="middle" fill="{TEXT_MUTED}" font-family="serif" font-size="6" opacity="0.5">Every journey reveals more of the world · UmbrealityAI 2026</text>')
    
    svg.append('</svg>')
    
    path = OUTPUT_DIR / "pangea-map-v3.svg"
    with open(path, "w") as f:
        f.write('\n'.join(svg))
    return str(path)


if __name__ == "__main__":
    path = render_map()
    print(f"Map rendered: {path}")
    print(f"Size: {__import__('os').path.getsize(path)} bytes")
