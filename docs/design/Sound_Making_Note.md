# Design note: making sound

**Status:** decided (D-055 and D-056, 3 October 2026; ADR-006). Built in Sprint 13 (S-110). Contract row A3 in
[Semantic_Contract.md](Semantic_Contract.md). Code: `funground/synth.py` (plain maths, no device) and
`funground/sound.py` (the `Sound` class and the only use of `pygame.mixer`).

## The problem

Sound playback and analysis (A1, A2) needed a file. A learner who wants to hear a note, write a tune or draw a
wave had to make a file somewhere else first. ADR-006 allows offline synthesis in pure Python. D-056 adds the
teaching pieces: plucked strings, a melody string with sargam, and pitch.

## The route

```
f.tone / f.note / f.pluck / f.melody ──► synth.py: a list of floats, -1 to 1, at 44 100 a second
f.create_sound(list) ──────────────────►        │
f.sequence / f.mix (any sounds) ───────►        ▼
                                  sound._from_samples: clip, resample to the mixer rate, make 16-bit
                                  samples in every channel, mixer.Sound(buffer=...)  ──►  Sound
```

A made sound is an ordinary `Sound` (A1, A2). It keeps its 16-bit samples from the start, as a loaded sound does
after its first analysis, so `level`, `spectrum` and `pitch` read the same way in silent mode. It also keeps its
original list of floats, so `samples()` gives back exactly what `create_sound()` was given.

## Choices

- **Pan is a channel volume, not a rebuilt buffer.** `Channel.set_volume(left, right)` is applied when the sound
  plays and whenever `pan()` is called. So it works on loaded sounds and on a sound that is already playing, and
  analysis (which reads the buffer) never sees it. Law: a balance control, `left = min(1, 1 - p)`,
  `right = min(1, 1 + p)`. Pan 0 is the sound unchanged. A constant-power law would make the centre quieter than
  a sound that was never panned. `save()` bakes the pan into the stereo file.
- **Waves** were the naive formulas in S-110. S-118 replaced them with band-limited waves: see "Sound quality" below.
- **Noise and the pluck's first burst** come from `canvas_sketch()._rng`, the generator `random_seed()` seeds, so
  they repeat after `random_seed()` (the same route as `Vector.random()`).
- **Pluck** is Karplus-Strong with a decay of 0.996 each trip round the loop. A loop of whole samples would tune
  badly at 1 kHz, so the loop is a whole number of samples plus a first-order all-pass filter, which also makes
  up the half sample of delay in the averaging filter. Measured pitch error from 80 Hz to 1 kHz (about 90 notes each): sine 0.001 per cent, triangle 0.006, pluck 0.02, square and saw 0.15.
- **Melody** timing is cumulative: each note ends at `round(beats so far x 60 / tempo x 44100)`, so a long tune
  does not drift. A chord is `mix()` of its notes' tones, so it equals a mix. Sargam uses equal temperament by
  default and the 5-limit just ratios (`1 16/15 9/8 6/5 5/4 4/3 45/32 3/2 8/5 5/3 9/5 15/8`) with
  `tuning="just"`. `tuning="just"` without `sa` is a `ValueError`, because there is no Sa to measure from.
- **Pitch** is normalised autocorrelation over the last 2 048 samples at the playing position, with the mean
  removed. Lags cover 50 to 2000 Hz. It takes the first peak that is within 90 per cent of the best one (so it does
  not jump an octave down) and refines it with a parabola through three points. It returns `None` when the
  window's RMS is below 0.01 (about -40 dB) or the best score is below 0.7 (a repeating wave scores about 1,
  noise about 0.1), and when the sound is not playing. It costs about 50 ms in plain Python, and is cached once
  per frame like `level()` and `spectrum()`.
- **Names** are rounded to the nearest semitone and use sharps (`"A#4"`). With `sa`, the nearest swara by
  equal-tempered distance, with `'` or `,` for octaves.

## Sound quality (S-118, D-064, contract A9)

The maintainer found the made sounds unpleasant "across the board". The causes were full-scale defaults that
clipped when layered, aliasing naive waves, a boxy linear envelope, a bare sine melody voice, a harsh pluck, no
room sound and an 11 025 Hz visualiser tune. Everything stays plain Python with no new dependency.

- **Headroom.** `tone`, `note`, `pluck`, `melody` and `drone` default to `volume=0.5`. The tala's loudest stroke is
  0.5 (`TALA_PEAK`; it has no `volume` argument). `mix` adds the parts and passes the sum through a soft limiter
  (`synth._limit`): samples up to 0.7 are untouched, louder ones bend on a tanh curve towards 0.9, and a sum whose
  peak passes 1.2 is first scaled down to 1.2 so the bend stays gentle. The peak is at most 0.897.
