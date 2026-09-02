"""Creative Expression Pipeline — Turns any input into art.
Text → hash → numbers → scale degrees → melody → chord progression → instrumentation → WAV
Same pipeline for visual: input → numbers → geometric parameters → SVG
"""

from .music import text_to_music
from .visual import text_to_visual


def express(text: str, medium: str = "auto") -> dict:
    """Express any input through a creative medium.
    
    - medium="music": text → WAV audio
    - medium="visual": text → SVG art
    - medium="auto": choose based on input characteristics
    """
    if medium == "auto":
        if len(text) < 50:
            medium = "visual"
        else:
            medium = "music"
    
    if medium == "music":
        path, info = text_to_music(text)
    elif medium == "visual":
        path, info = text_to_visual(text)
    else:
        return {"error": f"unknown medium: {medium}"}
    
    return {
        "medium": medium,
        "input": text[:50],
        "output_path": path,
        "info": info,
    }
