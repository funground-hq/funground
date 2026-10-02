# Research note: music in funground — making, playing and listening

**Status:** research and options only, written 3 October 2026 from a conversation with the maintainer. Nothing in this
note is decided **except** what is marked *Decided*. Licences, sizes and capabilities of outside libraries were
**checked on 3 October 2026** against PyPI, GitHub and project pages (sources are given in the tables). A claim still
marked *verify* could not be confirmed. Release dates and wheel lists come from PyPI and can change.

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

### 3.3 Routes to a real synth (checked 3 Oct 2026; sources in the last column)

| Route | What it is | Licence | Install | Fit | Source |
|---|---|---|---|---|---|
| pyo | A complete DSP engine in C, scripted from Python | LGPL-3.0 | Latest PyPI release 1.0.5 (26 Mar 2023). Wheels for Python 3.7–3.11 on Windows, macOS and Linux, **none for 3.12 or 3.13**. The repository still sees commits (July 2026) but has no newer release | The nearest to p5.sound; the release gap is a real risk | pypi.org/project/pyo; github.com/belangeo/pyo |
| sounddevice + numpy | A live audio callback (PortAudio) and arrays; we write the engine | MIT | Pure-Python wheels (any Python 3); the Windows and macOS wheels bundle PortAudio, Linux needs the system library. Needs numpy for arrays | Most control; we maintain a synth | pypi.org/project/sounddevice |
| pygame-ce `_sdl2.audio` output callback | Live output with no new dependency | — | Installed already | A few simple voices; Python speed limits polyphony and effects; experimental API | (own spike, §1) |
| FluidSynth (pyfluidsynth) | Plays SoundFonts, i.e. recorded instruments (§3.5) | FluidSynth LGPL-2.1 (v2.6.1, 19 Sep 2026, active); pyfluidsynth MIT (1.4.0, 30 May 2026, Python 3.10+) | pyfluidsynth is a pure-Python wheel; the **native FluidSynth library is a separate install** (fiddly on Windows: not confirmed either way) | Best for realistic instruments | github.com/FluidSynth/fluidsynth; pypi.org/project/pyfluidsynth |
| SuperCollider (supriya, FoxDot) | A professional audio server | SuperCollider GPL-3.0 (3.14.1, Nov 2025, active). supriya and FoxDot: *verify* | Separate install | Powerful, heavy for learners | github.com/supercollider/supercollider |
| Csound (ctcsound) | A classic synthesis language | Csound LGPL-2.1 (7.0.0-beta.18, 1 Oct 2026, active). ctcsound: *verify* | Separate install | Very capable, steep | github.com/csound/csound |

Any of these would be an L-sized project, and a new ADR because it changes ADR-003/006. It would be an
**optional extra**, never in the base install.

### 3.4 Notations: simpler ways to write music

| Notation | Looks like | Notes |
|---|---|---|
| Note names | `"C4 E4 G4 C5"` | What S-110's notes will accept |
| A melody string (idea) | `f.melody("C4 E4 G4/2 C5")` | Small and pure Python. Durations need a tiny syntax |
| ABC notation | `C D E F \| G2 G2 \|` | Plain-text folk notation; parsers exist (*verify*) |
| MIDI | Note on/off events in a file | The universal exchange format; `mido` reads and writes it. Checked: MIT, 1.3.3 (25 Oct 2024), pure-Python wheel, Python 3.7+ (pypi.org/project/mido) |
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

### 3.6 Orchestra-style libraries for Python (checked 3 Oct 2026)

| Library | What | Note |
|---|---|---|
| SCAMP | Compose for an ensemble of instruments in Python; plays through SoundFonts; exports notation | The closest to "an orchestra in Python". **GPL-3.0-only** (so an optional extra at most), version 0.13.0 (25 Sep 2026), Python 3.12+, wheels for Windows, macOS and Linux (pypi.org/project/scamp) |
| music21 | Notation and theory: scales, chords, parts, MusicXML/MIDI | For analysing and writing scores more than performing. BSD-3-Clause, 10.5.0 (17 Jun 2026), Python 3.11+, pure-Python wheel (pypi.org/project/music21) |
| pretty_midi, mido | Build multi-track MIDI | Play with any synth, or open in MuseScore or GarageBand. Both MIT. pretty_midi 0.2.11.post0 (28 Jul 2026), pure wheel; mido see §3.4 (pypi.org/project/pretty_midi) |
| FoxDot | Live coding on SuperCollider (`p1 >> pluck([0, 2, 4])`) | Performance-oriented. *verify* (licence, maintenance and wheels not checked) |
| Csound (ctcsound) | A literal orchestra and score | The most powerful and the steepest. Csound is LGPL-2.1 and active (§3.3); ctcsound *verify* |

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

