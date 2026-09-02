"""Library query tool for Sparks. Lets agents search the Alexandria repository."""

import os, json, glob
from pathlib import Path

ALEXANDRIA = Path("/home/nvii/projects/alexandria")


def search(query: str, max_results: int = 5) -> dict:
    """Search the Library of Alexandria for relevant texts."""
    query_lower = query.lower()
    results = []
    
    md_files = list(ALEXANDRIA.rglob("*.md")) + list(ALEXANDRIA.rglob("*.py"))
    
    for fpath in md_files:
        try:
            text = fpath.read_text()
            if query_lower in text.lower():
                rel_path = fpath.relative_to(ALEXANDRIA)
                lines = text.split("\n")
                # Find the matching line for context
                match_lines = []
                for i, line in enumerate(lines):
                    if query_lower in line.lower():
                        start = max(0, i - 1)
                        end = min(len(lines), i + 2)
                        snippet = "\n".join(lines[start:end])
                        match_lines.append(snippet[:200])
                
                results.append({
                    "path": str(rel_path),
                    "title": lines[0].replace("#", "").strip() if lines[0].startswith("#") else rel_path.name,
                    "matches": len(match_lines),
                    "snippet": match_lines[0] if match_lines else text[:200],
                })
        except:
            continue
    
    results.sort(key=lambda r: r["matches"], reverse=True)
    return {
        "query": query,
        "total": len(results),
        "results": results[:max_results],
    }


def get_collection() -> dict:
    """Return all sections/collections in the library."""
    sections = {}
    for d in sorted(ALEXANDRIA.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            files = list(d.rglob("*.md")) + list(d.rglob("*.py"))
            sections[d.name] = [f.relative_to(ALEXANDRIA).name for f in files]
    return sections
