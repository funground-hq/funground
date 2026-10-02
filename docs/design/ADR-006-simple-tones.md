# ADR-006: Simple tones and notes, without a synthesis engine

## Status

Accepted, 3 October 2026 (maintainer, D-055). Narrows [ADR-003](ADR-003-out-of-scope.md)'s "Sound synthesis" row. ADR-003 stays
in force for real-time synthesis.

## Context

Sprint 11 gave funground sound playback and analysis (contract A1, A2). Learners who want to *make* a tune
still need a sound file made elsewhere. ADR-003 put sound synthesis out of scope, because a synthesis engine
(oscillators, envelopes, filters and effects changing live while sound plays) is a project of its own and
needs numpy or a native audio library.

## Options

1. **Keep ADR-003 as it is:** playback only.
2. **Offline tones:** compute a sound's samples in pure Python, then play it through the existing pygame-ce mixer. This covers:
   - sound from a list of numbers;
   - tones in a few wave shapes;
   - named notes;
   - a simple fade;
   - pan;
   - saving as WAV.
3. **A real-time synth:** a new dependency (pyo, or sounddevice with numpy, or FluidSynth) and a live audio callback.

## Decision

Option 2, for release 0.1:
- `create_sound(samples, rate)`;
- tones and notes with wave shapes and a fade;
- sequencing and chords by combining sounds;
- `pan`;
- `sound.save("x.wav")`.

Everything is computed before it plays: nothing changes while a sound is playing, except volume and pan.

## Consequences

- No new dependency, and the base install is unchanged.
- Learners can compose simple tunes and chords, and the maths of waves becomes visible in the code.
- Live sound design is still out of scope: sliders that bend a playing note, filters, effects, polyphonic instruments, and sampled instruments (SoundFonts). That needs option 3, which would be a new ADR.
