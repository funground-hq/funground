# Example provenance

## What is claimed

Every example in funground is original to this project, and every example is published
as CC0 (public domain) — see `examples/LICENSE` and D-026. That is only honest if the
examples really are our own written expression. This page states where they came from
and how that claim was checked.

- `examples/gallery/*` and `examples/reference/*` — written for funground in Sprints
  4–6, from the feature each one shows, not from a sketch seen elsewhere.
- `examples/session1/01_first_sketch.py` to `14_paths.py` — written to follow the v0.5
  Quick Reference (`docs/reference/Quick_Reference.md`), which was
  itself written by a different AI assistant at the maintainer's direction (see
  `AI-USAGE.md`). They are learner code and never change to make a test pass
  (`docs/PROCESS.md`).
- `examples/hello_visual.py` — comes from the v0.5 package, the same origin as the
  Session-1 sketches.
- The Python code blocks in `docs/guide/*.md` — written alongside the guide chapters,
  Sprint 6. `docs/guide/15_coming_from_drawbot.md` also contains one block that is
  explicitly presented, in the surrounding prose, as DrawBot's own syntax (a "porting
  walk-through": DrawBot code, then the funground translation next to it) rather than
  as an original funground example. It is still a `python`/`py` fence in that file, so
  the tool checked it like everything else; see its row in the results table below.
  **Resolved by the main session, 30 Sept 2026:** that snippet (and the p5.js snippet in
  chapter 14) is ours too. It was written for the guide in DrawBot's (or p5's) syntax to show
  what porting looks like, not taken from their documentation. Function names are not
  copyrightable, so the snippets are original and CC0 like the rest.
- **The check catches real copies.** As a control, a DrawBot example and a Processing example
  were copied verbatim from the corpora and checked as if they were ours: both were flagged.

## How it was checked

`tools/check_originality.py` compares our example code against a corpus of files from
well-known creative-coding collections. Because most of those collections are
JavaScript or Java and ours is Python, it does not compare raw text; it compares four
normalised fingerprints:

- **Calls** — the ordered sequence of called function/method names, camelCase folded to
  snake_case, any receiver dropped. Scored by 5-gram containment (the share of our
  5-grams found in the other file).
- **Numbers** — the ordered numeric literals from the code itself (not comments or
  strings), ignoring 0, 1, 2 and common canvas sizes. Scored by 4-gram containment.
- **Words** — the words in comments and string literals, lower-cased. Scored by the
  longest common contiguous run; eight or more words in a row is treated as a strong
  signal on its own.
- **Identifiers** — the set of user-chosen names, excluding API names and very common
  words (`x`, `y`, `setup`, `draw`, `width`, …). Scored by Jaccard similarity.

A pair is flagged when a combined score (weighted: numbers and words most heavily,
then calls, then identifiers) crosses 0.55, or when one strong signal is convincing on
its own: a long run of matching words (8+), a decent share of matching calls *and*
numbers together, or a strong run of matching numbers *and* calls together. Calls
alone never flag a pair, however long the run: this corpus's sketches all draw with
the same small vocabulary (`background`, `fill`, `circle`, `rect`, …), so on a corpus
of nearly 3,000 files a run of six or more matching call names turns up by chance —
that was observed directly while tuning the tool (see `tools/check_originality.py`'s
module docstring and the comment beside `compare()`) and is why calls only corroborate
a match rather than deciding it. The thresholds were tuned against
`tests/test_check_originality.py`: a faithful translation is flagged, the same
translation with names and comments changed (but calls and numbers kept) is still
flagged, and two sketches that only share `setup`/`draw`/`background`/`circle` are not.

## The corpora

Fetched with `python tools/check_originality.py --fetch DIR` into
`C:\Projects\funground-corpora` (outside this repository), 65 MB in total. Shallow,
sparse clones; the commit compared is recorded in `corpora.json` in that folder.

| Corpus | URL | Commit | Files compared | Licence |
|---|---|---|---|---|
| p5.js-website examples | https://github.com/processing/p5.js-website | `424ac4127451` | 287 | MIT (repository LICENSE) |
| p5.js reference (`@example` code in `src/`) | https://github.com/processing/p5.js | `5c627cd70aa9` | 1441 | LGPL-2.1-or-later (repository LICENSE) |
| Processing examples | https://github.com/processing/processing-examples | `b10c9e9a05a0` | 315 | Public domain (Reas/Fry/Shiffman), or the credited author's own copyright, per the repository's README |
| DrawBot examples and docs | https://github.com/typemytype/drawbot | `71cff6df68ff` | 19 | BSD (`license.txt`) |
| py5 examples | https://github.com/py5coding/py5examples | `a74bc6fd76ca` | 3 | MIT (LICENSE) |
| p5 (Python package) examples | https://github.com/p5py/p5 | `ae80091506f3` | 56 | GPL-3.0 (LICENSE) |
| pygame-ce examples | https://github.com/pygame-community/pygame-ce | `6f9951101660` | 49 | Public domain (README.rst: "the programs in the examples subdirectory") |
| Nature of Code examples (Processing) | https://github.com/nature-of-code/noc-examples-processing | `c7ff604faf9e` | 533 | MIT (repository LICENSE) |
| Nature of Code examples (p5.js) | https://github.com/nature-of-code/noc-examples-p5.js-archived | `98cbd0def444` | 271 | MIT (repository LICENSE) |

