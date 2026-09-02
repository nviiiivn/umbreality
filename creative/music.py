"""Music generation for agents. Pure Python, no external deps.
Creates WAV files using numpy arrays for audio synthesis."""

import struct, math, os, random
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs" / "music"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NOTES = {
    "C": 261.63, "C#": 277.18, "D": 293.66, "D#": 311.13,
    "E": 329.63, "F": 349.23, "F#": 369.99, "G": 392.00,
    "G#": 415.30, "A": 440.00, "A#": 466.16, "B": 493.88,
}

SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11, 12],
    "minor": [0, 2, 3, 5, 7, 8, 10, 12],
    "pentatonic": [0, 2, 4, 7, 9, 12],
    "blues": [0, 3, 5, 6, 7, 10, 12],
    "chromatic": list(range(13)),
}


def _wav_header(sample_rate, data):
    n_samples = len(data)
    block_align = 2
    byte_rate = sample_rate * block_align
    data_bytes = b"".join(struct.pack("<h", int(s * 32767 * 0.5)) for s in data)
    header = b"RIFF" + struct.pack("<I", 36 + len(data_bytes)) + b"WAVE"
    header += b"fmt " + struct.pack("<I", 16)  # chunk size
    header += struct.pack("<HHIIHH", 1, 1, sample_rate, byte_rate, block_align, 16)
    header += b"data" + struct.pack("<I", len(data_bytes))
    return header + data_bytes


def generate_tone(freq=440, duration=2.0, sample_rate=44100, wave="sine", harmonics=True):
    samples = int(sample_rate * duration)
    t = [i / sample_rate for i in range(samples)]
    
    if wave == "sine":
        signal = [math.sin(2 * math.pi * freq * ti) for ti in t]
    elif wave == "square":
        signal = [1.0 if math.sin(2 * math.pi * freq * ti) >= 0 else -1.0 for ti in t]
    elif wave == "saw":
        signal = [2.0 * (freq * ti - math.floor(freq * ti + 0.5)) for ti in t]
    elif wave == "triangle":
        signal = [2.0 * abs(2.0 * (freq * ti - math.floor(freq * ti + 0.5))) - 1.0 for ti in t]
    else:
        signal = [math.sin(2 * math.pi * freq * ti) for ti in t]
    
    if harmonics:
        for h in [2, 3, 4, 5]:
            amp = 1.0 / h
            signal = [s + amp * math.sin(2 * math.pi * freq * h * ti) for s, ti in zip(signal, t)]
    
    # Normalize and fade
    max_val = max(abs(s) for s in signal) or 1
    fade_n = int(sample_rate * 0.05)
    for i in range(fade_n):
        signal[i] *= i / fade_n
        signal[-(i+1)] *= i / fade_n
    
    return [s / max_val for s in signal]


def generate_melody(scale="minor", bpm=120, duration=8.0, sample_rate=44100):
    """Generate a simple melody using scale tones."""
    scale_tones = SCALES.get(scale, SCALES["minor"])
    beat_len = 60.0 / bpm
    total_beats = int(duration / beat_len)
    
    signal = []
    base_note = 220  # A3
    notes_list = [base_note * (2 ** (s / 12)) for s in scale_tones]
    
    for _ in range(total_beats):
        freq = random.choice(notes_list)
        note_dur = beat_len * random.choice([0.5, 1.0, 1.0, 2.0])
        tone = generate_tone(freq, note_dur, sample_rate, "sine", harmonics=True)
        signal.extend(tone)
    
    return signal[:int(sample_rate * duration)]


def generate_ambient(duration=30.0, sample_rate=44100):
    """Generate ambient drone music."""
    signal = [0.0] * int(sample_rate * duration)
    t = [i / sample_rate for i in range(len(signal))]
    
    # Multiple slow sine waves
    for freq in [55, 82.5, 110, 165, 220]:
        amp = random.uniform(0.05, 0.15)
        phase = random.uniform(0, 2 * math.pi)
        for i in range(len(signal)):
            signal[i] += amp * math.sin(2 * math.pi * freq * t[i] + phase)
    
    fade = int(sample_rate * 2)
    for i in range(fade):
        signal[i] *= i / fade
        signal[-(i+1)] *= i / fade
    
    max_val = max(abs(s) for s in signal) or 1
    return [s / max_val for s in signal]


def compose(style="ambient", duration=15.0) -> str:
    """Compose a piece of music and save to WAV. Returns path."""
    if style == "melody":
        signal = generate_melody("minor", 100, duration)
    elif style == "drone":
        signal = generate_ambient(duration)
    elif style == "chant":
        # Simple two-note chant
        signal = []
        for freq in [110, 110, 165, 110, 220, 165, 110]:
            signal.extend(generate_tone(freq, duration / 7, 44100, "sine", harmonics=True))
        signal = signal[:int(44100 * duration)]
    else:
        signal = generate_ambient(duration)
    
    data = _wav_header(44100, signal)
    path = OUTPUT_DIR / f"{style}_{random.randint(1000,9999)}.wav"
    with open(path, "wb") as f:
        f.write(data)
    return str(path)
