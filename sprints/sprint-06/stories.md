# Sprint 6 — Phase 2c: compositing, canvases, text layout, release 0.1

**Dates:** opened 26 Sept 2026 on the maintainer's word. Sprint 5's review awaits sign-off in
parallel.
**Release context (D-019):** this sprint ends Phase 2. Its result is published on PyPI as
**0.1**, the first public release. The D-015 deliverables stand: the code, a **User Guide**, and an
**Examples Gallery** covering every public name.

**Goal:** the remaining pieces a typical p5/Processing sketch or DrawBot single-page composition
needs: text alignment and layout, fonts, gradients, blending and shadows, off-screen canvases,
vectors, frame-sequence export and window control. Then finish the guide and gallery and release.

**Checkpoint:** every existing golden and IR snapshot is unchanged (all additive); every new public
name has a contract row or semantic test, a gallery example with golden and snapshot, and a guide
section; the Phase 2 exit criterion in `themes_and_epics.md` is demonstrated by two ported sketches
(one p5, one DrawBot) in the gallery.

**Working rule from the Sprint 5 retrospective:** write each story's gallery example first.

## Ordering

1. Stories needing no decision: S-055 → S-049 → S-053 → S-050 → S-051 → S-056 → S-057.
2. S-075, the rename to `funground` (D-020), before any more stories, so all later work uses the new name.
3. S-052 and S-054 (D-021, D-022 decided).
4. Close: S-071 (guide), S-072 (gallery), S-039 (CI, needs a git remote), S-073 (release).

## Decisions to take

### D-020 PyPI distribution name — **decided 26 Sept 2026: `funground`, `import funground as f`** (options below kept as presented; the maintainer also weighed funfair, vizzard, vizkid, viswonder, wonderland, funbot, playbot, funlab and playlab — see the decision log)

**Context.** Publishing on PyPI needs a distribution name, the name in `pip install …`. The name
`playground` belongs to Google DeepMind's MuJoCo Playground, which is actively released (0.2.0,
March 2026), so a name transfer is not possible. Its wheel installs the modules
`mujoco_playground` and `learning`, so our `import playground as p` does not clash with it. The
distribution and import names may differ, as with `pip install pillow` / `import PIL` and
`pip install pygame-ce` / `import pygame`. Without a name, S-073 cannot publish.

**Options** (all checked free on PyPI on 26 Sept 2026):
- **A `playground-sketch`**: `pip install playground-sketch`, then `import playground as p`.
- **B `playground2d`**: the same, with a shorter name that says what it draws.
- **C Rename the import too**, for example `sketchplay` everywhere: `import sketchplay as p`.
- **D Do not publish** (current state): learners install from a zip or git.

**Trade-offs.**

| | A `playground-sketch` | B `playground2d` | C new import name | D no PyPI |
|---|---|---|---|---|
| Learner code changes | none | none | every sketch, guide page, example | none |
| Install and import names match | no | no | yes | — |
| Says what it is | "sketch" is p5's and Processing's word | "2d" says 2D, nothing about creative coding | depends on the name | — |
| Effort | one line in `pyproject.toml` | same | a large rename | none |
| Reversible | publishing claims the name for good | same | same | yes |

**Recommendation:** A, `playground-sketch`.
**Why:** it keeps every sketch and document as written, and "sketch" is the word p5, Processing
and our own guide use. Different install and import names are common, and the guide's first page
can say it once. B is equally workable. C only makes sense if you want to drop the name
"playground" altogether.

### D-021 Off-screen canvases and images: one type or two — **decided 26 Sept 2026: A, `create_graphics`**

**Context.** S-052 adds off-screen drawing: make a picture in memory, draw on it with the usual
verbs, then place it on the main canvas. Phase 3 adds `load_image`. The roadmap flagged the
question of whether these are the same kind of object. Deciding now avoids a rename after 0.1 is
public. Processing makes them one family (`PGraphics` is a `PImage`, made with `createGraphics`).
p5.js keeps `p5.Graphics` and `p5.Image` separate but lets `image()` draw both.

**Options.**
- **A One picture type.** `g = p.create_graphics(w, h)` returns a picture you can draw on
  (`g.circle(…)`, `g.fill(…)`). Phase 3's `p.load_image(path)` returns the same type.
  `p.image(g, x, y)` draws either.