The p5.js `src/` comparison splits each function's JSDoc `@example` sections into
their own small unit, rather than treating the whole source file (which concatenates
hundreds of tiny examples) as one; otherwise the shared reference-example idiom
(`createCanvas`/`background`/`fill`/`rect`/`describe`) produces long "common runs" by
coincidence rather than by copying. py5's current example collection is mostly Jupyter
notebooks, which this tool does not parse, so its comparison is thin (3 files); this is
noted here rather than worked around.

## Results

Checked 30 September 2026. 103 of our examples (66 `.py` files under `examples/`, plus
37 Python fenced blocks in `docs/guide/*.md`) compared against 2,974 corpus files.
**Zero pairs were flagged.**

### The five highest-scoring pairs that were not flagged

All five score well below the flagging threshold (0.55) and share no calls and no
numbers with their closest corpus file — only a short run of ordinary words. Judgement:
independently-written description of the same idea, not a copy or translation.

| Our example | Closest corpus file | calls | numbers | words run | identifiers | combined |
|---|---|---|---|---|---|---|
| `examples/session1/13_transforms.py` | p5.js `src/core/transform.js` (`@example`) | 0.00 | 0.00 | 5 | 0.09 | 0.20 |
| `examples/reference/05_text.py` | p5.js `src/math/calculation.js` (`@example`) | 0.00 | 0.00 | 5 | 0.08 | 0.20 |
| `examples/reference/02_shapes.py` | p5.js `src/core/helpers.js` | 0.00 | 0.00 | 5 | 0.07 | 0.20 |
| `examples/reference/10_transforms.py` | p5.js `src/core/transform.js` (`@example`) | 0.00 | 0.00 | 5 | 0.04 | 0.19 |
| `examples/gallery/lines/03_pixel_art.py` | p5.js-website `penrose_tiles.js` example | 0.00 | 0.00 | 5 | 0.04 | 0.19 |

- `13_transforms.py` / `transform.js`: the shared five words are "a little more each
  frame" — an ordinary phrase for describing a value that changes slowly. No shared
  calls, no shared numbers.
- `05_text.py` / `calculation.js`: the shared five words are "the top left of the" —
  again an ordinary phrase, here describing where a coordinate is measured from.
- `02_shapes.py` / `helpers.js`: "the top left corner" plus one more word — the standard
  way to describe `rect()`'s anchor point in this domain; every corpus that documents
  `rect()` says something close to this.
- `10_transforms.py` / `transform.js`: "the origin is now at" — the standard phrase for
  describing what `translate()` does.
- `03_pixel_art.py` / `penrose_tiles.js`: the "run" here is the single letter `x`
  repeated five times — not a meaningful word match at all, just an artefact of `x`
  being a common short token in both files' comments. Not a real signal.

None of these are the same written expression; they are independent descriptions of
the same small, standard vocabulary that every creative-coding tutorial uses for these
ideas (top-left anchors, translated origins, slow change).

### Later additions

- **S-110, 3 October 2026.** `examples/gallery/sound/02_write_a_tune.py` and
  `03_sargam_over_a_drone.py` were checked on their own against the same 2,974 corpus files.
  Nothing was flagged (combined score 0.16 each, no shared calls or numbers). Both were
  written from the sound features they show (`melody`, `mix`, `pluck`, `pitch`).

## Limits, stated honestly

- This check only ever compares against the nine collections listed above. It cannot
  see the whole web, books, videos or any collection not fetched here.
- It detects matching **written expression** — the same calls, in the same order, with
  the same numbers or wording — not a matching **idea**. Two people can write a
  bouncing ball, a noise-driven line, or a mover with velocity and gravity,
  independently, and this tool will not flag that; nor should it.
- AI-written code can echo patterns from its training data in ways a comparison
  against a finite, named corpus cannot rule out. This check is evidence, not proof.
- The corpus itself is imperfect: py5's public examples today are mostly notebooks,
  which are not parsed; some collections (p5 Python package, DrawBot) are small.

## How to repeat it

```
python tools/check_originality.py --fetch C:\Projects\funground-corpora
python tools/check_originality.py --report docs/qa/originality_report.md \
    --corpus C:\Projects\funground-corpora\p5.js-website \
    --corpus C:\Projects\funground-corpora\p5.js \
    --corpus C:\Projects\funground-corpora\processing-examples \
    --corpus C:\Projects\funground-corpora\drawbot \
    --corpus C:\Projects\funground-corpora\py5examples \
    --corpus C:\Projects\funground-corpora\p5 \
    --corpus C:\Projects\funground-corpora\pygame-ce \
    --corpus C:\Projects\funground-corpora\noc-examples-processing \
    --corpus C:\Projects\funground-corpora\noc-examples-p5.js-archived
```

The first command clones the pinned corpora (see `CORPORA` in
`tools/check_originality.py`) outside the repository and records their commit hashes.
The second checks every example against them and writes the results table.
