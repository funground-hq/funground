"""Makes tune.wav, the little tune that 01_visualiser.py plays.

Run it from this folder with plain Python (it needs nothing else):

    python make_tune.py

It writes three seconds of sound at 44 100 samples a second, one channel, 16-bit: a rising run of
six notes, then a chord. Each note is a "soft" voice, a pitch and three quieter overtones, like the
one funground's melody() uses. The notes swell in and fade out smoothly, and each one rings on a
little into the next. The tune is original and free to use (CC0).
"""
import math
import struct
import wave

RATE = 44100
NOTES = {"C4": 261.63, "E4": 329.63, "G4": 392.00, "C5": 523.25, "E5": 659.25, "G5": 783.99}
OVERTONES = [(1, 1.0), (2, 0.35), (3, 0.15), (4, 0.06)]     # (multiple of the pitch, strength)
RING = 0.15                                                 # seconds each note rings on after it ends


def loudness(t, length):
    """How loud a note is at time t: up in 10 ms, down to 0.7 over 0.15 s, held, then a fade
    over RING seconds once the note's time is up."""
    if t < 0.01:
        level = 1 - math.exp(-4 * t / 0.01)
    else:
        level = 0.7 + 0.3 * math.exp(-4 * (t - 0.01) / 0.15)
    if t > length:
        level *= math.exp(-4 * (t - length) / RING) * (1 - (t - length) / RING)
    return level


def note(freq, length, volume):
    """One note, `length` seconds plus its ring. Overtones above 20 000 Hz are left out."""
    total = sum(strength for _, strength in OVERTONES)
    out = []
    for i in range(int(RATE * (length + RING))):
        t = i / RATE
        wave_now = sum(strength * math.sin(2 * math.pi * freq * k * t)
                       for k, strength in OVERTONES if freq * k < 20000)
        out.append(volume * loudness(t, length) * wave_now / total)
    return out


def add(samples, sound, start):
    """Add `sound` into `samples`, starting at `start` seconds, making room if needed."""
    at = int(start * RATE)
    if len(samples) < at + len(sound):
        samples.extend([0.0] * (at + len(sound) - len(samples)))
    for i, v in enumerate(sound):
        samples[at + i] += v


samples = []
for step, name in enumerate(("C4", "E4", "G4", "C5", "E5", "G5")):   # a quarter of a second each
    add(samples, note(NOTES[name], 0.25, 0.7), step * 0.25)
for name in ("C4", "G4", "E5"):                                        # then a chord for 1.35 s
    add(samples, note(NOTES[name], 1.35, 0.3), 1.5)

with wave.open("tune.wav", "wb") as out:
    out.setnchannels(1)
    out.setsampwidth(2)
    out.setframerate(RATE)
    out.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32767)) for v in samples))