- **B Two types.** An off-screen `Graphics` now and a separate `Image` in Phase 3. `p.image()`
  accepts both, and `g.to_image()` converts.
- **C Defer** (current state): no off-screen drawing in 0.1; decide with images in Phase 3.

**Trade-offs.**

| | A one type | B two types | C defer |
|---|---|---|---|
| Concepts to learn | one: a picture | two, plus a conversion | none now |
| Draw on a loaded photo | yes, directly | convert first | — |
| Porting from Processing | matches | extra conversion calls | — |
| Porting from p5 | matches how `image()` is used | matches p5's types | — |
| Vector export (PDF/SVG) | a drawn picture replays as vectors; a loaded one embeds pixels | same | — |
| Risk | the one type grows large in Phase 3 | two types to keep in step | Phase 2 exit criterion unmet for off-screen work |

**Recommendation:** A, one picture type, made with `p.create_graphics(w, h)`.
**Why:** one concept is easier to teach, and it matches Processing. `create_graphics` is the name
both p5 and Processing use. `create_canvas` would mislead p5 users, for whom it makes the main
window. What would change this: if you prefer "canvas" as the word learners see, the type stays
the same and only the function name changes.

### D-022 Bold and italic text — **decided 26 Sept 2026: A, bundle the DejaVu Sans family**

**Context.** S-054 adds font choice and styles. Today one font ships: DejaVu Sans Regular
(757 KB). p5's `textStyle(BOLD)` lets a learner write bold text without finding a font file.
Bundling more fonts changes what the base install contains, which is a decision under our process.

**Options.**
- **A Bundle the family.** Add DejaVu Sans Bold, Oblique and Bold Oblique (about 2 MB more, same
  free licence). `p.text_style("bold")` works everywhere and looks identical everywhere.
- **B Synthesise.** Fake bold (thickened outline) and fake italic (slanted) from the regular font.
  No new files.
- **C Styles only for loaded fonts.** The learner loads `Font-Bold.ttf` themselves; no `text_style`.
- **D No styles** (current state).

**Trade-offs.**

| | A bundle | B synthesise | C loaded only | D none |
|---|---|---|---|---|
| Install size | about +2 MB | +0 | +0 | +0 |
| Looks like real bold and italic | yes | passable; crude at large sizes | yes | — |
| Same on every machine | yes | yes | depends on the learner's file | — |
| p5 `textStyle` ports | yes | yes | no | no |
| Effort | small | moderate | small | none |

**Recommendation:** A, bundle the DejaVu Sans family.
**Why:** real bold and italic look right, cost about 2 MB, and render identically everywhere, which
the golden tests depend on. Loading any other font file comes with S-054 whichever option wins.
What would change this: a hard install-size budget for classrooms.

## Story set

### S-055 Vector — E-27 ✅
*As built:* `playground/vector.py`; contract H5. `cross` returns a number (p5 returns a 3D vector), listed for chapter 14's differences table.
- [x] S-055.1 `p.Vector(x, y)` with p5's meaning: methods change the vector in place and return it
  (`add`, `sub`, `mult`, `div`, `normalize`, `limit`, `set_mag`, `rotate`, `lerp`); queries return
  values (`mag`, `mag_sq`, `heading`, `dist`, `dot`, `cross`, `angle_between`); `copy()`;
  operators `+ - * /` return new vectors; unpacking `x, y = v`; `Vector.from_angle`,
  `Vector.random_2d`. Angles in degrees (D-002)
- [x] S-055.2 Contract row; tests; gallery `motion/` (a mover with velocity and acceleration);
  guide chapter 12 section
*Acceptance:* a p5 "mover" sketch using `createVector`, `add` and `limit` ports by renaming only.

