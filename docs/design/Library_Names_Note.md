# The names in the sound, sangeet and camera libraries (D-123)

**Status:** proposed 28 October 2026; accepted 29 October 2026 (D-123, option a, with the callable module type for `f.camera()`). Needed before S-246 and S-247 are built. Follows D-120 and
[ADR-007](ADR-007-core-and-libraries.md), whose rule 5 says the names of each library go to the maintainer before
building.

## Context

D-120 moves 27 names off `f` into three libraries that a sketch imports:

```python
import funground as f
from funground import sound
```

Moving is the one chance to drop a word the library's name already says: `sound.load()` reads better than
`sound.load_sound()`. Every other name should stay as it is, so that a learner who knows 0.1 recognises it. No meaning
changes: each function takes the same arguments and returns the same thing. Only the spelling of the call changes.

Measured today: `f` has 210 public names (not 211, as D-120's note says). It will have 186 after S-246 and 183 after
S-247.

## Proposed names

Changes are in **bold**. Everything else keeps its 0.1 name.

### `sound` (18 names)

| Today | Proposed | Why |
|---|---|---|
| `f.create_sound(samples, rate=44100)` | **`sound.create(samples, rate=44100)`** | the library says "sound" |
| `f.load_sound(path)` | **`sound.load(path)`** | the same; matches `load_image` and `load_font`, whose words name what they load |
| `f.tone`, `f.note`, `f.pluck`, `f.drone`, `f.melody` | `sound.tone`, `sound.note`, `sound.pluck`, `sound.drone`, `sound.melody` | each makes a sound; the word says which kind |
| `f.sequence`, `f.mix` | `sound.sequence`, `sound.mix` | |
| `f.chord_notes`, `f.note_to_frequency`, `f.frequency_to_note` | unchanged, on `sound` | they return names and numbers, not sounds; the full words say so |
| `f.microphone`, `f.microphones` | `sound.microphone`, `sound.microphones` | the library is sound, not the microphone, so the word stays |
| `f.draw_wave`, `f.draw_spectrum`, `f.draw_pitch_line`, `f.spectrogram` | unchanged, on `sound` | `draw_` says it draws on the canvas, as in the core |

### `sangeet` (6 names)

| Today | Proposed |
|---|---|
| `f.raga`, `f.ragas`, `f.match_ragas` | `sangeet.raga`, `sangeet.ragas`, `sangeet.match_ragas` |
| `f.tala`, `f.tala_info`, `f.talas` | `sangeet.tala`, `sangeet.tala_info`, `sangeet.talas` |

All six are unchanged. `tala()` makes a sound while `raga()` returns the raga's facts, and `tala_info()` gives the
tala's facts. That asymmetry is a design question of its own, and moving the names is not the place to change meaning.
`drone` and `melody` (with `sa=` and `tuning=`) stay in `sound`, as D-120 placed them: any music uses them.

### `camera` (3 names)

| Today | Proposed | Why |
|---|---|---|
| `f.camera(name=None)` | **`camera.open(name=None)`** | `camera.camera()` repeats itself; `open` says a camera starts |
| `f.cameras()` | **`camera.names()`** | it returns the cameras' names; `camera.list()` was the other candidate, but `list` is a Python word |
| `f.load_clip(path)` | `camera.load_clip(path)` | unchanged: `camera.load()` would not say that it reads a GIF or WebP clip, not a camera |

A sketch reads:

```python
from funground import camera

cam = camera.open()
```

The guide always names the object `cam`. Writing `camera = camera.open()` would hide the library, and the error a
learner then gets is checked in S-247's tests.

## A moved name used on `f`

D-120 rule 4: `f.note(...)` gives one plain sentence, never a bare `AttributeError`.

> f.note() has moved to the sound library: add `from funground import sound` and write sound.note().

For `f.load_sound` the sentence names `sound.load()`. It is made by `funground.__getattr__` from one table of the 27
names, and it applies to the desktop and to Play.

**The camera needs care.** Once `funground/camera/` is a package and has been imported, `f.camera` *is* that package.
Old code that calls `f.camera()` would then get Python's own `TypeError: 'module' object is not callable`. There are
two ways out:

1. **The camera library's module type is callable and raises the sentence:** "f.camera() has moved: add `from funground
   import camera` and write camera.open()". This uses Python's documented way of giving a module its own class
   (`sys.modules[__name__].__class__`, since Python 3.5). It is one small class with a comment.
2. **Accept the bare error.** No user has run `f.camera()`: it was never released (D-120).

Recommendation: **1**, because the course's camera lessons and old notes will say `f.camera()` for a while, and a
learner deserves the sentence. It is tested on its own.

## Options

- **Keep the names as they are** (`sound.create_sound`, `sound.load_sound`, `camera.camera`, `camera.cameras`): no
  new spelling to learn, but they repeat the library's name.
- **a. The table above** (recommended): four names change (`create`, `load`, `open`, `names`); the rest is unchanged.
- **b. Shorter still:** also `sound.chord` for `chord_notes`, `sound.wave` for `draw_wave` and `sangeet.match` for
  `match_ragas`. Shorter, but `wave` is already an argument (`wave="sine"`), and `chord` sounds as if it makes a sound.

## Trade-offs

| | Keep | a | b |
|---|---|---|---|
| Names that change spelling beyond the prefix | 0 | 4 | 7 |
| Says something twice (`camera.camera()`) | 3 names | none | none |
| A 0.1 learner recognises it | all | all but 4 | all but 7 |
| Clashes with a Python word or an argument | none | none (`names`, not `list`) | `wave` |

## Recommendation: a

**Why:** it removes only the repetition the move creates, so every other name is the one the guide already teaches.

**What would change it:** if the maintainer prefers "every name moves exactly as it is", Keep is consistent and simplest.
`camera.camera()` is its one awkward call.
