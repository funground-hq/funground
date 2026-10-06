# Third-party licences

Where each piece of software, method, data set, font and idea comes from is in [CREDITS.md](CREDITS.md). This page is about licences.

funground itself is licensed under the **GNU Lesser General Public License, version 2.1 or (at
your option) any later version** (`LGPL-2.1-or-later`); see [LICENSE](LICENSE). The software it
builds on keeps its own licence, listed here. Where the two differ, each component's own licence
governs that component.

## Example code

The sketches in `examples/` and the code blocks in the User Guide and Quick Reference are **not**
under the LGPL: they are dedicated to the public domain under **CC0 1.0**
([examples/LICENSE](examples/LICENSE)), so learners can reuse them freely. They are original to
funground; see [docs/qa/Example_Provenance.md](docs/qa/Example_Provenance.md).

## Included in funground

These are part of the funground package itself.

| Component | Where | Licence | Notes |
|---|---|---|---|
| DejaVu Sans fonts (Regular, Bold, Oblique, Bold Oblique), version 2.37 | `funground/fonts/` | Bitstream Vera Fonts licence; DejaVu's own changes are in the public domain | Full text in `funground/fonts/DejaVu-LICENSE.txt`, shipped with the package. The fonts may not be sold on their own, and a modified font must be renamed. |
| Noto Emoji (static instance at weight 400 of the variable font, version 3.002), Noto Sans Symbols 2, Noto Sans Devanagari | `funground/fonts/` | SIL Open Font License 1.1 (© Google LLC; © The Noto Project Authors) | Fallback fonts for letters the current font does not have (contract T18). Full text and copyright lines in `funground/fonts/Noto-OFL.txt`, shipped with the package. None declares a Reserved Font Name. The fonts may not be sold on their own. |
| Noise function | `funground/noise.py` | LGPL-2.1, from p5.js (© the p5.js contributors) | A Python translation of p5.js's `noise()`, `noiseSeed()` and `noiseDetail()`, so seeded values match p5 exactly. Source: <https://github.com/processing/p5.js> |
| Colour-name table | `funground/_colornames.py` | Derived from pygame-ce's colour table (LGPL-2.1), which lists the X11 colour names from `rgb.txt` (X11/MIT-style licence) | Names and RGB values only |
| DejaVu Sans Mono font, version 2.37 | `examples/gallery/text/fonts/` (repository only, not in the installed package) | Bitstream Vera Fonts licence, as above | Used by one gallery example to show `load_font`; its licence file sits beside it. |

## Installed alongside funground

pip installs these as separate packages. funground imports them and includes none of their code.
Their licences apply to them as installed.

| Package | Licence | Includes |
|---|---|---|
| [pygame-ce](https://pyga.me) | LGPL-2.1 | [SDL](https://www.libsdl.org) (zlib licence) and other libraries in its wheels, each under its own licence |
| [pycairo](https://github.com/pygobject/pycairo) | LGPL-2.1-only or MPL-1.1 | [Cairo](https://www.cairographics.org) (LGPL-2.1 or MPL-1.1) and its dependencies in the wheels |
| [fontTools](https://github.com/fonttools/fonttools) | MIT | — |
| [uharfbuzz](https://github.com/harfbuzz/uharfbuzz) | Apache-2.0 | [HarfBuzz](https://harfbuzz.github.io) (Old MIT licence) |
| [skia-pathops](https://github.com/fonttools/skia-pathops) | BSD-3-Clause | a cut-down build of [Skia](https://skia.org)'s path code (BSD-3-Clause) |
| [svgelements](https://github.com/meerk40t/svgelements) | MIT | — |
| [pypdf](https://github.com/py-pdf/pypdf) | BSD-3-Clause | — |
| [Pillow](https://pillow.readthedocs.io) (optional, `funground[extras]`) | MIT-CMU (formerly called HPND) | Used for some picture filters when it is installed; funground works without it |
| [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) (optional, `funground[video]`) | BSD-2-Clause; the ffmpeg program it bundles is a GPLv3 build, run as a separate program and never linked | — |

The licence versions shown are those declared by the releases funground is tested with
(pygame-ce 2.5.8, pycairo 1.29.1, fontTools 4.66, uharfbuzz 0.56). Always check the package you
actually install.

## Inspirations, no code taken

funground borrows ideas and function names from these projects but none of their code, apart from
the noise function above:

- [Processing](https://processing.org): core library LGPL-2.1.
- [p5.js](https://p5js.org): LGPL-2.1.
- [DrawBot](https://www.drawbot.com): BSD-style licence.
- [The Nature of Code](https://natureofcode.com/) (Daniel Shiffman): a book whose ideas on motion and forces the examples
  resemble; its example collections were used only as a comparison set for the originality check.

The methods, books and papers behind the sound and the raga data are credited in [CREDITS.md](CREDITS.md).
