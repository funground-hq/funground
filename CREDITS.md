# Credits and sources

This is the one page to read if you ask "where did this come from?" It says who made funground,
what it is built on, where the sound methods, the raga and tala facts, the fonts and the pictures
come from, and which well-known ideas the examples build on.

It credits in short lines, in our own words. It does not copy text from the sources. The
**licences** are in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md). How the AI was used is in
[AI-USAGE.md](AI-USAGE.md). We checked each reference below against the publisher's or a library
catalogue's record when we wrote this page. If you find a mistake, please say so.

## The people and the AI

funground is made by its maintainer, **Samir Joshi**, who sets the goals, takes every decision and
reviews the work. AI assistants (Anthropic's Claude, through Claude Code) wrote much of the code,
the examples, the tests and the documentation, under the maintainer's direction. [AI-USAGE.md](AI-USAGE.md) says
how, model by model, and every decision is in
[docs/design/Decision_Log.md](docs/design/Decision_Log.md).

The starting point, the *playground* v0.5 package, was itself written by another AI assistant at the
maintainer's direction.

## Software funground is built on

funground installs these as separate packages and uses them; it includes none of their code. Versions
are the minimums in `pyproject.toml`. Licences are in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

| Package | Needed version | What it does for funground |
|---|---|---|
| [pygame-ce](https://pyga.me) and [SDL](https://www.libsdl.org) | 2.5 or later | The window, mouse and keyboard, picture loading, the sound mixer and the microphone |
| [pycairo](https://github.com/pygobject/pycairo) and [Cairo](https://www.cairographics.org) | 1.27 or later | Draws the shapes, and writes the PDF and SVG files |
| [HarfBuzz](https://harfbuzz.github.io) through [uharfbuzz](https://github.com/harfbuzz/uharfbuzz) | 0.45 or later | Text shaping: ligatures, scripts such as Devanagari, font features |
| [fontTools](https://github.com/fonttools/fonttools) | 4.55 or later | Reads fonts (glyph outlines, variable-font axes, which letters a font has) and cuts the font pieces that go into PDF and SVG files |
| [skia-pathops](https://github.com/fonttools/skia-pathops) (path code from [Skia](https://skia.org)) | 0.9 or later | Path booleans: union, intersection, difference, xor, remove-overlap |
| [svgelements](https://github.com/meerk40t/svgelements) | 1.9 or later | Reads SVG files |
| [pypdf](https://github.com/py-pdf/pypdf) | 5 or later | Edits the PDF files funground writes: layers, real selectable text, and the document's details |
| [Pillow](https://pillow.readthedocs.io) | 11 or later, optional (`funground[extras]`) | Used for some picture filters when it is installed; funground works without it |
| [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) and [FFmpeg](https://ffmpeg.org) | 0.5 or later, optional (`funground[video]`) | Writes MP4 video; FFmpeg runs as a separate program |

## Sound

**Which libraries.**

- **Playing and mixing** go through pygame-ce's mixer, which uses SDL's audio.
- **The microphone** goes through pygame-ce's `pygame._sdl2.audio` module (see
  `funground/microphone_input.py`). That module is marked experimental by pygame-ce.
- **Making sound, analysing it and the effects** are funground's own pure-Python code. They use only
  Python's `math`, `cmath` and `random`: no numpy and no audio library. The files are
  `funground/synth.py`, `analysis.py`, `sound.py`, `sound_views.py` and `hindustani.py`.

**The methods.** These are textbook or published methods. We list each one with a reference. The
code is funground's own; where it differs from the paper, the design notes say so
([Sound making](docs/design/Sound_Making_Note.md), [Music analysis](docs/design/Music_Analysis_Note.md)).

| What funground does | The method | Reference |
|---|---|---|
| `pluck()` and the tanpura-like `drone()`: a plucked string | Karplus-Strong: a burst of noise goes round a loop that averages neighbours | K. Karplus and A. Strong, "Digital synthesis of plucked-string and drum timbres", *Computer Music Journal* 7(2), 1983, pp. 43-55. [doi:10.2307/3680062](https://doi.org/10.2307/3680062) |
| Tuning the plucked string to the exact pitch | A fractional delay made with an all-pass filter, as in the extensions to Karplus-Strong | D. A. Jaffe and J. O. Smith, "Extensions of the Karplus-Strong plucked-string algorithm", *Computer Music Journal* 7(2), 1983. [doi:10.2307/3680063](https://doi.org/10.2307/3680063) |
| Square, saw, triangle and soft waves | A one-period table built by adding the harmonics (additive synthesis), stopping below half the sample rate so high notes do not alias. A well-known technique; no single paper | none needed |
| Note envelopes | Attack, decay, sustain, release (ADSR), a standard synthesiser idea; no single paper | none needed |
| `reverb()` | A Schroeder-style reverberator: feedback comb filters side by side, then all-pass filters in a row | M. R. Schroeder, "Natural sounding artificial reverberation", *Journal of the Audio Engineering Society* 10(3), 1962, pp. 219-223. [AES e-library](https://aes.org/publications/elibrary-page/?id=849) |
| `spectrum()` | A fast Fourier transform (radix-2, Cooley-Tukey) of a Hann-windowed frame; the Hann window is a standard taper | J. W. Cooley and J. W. Tukey, "An algorithm for the machine calculation of complex Fourier series", *Mathematics of Computation* 19(90), 1965, pp. 297-301. [doi:10.1090/S0025-5718-1965-0178586-1](https://doi.org/10.1090/S0025-5718-1965-0178586-1) |
| `pitch()` and the tuner | Normalised autocorrelation, with a parabola through the peak for a finer answer. funground does **not** use YIN | L. R. Rabiner, "On the use of autocorrelation analysis for pitch detection", *IEEE Transactions on Acoustics, Speech, and Signal Processing* 25(1), 1977, pp. 24-33. [doi:10.1109/TASSP.1977.1162905](https://doi.org/10.1109/TASSP.1977.1162905) |
| `onsets()` and `is_onset()` | Spectral flux: how much the spectrum rose from one frame to the next | J. P. Bello, L. Daudet, S. Abdallah, C. Duxbury, M. Davies and M. B. Sandler, "A tutorial on onset detection in music signals", *IEEE Transactions on Speech and Audio Processing* 13(5), 2005, pp. 1035-1047. [doi:10.1109/TSA.2005.851998](https://doi.org/10.1109/TSA.2005.851998) |
| `tempo()` and `beats()` | Autocorrelation of the onset strength, weighted towards tempi near 120 beats a minute, in the manner of Ellis's beat tracker; funground then fine-tunes the tempo and the beat positions from the onset times | D. P. W. Ellis, "Beat tracking by dynamic programming", *Journal of New Music Research* 36(1), 2007, pp. 51-60. [doi:10.1080/09298210701653344](https://doi.org/10.1080/09298210701653344) |
| `chroma()` and `chord()` | A twelve-note "pitch class" profile, matched against chord templates | T. Fujishima, "Realtime chord recognition of musical sound: a system using Common Lisp Music", *Proceedings of the International Computer Music Conference*, 1999, pp. 464-467. [ICMC archive](https://quod.lib.umich.edu/i/icmc/bbp2372.1999.446/--realtime-chord-recognition-of-musical-sound-a-system-using?view=image) |
| `key()` | The Krumhansl-Schmuckler key-finding method: chroma compared with major and minor key profiles | C. L. Krumhansl and E. J. Kessler, "Tracing the dynamic changes in perceived tonal organization in a spatial representation of musical keys", *Psychological Review* 89(4), 1982, pp. 334-368. [doi:10.1037/0033-295X.89.4.334](https://doi.org/10.1037/0033-295X.89.4.334). The same ratings are in C. L. Krumhansl, *Cognitive Foundations of Musical Pitch* (Oxford University Press, 1990) |
| Just intonation (`tuning="just"`, the drone) | The usual twelve-note 5-limit ratios from Sa (1, 16/15, 9/8, 6/5, 5/4, 4/3, 45/32, 3/2, 8/5, 5/3, 9/5, 15/8) | [Five-limit tuning](https://en.wikipedia.org/wiki/Five-limit_tuning) lists the same set |
| `drone()` | A tanpura has four strings, usually tuned Pa, Sa, Sa, Sa with one Sa an octave lower; funground plucks four such strings in turn | [Tanpura](https://en.wikipedia.org/wiki/Tanpura) |
| Meend (a glide between notes) | A smoothstep curve in log-frequency; a common choice, no source | none needed |

Two limits to know. The Krumhansl-Kessler numbers in `funground/analysis.py` were checked against
published copies on 4 October 2026 (see the code comment there); an earlier line in the
[Music analysis note](docs/design/Music_Analysis_Note.md) still says they were written from memory.
And these are simple versions of the methods, tuned to run in plain Python, so do not treat the
results as research-grade.

## Indian music: ragas and talas

The table in `funground/data/ragas.json` has **13 ragas** and **6 talas**: Teentaal, Ektaal,
Jhaptaal, Rupak, Dadra and Keherwa. It was built in October 2026. Each fact was checked against the
pages below while building it, rather than written from memory, and each raga and tala lists the
sources that back it (the `sources` list of its entry, with a note on which facts each one supports).
[Ragas for learners](docs/design/Ragas_Note.md) is the full account.

**The sources**

| Source | Used for |
|---|---|
| [Tanarang: raga pages by Acharya Vishwanath Rao Ringe "Tanarang"](https://tanarang.com/) | Thaat, swaras, aroha, avaroha, main phrases, vadi, samvadi, time |
| [SwarGanga Music Foundation: raag and taal pages](https://www.swarganga.org/) | The same for ragas; beats, divisions, tali, khali and theka for talas |
| [Rajan Parrikar: essays on Hindustani ragas](https://www.parrikar.org/hindustani/) | Phrases, history and where teachers disagree |
| [Wikipedia](https://en.wikipedia.org/) raga and tala articles | A third check |
| [NCERT, *Kriti* (class 8), chapter 7, Indian Classical Music](https://ncert.nic.in/textbook/pdf/hekr107.pdf) | Asavari |
| [NIOS, *Hindustani Music (242)*, Practical Book 2, chapter 4, Description of Talas](https://www.nios.ac.in/media/documents/Hindustani_Music_242/hindustanimusicpracticalbook2/ch_HMB2-4.pdf) | Theka and structure of five talas |
| [Darbar: raga guide pages](https://darbar.org/raga/) | Vadi, samvadi, aroha, avaroha and time for four ragas |
| [David Courtney, Chandrakantha.com: index of tals](https://chandrakantha.com/music-and-dance/i-class-music/index-of-tals/) | Tala structure |
| [University of Washington, Music 428: thekas](https://sites.math.washington.edu/~gangolli/Music428Thekas.html) | Thekas for all six talas |
| [ITC Sangeet Research Academy: Samay Raga](https://www.itcsra.org/samay-raga) | Time of day, as a weaker check |
| [IndianClassicalMusic.com: Bhoop, Deshkar and Shuddh Kalyan](https://www.indianclassicalmusic.com/bhoop-deshkar-shuddhkalyan) | Bhupali and Deshkar |
| [Raag Hindustani (Sadhana)](https://raag-hindustani.com/) | Raga pages, with a lakshan geet for Durga |
| [Ragajunglism](https://ragajunglism.org/ragas/) | A weaker check for single facts |

**The books those sources cite.** Several of the sources above, mostly Wikipedia and Parrikar,
rest on these books. funground's maintainer and the AI did **not read them directly**; they are
cited through the sources above, which are the only way we saw them
([Ragas note](docs/design/Ragas_Note.md#1-the-table-and-its-sources) says so):

- Joep Bor (editor) and others, *The Raga Guide: A Survey of 74 Hindustani Ragas* (Nimbus Records,
  1999). [Wikipedia's article on the book](https://en.wikipedia.org/wiki/The_Raga_Guide).
- Walter Kaufmann, *The Ragas of North India* (Indiana University Press, 1968).
  [Library record](https://search.worldcat.org/oclc/11369).
- V. N. Bhatkhande, *Hindustani Sangeet Paddhati* and *Kramik Pustak Malika*: the early-twentieth-century
  works that set out the thaat system and the notation most sources follow.

**When sources disagree.** Teachers and gharanas differ, so the table gives the most common form
and the entry's `notes` field says what else you may be taught and which source says what. The list
of disagreements (Kafi's samvadi, Bhairavi's vadi, the time of Marwa and others) is in section 1 of
the [Ragas note](docs/design/Ragas_Note.md#1-the-table-and-its-sources). The note also says that a
reviewer with the books should check the pakads first. **A teacher is still the best authority.**
If your teacher says something different, follow your teacher.

**Background reading** for the sound side, and for what exists in this area, is in the
[Music research note](docs/design/Music_Research_Note.md), section 6.

## Drawing and maths

- **Noise.** `f.noise()` is a Python translation of p5.js's `noise()`, `noiseSeed()` and
  `noiseDetail()` (the p5.js contributors, LGPL-2.1), so seeded values match p5. It is smooth noise on
  a lattice that mixes several octaves, in the tradition of Ken Perlin's noise: K. Perlin, "An image
  synthesizer", *SIGGRAPH '85 Proceedings* (Computer Graphics 19(3)), 1985, pp. 287-296,
  [doi:10.1145/325165.325247](https://doi.org/10.1145/325165.325247). p5's version is its own simpler
  form (cosine-smoothed lattice values), not Perlin's later "improved noise". The code is
  `funground/noise.py`.
- **Named colours.** The table of colour names comes from pygame-ce's colour table, which lists the X11
  colour names from `rgb.txt`. Names and values only.
- **Colour models.** `hsb()` and `hsl()` use Python's standard `colorsys` module for the conversions.
- **Path booleans** (`union`, `intersection`, `difference`, `xor`, `remove_overlap`) come from Skia's
  path code, through [skia-pathops](https://github.com/fonttools/skia-pathops).
- **Text shaping** is done by [HarfBuzz](https://harfbuzz.github.io), through uharfbuzz.
- **Curves.** `bezier()` draws a Bezier curve, named for the engineer Pierre Bezier;
  [Bezier curve](https://en.wikipedia.org/wiki/B%C3%A9zier_curve) tells the history (Paul de Casteljau
  found them first, at Citroen).
- **Springs and forces.** The examples that use springs follow Hooke's law: the pull is in proportion
  to the stretch ([Hooke's law](https://en.wikipedia.org/wiki/Hooke%27s_law)).

funground does not name or credit any other easing or curve formula, because the code does not use
one by name.

## Fonts

| Font | Where | Licence | Link |
|---|---|---|---|
| DejaVu Sans (Regular, Bold, Oblique, Bold Oblique) 2.37, and DejaVu Sans Mono (one gallery example) | `funground/fonts/` and `examples/gallery/text/fonts/` | Bitstream Vera Fonts licence; DejaVu's own changes are public domain | [DejaVu fonts](https://dejavu-fonts.github.io/). They are based on Bitstream's Vera fonts |
| Noto Emoji | `funground/fonts/` | SIL Open Font License 1.1 | [googlefonts/noto-emoji](https://github.com/googlefonts/noto-emoji) |
| Noto Sans Symbols 2 and Noto Sans Devanagari | `funground/fonts/` | SIL Open Font License 1.1 | [Noto fonts](https://notofonts.github.io/) |

The full licence texts ship with the fonts (`DejaVu-LICENSE.txt` and `Noto-OFL.txt`).

## Images and media

funground and its examples bundle very little. Each file, and where it came from:

| File | Where it came from |
|---|---|
| `examples/gallery/images/data/photo.jpg` | **Made by funground.** `make_photo.py`, beside it, draws a small scene with funground and saves it; the JPEG is that picture re-saved. It is not a photograph. CC0. |
| `examples/gallery/images/data/badge.svg` | Written by hand for the gallery (its first lines say so). CC0. |
| `examples/gallery/sound/data/tune.wav` | **Made by Python.** `make_tune.py`, beside it, computes three seconds of sound from note frequencies and writes the WAV. CC0. |
| `funground/data/ragas.json` | The raga and tala table, described above. |
| The pictures in `docs/gallery/images/` and `docs/reference/images/` | Pictures of the examples and reference sketches, saved by funground itself (`tools/make_gallery.py`, `tools/make_reference_images.py`). |
| Sounds in the examples (chimes, drones, tunes) | Made on the spot by funground's own synthesiser. No recorded sound is bundled. |

No photograph, recording or clip-art from another source is in the repository.

## Ideas the examples build on

The examples are not copies of anyone's sketches. Many of them build on a well-known technique,
tradition or game, and this table says which, so the idea is credited. The wording is "builds on the
idea of": we do not claim a particular author's sketch was the model, because it was not.

| Example | The idea or tradition | Where to read about it |
|---|---|---|
| Project 4, Voice-controlled game (`projects/04_voice_game.py`) | The one-input, fly-through-the-gaps game of Flappy Bird (Dong Nguyen, 2013), here steered by the loudness of your voice | [Flappy Bird](https://en.wikipedia.org/wiki/Flappy_Bird) |
| Project 2, Rangoli and mandala (`projects/02_rangoli.py`) | Rangoli, the Indian festival floor art made from patterns that repeat round a centre | [Rangoli](https://en.wikipedia.org/wiki/Rangoli) |
| Project 3, Raga explorer (`projects/03_raga_explorer.py`); `music/04_hear_a_raga.py` | Hindustani ragas: aroha, avaroha, vadi, samvadi, pakad and time of day | [Raga](https://en.wikipedia.org/wiki/Raga); sources above |
| `music/05_tala.py` | Tala: a cycle of beats with sam, tali and khali, and bols | [Tala](https://en.wikipedia.org/wiki/Tala_(music)); sources above |
| `music/03_sing_with_the_drone.py`, `sound/03_sargam_over_a_drone.py`, Project 3 | The tanpura drone under a singer | [Tanpura](https://en.wikipedia.org/wiki/Tanpura) |
| Project 5, Typographic portrait (`projects/05_typographic_portrait.py`) | Pictures made from letters, in the tradition of ASCII art | [ASCII art](https://en.wikipedia.org/wiki/ASCII_art) |
| Project 6, Kinetic type (`projects/06_kinetic_type.py`) | Springs that pull each dot home (Hooke's law), with the mouse pushing the dots away | [Hooke's law](https://en.wikipedia.org/wiki/Hooke%27s_law) |
| Project 7, Scratch-card game (`projects/07_scratch_card.py`) | The scratchcard: a coating you rub off to see what is under it | [Scratchcard](https://en.wikipedia.org/wiki/Scratchcard) |
| Project 8, Flow-field print (`projects/08_flow_field_print.py`) | Flow fields: a grid of angles, here taken from noise, that walkers follow to draw lines. A widely used generative-art technique | Tyler Hobbs, [Flow Fields](https://www.tylerxhobbs.com/words/flow-fields) (2020) |
| `randomness/03_noise.py`; Project 8 | Smooth noise, in the tradition of Perlin noise, as p5.js implements it | See "Drawing and maths" above |
| `motion/01_movers.py`; Project 6 | Moving things with vectors, velocity and forces: the approach taught in *The Nature of Code*. funground's example was written for funground | Daniel Shiffman, [The Nature of Code](https://natureofcode.com/) |
| `lines/03_pixel_art.py` | Pixel art with square blocks; the sprite is named for the "invaders" of 1970s arcade games such as Space Invaders (Taito, 1978; designer Tomohiro Nishikado) | [Space Invaders](https://en.wikipedia.org/wiki/Space_Invaders) |
| `curves/01_curves.py` | Bezier curves | [Bezier curve](https://en.wikipedia.org/wiki/B%C3%A9zier_curve) |
| `compositing/02_graphics.py` | The off-screen picture used for a fading trail, the way Processing's `PGraphics` is used (the example's own comment says so) | [Processing](https://processing.org/) |
| `documents/02_flip_book.py` | The flip book: pages that make a picture move when they are flipped | [Flip book](https://en.wikipedia.org/wiki/Flip_book) |
| `music/02_see_a_chord.py` | Pitch-class (chroma) profiles and chord templates | Fujishima (1999), above |
| `sound/04_tuner.py` | The chromatic tuner, with pitch found by autocorrelation | Rabiner (1977), above |
| `music/09_compose_and_save.py` | The grid or step sequencer, and the pentatonic scale | [Step sequencer](https://en.wikipedia.org/wiki/Music_sequencer); [Pentatonic scale](https://en.wikipedia.org/wiki/Pentatonic_scale) |
| `music/10_ear_training.py` | Ear training: naming the interval between two notes, and in swara mode the swara above Sa | [Ear training](https://en.wikipedia.org/wiki/Ear_training) |
| `music/11_piano_roll.py` | The piano roll: notes as bars, time across and pitch up, as in music software | [Piano roll](https://en.wikipedia.org/wiki/Piano_roll) |

**The code of every example was written for funground and is CC0;
[Example_Provenance](docs/qa/Example_Provenance.md) shows how originality was checked.** The check
found no copied code, compared against nine collections of well-known sketches, and it cannot rule
out every similarity (the page says so). The check looks at written expression, not at ideas; this
table is where the ideas are credited.

## Teaching and tools we learned from

funground borrows ideas and function names, not code, from these projects (apart from the noise
function, above). They are the tools many learners meet first.

- [Processing](https://processing.org/), started by Ben Fry and Casey Reas: the setup-and-draw
  way of working that funground and p5.js share.
- [p5.js](https://p5js.org/), created by Lauren Lee McCarthy in 2013: Processing's ideas for the web,
  and the source of funground's `noise()`.
- [DrawBot](https://www.drawbot.com), by Just van Rossum, Erik van Blokland and Frederik Berlaen: a
  Python tool for drawing, pages and PDFs, which funground's page and document features follow.
- [*The Nature of Code*](https://natureofcode.com/) by Daniel Shiffman: a book on motion, forces and
  nature-inspired code. Its examples are one of the nine collections we compared our examples
  against.

**funground is not affiliated with, endorsed by or sponsored by** Processing, the Processing
Foundation, p5.js, DrawBot, Daniel Shiffman, or any of the other people and projects named on
this page. Names are used only to say where an idea comes from. Funground's
[comparison page](docs/reference/Compared_with_p5_and_DrawBot.md) shows how the names line up.
