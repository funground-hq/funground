# funground

[![CI](https://github.com/funground-hq/funground/actions/workflows/ci.yml/badge.svg)](https://github.com/funground-hq/funground/actions/workflows/ci.yml)

**Creative coding for learners.** funground is a small Python library for drawing and animation,
in the spirit of [Processing](https://processing.org), [p5.js](https://p5js.org) and
[DrawBot](https://www.drawbot.com). You write a short Python file, run it, and a window opens with
your picture in it.

> **Status: pre-release.** The first release, 0.1, will be published on PyPI as `funground`.
> Until then, install from this repository (below). Names may still change before 0.1.

> **Built with AI.** funground is developed by Samir Joshi with substantial help from Anthropic's
> Claude, used through Claude Code: most of the code, tests and documentation were written by
> Claude under the maintainer's direction. The maintainer sets the direction, takes every design
> decision, and reviews and signs off each sprint. The full test suite of more than 1,600 tests,
> including pixel-exact images, checks every change. Commits Claude helped write say so in a
> `Co-Authored-By: Claude …` line. See [AI disclosure](#ai-disclosure) below and
> [AI-USAGE.md](AI-USAGE.md) for the full account.

**Documentation:** start at the [documentation front door](docs/README.md).

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

## Install (before 0.1)

You need Python 3.11 or newer.

```
python -m pip install git+https://github.com/funground-hq/funground
```

- **Windows:** nothing else is needed.
- **macOS:** usually nothing else. If the install fails while building `pycairo`, run
  `brew install cairo pkg-config` first.
- **Linux:** install the Cairo library first, for example on Debian or Ubuntu:
  `sudo apt install libcairo2-dev pkg-config python3-dev`.

## Learn

- [User Guide](docs/guide/README.md): chapters from your first sketch to animation, interaction,
  text, pictures and saving your work.
- [Examples Gallery](docs/gallery/README.md): every feature shown in a small sketch, with its picture.
- [Showcase](docs/gallery/SHOWCASE.md): a dozen of the best pictures on one page.
- See every example in a window: `python -m funground.gallery`
- [Quick Reference](docs/reference/Quick_Reference.md): every function on one page.
- [API reference](docs/reference/API.md): every name, with its arguments and an example.
- [All the documentation](docs/README.md): one page that links everything, in the order you need it.

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
reviews, a decision log and architecture decision records. See [docs/PROCESS.md](docs/PROCESS.md),
[docs/Roadmap.md](docs/Roadmap.md) and [docs/design/](docs/design/).
To contribute, start with the [developer documentation](docs/developer/README.md).

## AI disclosure

- **Who does what.** The maintainer, Samir Joshi, decides what funground is and how it behaves. Every
  decision is recorded in [docs/design/Decision_Log.md](docs/design/Decision_Log.md). Claude proposes
  options and recommendations, writes code, tests and documentation, and runs the checks. The
  maintainer reviews each sprint before it closes.
- **Models.** The commit history names the models that helped:
  - Claude Fable 5.1;
  - Claude Opus 5;
  - Claude Opus 5.5;
  - Claude Sonnet 5, as a sub-agent for well-specified stories, reviewed by the main model before
    commit.

  How work is split between models is described in [docs/PROCESS.md](docs/PROCESS.md), under
  "Who does what".
- **How changes are checked.** Nothing is merged without the full test suite passing:
  - the public API contract;
  - behaviour pinned in [docs/design/Semantic_Contract.md](docs/design/Semantic_Contract.md);
  - drawing-operation snapshots;
  - pixel-exact golden images.
- **Attribution.** Commits written with Claude's help end with a `Co-Authored-By: Claude …` line,
  so GitHub shows Claude as a co-author.
- **The full account,** with the instructions that steer the work and a sprint-by-sprint log, is in
  [AI-USAGE.md](AI-USAGE.md).

## Licence

funground is licensed under the **GNU Lesser General Public License, version 2.1 or later**
(`LGPL-2.1-or-later`), the same family as p5.js, Processing's core library and pygame-ce. See
[LICENSE](LICENSE). In short: you may use funground in any project, under any licence. If you
change funground itself and share the result, share those changes under the LGPL too.

**Example code is freer still.** The sketches in [examples/](examples/README.md) and the code in the
guide are public domain (CC0): copy them into your own work with no conditions.

funground's dependencies and the bundled DejaVu fonts **keep their own licences**. They are listed
in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

## Credits

Who made funground, the software and the sound methods it is built on, where the raga data and fonts
come from, and the ideas the examples build on are in [CREDITS.md](CREDITS.md).
