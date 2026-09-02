"""Music Expression Pipeline — Any text → musical composition.
The "fart sonata" pipeline: input text is hashed, the hash seeds a deterministic
melody generator that applies music theory (scales, chords, rhythm, dynamics)."""

import hashlib, struct, math, random, json
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "music"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11, 12],
    "minor": [0, 2, 3, 5, 7, 8, 10, 12],
    "pentatonic": [0, 2, 4, 7, 9, 12],
    "blues": [0, 3, 5, 6, 7, 10, 12],
    "chromatic": list(range(13)),
}

MOOD_TEMPO = {
    "joyful": 140, "sad": 60, "angry": 160, "calm": 80,
    "mysterious": 90, "playful": 120, "majestic": 100, "chaotic": 180,
}

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _text_to_seed(text: str) -> int:
    """Convert any text to a deterministic seed."""
    return int(hashlib.sha256(text.encode()).hexdigest()[:12], 16)


def _detect_mood(text: str) -> str:
    """Analyze text for emotional tone using keyword spotting."""
    text_lower = text.lower()
    mood_scores = {
        "joyful": ["happy", "joy", "beautiful", "love", "wonder", "bright", "laugh", "smile"],
        "sad": ["sad", "lonely", "cry", "dark", "loss", "grief", "silence", "void"],
        "angry": ["angry", "rage", "fury", "hate", "war", "destroy", "break", "punch"],
        "calm": ["calm", "peace", "still", "quiet", "gentle", "soft", "flow", "rest"],
        "mysterious": ["mystery", "shadow", "secret", "unknown", "strange", "void", "deep"],
        "playful": ["play", "dance", "fart", "silly", "fun", "wiggle", "bounce"],
        "majestic": ["majestic", "glory", "throne", "god", "universe", "infinite", "sacred"],
        "chaotic": ["chaos", "random", "wild", "storm", "fracture", "shatter", "noise"],
    }
    scores = {}
    for mood, keywords in mood_scores.items():
        scores[mood] = sum(1 for kw in keywords if kw in text_lower)
    if all(s == 0 for s in scores.values()):
        return "mysterious"
    return max(scores, key=scores.get)


def _generate_melody(seed: int, scale_name: str = "minor", note_count: int = 16) -> list:
    """Generate a sequence of (pitch, duration, velocity) tuples from a seed."""
    rng = random.Random(seed)
    scale = SCALES.get(scale_name, SCALES["minor"])
    base_freq = 220  # A3
    
    melody = []
    for i in range(note_count):
        degree = rng.choice(scale[:-1])  # Don't pick the octave
        freq = base_freq * (2 ** (degree / 12))
        # Add slight variation from adjacent degrees
        if rng.random() < 0.3:
            freq *= 2 ** (rng.choice([-1, 1]) / 12)
        duration = rng.choice([0.25, 0.5, 0.5, 0.75, 1.0, 1.5, 2.0])
        velocity = rng.randint(60, 100)
        melody.append((freq, duration, velocity))
    
    return melody


def _generate_chords(seed: int, scale_name: str = "minor", chord_count: int = 4) -> list:
    """Generate chord progression from seed."""
    rng = random.Random(seed + 999)
    scale = SCALES.get(scale_name, SCALES["minor"])
    base = 110
    
    progressions = []
    for i in range(chord_count):
        root_degree = scale[i % len(scale)]
        root = base * (2 ** (root_degree / 12))
        third = root * (2 ** (rng.choice([3, 4]) / 12))  # minor or major third
        fifth = root * (2 ** (7 / 12))
        duration = rng.choice([2.0, 4.0, 4.0, 8.0])
        progressions.append(((root, third, fifth), duration))
    
    return progressions


def _render_wav(melody: list, chords: list, tempo: int, sample_rate: int = 44100) -> bytes:
    """Render melody + chords to WAV bytes."""
    beat_duration = 60.0 / tempo
    total_samples = 0
    
    # Calculate total length
    chord_idx = 0
    chord_time = 0.0
    for freq, dur, vel in melody:
        total_samples = max(total_samples, int((chord_time + dur * beat_duration) * sample_rate))
        if chord_idx < len(chords):
            chord_end = chord_time + chords[chord_idx][1]
            if chord_time + dur * beat_duration > chord_end:
                chord_idx += 1
        chord_time += dur * beat_duration
    
    # Render
    signal = [0.0] * (total_samples + sample_rate)
    t = [i / sample_rate for i in range(len(signal))]
    
    chord_idx = 0
    chord_time = 0.0
    sample_pos = 0
    
    for freq, dur, vel in melody:
        start_sample = sample_pos
        note_samples = int(dur * beat_duration * sample_rate)
        amp = vel / 127.0
        
        # Check chord changes
        if chord_idx < len(chords):
            chord_end = chord_time + chords[chord_idx][1]
            if chord_time + dur * beat_duration > chord_end:
                chord_idx += 1
        
        chord = chords[chord_idx] if chord_idx < len(chords) else chords[-1]
        
        for i in range(note_samples):
            idx = start_sample + i
            if idx >= len(signal):
                break
            ti = i / sample_rate
            
            # Melody note (sine with harmonics)
            note_val = amp * math.sin(2 * math.pi * freq * ti)
            note_val += amp * 0.5 * math.sin(2 * math.pi * freq * 2 * ti)
            note_val += amp * 0.25 * math.sin(2 * math.pi * freq * 3 * ti)
            
            # Chord (subtle pad)
            chord_val = 0
            for cf in chord[0]:
                chord_val += amp * 0.15 * math.sin(2 * math.pi * cf * ti)
            
            signal[idx] += note_val + chord_val
            
            # Fade in/out
            if i < 100:
                signal[idx] *= i / 100
            if i > note_samples - 100:
                signal[idx] *= (note_samples - i) / 100
        
        sample_pos += note_samples
        chord_time += dur * beat_duration
    
    # Normalize
    max_val = max(max(abs(s) for s in signal), 0.01)
    signal = [s / max_val * 0.7 for s in signal]
    
    # Convert to WAV
    data_bytes = b"".join(struct.pack("<h", int(s * 32767)) for s in signal)
    header = b"RIFF" + struct.pack("<I", 36 + len(data_bytes)) + b"WAVE"
    header += b"fmt " + struct.pack("<I", 16)
    header += struct.pack("<HHIIHH", 1, 1, sample_rate, sample_rate * 2, 2, 16)
    header += b"data" + struct.pack("<I", len(data_bytes))
    return header + data_bytes


def text_to_music(text: str) -> tuple:
    """Convert any text to a WAV file. Returns (path, metadata)."""
    seed = _text_to_seed(text)
    mood = _detect_mood(text)
    tempo = MOOD_TEMPO.get(mood, 100)
    scale_name = "minor" if mood in ("sad", "mysterious", "calm") else "major"
    
    # Adjust note count based on text length
    note_count = max(8, min(64, len(text) * 2))
    
    melody = _generate_melody(seed, scale_name, note_count)
    chords = _generate_chords(seed, scale_name, max(2, note_count // 4))
    
    data = _render_wav(melody, chords, tempo)
    
    name_hash = hashlib.md5(text.encode()).hexdigest()[:6]
    filename = f"expression_{mood}_{name_hash}.wav"
    path = OUTPUT_DIR / filename
    with open(path, "wb") as f:
        f.write(data)
    
    info = {
        "mood": mood,
        "tempo": tempo,
        "scale": scale_name,
        "notes": note_count,
        "chords": len(chords),
        "seed": seed,
        "duration_s": round(len(data) / 44100 / 2, 1),
    }
    return str(path), info