### S-049 Text alignment and metrics — E-15 ✅
*As built:* alignment lives in the drawing state and is resolved by the Sketch, so the renderer and IR meaning are unchanged (a Text op's x, y is always top-left). Contract T7, T8.
- [x] S-049.1 `text_align(horizontal, vertical="top")`: `"left" | "center" | "right"` and `"top" |
  "center" | "baseline" | "bottom"`. The default stays top-left (v0.5 contract). p5's baseline
  default is listed among the differences in chapter 14
- [x] S-049.2 `text_ascent()`, `text_descent()` for the current size
- [x] S-049.3 Contract rows; tests; gallery `text/`; guide chapter 6
*Acceptance:* centred text stays centred when its size or content changes.

### S-053 Multi-line text and text boxes — E-15 ✅
*As built:* the box form is a separate `p.text_box(message, x, y, width, height=None, color=None)` returning the overflow, not extra `p.text()` parameters: `text()`'s v0.5 signature is frozen, and DrawBot uses the name `textBox`. p5's `text(s, x, y, w, h)` ports by renaming. Contract T9, T10.
- [x] S-053.1 `\n` in `p.text()` starts a new line; `text_leading(n)` sets the line spacing
- [x] S-053.2 `p.text(message, x, y, width, height)` wraps words inside the box, honours
  `text_align`, and drops lines that do not fit; the text that did not fit can be recovered, as
  DrawBot's `textBox` returns it
- [x] S-053.3 Contract rows; tests; gallery `text/` (a poster); guide chapter 6
*Acceptance:* a DrawBot `textBox` layout ports with naming changes only.

### S-050 Gradients — E-25 ✅
*As built:* `playground/paint.py` (`Gradient`, `parse_paint`); the list parameter is `colors`, matching `p.color` and `color=`. A gradient is data in the IR; the Cairo renderer makes a pattern in user space. Contract S13.
- [x] S-050.1 `p.linear_gradient(x1, y1, x2, y2, colours, stops=None)` and
  `p.radial_gradient(x, y, r, colours, stops=None)`, usable wherever a fill or stroke colour is
- [x] S-050.2 IR op or style field, omitted when unused so snapshots stay identical; Cairo
  renderer; PDF/SVG export keeps gradients as vectors
- [x] S-050.3 Contract row; tests; gallery `colour/`; guide chapter 4
*Acceptance:* a gradient-filled shape exports to PDF as a vector gradient.

### S-051 Blend modes, opacity, shadow — E-25 ✅
*As built:* 17 blend modes, each exactly a Cairo operator. Opacity multiplies each fill's and stroke's alpha separately, as DrawBot does, so there are no groups and no cost. Shadows are layers of the shape grown outward, at most 12, and stay vector in PDF/SVG, because Cairo has no blur and a pure-Python pixel blur is too slow. They fade evenly from the edge, not as a Gaussian. Contract S14.
- [x] S-051.1 `blend_mode(name)`: `"normal"`, `"multiply"`, `"screen"`, `"overlay"`, `"darken"`,
  `"lighten"`, `"add"`, `"difference"`, `"exclusion"`; `opacity(0–255)` for everything drawn after
- [x] S-051.2 `shadow(dx, dy, blur, colour)` and `no_shadow()`
- [x] S-051.3 Contract rows; tests; gallery `compositing/`; guide chapter 5
*Acceptance:* each blend mode matches Cairo's operator of the same name, pixel-tested.

### S-056 Frame-sequence export — E-19 ✅
*As built:* numbering starts at 1, which ffmpeg's `%04d` reads directly; the folder is created. A test proves the gallery example's 30 frames loop seamlessly. Contract R11.
- [x] S-056.1 `p.save_frames("frames/####.png", count)`: saves the next `count` frames, numbered;
  works headless
- [x] S-056.2 Tests; gallery `saving/`; guide chapter 13, including how to make a GIF or video
  from the frames
*Acceptance:* a headless run writes exactly `count` numbered files.

### S-057 Window control — E-29 ✅
*As built:* the Platform protocol gains `open_full_screen` and `set_cursor`. Headless full screen is a fixed 1920 × 1080. The frozen Spike 08 platform was not updated. Tested on the real pygame platform with SDL's dummy driver; not tried on a physical full screen. Contract R12.
- [x] S-057.1 `cursor(kind)` / `no_cursor()`; `full_screen()`; `resize_canvas(w, h)` at run time,
  keeping HiDPI correct
- [x] S-057.2 The headless platform accepts and ignores them; tests; guide chapter 2
*Acceptance:* resizing mid-run keeps drawing sharp on a scaled display.

### S-075 Rename to funground — E-02 *(D-020 decided)* ✅
*As built:* by the Sonnet `story-builder` subagent (first delegated story), reviewed and committed by the main session. `PlaygroundError` also became `FungroundError`. Kept on purpose: the drawn text "Hello, Playground!" in `gallery/text/01_text.py`, because changing it moves pixels and needs a reviewed golden regeneration; and "Coming from Playground 0.5", which names the old version. Follow-ups for S-071/S-073: the Semantic Contract's prose and the root README still say Playground.
- [x] S-075.1 Package folder `playground/` → `funground/`; `pyproject.toml` name `funground`, description no longer "a wrapper around pygame-ce"; `import funground as f` in every example (`examples/`), the guide, the Quick Reference, the README and the tools
- [x] S-075.2 Tests import `funground`; error messages and warnings that say "playground" (e.g. `PlaygroundWarning`) renamed where learners see them; environment variables `PLAYGROUND_*` renamed `FUNGROUND_*`
- [x] S-075.3 Historical records keep the old name: `src_v0.5/`, spikes, earlier sprint folders, ADRs and the decision log are not rewritten; the Roadmap and backlog say "funground" from here on
- [x] S-075.4 Guide chapter 1: install with `pip install funground`; one line warning not to name your own variables `f`
- [x] S-075.5 Full suite green; every golden image and IR snapshot byte-identical (a rename changes no drawing)
*Acceptance:* `grep -ri playground` over the package, examples, guide and tests finds only deliberate historical mentions; nothing learners run says "playground".

### S-054 Fonts and styles — E-15 *(D-022 = A)* ✅
*As built:* by the Sonnet `story-builder` subagent from pinned rows T11/T12; reviewed here, and one duplicated style list removed. DejaVu 2.37 was verified byte-identical to the bundled regular face before the new files were added: Bold 706 KB, Oblique 635 KB, Bold Oblique 643 KB. Known limit: a loaded font's IR key only resolves in the process that loaded it, so replaying saved IR elsewhere needs the file. That matters for the browser track, not for 0.1.
- [x] S-054.1 `p.text_font(path_or_font)` uses a TTF/OTF file; `p.load_font(path)` returns a font
- [x] S-054.2 Bundle DejaVu Sans Bold, Oblique, Bold Oblique (2.37) with the licence; `text_style("normal" | "bold" | "italic" | "bold_italic")`, part of the saved state
- [x] S-054.3 Contract rows; tests; gallery `text/`; guide chapter 6
*Acceptance:* the same text in a loaded font renders identically on every run.

### S-052 Off-screen graphics — E-28 *(D-021 = A)*
- [ ] S-052.1 `g = f.create_graphics(w, h)`: one picture type (Phase 3's `load_image` returns the same type); an off-screen picture with the full drawing vocabulary, its own state and
  transform, drawn onto the canvas with `p.image(g, x, y, w=None, h=None)`
- [ ] S-052.2 IR: a picture's ops are recorded separately and rendered to their own surface;
  vector export replays them as vectors
- [ ] S-052.3 Contract rows; tests; gallery `compositing/`; a new guide chapter, "Pictures"
*Acceptance:* a Processing `PGraphics` trail effect ports by renaming only.

### S-071 User Guide completed — E-22
- [ ] S-071.1 Every chapter complete; chapter 14 "Coming from p5/Processing" with the table of
  deliberate differences; chapter 15 "Coming from DrawBot"; both link ADR-003
- [ ] S-071.2 First page: how to install (`pip install <D-020 name>`) and run the first sketch
*Acceptance:* the guide test passes and no chapter says "planned".

### S-072 Examples Gallery completed — E-22
- [ ] S-072.1 Coverage test green for all of `__all__` (it already is; keep it so)
- [ ] S-072.2 A curated showcase page; the two Phase 2 exit ports (one p5 sketch, one DrawBot page)
*Acceptance:* the showcase renders from the code, headless.

### S-039 CI first run — E-02 *(carried; blocked until a git remote exists)*

### S-073 Release 0.1 on PyPI — E-02 *(needs D-020 and S-039)*
- [ ] S-073.1 Packaging: distribution name per D-020; description no longer "a wrapper around
  pygame-ce"; classifiers, licence, README; fonts and licence files inside the wheel
- [ ] S-073.2 Quick Reference renamed for 0.1; changelog from v0.5; version `0.1.0`
- [ ] S-073.3 Build the wheel and sdist; install into a clean venv and run the gallery headless;
  `twine check`; publish to TestPyPI, then PyPI **only with the maintainer's go-ahead**; tag
*Acceptance:* `pip install <name>` in a fresh venv runs the first guide sketch.

## Out of scope this sprint
Images and pixels, documents and pages, path booleans, rich typography, SVG, sound, and motion
export beyond frame sequences (Phase 3, releases 0.2 onward). ADR-003 lists what is out altogether.
