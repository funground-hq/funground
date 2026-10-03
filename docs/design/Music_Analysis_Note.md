# Design note: music analysis (rhythm and harmony)

**Status:** built in Sprint 14 (S-112, S-113; D-061). Contract rows A5 (rhythm) and A6 (harmony) in
[Semantic_Contract.md](Semantic_Contract.md). Code: `funground/analysis.py` (plain Python, no pygame); the methods are
on `sound._Analysis` and `Sound` in `funground/sound.py`. Tests: `tests/test_rhythm_harmony.py`.

## Where things live

- `_Analysis` (shared by sounds and microphones): `is_onset()`, `chroma()`, `chord()`.
- `Sound` only: `onsets()`, `tempo()`, `beats()`, `key()`. They look at the whole sound and are cached on the sound.
- `Microphone`: has no `onsets`, `tempo`, `beats` or `key`. Calling one raises `ValueError` that says to use
  `mic.capture(seconds).<method>()`. A microphone has no whole sound, and `capture()` already gives one, so this is the
  simplest choice that fits A5 and A6.
- `f.chord_notes(name)`: `api.py` calls `analysis.chord_notes`.

## Rhythm (A5)

- **Rate.** The sound is averaged down to 5 512 Hz first. A pure Python FFT of 1 024 points at 44.1 kHz would take
  about a minute for a three-minute song. Frames are 256 samples (46 ms) with a hop of 64 (11.6 ms) at that rate, which
  is the same time span as 2 048/512 at 44.1 kHz. Two real frames share one complex FFT.
- **Onset strength.** Spectral flux: Hann window, magnitude, `log(1 + 100 * magnitude)`, positive differences summed over
  bins (30 Hz up).
- **Peaks.** A local maximum that beats `1.6 * local median (0.5 s each side) + max(2, 0.15 * strongest flux)`, with at
  least 50 ms between peaks. Onset time is the end of the peak frame minus 18 ms (found by test, so the times are
  centred on the true onsets).
- **Tempo.** Autocorrelation of the envelope (minus its slow average) over lags for 60 to 200 BPM, times a prior
  (a Gaussian in octaves around 120, width one octave), with a parabola for sub-frame lags. No tempo when fewer than
  4 onsets or the best normalised autocorrelation is below 0.12. The tempo is then fine-tuned from the onset times:
  for tempi within 6 per cent in steps of 0.25 per cent, onset phases are put in a histogram and the tightest
  cluster wins. That gives the tempo to about 0.1 BPM and the beat phase.
- **Beats.** The grid at that tempo and phase, from the start to the end of the sound.
- **Live `is_onset()`.** The last 0.3 s, hop 128 (23 ms). The first frames are skipped (they hold made-up silence), and the
  newest frame can be a peak as soon as it rises, so a light flashes about one hop after the note. A flash needs 0.1 s
  since the last one. State is kept on the object (`_onset_last`) and the answer is cached per frame.

## Harmony (A6)

- **Chroma.** The last 2 048 samples at about 11 025 Hz (0.19 s). Each spectral peak between 65 Hz and 2 kHz, with a
  parabola for its pitch, is put on the nearest note and weighted by its magnitude. The result is divided by its largest
  value.
- **Chord.** Cosine match with binary templates for the seven qualities on all 12 roots. `None` below 0.85, or when the
  second strongest pitch class is under 0.2 of the strongest (one voice). Roots use sharps. An augmented chord is the
  same on three roots; the lowest pitch class wins.
- **Key.** Chroma of up to 400 frames spread over the sound, each scaled to a maximum of 1, is added up and correlated
  with the Krumhansl-Schmuckler major and minor profiles on all 12 tonics (best must reach 0.3).
- **Profiles.** From the probe-tone ratings in Krumhansl and Kessler (1982), Psychological Review 89, 334-368
  (also Krumhansl 1990): major 6.35 2.23 3.48 2.33 4.38 4.09 2.52 5.19 2.39 3.66 2.29 2.88; minor 6.33 2.68 3.52 5.38
  2.60 3.53 2.54 4.75 3.98 2.69 3.34 3.17. They were written from memory and could not be checked against the paper
  in this build (no network, no copy). Check them before release.

## Measured (Windows, pure Python)

- Click, note and plucked tracks at 80, 100, 120 and 150 BPM, 16 beats: tempo within 0.4 BPM; every onset within 9 ms and
  every beat within 10 ms of the truth.
- Three-minute song (360 hits): rhythm about 6 s, `key()` about 2 s, on top of reading the samples.
- `chord()`: about 6 ms. `is_onset()`: 5 to 10 ms per call.

## Limits

- Smooth singing and bowed strings have soft starts, so onsets are weak. Naive saw waves give extra onsets (aliasing).
- Chords: clear piano, guitar and synth chords. Low notes (below about C3) smear over neighbouring pitch classes.
- Fast subdivisions can make the tempo double or halve; the 120 prior helps but cannot decide every case.
