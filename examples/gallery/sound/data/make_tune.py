"""Makes tune.wav, the little tune that 01_visualiser.py plays.

Run it from this folder with plain Python (it needs nothing else):

    python make_tune.py

It writes four seconds of notes made of a few sine tones each: a rising run of notes, then a chord. The tune
is original and free to use (CC0).
"""
import math
import struct
import wave

RATE = 11025
NOTES = {"C4": 261.63, "E4": 329.63, "G4": 392.00, "C5": 523.25, "E5": 659.25, "G5": 783.99}


OVERTONES = [(1, 1.0), (2, 0.5), (3, 0.3), (4, 0.2), (6, 0.1)]     # (multiple of the pitch, strength)


def tone(freq, seconds, volume):
    """One note: a pitch and a few overtones, so it sounds less plain, fading out smoothly."""
    count = int(RATE * seconds)
    total = sum(strength for _, strength in OVERTONES)
    return [volume * (1 - i / count) ** 1.5 / total
            * sum(strength * math.sin(2 * math.pi * freq * k * i / RATE) for k, strength in OVERTONES)
            for i in range(count)]


samples = []
for name in ("C4", "E4", "G4", "C5", "E5", "G5"):          # six notes, a third of a second each
    samples += tone(NOTES[name], 1 / 3, 0.8)

chord = [0.0] * int(RATE * 2)                               # then a chord for two seconds
for name in ("C4", "G4", "E5"):
    for i, v in enumerate(tone(NOTES[name], 2, 0.3)):
        chord[i] += v
samples += chord

with wave.open("tune.wav", "wb") as out:
    out.setnchannels(1)
    out.setsampwidth(2)
    out.setframerate(RATE)
    out.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32767)) for v in samples))