### 4.2 Analysis libraries (checked 3 Oct 2026; sources are the PyPI pages `pypi.org/project/<name>`)

| Library | Good at | Licence | Weight and install |
|---|---|---|---|
| librosa | Pitch (pYIN), onsets, tempo, beats, chroma, key | ISC | 1.0.0 (11 Aug 2026), pure wheel, **requires Python 3.12+** (no 3.11). Dependencies (numpy, scipy, numba, soundfile) not re-checked |
| aubio | Real-time pitch, onsets, tempo | GPL-3.0+ | **Stale:** last PyPI release 0.4.9 (8 Feb 2019), source only, no wheels |
| madmom | Beat and tempo tracking | BSD code; model files CC BY-NC-SA 4.0 (non-commercial) | **Stale on PyPI:** 0.16.1 (14 Nov 2017), source only, no wheels. Newer GitHub activity not checked |
| essentia | A large toolbox: key, chords, tempo, mood, and Indian-music tonic and melody algorithms (§6.3) | **AGPL-3.0** (`pip` metadata and GitHub) | 2.1b6.dev1438 (19 May 2026); GitHub active (push 2 Oct 2026). Wheels for Python 3.11–3.13 on **Linux and macOS only**; the install guide says Python bindings are not supported on Windows (essentia.upf.edu/installing.html). Heavy |
| basic-pitch (Spotify) | Polyphonic audio → MIDI | Apache-2.0 | 0.4.0 (16 Aug 2024), pure wheel. Needs librosa and a platform ML runtime (TensorFlow Lite on Linux, CoreML on macOS, ONNX Runtime on Windows). Python 3.11+ support not stated in its metadata |
| CREPE | Accurate single-voice pitch | MIT | 0.0.16 (19 Aug 2024); **requires TensorFlow 2.x**, so heavy. Python 3.11+ support not stated |
| music21 | Theory once notes are known | BSD-3-Clause | 10.5.0, Python 3.11+, pure wheel (§3.6) |

A powerful pipeline: **basic-pitch → MIDI → music21** turns a recording into notes, key, chords and sheet music.
Licence notes for a permissive (LGPL) package:
- GPL and AGPL libraries could only ever be optional, user-installed extras;
- madmom's model licence would block some uses;
- aubio and madmom have had no PyPI release for years, so neither is a safe optional extra;
- librosa 1.0 needs Python 3.12 or later, so a `funground[music]` extra would raise the minimum Python for that extra.

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

## 6. Ragas and Indian music

Indian art music (Hindustani in the north, Carnatic in the south) fits funground well. A raga is built on a tonic
that the performer chooses, uses pitches that are not always equal-tempered, and moves by glides and ornaments.
Those are numbers that a learner can draw, and they are what the 0.1 melody string and the Sprint 14 drawings are
for. This section says what each idea is, how it fits, and what outside work exists.

**Status words used below.**
- *Decided* means contract row A3 (`docs/design/Semantic_Contract.md`) and D-056 (`Decision_Log.md`).
- *Planned* means a story in `sprints/sprint-14/stories.md` (S-114, ragas), not yet built.
- *Later* means nothing is planned.
- D-057 (ragas in 0.1, `Decision_Log.md`) was accepted after this note was drafted; this section does not rely on it.

### 6.1 Concepts and their fit with funground

