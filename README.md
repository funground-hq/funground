# funground

[![CI](https://github.com/funground-hq/funground/actions/workflows/ci.yml/badge.svg)](https://github.com/funground-hq/funground/actions/workflows/ci.yml)

**Creative coding for learners.** funground is a small Python library for drawing and animation,
in the spirit of [Processing](https://processing.org), [p5.js](https://p5js.org) and
[DrawBot](https://www.drawbot.com). You write a short Python file, run it, and a window opens with
your picture in it.

> **Status: pre-release.** The first release, 0.1, will be published on PyPI as `funground`.
> Until then, install from this repository (below). Names may still change before 0.1.

**Documentation:** start at the [documentation front door](https://github.com/funground-hq/funground/blob/v0.1.0/docs/README.md).

```python
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("tomato")
    f.circle(f.mouse_x, f.mouse_y, 80)


f.run()
```

## Install

You need Python 3.11 or newer. The [release notes](https://github.com/funground-hq/funground/blob/v0.1.0/docs/releases/0.1.0.md)
of funground 0.1.0 list what has not yet been tried by hand.

```
python -m pip install funground
```

- **Windows:** nothing else is needed.
- **macOS:** usually nothing else. If the install fails while building `pycairo`, run
  `brew install cairo pkg-config` first.
- **Linux:** install the Cairo library first, for example on Debian or Ubuntu:
  `sudo apt install libcairo2-dev pkg-config python3-dev`.

## Learn

- [User Guide](https://github.com/funground-hq/funground/blob/v0.1.0/docs/guide/README.md): chapters from your first sketch to animation, interaction,
  text, pictures and saving your work.
- [Examples Gallery](https://github.com/funground-hq/funground/blob/v0.1.0/docs/gallery/README.md): every feature shown in a small sketch, with its picture.
- See every example in a window: `python -m funground.gallery`
- [Quick Reference](https://github.com/funground-hq/funground/blob/v0.1.0/docs/reference/Quick_Reference.md): every function on one page.
- [API reference](https://github.com/funground-hq/funground/blob/v0.1.0/docs/reference/API.md): every name, with its arguments and an example.
- [All the documentation](https://github.com/funground-hq/funground/blob/v0.1.0/docs/README.md): one page that links everything, in the order you need it.

## What it can do

Shapes, rounded corners, curves and paths, with path booleans (union, difference and more); colour,
gradients, blend modes and shadows; transforms; text with alignment, text boxes, ligatures, mixed
styles and fonts; animation and loop control; mouse and keyboard events; sliders, checkboxes and
buttons; noise and randomness; vectors; pictures, SVG drawings, pixels and filters; off-screen
graphics; sound (play a tune, read its volume, listen through the microphone, and learn with it: draw a wave and hear it, compose and save, ear training, a piano roll); and saving as PNG, PDF (with real text and several
pages), SVG, numbered frames, or an animated GIF or MP4. Text is drawn the same way on every
computer. PDF and SVG output stays sharp at any size.

## How it is built

funground draws with [Cairo](https://www.cairographics.org) and opens its window with
[pygame-ce](https://pyga.me). The project is run as a small software process: sprints with
reviews, a decision log and architecture decision records. See [docs/PROCESS.md](https://github.com/funground-hq/funground/blob/v0.1.0/docs/PROCESS.md),
[docs/Roadmap.md](https://github.com/funground-hq/funground/blob/v0.1.0/docs/Roadmap.md) and [docs/design/](https://github.com/funground-hq/funground/blob/v0.1.0/docs/design/).
To contribute, start with the [developer documentation](https://github.com/funground-hq/funground/blob/v0.1.0/docs/developer/README.md).

## Licence

funground is licensed under the **GNU Lesser General Public License, version 2.1 only**
(`LGPL-2.1-only`), the same family as p5.js, Processing's core library and pygame-ce. See
[LICENSE](https://github.com/funground-hq/funground/blob/v0.1.0/LICENSE). In short: you may use funground in any project, under any licence. If you
change funground itself and share the result, share those changes under the LGPL too.

**Example code is freer still.** The sketches in [examples/](https://github.com/funground-hq/funground/blob/v0.1.0/examples/README.md) and the code in the
guide are public domain (CC0): copy them into your own work with no conditions.

funground's dependencies and the bundled DejaVu fonts **keep their own licences**. They are listed
in [THIRD_PARTY_LICENSES.md](https://github.com/funground-hq/funground/blob/v0.1.0/THIRD_PARTY_LICENSES.md).

## Credits

Where the software, sound methods, raga data, fonts and example ideas come from is in
[CREDITS.md](https://github.com/funground-hq/funground/blob/v0.1.0/CREDITS.md). funground is developed with AI assistance; [AI-USAGE.md](https://github.com/funground-hq/funground/blob/v0.1.0/AI-USAGE.md)
describes how.
