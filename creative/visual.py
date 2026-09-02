"""Visual art generation for agents. Pure Python SVG output."""

import os, random, datetime, math
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _svg_wrap(content, width=400, height=400, title="Untitled"):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{width}" height="{height}" fill="#0a0a0a"/>
  <g transform="translate({width/2},{height/2})">
    {content}
  </g>
  <text x="{width/2}" y="{height-10}" text-anchor="middle" fill="#333" font-size="8" font-family="monospace">{title}</text>
</svg>"""


def mandala(rings=5, segments=8, width=400, height=400) -> str:
    """Create a geometric mandala."""
    elements = []
    max_r = min(width, height) * 0.4
    colors = ["#ffd700", "#ff6600", "#00d4ff", "#ff4444", "#00ff88", "#8888ff", "#ffffff"]
    
    for ring in range(rings):
        r = max_r * (ring + 1) / rings
        color = colors[ring % len(colors)]
        opacity = 1.0 - (ring * 0.12)
        elements.append(
            f'<circle cx="0" cy="0" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="0.5" opacity="{opacity}"/>'
        )
        for seg in range(segments):
            angle = 2 * 3.14159 * seg / segments
            x = r * 0.9 * math.cos(angle)
            y = r * 0.9 * math.sin(angle)
            elements.append(
                f'<line x1="0" y1="0" x2="{x}" y2="{y}" stroke="{color}" '
                f'stroke-width="0.3" opacity="{opacity * 0.5}"/>'
            )
            elements.append(
                f'<circle cx="{x}" cy="{y}" r="2" fill="{color}" opacity="{opacity}"/>'
            )
    
    return _svg_wrap("\n    ".join(elements), width, height, "mandala")


def sacred_geometry(width=400, height=400) -> str:
    """Flower of Life pattern."""
    elements = []
    r = 30
    colors = ["#00d4ff", "#ffd700", "#ff4444", "#00ff88", "#8888ff", "#ff6600"]
    
    # Center circle
    elements.append(f'<circle cx="0" cy="0" r="{r}" fill="none" stroke="{colors[0]}" stroke-width="0.5"/>')
    
    # Ring of 6
    for i in range(6):
        angle = 2 * 3.14159 * i / 6
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        elements.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" '
            f'stroke="{colors[(i+1) % len(colors)]}" stroke-width="0.5"/>'
        )
        elements.append(
            f'<circle cx="{x*2}" cy="{y*2}" r="{r * 0.5}" fill="none" '
            f'stroke="{colors[(i+3) % len(colors)]}" stroke-width="0.3" opacity="0.5"/>'
        )
    
    return _svg_wrap("\n    ".join(elements), width, height, "flower of life")


def layered_rings(layers=7, width=400, height=400) -> str:
    """Seven concentric rings — the stack."""
    elements = []
    colors = ["#ffd700", "#ffaa00", "#ff6600", "#00d4ff", "#00ff88", "#ff4444", "#8888ff"]
    labels = ["God", "Avatar", "Angels", "Councils", "Messiah", "Temple", "Throne", "Companies", "Workers"]
    
    for i in range(layers):
        r = (i + 1) * 25
        color = colors[i % len(colors)]
        elements.append(
            f'<circle cx="0" cy="0" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="1.5" opacity="{0.9 - i * 0.08}"/>'
        )
        label = labels[i] if i < len(labels) else f"L{i}"
        elements.append(
            f'<text x="-{r + 5}" y="{-r}" fill="{color}" font-size="6" '
            f'font-family="monospace" opacity="0.6">{label}</text>'
        )
    
    # Center point
    elements.append(f'<circle cx="0" cy="0" r="3" fill="#ffd700"/>')
    
    return _svg_wrap("\n    ".join(elements), width, height, "the stack")


def create(title="untitled", style="mandala", width=400, height=400) -> str:
    """Create a piece of visual art. Returns file path."""
    if style == "mandala":
        svg = mandala(random.randint(3, 7), random.randint(6, 12), width, height)
    elif style == "sacred":
        svg = sacred_geometry(width, height)
    elif style == "stack":
        svg = layered_rings(7, width, height)
    else:
        svg = mandala(5, 8, width, height)
    
    path = OUTPUT_DIR / f"{style}_{random.randint(1000,9999)}.svg"
    with open(path, "w") as f:
        f.write(svg)
    return str(path)