- **Band-limited waves.** Square (odd k, 1/k), saw (all k, 1/k), triangle (odd k, ±1/k²) and the new `soft`
  (harmonics 1 to 4 at 1, 0.35, 0.15, 0.06) are built from their harmonics up to 20 kHz (and below half the rate).
  One period goes in a 4 096-point table, made by an inverse FFT and scaled to peak 1, and the note reads it with
  linear interpolation. The number of harmonics is rounded down to one of a few dozen sizes (every count to 16,
  then steps of an eighth of an octave), so tables are shared and cached. Measured: a 3 s note takes 0.04 to 0.08 s;
  at 3 kHz the energy away from the harmonics is about 1e-13 of the total (the naive square had 5 %, the saw 8 %).
  The soft wave's spectral centroid at 440 Hz is 670 Hz (triangle 910 Hz), a gentle, recorder-like voice.
  Glides (meend, kan) use the table for the highest pitch they reach. Sine and noise are unchanged.
- **Envelope.** `synth.envelope(n, attack, decay, sustain, release)`: rise `(1 - e^(-4u)) / (1 - e^-4)`, decay from 1
  to `sustain` and release to 0 on `(e^(-4u) - e^-4) / (1 - e^-4)`, so each segment is fast at first and then
  levels off, and ends exactly on its target. A release that starts during the attack or decay starts from the level
  there. Defaults: attack 0.01 s, decay 0.15 s, sustain 0.7, release 0.15 s. Curves are cached per length.
