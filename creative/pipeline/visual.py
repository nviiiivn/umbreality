"""Visual Expression Pipeline — Any text → SVG art.
Text is hashed, the seed drives geometric parameters for unique visual output."""

import hashlib, random, math
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COLOR_PALETTES = {
    "warm": ["#ff3333", "#ff8800", "#ffcc00", "#ff6600", "#ffaa44"],
    "cool": ["#0044ff", "#0088ff", "#00ccff", "#4444ff", "#0066cc"],
    "nature": ["#00cc44", "#44ff88", "#88ff44", "#006633", "#33cc66"],
    "royal": ["#8800ff", "#cc44ff", "#ff88cc", "#6600aa", "#aa44ff"],
    "dark": ["#ff0088", "#ff4444", "#880044", "#cc0066", "#ff6688"],
    "gold": ["#ffd700", "#ffaa00", "#ffdd44", "#ccaa00", "#ffee88"],
    "stack": ["#ffd700", "#ff6600", "#00d4ff", "#ff4444", "#00ff88"],
}


def _text_to_seed(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest()[:12], 16)


def _get_palette(text: str) -> list:
    text_lower = text.lower()
    palette_scores = {}
    keywords = {
        "warm": ["fire", "hot", "sun", "passion", "anger", "energy"],
        "cool": ["cold", "ice", "water", "ocean", "sky", "calm", "blue"],
        "nature": ["green", "tree", "earth", "grow", "leaf", "forest", "grass"],
        "royal": ["crown", "throne", "royal", "purple", "king", "queen", "noble"],
        "dark": ["dark", "shadow", "night", "void", "deep", "black"],
        "gold": ["gold", "light", "shine", "divine", "holy", "sun", "glory"],
        "stack": ["layer", "stack", "system", "code", "reality", "structure"],
    }
    for name, kws in keywords.items():
        palette_scores[name] = sum(1 for kw in kws if kw in text_lower)
    if all(v == 0 for v in palette_scores.values()):
        return COLOR_PALETTES["stack"]
    best = max(palette_scores, key=palette_scores.get)
    return COLOR_PALETTES[best]


def _generate_mandala(seed: int, palette: list) -> str:
    """Generate a unique mandala from seed values."""
    rng = random.Random(seed)
    rings = rng.randint(3, 8)
    segments = rng.randint(6, 16)
    width, height = 500, 500
    max_r = min(width, height) * 0.42
    
    elements = []
    for ring in range(rings):
        r = max_r * (ring + 1) / rings
        color = palette[ring % len(palette)]
        opacity = max(0.2, 1.0 - (ring * 0.1))
        stroke_w = max(0.3, 2.0 - ring * 0.2)
        
        elements.append(f'<circle cx="250" cy="250" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke_w}" opacity="{opacity}"/>')
        
        for seg in range(segments):
            angle = 2 * math.pi * seg / segments
            # Vary radius by seed — creates unique patterns
            vr = r * (0.8 + rng.random() * 0.4)
            x = 250 + vr * math.cos(angle)
            y = 250 + vr * math.sin(angle)
            
            elements.append(f'<line x1="250" y1="250" x2="{x}" y2="{y}" stroke="{color}" stroke-width="0.5" opacity="{opacity * 0.4}"/>')
            
            dot_r = 1.5 + rng.random() * 3
            elements.append(f'<circle cx="{x}" cy="{y}" r="{dot_r}" fill="{color}" opacity="{opacity * 0.7}"/>')
    
    # Seed-based decorative center
    center_glow = palette[rng.randint(0, len(palette)-1)]
    elements.append(f'<circle cx="250" cy="250" r="8" fill="{center_glow}" opacity="0.8"/>')
    elements.append(f'<circle cx="250" cy="250" r="15" fill="none" stroke="{center_glow}" stroke-width="0.5" opacity="0.4"/>')
    
    svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    svg += f'<rect width="{width}" height="{height}" fill="#0a0a0a"/>\n'
    svg += '\n'.join(elements)
    svg += '\n</svg>'
    return svg


def _generate_geometry(seed: int, palette: list) -> str:
    """Generate sacred-geometry-inspired pattern from seed."""
    rng = random.Random(seed + 777)
    width, height = 500, 500
    
    elements = []
    base_r = 20 + rng.randint(10, 40)
    center_x, center_y = 250, 250
    
    # Center circle
    elements.append(f'<circle cx="{center_x}" cy="{center_y}" r="{base_r}" fill="none" stroke="{palette[0]}" stroke-width="1.5"/>')
    
    # Rings of circles (flower of life inspired)
    for ring in range(1, min(5, 2 + rng.randint(0, 3))):
        r = base_r * ring
        count = 6 * ring
        for i in range(count):
            angle = 2 * math.pi * i / count
            x = center_x + r * math.cos(angle)
            y = center_y + r * math.sin(angle)
            cr = base_r * 0.8 / ring
            color = palette[(ring + i) % len(palette)]
            elements.append(f'<circle cx="{x}" cy="{y}" r="{cr}" fill="none" stroke="{color}" stroke-width="0.8" opacity="0.7"/>')
            
            # Connecting lines
            if i > 0:
                prev_angle = 2 * math.pi * (i - 1) / count
                px = center_x + r * math.cos(prev_angle)
                py = center_y + r * math.sin(prev_angle)
                elements.append(f'<line x1="{px}" y1="{py}" x2="{x}" y2="{y}" stroke="{color}" stroke-width="0.3" opacity="0.3"/>')
    
    svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    svg += f'<rect width="{width}" height="{height}" fill="#0a0a0a"/>\n'
    svg += '\n'.join(elements)
    svg += '\n</svg>'
    return svg


def text_to_visual(text: str) -> tuple:
    """Convert any text to an SVG file. Returns (path, metadata)."""
    seed = _text_to_seed(text)
    palette = _get_palette(text)
    
    # Choose style based on text length
    rng = random.Random(seed)
    if rng.random() < 0.5:
        svg = _generate_mandala(seed, palette)
        style = "mandala"
    else:
        svg = _generate_geometry(seed, palette)
        style = "geometry"
    
    name_hash = hashlib.md5(text.encode()).hexdigest()[:6]
    filename = f"expression_{style}_{name_hash}.svg"
    path = OUTPUT_DIR / filename
    with open(path, "w") as f:
        f.write(svg)
    
    info = {
        "style": style,
        "palette": len(palette),
        "seed": seed,
    }
    return str(path), info