| Concept | What it is | Fit with funground |
|---|---|---|
| Sa as a movable tonic; sargam names | Sa is the home note. The performer picks its pitch (a singer's Sa might be C#4, a flautist's lower), and every other note is a ratio to it. The seven names are Sa Re Ga Ma Pa Dha Ni; Sa and Pa never change | *Decided* (A3): `f.melody(text, sa="C#4")` reads `S r R g G m M P d D n N`, with `'` for the octave above and `,` for the octave below. `f.note_to_frequency(name, sa=...)` and `f.frequency_to_note(hz, sa=...)` also take `sa`. *Planned*: the pitch line and histogram draw against Sa |
| Komal and tivra | Re, Ga, Dha and Ni each have a flat form (komal); Ma has a sharp form (tivra) | *Decided* (A3): lower-case `r g d n` are komal; capital `M` is tivra Ma; `m` is natural Ma |
| Just intonation; the 22 shrutis | Many singers tune notes to simple ratios of Sa (for example Pa = 3/2, Ga = 5/4), not to equal temperament. Traditional theory divides the octave into 22 small steps (shrutis); how they are used in practice is debated, and the 12 swaras sit on a subset of them | *Decided* (A3): `tuning="just"` uses just-intonation ratios from Sa instead of equal temperament. *Later*: a table of the 22 shrutis, and reading Scala tuning files (§6.3) so a learner can try other tunings |
| Meend and gamaka | Meend is a smooth glide between notes (Hindustani). Gamaka is the family of ornaments, such as shakes, slides and oscillations around a note, central to Carnatic music | **Not in A3**: a melody token is a steady note, so there is no glide. *Planned*, but the design is open: a glide would need a pitch that moves inside one tone (a new argument or token), and gamaka would be a few named shapes. Open question 11 |
| The tanpura drone | A long-necked lute that plays Sa and Pa (sometimes Ma) in a repeating cycle, with rich overtones. It gives the singer a fixed reference | *Planned*: a tanpura made from `tone` and `pluck` (S-114), looped, so a learner can sing against it. It is an approximation; a real tanpura's buzzing overtones (jivari) are hard to copy |
| Aroha and avaroha; pakad; vadi and samvadi | Aroha is the rising scale, avaroha the falling one; they can differ (a raga may skip or bend notes in one direction). The pakad is a short phrase that identifies the raga. The vadi is its most important note and the samvadi the second | *Planned*: a small raga table holding aroha, avaroha, vadi and samvadi; compose from aroha and avaroha. *Later*: using the pakad as a phrase to match or to test a learner's tune against |
| Tala (teentaal, rupak; tabla bols) | A tala is a repeating cycle of beats with a pattern of claps (tali) and waves (khali). Teentaal has 16 beats in 4+4+4+4. Rupak has 7 in 3+2+2, and begins on a wave. Tabla bols are spoken syllables for drum strokes (Dha, Dhin, Na, Tin, Ta…); the standard pattern for a tala is its theka | *Planned* only as a teaching idea (a tala clap-along, §6.4). *Later*: a tala table (beats, claps, theka) and a simple percussion sound. A convincing tabla is a sampled-sound problem, not a synthesis one, so a simple click or noise burst per bol is the realistic aim |
| Thaat and melakarta | Thaat is Bhatkhande's scheme of 10 parent scales for Hindustani ragas (Bilawal, Khamaj, Kafi, Asavari, Bhairavi, Bhairav, Kalyan, Marwa, Poorvi, Todi). Melakarta is the Carnatic scheme of 72 parent scales, generated by the choice of Ri, Ga, Dha and Ni variants and one of two Ma | *Planned* as one field in the raga table (thaat). *Later*: the 72 melakartas as a generated table, and "which thaat is this histogram nearest to?" |

Two example ragas for the table. Yaman is in the Kalyan thaat, with tivra Ma. Its aroha is `N, R G M P D N S'`
and its avaroha is `S' N D P M G R S`, written in the A3 notation. Its vadi is Ga and its samvadi Ni, as widely
taught. Its pakad should be copied from a named teaching source, not from memory (*verify*).

### 6.2 Analysis

