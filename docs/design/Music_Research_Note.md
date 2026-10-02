# Research note: music in funground — making, playing and listening

**Status:** research and options only, written 3 October 2026 from a conversation with the maintainer. Nothing in this
note is decided **except** what is marked *Decided*. Licences, sizes and capabilities of outside libraries are from
general knowledge and **must be checked** before any decision relies on them (marked *verify*).

**Related:**
- Contract rows A1 and A2 (sound playback and analysis).
- [ADR-003](ADR-003-out-of-scope.md), out of scope: sound synthesis.
- [ADR-006](ADR-006-simple-tones.md), simple tones and notes.
- D-046 (sound API) and D-055 (tones, notes and pan in 0.1).
- Sprint 13 (S-108 microphone, S-110 tones and notes).
- `spikes/` has no music spike yet.

## 1. Where we are

| Area | State |
|---|---|
| Playing sound files | *Built* (Sprint 11, A1): `f.load_sound` (WAV/OGG/MP3); `play`, `loop`, `pause`, `stop`, `set_volume`, `get_volume`, `is_playing`, `duration`, `current_time`. Several sounds play at once (pygame-ce's mixer mixes them). Silent but time-keeping when there is no audio device |
| Analysing sound | *Built* (A2): `level()` (loudness, RMS) and `spectrum(bands)` (a pure-Python FFT), for visualisers |
| Microphone | *Planned* (Sprint 13, S-108). Explored 2 Oct: `pygame._sdl2.audio.AudioDevice(iscapture=True)` captured 44 100 samples/s on Windows with no new dependency. pygame-ce marks that module experimental. macOS asks for permission. CI has no input device |
| Making sound | *Decided for 0.1* (D-055, ADR-006): `f.create_sound(samples, rate)`; tones in sine, square, saw and triangle; named notes; a simple fade; sequences and chords by combining sounds; `pan`; `sound.save("x.wav")`. Computed before playing, pure Python |
| MP4 with sound | Not planned: GIF/MP4 export (M1) is silent |

## 2. Two directions, one set of numbers

```text
 synthesis:   notes ──► numbers (samples) ──► sound          (what S-110 starts)
 analysis:    sound ──► numbers (spectrum) ──► notes, tempo   (what A2 starts)
```

Both work on the same thing: a list of numbers, one per instant of sound. That is the teaching opportunity.
A learner can make a C4 in code, analyse it, and see the peak at 261.6 Hz. Making and then measuring closes
the loop between music, maths and physics.

## 3. Making sound

### 3.1 What a "real synth" is

A synthesiser computes sound **live**, a few milliseconds at a time, while it plays. The audio device asks for the
next block about every 5–10 ms; a late answer is a click. Its building blocks:

| Block | Role | Heard as |
|---|---|---|
| Oscillator | The raw wave | Sine (pure, flute-like), square (hollow, retro game), saw (bright, brassy), triangle (soft), noise (drums, wind) |
| Envelope (ADSR) | Loudness over time: attack, decay, sustain, release | Why a piano "plinks" and a violin "swells" |
| Filter | Removes highs or lows | Darker or brighter; a sweep gives "wah" |
| LFO, modulation | A slow wave moving another setting | Vibrato, tremolo, filter sweeps |
| Effects | Reverb, delay, distortion, chorus | Room, echo, grit |
| Polyphony | Many notes at once, each with its own voice | Chords on an instrument |

### 3.2 The 0.1 plan compared with a real synth

| | funground 0.1 (offline, decided) | Real synth (live, not decided) |
|---|---|---|
| How | Compute the whole sound, then play it | Compute continuously while playing |
| Changes while playing | Volume and pan only | Everything (pitch, filter, timbre), following sliders or the mouse |
| Blocks | 4 waves, a fade, notes, chords, sequences | Oscillators, ADSR, filters, LFOs, effects, polyphony |
| Quality | Clean sine; square and saw slightly harsh (no anti-aliasing) | Band-limited oscillators, smooth envelopes |
| Speed | Pure Python, a moment to compute a few seconds | Native engine, real time |
| Dependencies | None | A native library (§3.3) |
| Metaphor | A music box | An instrument |

### 3.3 Routes to a real synth (all *verify*)

| Route | What it is | Licence | Install | Fit |
|---|---|---|---|---|
| pyo | A complete DSP engine in C, scripted from Python | LGPL-3 | Wheels have historically lagged new Pythons | The nearest to p5.sound; its release cadence is a risk |
| sounddevice + numpy | A live audio callback (PortAudio) and arrays; we write the engine | MIT / BSD | Easy wheels | Most control; we maintain a synth |
| pygame-ce `_sdl2.audio` output callback | Live output with no new dependency | — | Installed already | A few simple voices; Python speed limits polyphony and effects; experimental API |
| FluidSynth (pyfluidsynth) | Plays SoundFonts, i.e. recorded instruments (§3.5) | LGPL-2.1 | Native library, fiddly on Windows | Best for realistic instruments |
| SuperCollider (supriya, FoxDot) | A professional audio server | GPL | Separate install | Powerful, heavy for learners |
| Csound (ctcsound) | A classic synthesis language | LGPL | Separate install | Very capable, steep |

Any of these would be an L-sized project, and a new ADR because it changes ADR-003/006. It would be an
**optional extra**, never in the base install.

### 3.4 Notations: simpler ways to write music

| Notation | Looks like | Notes |
|---|---|---|
| Note names | `"C4 E4 G4 C5"` | What S-110's notes will accept |
| A melody string (idea) | `f.melody("C4 E4 G4/2 C5")` | Small and pure Python. Durations need a tiny syntax |
| ABC notation | `C D E F \| G2 G2 \|` | Plain-text folk notation; parsers exist (*verify*) |
| MIDI | Note on/off events in a file | The universal exchange format; `mido` (MIT, *verify*) reads and writes it |
| TidalCycles / Strudel mini-notation | `"bd sn [hh hh] sn"` | Rhythm patterns in one string; popular for live coding (Haskell / JavaScript) |
| Sonic Pi | `play 60; sleep 0.5` | Designed for teaching children; Ruby-like, a separate app |
| Csound orchestra + score | Instruments in one file, notes in another | The original "orchestra" model |
| LilyPond | `\relative c' { c4 e g c }` | Engraving sheet music; `abjad` drives it from Python |

### 3.5 Instruments

1. **Synthesised.**
   - **Additive:** harmonics added together, as the tune generator for the sound gallery example does.
   - **FM:** gives bells and electric pianos.
   - **Physical models:** **Karplus–Strong**, a few lines of code, makes a convincing plucked string.

   They are small, teachable and pure Python, but they sound "synthy". Our four waves already differ in character: a
   sine is flute-like, a square is a retro game, a saw is buzzy brass.
2. **Sampled (SoundFont `.sf2`).**
   - These are recordings of real instruments.
   - A General MIDI SoundFont has 128 standard instruments (piano, strings, brass, drums).
   - The files are 6–150 MB, each with its own licence (*verify*), and need a player such as FluidSynth.
   - Realistic, but heavy.

### 3.6 Orchestra-style libraries for Python (*verify*)

| Library | What | Note |
|---|---|---|
| SCAMP | Compose for an ensemble of instruments in Python; plays through SoundFonts; exports notation | The closest to "an orchestra in Python" |
| music21 (BSD) | Notation and theory: scales, chords, parts, MusicXML/MIDI | For analysing and writing scores more than performing |
| pretty_midi, mido | Build multi-track MIDI | Play with any synth, or open in MuseScore or GarageBand |
| FoxDot | Live coding on SuperCollider (`p1 >> pluck([0, 2, 4])`) | Performance-oriented |
| Csound (ctcsound) | A literal orchestra and score | The most powerful and the steepest |

## 4. Listening: analysing music

### 4.1 Tasks, easiest first

| Task | Tells you | Method | Pure Python in funground? |
|---|---|---|---|
| Loudness | How loud now | RMS | Built (`level`) |
| Spectrum | Which frequencies | FFT | Built (`spectrum`) |
| Pitch of one voice | "A4, 440 Hz, 8 cents sharp" | Autocorrelation / YIN | Yes, S. Whistling, singing, one instrument |
| Note ↔ frequency | 440 Hz ↔ "A4" | A formula, 12 steps per octave | Yes, trivial; S-110 needs it |
| Onsets | When notes or beats start | Spectral flux | Yes, M. Clear on drums and plucks, weaker on smooth strings |
| Tempo, beats | "About 120 BPM, beats here" | The period of the onsets | M. Good on steady music, rough on rubato |
| Key | "Probably G major" | Chroma (energy per pitch class) against key profiles | M. Works on whole pieces |
| Chords | "C – Am – F – G" | Chroma over time against chord templates | M–L. Clear guitar or piano yes, busy mixes poorly |
| Full transcription | Every note of every instrument | Machine-learning models | No. Needs an ML runtime |

**The hard line is polyphony.** One note at a time is a small, solved problem. Separating a chord, or a band, into
notes is hard; good results come from neural networks.

### 4.2 Analysis libraries (all *verify*)

| Library | Good at | Licence | Weight |
|---|---|---|---|
| librosa | Pitch (pYIN), onsets, tempo, beats, chroma, key | ISC | numpy, scipy, numba, soundfile |
| aubio | Real-time pitch, onsets, tempo | GPL-3 | Native, small |
| madmom | Beat and tempo tracking | BSD code; its models are non-commercial | Medium |
| essentia | A large toolbox: key, chords, tempo, mood | AGPL | Heavy |
| basic-pitch (Spotify) | Polyphonic audio → MIDI | Apache-2.0 | ML runtime |
| CREPE | Accurate single-voice pitch | MIT | ML runtime |
| music21 | Theory once notes are known | BSD | Pure Python |

A powerful pipeline: **basic-pitch → MIDI → music21** turns a recording into notes, key, chords and sheet music.
Licence notes for a permissive (LGPL) package:
- GPL and AGPL libraries could only ever be optional, user-installed extras;
- madmom's model licence would block some uses.

## 5. Teaching scenarios

Each is a gallery example or a guide exercise once its pieces exist:

| Scenario | Needs |
|---|---|
| Draw a wave, hear it: plot `create_sound` samples, then play them | S-110 |
| Compose a tune or chords and save the WAV | S-110 (+ melody string) |
| Make a note, analyse it, find its peak | S-110 + `spectrum` |
| A tuner: note name plus a sharp/flat needle | Microphone (S-108) + pitch |
| Ear training: the sketch plays a note, the learner sings it back, the sketch scores it | S-110 + microphone + pitch |
| See a chord: C-E-G peaks, labelled "C major" | `spectrum`, then chroma and chords |
| Tap along: a beat light on a song | Onsets + tempo |
| Piano roll from a recording | Transcription (optional extra) |
| A visualiser that dances to music | Built today (`level`, `spectrum`) |

## 6. Open questions

1. **Scope of 0.1 beyond D-055:**
   - Add the Karplus–Strong **pluck**?
   - Add the **melody string** (`f.melody("C4 E4 G4/2")`)?
   - Add **pitch helpers**: `note_to_frequency`, `frequency_to_note`, `sound.pitch()`, `mic.pitch()`?
2. **Melody syntax:**
   - Note names and `/2` for durations, or a subset of ABC?
   - Rests? Tempo? Ties?
3. **Envelope:**
   - Is a single fade enough for 0.1?
   - Or a simple ADSR (attack, release) as named arguments?
4. **Live synthesis later:**
   - pyo, sounddevice + numpy, or pygame-ce's callback?
   - Is a real-time synth worth an optional extra at all?
5. **Instruments later:**
   - FluidSynth plus a small permissively licensed SoundFont as an extra?
   - Which SoundFont, and under what licence?
6. **MIDI:**
   - Export only (`mido`) so learners can open their tunes elsewhere?
   - MIDI import?
   - MIDI keyboards as input?
7. **Analysis depth:**
   - Pure-Python onsets, tempo, chroma, key and chords in funground (no dependency, modest accuracy)?
   - Or an optional `funground[music]` extra wrapping librosa (better, heavy)?
8. **Transcription:** a later optional extra with basic-pitch, or leave it to other tools?
9. **Sound in videos:** should MP4 export carry the sketch's sound? It needs mixing to a WAV track for ffmpeg.
10. **The microphone API's stability:** wrap `pygame._sdl2.audio` and pin pygame-ce, or wait for a stable API?

## 7. Recommendations (tentative)

- Keep the base install free of numpy and native audio. Everything in the base is pure Python on pygame-ce's mixer.
- Teach with the **offline music box** first. Every number of a wave can be printed and plotted, which a live
  engine hides.
- Add the **small, high-value** pieces to 0.1 if the sprint has room: the pitch helpers (a tuner and ear training
  become possible), the pluck and the melody string. All are S-sized and pure Python.
- Treat **polyphonic transcription** and **real instruments** as optional extras, chosen later on licence and
  install weight.

## 8. Tentative roadmap (not decided)

```text
0.1   playback, level, spectrum                       (built)
      create_sound, tones, notes, fade, pan, save WAV (decided, S-110)
      microphone                                      (planned, S-108)
      ? pitch helpers, pluck, melody string           (open, §6.1)

0.2   "music analysis" epic, pure Python: onsets, tempo/beats, chroma, key, simple chords
      MIDI export (mido, optional)
      a simple ADSR; maybe rests, tempo and ties in the melody string

0.3+  optional extras, each its own ADR:
        funground[synth]      live synthesis (pyo or sounddevice + numpy)
        funground[instrument] SoundFont playback (FluidSynth + a small SoundFont)
        funground[music]      richer analysis (librosa) and transcription (basic-pitch → MIDI → music21)
      sound in MP4 export
```