- **Legato melody timing.** Each note starts on its beat (cumulative rounding, so no drift) and holds until its last
  beat ends. Then its release (0.15 s, or the note's length if shorter) rings on over the next note. The melody lasts
  its beats plus the last note's release where that passes the end; a final rest of at least 0.15 s holds it, so a
  looping tune can keep exact beats. A chord is `mix` of its notes; if overlapping notes would pass 1 the melody
  goes through the same limiter. Overlap raises a melody's peak to about 0.76 at the default volume.
- **Legato against analysis.** Overlapping notes make some pitch-track frames hear two notes at once. Measured on
  the test phrases (tempo 150): Yaman's share of time on its own swaras falls from 0.96 to 0.92, and the
  Bhupali-Yaman score gap from 0.20 to 0.14; rankings are unchanged. `synth.LEGATO_LEAD` (0 now) moves part of
  each release before the note's end. Swept: lead 0.2 gives 0.95 and 0.15 with a 4 ms dip below half level at each
  join; lead 0.5 gives 0.97 and 0.25 but a 67 ms dip, longer than the old envelope's 30 ms, so not legato.
  Lead 0 (no dip) was chosen; the main session may prefer another value.
- **Pluck.** The burst is smoothed four times round the loop by (1, 2, 1)/4 (`synth.soft_burst`, about a 4 kHz
  low-pass). The spectral centroid of the first 50 ms drops from 7.6/6.0/4.6/3.3 kHz to 3.7/3.1/2.6/2.1 kHz at
  110/220/440/880 Hz. Pitch accuracy is unchanged (the loop sets the pitch). The drone uses the same function with
  32 passes, so its sound is unchanged apart from its level.
- **Reverb.** `sound.reverb(amount)` (`synth.reverb_samples`): four feedback combs (1 229, 1 373, 1 499, 1 621
  samples) with a two-tap damping in the loop, summed (echoes only), then two all-pass filters (373 and 131
  samples, gain 0.6). The decay time is `0.3 + 1.7 × amount` seconds to −60 dB; `1.5 × amount` seconds of tail
  are added, the last 0.3 s faded out. The wet level grows with √amount. The result is scaled down if its peak
  would pass the input's. Both filters run a block of one delay at a time with list comprehensions, as each block
  needs only earlier ones: 5 s of sound takes about 0.3 s. Amount 0 returns the samples unchanged. At 0.3 the
  ring just after a note ends is about 13 dB below the note, at 1 about 6 dB. A looped sound with reverb gets a
  short pause at the loop point; the gallery drone examples fold the tail back onto the start with a small helper.
- **Gallery.** Every example that plays sound was retuned, and a simulation of the mixer sum (each sound's samples
  times its `set_volume`, loops wrapped) checked the peaks: all between 0.5 and 0.77, none clipping (before, "Hear
  a raga" peaked at 1.37). `tune.wav` is 44 100 Hz, mono, 16-bit, 3 s, made by `make_tune.py` with a soft voice.

## The microphone (S-108, D-058, contract A4)

- **Capture:** `funground/microphone_input.py` opens an input with pygame-ce's `pygame._sdl2.audio` (an
  experimental module, pygame-ce 2.5 or newer). All access is in three small functions, so a change in pygame
  touches one place. A missing module gives a `RuntimeError` that names the pygame version.
- **Format:** the device is asked for 44 100 Hz, 32-bit float, one channel, 512-sample chunks, and only the
  sample format may change. On Windows (pygame-ce 2.5.8, SDL 2.32.10) SDL granted float, 44 100 Hz, one channel. The
  callback also handles 16-bit and several channels.
- **Threads:** SDL calls the callback on its own thread. It does the least it can: copy the bytes, convert, and
  append to a ring buffer of the last 10 seconds. A lock guards the buffer, held for one slice copy by the
  writer and by each reader, so a reader never sees a half-written chunk.
- **Analysis:** `level`, `spectrum` and `pitch` are in `sound._Analysis`, which `Sound` and `Microphone` share. A
  microphone supplies only "the newest N samples" and whether it is listening. The window sizes and the
  once-a-frame cache are the same as for sounds.
- **Capture:** `capture(seconds)` goes through the same path as `create_sound`. If less than `seconds` was heard,
  the start is silence, so the length is always as asked (this also makes a headless capture work).
- **Headless and tests:** `FUNGROUND_HEADLESS=1` gives a silent microphone with an empty buffer. Tests replace
  the device functions and call `mic._feed(samples)`; they never open a real microphone.
- **Not here:** playing the microphone back, echo and noise handling, choosing the sample rate.

## Drawing sound (S-111, D-061, contract A7)

The four views live in `funground/sound_views.py`. The public functions in `api.py` only pass in the
sketch to draw on, so the code is plain and easy to test.

- **Ordinary drawing.** `draw_wave`, `draw_spectrum` and `draw_pitch_line` call `begin_shape`/`vertex`,
  `line`, `rect` and `text` on `active_sketch()`. They record normal ops, so layers, pictures, PDF and SVG
  work with no extra code. `draw_spectrum` and the guides run inside `saved_state()` so they do not leave a
  changed style (or `rect_mode`) behind.
- **Wave.** The wave is one closed shape: the highest sample in each pixel column along the top, the lowest
  back along the bottom. It is filled and stroked in the current style. A sound's columns are kept on the
  sound (`_views`, one pair of lists for each width), so drawing it every frame costs one pass over `w`
  points. A 12-second sound at 400 columns takes about 35 ms the first time and 2 to 4 ms after. A
  microphone is read afresh each frame (the last 0.5 s). The playhead is a `line()` in the current stroke, drawn
  only while the sound plays.
- **Spectrogram.** One 1 024-point FFT (the same code as `spectrum()`) for each pixel column, at the
  column's centre. Rows are log frequency from 40 Hz to 16 kHz (or the sound's top frequency). A row that
  covers whole bins takes the loudest one, a narrower row reads between bins, as `spectrum()` does.
  Loudness is decibels from -60 up to 0 (a full-strength tone), mapped to 0 to 1 and squared, so a clear note
  stands out from its spread. The brightness scales
  the **current fill**, so the default is grey and `f.fill("orange")` gives orange on black. This was
  simpler than a built-in colour ramp, and the learner already knows how to change it. A 12-second sound at
  400 by 200 takes about 0.7 s in plain Python. Low rows are blurry because one bin is 43 Hz wide.
- **Pitch line.** The history is a list of `(clock time, hertz or None)` kept on the source as
  `_pitch_history`. One reading is added for each frame (every call in a script, where the frame number is 0),
  readings older than 30 s are dropped, and the line shows the last `seconds`. `None` and a wait of more than
  0.3 s break the line. The time is `sound.clock`, the same injectable clock the sound uses.

## Not here

- Live synthesis, filters and effects other than `reverb`, sampled instruments (ADR-006). ADSR came in S-118.
- Polyphonic pitch (several notes at once, each with its own octave). Onsets, beats, chroma, chords and key are in [Music_Analysis_Note.md](Music_Analysis_Note.md) (S-112, S-113).
- A pluck inside `melody()` (A3 gives `melody()` the five waves only).

## Open points

- `sequence()` and `mix()` use the samples as they are. A volume or pan set on an input sound is not carried
  into the result.
- A `pitch()` window that is part silence (the first 2 048 samples of a sound) can give a wrong note for a moment.
