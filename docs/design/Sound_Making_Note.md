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
- **Waves** are the naive formulas. Square, saw and triangle alias at high notes. That is fine for teaching.
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

- Live synthesis, filters, effects, ADSR with a sustain level, sampled instruments (ADR-006).
- Chord or polyphonic pitch, beat and onset detection, chroma and chords: Sprint 14.
- A pluck inside `melody()` (A3 gives `melody()` the five waves only).

## Open points

- `sequence()` and `mix()` use the samples as they are. A volume or pan set on an input sound is not carried
  into the result.
- A `pitch()` window that is part silence (the first 2 048 samples of a sound) can give a wrong note for a moment.