| Task | Idea | Difficulty for funground |
|---|---|---|
| Pitch contour | The pitch of the voice over time. Draw it as a line against horizontal lines at Sa, Pa and the raga's notes. The microphone and `sound.pitch()` (A3, autocorrelation) already give one pitch per moment | S. Planned (the pitch line in S-111 and S-114) |
| Tonic (Sa) identification | Find the singer's Sa from a recording. Common methods build a histogram of pitch, find the peaks, and choose among them with rules or a classifier (Essentia's `TonicIndianArtMusic` does this, §6.3). Octave and Pa errors are the main failures. A learner can simply **tell** the sketch their Sa | M for a simple version (the strongest peak of a histogram folded to one octave); research-grade accuracy is *Later* |
| Pitch-class (swara) histogram | Take the pitch contour, convert each value to cents above Sa, fold to one octave and count. Peaks show which swaras are used and how long they are held. Two ragas with the same notes can still differ in the shape of the peaks | S. Planned (S-114) |
| Raga recognition | A research area: given a recording, name the raga. Published work uses histograms, melodic phrases and delay-coordinate features (§6.3), with high accuracy on curated sets of 30–40 ragas. For funground only a basic **compare to a small table** is realistic | M for matching a histogram to a few ragas; *Later* and an optional extra for anything deeper |
| Note segmentation | Cut the contour into separate notes | **Hard**. In many ragas a note is not a steady pitch: it is approached by a glide, oscillated around, or only touched. A fixed pitch threshold cuts one gamaka into several false notes or merges two real ones. This is why histograms and whole-contour features are used instead of note-by-note transcription, and why this note does not plan a recording-to-notes feature |

### 6.3 Existing work to build on (checked 3 Oct 2026)

**CompMusic and the Music Technology Group (MTG), Universitat Pompeu Fabra, Barcelona.**
- CompMusic was a European Research Council project directed by Xavier Serra, running 2011–2017. It studied five
  traditions, including Hindustani and Carnatic. Its site lists corpora, software, publications and a MOOC on North
  Indian classical music (compmusic.upf.edu).
- **Dunya** is the project's music browser, and its code is on GitHub (github.com/MTG/dunya): AGPL-3.0, no releases,
  last push July 2026. The rules for getting data through its API were not checked (*verify*).
- **Saraga** is the main dataset (mtg.github.io/saraga; zenodo.org/records/4301737). Latest data update April 2022; 357
  recordings (108 Hindustani, 249 Carnatic), 96.3 hours, 61 ragas, 19 talas. It has melody, tonic, section, tempo and
  tala-cycle annotations, and phrase annotations in solfège. A subset of the Carnatic recordings is multitrack. The
  MTG still maintains it. Cite: A. Srinivasamurthy, S. Gulati, R. Caro and X. Serra, "Saraga: Open Datasets for
  Research on Indian Art Music", *Empirical Musicology Review* 16(1), 85–98, 2021.
- Publications whose titles and years were confirmed:
  - Gulati, Bellur, Salamon, Ranjani, Ishwar, Murthy and Serra, "Automatic tonic identification in Indian art music:
    approaches and evaluation", *Journal of New Music Research* 43(1), 53–71, 2014. About 90% accuracy on average
    for the best (multipitch plus machine learning) methods on six datasets.
  - "A Multipitch Approach to Tonic Identification in Indian Classical Music", ISMIR 2012 (cited by Essentia; the
    author list was not checked).
  - Salamon and Gómez, "Melody extraction from polyphonic music signals using pitch contour characteristics",
    *IEEE Transactions on Audio, Speech and Language Processing* 20(6), 1759–1770, 2012 (the Melodia algorithm).
  - Gulati, Serrà, Ganguli, Şentürk and Serra, "Time-delayed melody surfaces for rāga recognition", ISMIR 2016,
    751–757: 98% on 300 Hindustani recordings of 30 ragas, 87% on 480 Carnatic recordings of 40 ragas.
  - Gulati, Serrà, Ishwar, Şentürk and Serra, "Phrase-based raga recognition using vector space modeling", ICASSP
    2016 (title and venue from a search result; not opened).
  - The free ebook "Indian Art Music: A Computational Perspective" is listed on the CompMusic site (not opened).

**Software.**

