
"""Fractal generation for Sparks — pure Python, no dependencies."""

import random, math
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def tree(iterations=8, angle=25, branch_length=50, filename=None):
    """Generate a fractal tree SVG."""
    svg = []
    svg.append(f'<svg width="400" height="400" xmlns="http://www.w3.org/2000/svg">')
    svg.append(f'<rect width="400" height="400" fill="#0a0a0a"/>')
    
    def branch(x, y, length, angle, depth):
        if depth == 0 or length < 2:
            return
        x2 = x + length * math.cos(math.radians(angle))
        y2 = y - length * math.sin(math.radians(angle))
        color = f"#{int(255 * depth / iterations):02x}{int(255 * (1 - depth / iterations)):02x}88"
        svg.append(f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{max(0.5, depth / 2)}" opacity="{0.3 + 0.7 * depth / iterations}"/>')
        branch(x2, y2, length * 0.7, angle - random.uniform(10, angle), depth - 1)
        branch(x2, y2, length * 0.7, angle + random.uniform(10, angle), depth - 1)
    
    branch(200, 380, branch_length, 90, iterations)
    svg.append('</svg>')
    
    content = "\n".join(svg)
    path = OUTPUT_DIR / (filename or f"fractal_tree_{random.randint(1000,9999)}.svg")
    with open(path, "w") as f:
        f.write(content)
    return str(path)

def koch_snowflake(iterations=4, filename=None):
    """Generate a Koch snowflake SVG."""
    svg = [f'<svg width="400" height="400" xmlns="http://www.w3.org/2000/svg">',
           f'<rect width="400" height="400" fill="#0a0a0a"/>']
    
    def koch(p1, p2, depth):
        if depth == 0:
            svg.append(f'<line x1="{p1[0]}" y1="{p1[1]}" x2="{p2[0]}" y2="{p2[1]}" stroke="#00d4ff" stroke-width="0.5" opacity="0.5"/>')
            return
        dx = (p2[0] - p1[0]) / 3
        dy = (p2[1] - p1[1]) / 3
        a = (p1[0] + dx, p1[1] + dy)
        c = (p1[0] + 2*dx, p1[1] + 2*dy)
        # Peak point
        px = a[0] + dx/2 - dy * math.sqrt(3)/2
        py = a[1] + dy/2 + dx * math.sqrt(3)/2
        b = (px, py)
        koch(p1, a, depth-1); koch(a, b, depth-1); koch(b, c, depth-1); koch(c, p2, depth-1)
    
    size = 300
    p1 = (50 + size/2, 50 + size * math.sqrt(3)/2)
    p2 = (50, 50 + size * math.sqrt(3)/2)
    p3 = (50 + size, 50 + size * math.sqrt(3)/2)
    koch(p1, p2, iterations); koch(p2, p3, iterations); koch(p3, p1, iterations)
    svg.append('</svg>')
    
    path = OUTPUT_DIR / (filename or f"snowflake_{random.randint(1000,9999)}.svg")
    with open(path, "w") as f:
        f.write("\n".join(svg))
    return str(path)

if __name__ == "__main__":
    print(tree())
    print(koch_snowflake())
