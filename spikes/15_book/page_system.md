# Spike S-225: the page system

This is the page system for the funground book, following the study (`study.md`) and its review. Its numbers are a
starting point for the test spread. They change only if the test spread shows a reason, and that reason is recorded
here.

Units are points (pt), 72 to the inch, which is what funground's pages use. Millimetres are in brackets.

## 1. Trim and bleed

The test spread is built at both trims. We choose between them from the two PDFs, on screen and printed at home
(section 8).

| | Square | B5 |
|---|---|---|
| Trim | 600 x 600 pt (211.7 x 211.7 mm), funground's `"Square"` | 499 x 709 pt (176 x 250 mm), funground's `"B5"` |
| Bleed | 8.5 pt (3 mm) on every outer edge | the same |
| Margins | inner 48 (17 mm, room for binding), outer 36, top 36, bottom 54 (the folio sits in it) | inner 48, outer 36, top 36, bottom 48 |
| Text area | 516 x 510 pt | 415 x 615 pt |

**The PDF:**
- Pages are written with funground's print setup: `f.save("chapter.pdf", bleed=f.mm(3), marks=True)` for the printer.
- A copy without marks is for reading on screen.
- A picture that runs into the bleed does so only on the picture page of a spread, never across the gutter.

## 2. Grid

**Columns:** 6 columns with 12 pt gutters.
- Square: each column is 76 pt.
- B5: each column is 59.2 pt.

**The line:** body text is 11 pt on 15 pt lines. Every vertical distance in the book is a whole number of lines (15 pt).

**Rows:** the fields' heights are whole lines, with one empty line between fields.
- Square: 5 rows of 6 lines, plus 4 gutter lines, make 34 lines (510 pt).
- B5: 6 rows of 6 lines, plus 5 gutter lines, make 41 lines (615 pt).

**Where things go on the grid:**
- **A picture:** a whole page, or a block of columns by rows. The canvas is always square in Chapters 1 and 2: 4 x 4
  fields (Square) or 6 x 4 fields (B5).
- **Code:** 4 columns.
  - Square: 340 pt, about 59 characters at 9.5 pt.
  - B5: 272 pt, about 47 characters.
  - A sketch line longer than the measure is a finding to record, not a reason to shrink the type.
- **Side notes:** the outer 2 columns, beside the code.
- **A Compare strip:** 3 panels of 2 columns each, or 2 panels of 3 columns each.

The grid is a handful of numbers in one place in the build script. Changing the trim reflows everything.

## 3. Type

These are the site's three fonts, all under the SIL Open Font License, which allows embedding in a PDF and printing. The
build fetches them with `f.load_font(..., provider=f.CONSTANTS.PROVIDERS.GOOGLE_FONTS)` (S-230) and keeps the copies.

| Role | Font | Size / line |
|---|---|---|
| Chapter title | Bricolage Grotesque, bold | 48 / 60 (4 lines) |
| Spread heading | Bricolage Grotesque, bold | 22 / 30 (2 lines) |
| Body | Atkinson Hyperlegible Next | 11 / 15 |
| Code | JetBrains Mono | 9.5 / 15, on the body's line |
| Side note | Atkinson Hyperlegible Next | 8.5 / 11; the first baseline sits on the code line it explains |
| Label (sketch name, Compare values) | JetBrains Mono | 8 / 11 |
| Folio and running head | Atkinson Hyperlegible Next | 8 / 11, in the bottom margin |

**Prose:**
- Ranged left, with no hyphenation.
- At most about 60 characters a line. Prose takes at most 4 columns, even when a page has room for 6.

## 4. Colour

The site's tokens (`funground-hq.github.io/design/tokens.json`) are the book's palette.

**Paper:** oldlace `#fdf5e6` covers every page and runs into the bleed. The book looks like the site and Play.

**Ink:** midnightblue `#191970` for text.

**Code:** colours as on the site.
- Keywords are orchid.
- Strings are firebrick.
- Numbers use the site's number colour.
- Function names are ink.
- There is no grey box: code sits on the paper.

**Accents for fills:**
- tomato: the brand colour;
- gold: Try this;
- hotpink and turquoise: the Predict and Compare frames.

**The CMYK risk.**
- Tomato, hotpink and turquoise are bright RGB colours. Hotpink and turquoise are likely to dull in CMYK.
- The test spread is converted with `spikes/11_cmyk`'s route, and the change is measured as ΔE for each token.
- A token that moves by more than ΔE 10 gets a print variant chosen by eye. The sketches' own colours are left
  alone: they are what the reader's screen shows.

## 5. Components

Each component is a function in the build script that draws on the grid.