| Item | What it gives | Licence | Maintained? Python 3.11+? | Source |
|---|---|---|---|---|
| Essentia | `TonicIndianArtMusic`: Sa of the lead artist from a pitch-salience histogram plus a decision tree (default 100–375 Hz). `PredominantPitchMelodia`: the Melodia melody contour | **AGPL-3.0** | Active (2.1b6.dev1438, 19 May 2026). Wheels for 3.11–3.13 on Linux and macOS, **not Windows** | essentia.upf.edu/reference/std_TonicIndianArtMusic.html; std_PredominantPitchMelodia.html; pypi.org/project/essentia |
| mirdata | Downloads, validates and loads MIR datasets in a common form. Has loaders `saraga_carnatic`, `saraga_hindustani` and `compmusic_raga` (so it **does load Saraga**) | BSD-3-Clause | 1.0.0 (23 Sep 2025); repository active (July 2026). Pure wheel, Python 3.8+; its CI lists 3.8–3.11 | pypi.org/project/mirdata; github.com/mir-dataset-loaders/mirdata |
| compIAM | "Common tools for the computational analysis of Indian Art Music": tonic, melody and raga tools, with optional Essentia, TensorFlow and PyTorch extras | **AGPL-3.0** | Latest PyPI release 0.4.1 (29 Nov 2024); repository push Feb 2026. It pins `numpy<=1.26.4`, `mirdata==0.3.9` and `compmusic==0.4`, so it probably does not install on current Pythons (not tested) | pypi.org/project/compiam; github.com/MTG/compIAM |
| Scala tuning files | `.scl` lists a scale as ratios or cents; `.kbm` maps keys. A de facto standard; the format is a few lines of text | The format is open to implement. The Scala program is freeware that "may not be sold, modified, or distributed" except as its own package; the licence of each file in the 4 000-file archive was not checked (*verify*) | music21 has a Scala reader (`music21.scale.scala`). Others not checked | en.wikipedia.org/wiki/Scala_(software); en.xen.wiki/w/A_shruti_list |

**Datasets.**

| Dataset | Contents | Licence |
|---|---|---|
| Saraga (Carnatic and Hindustani) | As above | **Non-commercial.** The Zenodo record says CC BY-NC-SA 4.0. The GitHub LICENSE.md says the audio, manual annotations and automatic annotations are CC BY-NC 4.0 and the repository code is AGPL-3.0. These two differ, so read the licence of the exact download before use |
| CompMusic Raga Recognition Dataset (Hindustani and Carnatic) | Raga labels, tonic, predominant pitch and nyas segments for 300 Hindustani recordings (116 hours, 30 ragas, 10 each) and the Carnatic set; Gulati et al. 2016 | Features: **CC BY 4.0** (zenodo.org/records/7278505). The audio is a separate Zenodo entry and needs a request |
| Indian art music tonic datasets | Tonic annotations used in the 2014 tonic study | Exists (repositori.upf.edu); licence not checked (*verify*) |

**Small Python projects (all checked on PyPI or GitHub; none is a safe dependency).**
- `bhargava-swara` (pypi.org/project/bhargava-swara): MIT, 0.0.15 (28 Apr 2025). "Analysis and synthesis of Indian
  classical music". It depends on `google-generativeai`, librosa, seaborn, sounddevice and scipy, so it is heavy and
  not a fit. The quality of its tabla and tanpura sound was not checked.
- `Tabalchi` (github.com/shreyanmitra/Tabalchi): a tabla-composition parser and player, 0.0.9 (26 Oct 2024). PyPI
  states no licence; GitHub reports BSD-3-Clause. It needs `torch`, `transformers`, FFmpeg and more. Not a fit.
- `pytheory` (github.com/kennethreitz/pytheory): MIT, Python 3.10+, depends on sounddevice and scipy. Its PyPI page
  lists an "Indian (Hindustani)" musical system among six. Claims that it has tabla, tanpura or the 22 shrutis
  could **not** be confirmed from its metadata (*verify*).
- A pure-Python "Raag Yaman with sitar, tabla and tanpura" project appeared in a search result only: *verify*
  (not located, nothing known about it).
- A **raga database** with a permissive licence was not found. Saraga's metadata is non-commercial. The small raga
  table for Sprint 14 should be written by hand from named teaching sources.

**Commercial apps, for inspiration only (not for code).**
- iTablaPro (App Store; electronic tabla and tanpura, many talas, tuner; listed at $29.99; a Lite version is free).
- iTabla Pandit Studio Pro (App Store; tanpura in several tunings, tabla, shruti, harmonium, over 80 Hindustani
  ragas, tuner).
