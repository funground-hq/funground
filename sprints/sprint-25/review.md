# Sprint 25 review — 0.2: a smooth start (E-35)

**Dates:** 14 October 2026, on branch `sprint-25` (funground), `feature/play-completion` (site PR #8) and
`s198-quiet-star` (sketchbook PR #1). Ran while 0.1.0 waits for the maintainer's Mac test. **Awaiting sign-off.**

## Outcome

Goal met: the editor suggests what to type in VS Code and in Play. `f.` lists every function with its arguments and a
sentence, `f.width` is a number, `f.fill("` offers the colour names, `f.COLORS.` and `f.CONSTANTS.ALIGN.` list
their names, and the star style is not flagged under the recommended settings. The first chapter shows where things
go on the canvas, with a picture and a live sketch. github.dev was a spike: Pylance there reads one file only, so its
suggestions must come from the funground extension (Sprint 26).

| Story | Result |
|---|---|
| S-130 Typing editors read | done: `py.typed`, literal `__all__`, 15 live values typed, every public function annotated; Pyright: `f.width` int, no export errors |
| S-174 Constants and colours | done, as D-103: `f.COLORS.TOMATO` (665 names) and `f.CONSTANTS.ALIGN.CENTER` (18 groups), read-only, iterable, "Did you mean"; option parameters typed `Literal[...]`; contract N1 |
| S-195 `completions.json` | done: generated with the API reference, in the wheel; members for the two namespaces |
| S-196 Suggestions in Play | done (site PR #8): names after `f.`, star names, colours with swatches, option words, inside `COLORS` and `CONSTANTS`; `test_editor.mjs` 21 of 21 |
| S-197 Spike: github.dev | done (`spikes/13_editor_completion/`): recommendation route B, the extension supplies suggestions; P1 (a real browser) left for the maintainer |
| S-198 VS Code on the desktop | done: `editable_mode=compat`, chapter 1 "Writing in VS Code", chapter 2 the star warning, sketchbook PR #1 |
| S-199 A gentle first chapter | done: "Where things are" rewritten, gallery `basics-05` and `basics-06` with goldens |

Also landed, from the maintainer's trial on a local server: gallery `colour-06` (colour schemes from your own lists,
with shapes chosen at random), `f.random_choice()` taking `f.COLORS`, a sentence for `f.random()` given a
non-number, and Play's spinner stopping when Python is ready.

**Tests:** full suite 4248 passed (two halves, before the merge of `main`); `test_editor.mjs` 21 of 21; the Pyright
probe in `tests/test_typing.py` passes with Pyright 1.1.390 (skipped where Pyright is absent, as in CI).

## Measurements

| What | Number | How |
|---|---|---|
| `completions.json` | 177 KB, 27.5 KB gzipped (101 KB before the namespace members) | `ls`, `gzip -c \| wc -c` |
| Play's editor bundle | 374 KB → 411.7 KB (+37 KB autocomplete, +0.6 KB namespaces) | file size |
| github.dev stub (spike only) | 25.8 KB, 591 lines | `gen_stub.py` |
| A colour-schemes sketch in local Play | finished in 0.8 s | headless Chrome, `check_s174.mjs` |

## Decisions

- **D-102** accepted (a): Play suggests from funground's own generated list.
- **D-103** accepted: two namespaces, `COLORS` and `CONSTANTS` (with groups), the same in both styles, instead of 84
  top-level constants. The maintainer's design, improved in two steps on 14 Oct.
- Decided by Claude, for review: the reference and the suggestions show a typed option parameter as its group
  (`mode: CONSTANTS.MODE`), not the code's alias name (`RectMode`); `f.COLORS` stays a plain list of names, with no
  colour families (agreed with the maintainer); `main` opened as `0.2.0.dev0` when Sprint 25 was merged, the 0.1.0
  release candidate being `19dd280` (Releasing.md step 10, done early because merges no longer wait for the release).

## Findings that change later work

1. **Trying it on a local server found two real bugs in an hour** (`f.random(f.COLORS)`'s message, the spinner),
   which no test had. Keep a local trial before each sprint's sign-off.
2. **The local server cached the runtime for an hour**, so a rebuilt funground did not reach the browser. Fixed by
   serving with `no-store` and a fresh port. The same problem awaits the real site's runtime cache (roadmap item 2):
   the cache must be keyed to the runtime's hash.
3. **Running the suite with `FUNGROUND_HEADLESS=1` set fails 9 tests** that need the window platform (they set the
   SDL dummy drivers themselves). Never set it for the whole suite.
4. **A random sequence drifts when list lengths differ**: `random_choice` on lists of different lengths uses up the
   generator differently, so the same seed gives different layouts. The colour-06 example chooses its shapes once
   in `setup()`, and the guide teaches that pattern.
5. Pylance in the browser reads one file at a time (pylance-release #4926, 1 Sept 2026); github.dev suggestions
   need the extension (Sprint 26).

## Built by subagents

S-196 and its namespace follow-up, S-199, S-174 (Sonnet builders); the S-174 audit and the S-197 spike (Sonnet
researchers). The main session reviewed every diff, fixed the reference's alias names and the Pyright probe the
builder could not run, ran the suites and committed.

## Retrospective

Kept: decisions as small questions with the list in a file (D-103 changed shape twice in an hour, cheaply,
before any code). Change: ask for the local trial earlier, and run the editor test and the Pyright probe on every
story that touches suggestions.