| Component | What it is |
|---|---|
| **Chapter opener** | A full spread. The left page is a picture drawn by a funground sketch, run into the bleed. The right page has the chapter title, one sentence and the chapter's spreads listed. |
| **Sketch panel** | The canvas, its picture made by running the sketch beside it, in a hand-drawn frame. The label underneath (`1.3 random.py`) is also the file name in Play. |
| **Code block** | The whole sketch, with numbered lines in the label face. 2 to 4 side notes, each tied by a thin hand-drawn line to the line it explains. |
| **Predict frame** | An empty hand-drawn frame the size of the sketch panel, captioned "What will change? Draw it." It sits on the recto (right-hand page), and the answer is on the next page. |
| **Compare strip** | Small multiples made with `f.variations`, the same size, one value changed, each labelled with that value. |
| **Try this** | A gold block of at most 3 lines, with one task for Play. |
| **Your page** | The last page of a chapter: an empty canvas frame and a prompt. |
| **Folio** | The page number and chapter name, in the bottom margin, on the outer side. |

**The hand-drawn manner** (the middle way, from the review):
- Frames, tie lines and arrows are drawn by the build with a wobbly line. The wobble comes from `f.noise()` with a fixed
  seed, so every build gives the same page.
- Sketch pictures are printed clean.
- Hand lettering and scanned drawings are left for later. The test spread uses none.

## 6. Spreads

Spreads come in four kinds. Each holds one idea, and the picture is bigger than the code.

1. **Show:** the code block and notes on the verso (left-hand page); the sketch panel large on the recto, run into the
   bleed.
2. **Predict:** the known picture small on the verso, with the changed line highlighted in gold. The Predict frame is on
   the recto.
3. **Reveal:** follows a Predict spread, after the page turn.
   - The verso has the real result, large.
   - The recto has the Compare strip and Try this.
4. **Opener** and **Your page** (section 5).

**Reading order:** in print, Predict and Reveal are a page turn apart. In the PDF on screen, scrolling one page at a
time keeps the answer out of sight, because the Predict page ends at its edge. The test spread checks this in two
viewers: a browser, and the PDF viewer Windows offers. The question to answer is whether one layout serves both, or
whether the screen PDF needs a separate single-page order.

## 7. Production route

The route is **funground as the layout engine**. A build script runs each sketch, places its output, sets the type on the
grid, and writes the PDF with bleed and marks.

| Route | For | Against |
|---|---|---|
| **funground** (chosen) | It already has the print pieces. It runs the sketch beside its picture, so code and picture cannot disagree (principle 5). The book is made by a program, as Maeda's was (principle 5). Every gap found is a funground story. | No hyphenation and no automatic flow between frames. Overflow from `text_box` is passed on by hand. Code colouring is made with `FormattedString` spans. |
| CSS paged media (Paged.js in headless Chrome) | The book could come from the repository's markdown. | Chrome's PDFs are RGB with no TrimBox or BleedBox. The sketches would run in a second place. |
| WeasyPrint | Good paged media. | It needs GTK on Windows: an installer, which this machine rules out. |
| Typst or LaTeX | Strong typesetting. | A new toolchain, sketches run outside it, and a second design system. |
| By hand in a layout app | Full control. | It cannot be rebuilt when a sketch changes, and it is not funground. |

**Where funground already has what's needed:**
- Bleed and marks: `f.save(..., bleed=, marks=)`.
- Pages: `f.new_page`.
- Wrapped text: `f.text_box` returns the text that did not fit.
- Fonts and colour spans: `f.load_font`, `FormattedString`.
- Vector pictures: `f.load_svg`.
- Small multiples: `f.variations`.

**How a sketch's picture reaches the page.** The build runs each sketch headless in its own process, saving SVG. It then
places the result with `load_svg`, so the picture stays vector for print. A sketch whose SVG differs from its PNG is
placed as a PNG at 300 pixels per inch, and the difference is recorded.

**The source of a chapter, for the spike:** a Python file per chapter that lists its spreads, components and sketch
files. If the whole book goes ahead, markdown with a few directives is the candidate. That choice belongs with the
recommendation.

## 8. What the test spread must show

The test chapter is 8 to 12 pages: an opener, then Show, Predict, Reveal and Your page. It is built at Square and B5.

**For each trim, measured and recorded in `RESULTS.md`:**
- Build time.
- PDF size.
- Whether every vertical position is on the 15 pt line.
- The longest code line against the measure.
- The CMYK ΔE of each token (section 4).
- How the PDF reads one page at a time.
- How long the build script is in lines, for the estimate of a whole book.

**Reported as findings:** every funground gap the build meets, such as text flow, highlighting or a missing font
feature.

**Chapter 1's own sketches need drawing without coordinates** (proposal D-121, `no_coordinates.md`).
- Until the maintainer answers, the spike uses a small helper of its own to stand in for the proposed calls.
- The book's pages print the proposed spelling.
- No product code changes.
