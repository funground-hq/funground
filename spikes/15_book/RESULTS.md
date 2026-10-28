# Spike S-225: test chapter results

The test chapter "One shape" (12 pages) was built at both trims with funground as the layout engine. This file holds
the numbers (from `make/measure.py`), what the build found out about funground, and what was not done.

Run it: `.venv/Scripts/python.exe spikes/15_book/make/build.py`, then `.venv/Scripts/python.exe spikes/15_book/make/measure.py`.
Output goes to `spikes/15_book/make/out/`: the print and screen PDFs, every page as PNG, and `spread_<trim>_<n>.png`.
The build is repeatable: the page and sketch PNGs of two builds have the same MD5 (checked on Square).

What was built (all in `spikes/15_book/make/`):

| File | What it is |
|---|---|
| `build.py` | The grid (`TRIMS`, `LINE`, `GUT`), the components, the 12 pages, the PDF and PNG writing. One command runs everything. |
| `run_sketch.py` | Runs one sketch in its own process (`FUNGROUND_HEADLESS=1`), then saves the canvas as SVG and as a 300 dpi PNG. |
| `nocoords.py` | Spike-only stand-in for proposal D-121: wraps `f.circle`, `f.square`, `f.rect`, `f.ellipse`, `f.triangle` (a monkeypatch). |
| `sketches/*.py` | The four sketches, written exactly as the pages print them (the opener's picture is one of them). |
| `measure.py` | The measurements below. |

The Compare strips are not sketch files: `f.variations` is called in the build, inside a throw-away `with f.mark()`,
and the returned marks are placed in the strip (gap 6).

## How a sketch's picture reaches the page (decided by test)

`f.show()` returns at once when headless, and the canvas is still there: `f.save("x.svg")` and `f.save("x.png", dpi=300)`
called after the sketch's last line work (found by reading `Sketch.show`, then tried). The runner does exactly that.

**The SVG differs visibly from the PNG.** The SVG is written, but `f.background("oldlace")` is saved as a Cairo mask and
filter group. `f.load_svg` ignores filters, so the picture is placed on a **black** square (shapes and strokes are right,
the paper is lost). The pages therefore place the **PNG at 300 pixels per inch** (2500 x 2500 for a 600 pt canvas, about
320 ppi at the largest size on the page). The pictures are not vector in the PDF. Each PDF is about 0.6 MB.

# Measurements

### 1. Build time and file size

| Trim | Build, whole process | Of which draw (fonts, pictures, layout) | Print PDF | Screen PDF | Pages |
|---|---|---|---|---|---|
| Square | 8.27 s | 0.86 s | 599 KB | 577 KB | 12 |
| B5 | 8.87 s | 0.91 s | 602 KB | 585 KB | 12 |

Square inside the process (seconds): print_pdf 3.16, screen_pdf 2.92, page_pngs 0.65, spreads 0.22
B5 inside the process (seconds): print_pdf 3.53, screen_pdf 3.01, page_pngs 0.73, spreads 0.26

The four sketches run first, one process each: 2.81 s in all (not in the trim times).

### 2. Grid check

Square: text area 34 lines; canvas side 330 pt; optical nudges inside a slot: caption +[1.5], code +[2.5], code number +[3.5], contents +[1.5, 3], folio +[2], label +[3], try this title +[1.5]; exempt: ['full-bleed picture (top at the bleed edge)']
B5: text area 41 lines; canvas side 405 pt; optical nudges inside a slot: caption +[1.5], code +[2.5], code number +[3.5], contents +[1.5, 3], folio +[2], label +[3], try this title +[1.5]; exempt: ['full-bleed picture (top at the bleed edge)']

| Trim | Items placed | Vertical positions checked (slot top and bottom, less nudge) | Off the 15 pt line | Result |
|---|---|---|---|---|
| Square | 133 | 264 | 0 | PASS |
| B5 | 133 | 264 | 0 | PASS |

### 3. Longest code line against the measure

| Trim | Longest line, characters | Measure, characters (4 columns less the number gutter, at 9.5 pt) | Result |
|---|---|---|---|
| Square | 30 (f.circle(at="random", size=80)) | 56 | fits |
| B5 | 30 (f.circle(at="random", size=80)) | 44 | fits |

### 4. PDF page boxes (read with pypdf)

| PDF | Pages | Boxes on every page (one line per distinct set) | Fonts in page resources (embedded subsets) |
|---|---|---|---|
| Square print | 12 | MediaBox=[0.0, 0.0, 651.0, 651.0] TrimBox=[25.5, 25.5, 625.5, 625.5] BleedBox=[17.0, 17.0, 634.0, 634.0] | AtkinsonHyperlegibleNext-Regular-wght400, AtkinsonHyperlegibleNext-Regular-wght700, BricolageGrotesque-96ptExtraBold-wght700, JetBrainsMono-Regular-wght400 |
| Square screen | 12 | MediaBox=[0.0, 0.0, 600.0, 600.0] TrimBox=[] BleedBox=[] | AtkinsonHyperlegibleNext-Regular-wght400, AtkinsonHyperlegibleNext-Regular-wght700, BricolageGrotesque-96ptExtraBold-wght700, JetBrainsMono-Regular-wght400 |
| B5 print | 12 | MediaBox=[0.0, 0.0, 550.0, 760.0] TrimBox=[25.5, 25.5, 524.5, 734.5] BleedBox=[17.0, 17.0, 533.0, 743.0] | AtkinsonHyperlegibleNext-Regular-wght400, AtkinsonHyperlegibleNext-Regular-wght700, BricolageGrotesque-96ptExtraBold-wght700, JetBrainsMono-Regular-wght400 |
| B5 screen | 12 | MediaBox=[0.0, 0.0, 499.0, 709.0] TrimBox=[] BleedBox=[] | AtkinsonHyperlegibleNext-Regular-wght400, AtkinsonHyperlegibleNext-Regular-wght700, BricolageGrotesque-96ptExtraBold-wght700, JetBrainsMono-Regular-wght400 |

### 5. Script length

| File | Lines |
|---|---|
| build.py | 651 |
| nocoords.py | 87 |
| run_sketch.py | 22 |
| measure.py | 214 |
| sketches/*.py (4 files) | 43 |

### 6. CMYK change of each palette token

Route: `spikes/11_cmyk` option d (littleCMS through Pillow, Windows' RSWOP.icm as the press profile, relative colorimetric with black point compensation). The 11_cmyk scripts print CMYK values only, so the delta-E step (CMYK back to Lab, against the colour's own Lab, CIE76 and CIEDE2000) is added here. The book PDFs themselves are still RGB: this measures what the conversion would do to each token.

| Token (day) | Hex | CMYK % (C/M/Y/K) | dE76 | dE2000 |
|---|---|---|---|---|
| paper (oldlace) | #fdf5e6 | 2/5/13/0 | 5.3 | 3.6 |
| paper-code | #fffaf0 | 2/4/9/0 | 5.9 | 4.7 |
| dot | #e6d8bd | 6/11/25/0 | 6.4 | 3.8 |
| ink (midnightblue) | #191970 | 96/91/7/33 | 21.2 | 8.2 |
| ink-muted | #5a4f7a | 72/71/18/3 | 5.4 | 4.7 |
| tomato | #ff6347 | 0/87/88/0 | 11.4 | 8.6 |
| gold | #ffd700 | 1/11/95/1 | 6.2 | 1.6 |
| hotpink | #ff69b4 | 1/85/3/0 | 13.4 | 9.1 |
| turquoise | #40e0d0 | 75/0/31/0 | 18.2 | 12.3 |
| teal | #008080 | 80/22/39/7 | 6.4 | 3.9 |
| orchid (code keyword) | #9932cc | 55/90/0/0 | 37.8 | 13.0 |
| link / code-string (firebrick) | #b22222 | 16/98/84/7 | 3.5 | 1.9 |
| code-number | #00706b | 80/29/46/16 | 9.7 | 5.2 |
| code-comment | #6b6380 | 58/55/19/9 | 4.1 | 4.1 |


How the PDF reads one page at a time: **not tested in a viewer** (no browser or PDF viewer was opened on this machine).
Structure only: every PDF page is one half of a spread, in reading order. The Predict recto (PDF page 6) is followed by
the Reveal verso (page 7), so scrolling one page at a time shows the answer on the next scroll, as the page system
intends. Whether a two-page view pairs pages as spreads depends on the viewer's "cover page" setting: page 1 is a verso
here (the chapter is imagined to start on page 2), so a viewer that shows page 1 alone pairs the pages wrongly. The
question for a person with a browser and the Windows viewer is still open.

## Notes about the numbers

- **Grid check.** Passes at both trims. It covers every vertical position the build passes to funground for text slots,
  code lines, labels, highlights, frames, panels, the Try this block and folios (133 items, 264 positions): the slot's top
  and bottom, less a declared optical nudge (0 to 3.5 pt, listed above) that centres text in its 15 pt slot. It does not
  cover the hand-drawn lines (the wobble is the point), the ends of the tie lines, the full-bleed picture's edge, and the
  second and later lines of a side note (8.5 on 11 leading: 7 notes, recorded). It checks the numbers the build sends, not rendered baselines.
- **Canvas size.** The page system said the canvas fills "4 x 4 fields", which is 340 x 405 pt on Square: not square. The
  build uses a square snapped down to whole lines: 330 pt on Square (4 columns are 340) and 405 pt on B5 (6 columns are 415).
  Small pictures are 150 pt (Square) and 120 pt (B5): 2 columns, snapped down.
- **Large pictures.** Square, run into the bleed on the outer edge and the top, bottom on a line: 524.5 pt (Square) and
  449.5 pt (B5). Nothing is cropped. The sketch's `oldlace` background is the same as the paper, so the picture's edge only
  shows because the build draws a hand-drawn frame on the two inner edges.
- **Code measure.** 4 columns less a 20 pt number gutter: 56 characters on Square, 44 on B5 (the page system said about
  59 and 47, which counted no gutter). The longest line in the chapter is 30 characters.
- **CMYK.** By CIE76, tomato, hotpink, turquoise, ink and orchid move by more than 10. By CIEDE2000, only turquoise
  (12.3) and orchid (13.0) do, and hotpink is at 9.1. The two rules disagree on tomato and ink, so the page system's
  "delta-E 10" needs one formula named. Even paper moves by 3.6 to 5.3 (it takes a faint tint). Pillow's 8-bit Lab has steps
  of about 0.4 for L and 1 for a and b. The route was not too heavy: `spikes/11_cmyk` option d takes a few lines. The book PDFs are still RGB.
- **Time.** About 8 to 9 s for a trim. Only 0.8 to 0.9 s of it is layout (with fonts and pictures loaded); the rest is
  funground writing the files (each PDF about 3 s, the 12 page PNGs about 0.7 s). The four sketches take about 2.9 s, once.
- **Script length.** `build.py` is 645 lines (540 without blank lines) for 12 pages and 8 components. It includes the
  orchestrator, the grid, the code colouring, the wobble and the spread images. The markdown source and its reader for a whole book are not counted.
- **Fonts.** All three load by name from Google Fonts at weights 400 and 700 (Atkinson also italic), kept in
  `make/fonts` (840 KB with `sources.json`). Nothing was installed. The PDFs hold them as subsets (table 4).

## funground gaps found

1. **SVG saved from a sketch loses `background()`.** `f.save("x.svg")` writes the background as a mask and filter;
   `f.load_svg` ignores filters, so the picture is black. Workaround: place the 300 dpi PNG, so the pictures are raster
   in the PDF. A fix is for `save` to write a plain rectangle, or for `load_svg` to read the group.
2. **`load_svg` ignores text.** Documented, but a sketch with `f.text` could not be placed as vector either.
3. **No hyphenation, and `text_box` does not say how many lines it used.** It returns the text that did not fit, but the
   grid needs the line count to stack blocks. The build counts lines itself with a greedy wrap using `f.text_width`
   (`wrap_count`) and passes a height as a check; no text overflowed. A returned height or line count would remove that function.
4. **No baseline grid.** `text` and `text_box` align by the top of the font's box, so each face needed an optical nudge
   (0 to 3.5 pt) to look centred in a 15 pt slot. `text_align("left", "baseline")` with a y on the grid would be a
   baseline grid; the build did not use it. A helper that puts the first baseline on the grid is missing.
5. **Leading that is not a multiple of the line.** Side notes (8.5 on 11) can have only their first line on the grid.
   Workaround: the note's top is on a whole line, and notes that would touch are pushed down by whole lines.
6. **`f.variations` always draws its sheet** over `f.ground.content`, with default-font labels, and each cell is the
   whole canvas scaled down. For a Compare strip in a layout, the build records it in a throw-away `with f.mark():`, keeps
   the returned marks and places them itself (clip, translate, scale, `place(0, 0)`). The shim also needed a way to say
   "the panel is 600 x 600" (`nocoords.canvas`), because `f.width` is the page. A way to give the cell's rectangle, or to
   skip the sheet, would remove this.
7. **`f.stroke_width` refuses less than 1** ("stroke width must be at least 1"). The hand-drawn tie lines wanted 0.5 pt;
   they are 1 pt. Fine on screen, heavy in print.
8. **No way to read the current stroke width, fill or font.** The shim for `at="random"` cannot keep the whole stroke
   inside the canvas as proposal D-121 says ("half its stroke"), so it ignores the stroke. Built inside funground, this is not a gap.
9. **No highlight for a run of text.** The gold highlight on the Predict page is a rectangle behind a line slot, drawn from
   the grid's numbers. It works only because code is one line per slot. A background for a `FormattedString` run would do it properly.
10. **Page numbers and running heads are by hand.** The build keeps its own page counter. There is no page-number token,
    no left-page and right-page master, and no way to say "this page is a verso".
11. **Page PNG names.** `f.save("Square.png")` on 12 pages writes `Square_1.png` to `Square_12.png`, not zero-padded, so
    the build sorts them by number.
12. **Randomness and printed code.** The pages print code with no `random_seed`, so the learner's circles land somewhere
    else on each run. The runner seeds `f.random_seed(7)` so the picture on the page is the same on every build. The book
    needs a sentence saying so, or a seed in the printed code.
13. **`font.style()` of a variable font is confusing.** `load_font("Bricolage Grotesque", weight=700)` reports
    "96pt ExtraBold Regular" and the PDF's font is named `BricolageGrotesque-96ptExtraBold-wght700`. The picture is right.
    The `opsz` axis stays at 96 (a display cut): fine for 22 and 48 pt, not tested at small sizes.
14. **Headless `show()` then `save()`** works but is written in neither docstring. The build depends on it.

No gap: the page names. `Square` is 600 x 600 pt and `B5` is 499 x 709, as the page system says. The print PDFs have a
MediaBox of 651 x 651 and 550 x 760 (they include the crop-mark margin), and TrimBox and BleedBox are right.

## Not done

- The viewer test of reading one page at a time (browser and Windows viewer): nothing may be opened on this machine.
- Printing at home.
- Vector pictures in the PDF (gap 1).
- CMYK conversion of the book itself: only the tokens' change was measured.
- Glyph coverage of the fonts (curly quotes, arrows): the chapter uses plain ASCII.

---

## Review (main session, 28 Oct)

**What was checked:**
- The test chapter was built by a Sonnet builder subagent and reviewed here.
- It was rebuilt from one command after its folder moved from `build/` (which the root `.gitignore` ignores) to `make/`:
  Square took 8.5 s and B5 took 8.4 s.
- Spreads 1, 2 and 4 were looked at as pictures.
- `make/.gitignore` keeps the fetched fonts, the per-page PNGs and the print PDFs out of git. The screen PDFs and the
  spread PNGs are committed.

**What works:**
- The pages hold to the page system: the grid check passes, and every picture was made by the sketch printed beside it.
- The opener is drawn by a funground sketch.
- All three fonts load by name. Two builds give identical pictures.
- The spike's pass criterion for the chapter is met: 12 pages, the chosen route, funground's pictures and an opener drawn
  by a sketch.

**Findings from looking at the spreads:**
1. **The sketch panel's frame is cut at the paper's edge** on a picture that runs into the bleed. Only its left and
   bottom sides show (spread 2, Square). In print, either the frame goes, or the picture stops at the margin.
   Recommended: no frame on a bleed picture. The ground colour change marks the edge instead. That means a sketch
   background that is not oldlace, or a slightly darker panel.
2. **funground's default black outline shows on every shape.** This is right, because the book prints the real output.
   But it makes Chapter 1's first circle look like a diagram. It is a question for the text: either explain the outline
   on the first spread, or start with `f.no_stroke()`. That is a writing choice, not a layout one.
3. **The Try this block has no inner padding,** and the tie line to `f.show()` is drawn at an angle. These are small
   fixes in the build.

**Decisions taken within the spike** (to check at the sprint review):
- **ΔE2000 is the measure for the CMYK check,** because it is the current standard. Two tokens need a print variant:
  turquoise (12.3) and orchid (13.0). Hotpink (9.1) and tomato (8.6) are close, and should be looked at in a real proof.
- **The pictures are placed as 300 dpi PNG,** not vector, until gap 1 is fixed.

**funground gaps worth stories** (candidates, from the list above):
- **Gap 1: SVG saved from a sketch loses `background()`.** A real product bug, worth fixing on its own, not only for the
  book.
- **Gap 7: `stroke_width` refuses widths below 1.** Print needs hairlines of 0.25 to 0.5 pt.
- **Gap 6: `f.variations` cannot be placed in a cell.** The book needs to put its contact sheet inside a box.
- **Gap 4: there is no baseline grid for text.** Text is placed by the top of the font's box, so each font needs an
  offset by hand.

Gaps 3 and 9 to 14 are smaller, and wait for the whole-book decision.

**The effort of a whole book** (an estimate, not measured):
- **The layout engine:** `make/build.py` is 540 lines. About 400 of them are components and the grid, used again for
  every chapter.
- **Making it a real tool** (markdown source, page masters, the four gap stories above): about one sprint.
- **Then each chapter:** about 10 spreads of writing and sketches. The writing dominates.
  - At the test chapter's pace, a chapter's layout takes about a day.
  - The writing and the sketches are the maintainer's and the course's work, and are not estimated here.

**Still to do for S-225:**
- The spreads on the site with Previous and Next.
- Reading one page at a time, in a viewer the maintainer opens.
- The choice between the two trims, which is the maintainer's choice from the spread pictures.
- ~~D-121's answer.~~ Answered 28 Oct: keep current behaviour (no new shape keywords; a package later if needed). The
  chapter's sketches use the proposed calls through the spike's shim and must be rewritten with today's calls before
  they are shown as the book.

### Rebuilt after the maintainer's review (28 Oct)

**What the maintainer saw:** pages 5, 8 and 11 looked cut off at the top. The pictures ran into the bleed with their frames
cut there, which is finding 1 of the review.

**What changed:**
- **Pictures:** the big sketch panels now sit inside the margins with the whole frame drawn.
- **Sketches:** rewritten with today's calls after D-121 (`f.circle(300, 300, 200)`, `f.square(150, 150, 300)`,
  `f.circle(f.random(600), f.random(600), 80)`). They now use `f.no_stroke()`, for the maintainer to judge by eye.
- **The code on the page:** it is now read from the sketch files, so the two cannot drift. `nocoords.py` is no longer
  used and stays only as D-121's evidence.
- **The grid check still passes:** 0 of 274 positions are off the line on Square, and 0 of 264 on B5.
- **The longest code line is 42 characters,** against a measure of 56 on Square and 44 on B5.

**Note for building on Windows:** writing a spread PNG while a viewer has the `out/` folder open fails at times with
`OSError: [Errno 22]`. Running the build again gets past it.

### Colour pass (28 Oct)

**Why:** the maintainer read the PDFs and found the two-page spreads decent, the cover playful but crowded, and most pages
too plain. Structure is unchanged; only the surface changed (`make/build.py`, `make/measure.py`, `sketches/1_0_opener.py`).

**What changed:**
- **Cover:** 8 circles (was 38 and a ring), bigger, with clear room between groups and one focal tomato ring. It keeps the
  palette, `f.no_stroke()`, today's calls and a fixed `f.random_seed(3)` (it only nudges each circle a little). The sketch
  is 14 lines. The picture no longer runs into the bleed. On B5 the cover is cropped to the middle of the canvas.
- **One accent for each spread:** opener tomato, spread 2 turquoise, 3 hotpink, 4 gold, 5 tomato, 6 turquoise.
- **Picture pages** (PDF pages 4, 6, 7 and 10): a ground of the accent mixed 20 per cent with oldlace, over the page and its bleed.
  The sketch's own oldlace canvas stays in its ink hand-drawn frame, with the accent offset 9 pt behind the frame.
- **Text pages** (PDF pages 2, 3, 5, 8, 11 and 12): a big hand-drawn shape in the accent (circle or tilted square) off the page corner,
  beside the heading and above the code and the compare strip, never behind text.
- **Headings** (and the chapter title): a gold marker stroke underneath, drawn before the words.
- **Line numbers, tie lines and contents numbers:** a shade of the accent (accent mixed with ink until it reaches 4.5 to 1
  on oldlace). Compare frames use the accent (a deeper gold on the gold spread).
- **Spot shapes** beside each folio, echoing the lesson: a circle; a square and a circle; three squares in growing sizes;
  scattered dots; a circle. The opener's right page has a tomato circle bleeding off the top corner, as on the cover, and two
  small dots in the bottom margin.
- **Predict and Your page frames:** still hand-wobbled, now in the accent with a tinted inside (Predict: 10 per cent of the
  accent on warm white, on a tinted page; Your page: 22 per cent on oldlace).
- **Try this:** now has padding inside the gold block.

**Checks (from `make/measure.py`):**
- Grid: 0 of 274 vertical positions off the 15 pt line, on both trims (138 items each). PASS.
- Longest code line: 42 characters, against a measure of 56 (Square) and 44 (B5). Fits.
- Contrast, every text colour against the ground it is on (new section 7, the build records each pair). Lowest 4.5:1, PASS:

| Text | Ground | Ratio |
|---|---|---|
| Ink on oldlace | #fdf5e6 | 13.7 |
| Ink on a hotpink tint (Predict caption) | #fdd9dc | 11.4 |
| Ink on gold (Try this, the highlighted code lines) | #ffd700 | 10.6 |
| Muted ink (folio, labels, notes) on oldlace | #fdf5e6 | 6.8 |
| Muted ink on the turquoise, gold and tomato tints | #d7f1e2, #fdefb8, #fdd8c6 | 6.2, 6.4, 5.6 |
| Muted ink on the hotpink tint | #fdd9dc | 5.7 |
| Code: string, number, keyword, comment on oldlace | #fdf5e6 | 6.2, 5.5, 5.3, 5.2 |
| Code on the highlight: keyword, number, string | #fee98a | 4.7, 4.9, 5.5 |
| Accent shades for numbers (hotpink, turquoise, tomato) | on oldlace | 4.9, 4.8, 4.5 |

- Gold's text shade (#806e3e, 4.6) is defined but not used: the gold spread has no code page.
- The highlight behind the changed code lines is now gold mixed 40 per cent with oldlace (#fee98a), not full gold: orchid
  on full gold was 4.1 and the number green 4.2. On the lighter highlight the lowest is 4.7. The line numbers on those rows
  take a darker shade (4.8).
- No text sits on tomato, hotpink or turquoise at full strength.
- Both trims build (Square 13.4 s, B5 14.2 s). `build.py` is now about 810 lines (it was 623).

**Not done:** CMYK check of the tints (hotpink and tomato tints will shift in print, like their tokens, section 6).

### The maintainer's verdict on the colour pass (28 Oct)

"For now this will work, but ideally we can try, at least for the screen version, something closer to Play's navy blue
version."

**To try next: a night version of the screen PDF.** It uses the site's dark tokens from `design/tokens.json`:
- the paper is midnightblue `#191970`;
- the ink is oldlace `#fdf5e6`;
- links and strings use lightsalmon `#ffa07a`.

The print PDF stays on oldlace.

**How:** the build takes a theme, so one layout gives both screen versions. The accents' tints become shades of navy
rather than mixes with oldlace. Contrast is measured again for every text colour.

**The sketch pictures** keep their own backgrounds, because they are the real output. The book's sketches could use
`f.background("midnightblue")`, as many gallery examples do, but that changes the sketch, so it is a writing choice.

## Night version (28 Oct)

The maintainer asked for a screen version closer to Play's navy one. The build now has `--theme day|night` (both by default).
Every colour the layout uses is in one table, `THEMES` in `build.py`; night is a second column of that table, not a set of `if`s.
Day is unchanged: the 12 page PNGs and 6 spread PNGs of each trim have the same MD5 as before the change.

**Files** (in `make/out/`): `chapter_<trim>_screen_night.pdf` (no print PDF for night), `spread_<trim>_night_<n>.png`,
`spread_<trim>_night_2b.png` (comparison), `report_<trim>_night.json`.

**Night colours** (the site's dark tokens): paper `#191970`, ink `#fdf5e6`, muted ink `#c4c0e6`; code strings `#ffa07a`, keywords
`#ee82ee`, numbers `#40e0d0`, comments `#a9a4d6`. Accents per spread stay as they are.
- Picture-page ground: the accent mixed 20 per cent with `#191970` (tomato `#472868`, turquoise `#214183`, hotpink `#47297e`,
  gold `#473f5a`). Corner shapes, spot shapes and the Predict and Your page frames use the full accent.
- Frames round pictures are navy (a cream frame vanished against the cream canvas). The offset block behind a picture frame is the
  site's sticker shadow `#05052e`, not the accent.
- Highlight behind the changed code lines: gold mixed 16 per cent with navy (`#3e375f`), plus a full gold bar at its left edge.
  A stronger gold mix failed 4.5 for the keyword colour; the first try (30 per cent) gave 3.5.
- Try this keeps its gold block with the dark navy text (cream on gold would fail). Headings keep the gold marker under the words.
- Line-number and contents shades: the accents already reach 4.5 on navy (5.0 to 10.6), so they are used as they are.

**Sketch pictures, two ways:**
- (a) The main night build: the sketches as they are, oldlace canvases in their frames.
- (b) Spread 2 only, `out/spread_<trim>_night_2b.png`: the sketch `sketches/1_1_circle_night.py`, identical to `1_1_circle.py` but
  for `f.background("midnightblue")`. Its code is printed from that file (line 4 reads `"midnightblue"`). Not in the PDF.
  The sketch canvas is the same navy as the page, so on this spread only the shadow and the circle show its edge.

**Checks** (`make/measure.py`, sections 2 and 8):
- Grid: 0 of 274 vertical positions off the 15 pt line, on both trims, in both themes.
- Contrast, night: lowest 4.7:1, PASS (keyword on the highlight; the rest are 5.0 or more).
- Build, night: Square about 8 to 11 s, B5 about 8 to 11 s, comparison spread about 1.5 to 3 s each.

### Where book building goes (D-122, 28 Oct)

**The maintainer's decision:** book building becomes a separate project, outside funground-hq. The content system, the
web book, search and content management go to questConquest (Astro, MDX, React). funground keeps and improves its print
PDF.

**What this changes in the review's estimate:** the "book tool" sprint (markdown source, page masters) is no longer
funground's work. funground's share is now two stories:
- **S-249:** the PDF gaps.
- **S-248:** the content contract that funground's print build reads, tested on Chapter 1, with the web half done in
  questConquest.

`make/build.py` stays as the spike's evidence and the starting point for the print build.