- Bandish (App Store; tabla, tanpura and manjira for practice) and Dha (tabla bols and tala; listens to the
  learner and grades timing).
- The Riyaz singing-practice app: **not found** in a search; *verify*.

### 6.4 Teaching scenarios for ragas

| Scenario | What the learner sees and does | Needs |
|---|---|---|
| Sing with the drone | A tanpura loops on Sa and Pa. The microphone pitch line scrolls, with horizontal lines at Sa and Pa. The learner sings and watches the line settle on the lines | Tanpura from `tone` and `pluck`; microphone (S-108); `mic.pitch()` against `sa`; scrolling pitch line (S-111) |
| See the raga | The learner sings or plays a phrase. A swara histogram appears, with the raga's swaras marked. Notes outside the raga stand out | Pitch contour; folding to cents above Sa; a raga table |
| Compose in Yaman | Rules from aroha and avaroha (rise and fall by steps, end on Sa, stress Ga). Then add meend between two notes and hear the difference | `f.melody(..., sa=..., tuning="just")` (*Decided*); a rule-based generator; a glide (*not in A3*) |
| A tala clap-along | A teentaal or rupak cycle: a beat counter, claps on tali, a wave on khali, with the bols shown. The learner claps (microphone onsets) | A tala table; clicks; onsets and tempo (S-112) |

### 6.5 Licence cautions

- funground is a permissive (LGPL) package. GPL and AGPL code can only ever be an **optional, user-installed extra**,
  never a base dependency. That covers Essentia (AGPL-3.0), compIAM (AGPL-3.0), Dunya (AGPL-3.0), aubio (GPL-3+),
  SCAMP (GPL-3.0-only) and SuperCollider (GPL-3.0).
- **Dataset licences are separate from code licences.** Saraga is non-commercial (CC BY-NC or CC BY-NC-SA, see the
  table above). funground must not bundle Saraga audio or annotations in the wheel or gallery. A guide may link to
  it and show mirdata code, and the learner downloads it under its terms. If a gallery example ships a recording,
  it must be our own or have a licence that allows redistribution.
- The Scala programme's terms bar redistribution except as its own package, so do not copy files from its archive
  into funground without checking each file.
- Pure-Python code that follows a published method (for example folding a pitch histogram) is ours to write; copying
  AGPL code, even a small function, is not.
- madmom's models are non-commercial (see §4.2).

## 7. Open questions

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
11. **Ragas (§6):**
    - How is a glide (meend) written in the melody string, given that A3 has only steady notes?
    - Which named shapes stand for gamaka?
    - Which teaching sources fix the raga table (aroha, avaroha, vadi, samvadi, pakad)?
    - Is the swara histogram a library function or just an example?

## 8. Recommendations (tentative)

- Keep the base install free of numpy and native audio. Everything in the base is pure Python on pygame-ce's mixer.
- Teach with the **offline music box** first. Every number of a wave can be printed and plotted, which a live
  engine hides.
- Add the **small, high-value** pieces to 0.1 if the sprint has room: the pitch helpers (a tuner and ear training
  become possible), the pluck and the melody string. All are S-sized and pure Python.
- Treat **polyphonic transcription** and **real instruments** as optional extras, chosen later on licence and
  install weight.

## 9. Tentative roadmap (not decided)

```text
0.1   playback, level, spectrum                       (built)
      create_sound, tones, notes, fade, pan, save WAV (decided, S-110)
      microphone                                      (planned, S-108)
      ? pitch helpers, pluck, melody string           (open, §7.1)

0.2   "music analysis" epic, pure Python: onsets, tempo/beats, chroma, key, simple chords
      MIDI export (mido, optional)
      a simple ADSR; maybe rests, tempo and ties in the melody string

0.3+  optional extras, each its own ADR:
        funground[synth]      live synthesis (pyo or sounddevice + numpy)
        funground[instrument] SoundFont playback (FluidSynth + a small SoundFont)
        funground[music]      richer analysis (librosa) and transcription (basic-pitch → MIDI → music21)
      sound in MP4 export
```
