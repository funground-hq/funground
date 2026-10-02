# Spike S-102.0: font fallback for funground text

Research only. Nothing outside this folder was changed; nothing was committed. Date: 2 October 2026.
Question: when the current font lacks a character (emoji, CJK, Devanagari, Arabic letters, symbols), how should
funground fall back to another font, and stay deterministic, work with real PDF text (T15), and leave today's
output untouched when nothing is missing?

## Answer in one paragraph

**Split each string into grapheme clusters, give every cluster to the first font in a fallback chain that has all
of its characters, merge neighbours that picked the same font into runs, and shape each run with its own font.**
Nothing changes when the primary font has every character (a cmap check, 0.1 microsecond per character,
then today's single shaping call). The mechanism needs no new dependency (about 40 lines using `unicodedata`; it
matched the `regex` module's `\X` on all 16 test strings, including ZWJ families, flags, skin tones, keycaps and
Devanagari conjuncts). It costs about 0.1 ms per line that actually needs fallback, 5 to 10 times a plain
shape, and can be memoised. Each fallback run is just another `Text` run in another font, so **PDF text (T15)
already embeds one subset per font**: I drew six fonts on one page with today's code and got six embedded
Type0 subsets, all `fsType` 0, copy-out correct in pdfium. For where the fonts come from, I recommend the **hybrid
(c)**, with a deliberately small bundled part: one monochrome emoji font (Noto Emoji, 0.86 MB as a static instance,
0.57 MB compressed) covers 98% of default-emoji characters, and everything bigger (CJK, 1.0 to 1.4 MB per language
even after subsetting) is opt-in through `f.text_fallback(font, ...)`. System fonts are only ever opt-in, never in
the default chain, so golden tests cannot depend on the machine. Colour emoji stay out of scope for now: COLRv0 is
a small story (about 30 lines of fontTools to draw, I did it); COLRv1, which Noto Color Emoji and Segoe UI Emoji
use, is a large one.

## 1. Options

Sizes are of the file I measured (raw) and of a zlib-9 copy (a proxy for what a wheel adds). "Subset" means
`fontTools.subset` with hinting dropped (funground never hints), all layout features kept. Today's four DejaVu
files weigh 2.74 MB raw.

| # | Option | Size | Licence | Coverage (measured, `out/exp3_coverage_sizes.txt`) | Effort | Risks |
|---|---|---|---|---|---|---|
| a1 | **Noto Emoji** (monochrome outlines, `NotoEmoji[wght].ttf` v3.002), instanced to wght 400 | whole font 1.98 MB (variable); **static 0.86 MB raw, 0.57 MB zlib**, 1,887 glyphs | SIL OFL 1.1, no `fsType` restriction (0) | **98%** of the 1,228 Emoji_Presentation characters (DejaVu alone: 8%); with DejaVu 1,205 of 1,228. ZWJ people, skin tones, flags (India, England tag flag) come out as one glyph. Rainbow flag, keycap, heart+VS16 become two glyphs | S | One colour only. Space in this font is 1.27 em wide, so spaces must never come from it |
| a2 | **Noto Sans Symbols 2** | 0.67 MB file; 0.65 raw, 0.29 zlib | OFL 1.1 | Games block (cards, mahjong, domino) 88% (DejaVu 62%), chess and extended symbols 61%, arrows 47%. Adds **nothing** for Emoji_Presentation beyond a1 | S | Marginal; nice to have, not needed for emoji |
| a2b | Noto Sans Symbols / Noto Sans Math | 0.23 MB / 0.99 MB files; 0.14 / 0.57 raw | OFL 1.1 | Math: DejaVu is already 100% of 2200-22FF | S | Not worth bundling |
| a3 | **Noto Sans Devanagari** | 0.24 MB file; **0.17 raw, 0.07 zlib** | OFL 1.1 | Devanagari block 100% (DejaVu 0%). Conjuncts such as क्ष, त्र shape as one cluster (kept in one run) | S | Hindi and Marathi only; other Indic scripts (Bengali, Tamil, Thai, Telugu...) each need their own font |
| a4 | **Noto Sans Arabic** / **Hebrew** | 0.13 / 0.02 MB raw | OFL 1.1 | DejaVu already has the basic Arabic and Hebrew letters (64% / 48% of the blocks); Noto Arabic adds Persian, Urdu and other extended letters and better joining | S | Direction: see section 3.6 |
| a5 | **Noto Sans CJK**, subset per language | Whole TTC: **19.5 MB** (OFL; one file holds JP, KR, SC, TC, HK). Subset: kana + punctuation only **0.18 MB raw**; kana + JIS level 1 kanji (2,965) **1.69 raw / 1.40 zlib**; + JIS level 2 (6,355 kanji) 3.57 / 2.93; GB 2312 level 1 (3,755 hanzi) 1.57 / 1.30; KS X 1001 hangul (2,350) 1.27 / 1.05 | OFL 1.1 (Adobe copyright; the variable file names the Reserved Font Name "Source"; a subset is a modified version, so rename the family, see D8) | JP subset covers 100% of JIS levels 1 and 2 and 98% of kana; **73% of GB 2312 level 1 and 99% of hangul** (so you need the SC and KR cuts too) | M | Han unification: the same code point has different glyph shapes in JP, SC, KR, TC. A chain with only JP draws Chinese text in Japanese forms. There is no language tag in a plain string |
| b | **Operating-system fonts**, found by a small lookup (`exp6`) | none to ship | Per vendor; all 374 faces on this PC have embedding allowed except 1 (`fsType` 8 for 348, 0 for 25, 14 for 1) | Windows 11 here: Devanagari (Aparajita, Kokila, Nirmala), Arabic, Hebrew, kana and Han (MS Gothic, JhengHei, Malgun for hangul), Thai, Bengali, Tamil (Nirmala), emoji (Segoe UI Emoji, COLR) and symbols (Segoe UI Symbol). Mac and Linux not run (see section 5) | S for lookup; M with a cache | **Non-deterministic across machines**: the same Hindi line hashes differently with Nirmala, Noto, or nothing (`exp7`). Scanning 374 faces took 4.9 to 5.1 s (13 ms per face), so an index must be cached or the lookup must be by name. Colour-emoji fonts differ per OS (COLR on Windows, sbix bitmaps on macOS, CBDT or COLR on Linux) |
| c | **Hybrid**: bundle small set a1 (+ optionally a2, a3, a4), everything else via `f.text_fallback(font)`; system fonts only on request, named by the learner | bundled part 0.86 MB (a1 only) to 1.83 MB raw (a1 + a2 + a3 + a4 + Hebrew) | OFL for the bundle; the learner owns the licence of the fonts they add | See a1 to a5 | M | Needs a contract row and a base-install decision (D-034) |
| d | Colour emoji: **Twemoji Mozilla** (COLRv0) | 1.47 MB file; 0.82 raw / 0.50 zlib for Emoji_Presentation only | Font code Apache 2.0; **artwork CC BY 4.0, needs attribution** | 96% of Emoji_Presentation. 3,689 glyphs, 1 to 44 layers (median 8) | M (renderer layers) | Attribution line in the licences file; PDF text mode needs thought (3.4) |
| e | Colour emoji: **Noto Color Emoji** (COLRv1) | **25.3 MB** file; 18.7 MB raw / 6.7 MB zlib for Emoji_Presentation only; 0.37 MB for 80 smileys | OFL 1.1 | 100% | **L** | Paint graph with linear and radial gradients, transforms (see 3.3); far too big to bundle |

Effort scale as in spike 09: S = under a day, M = one story of a few days with tests, L = a sprint.

## 2. What I measured

Run everything with `sh run_all.sh` (it needs the throwaway venv `.venv`, downloads the fonts into `fonts/`, which is
git-ignored, and writes `out/*.txt`). `fb.py` is the prototype (about 150 lines: a face wrapper that mirrors
`FontResource.shape`, the cluster splitter, `itemise`, and a HarfBuzz-style notdef re-shaper for comparison).

| Script | What it does |
|---|---|
| `exp1_inventory.py` | Every candidate font: size, glyph count, cmap size, `fsType`, outline format, colour tables, licence string |
| `exp2_itemise.py` | 16 tricky strings through two strategies, plus timings |
| `exp3_coverage_sizes.py` | Coverage of each font over Unicode groups (Emoji_Presentation, symbol blocks, scripts, JIS, GB 2312, KS X 1001) and subset sizes |
| `exp4_emoji.py` | Which emoji sequences each font composes into one glyph; COLRv0 drawn with fontTools and Cairo (`out/exp4_emoji.png`); COLRv1 paint-node census |
| `exp5_pdf_embed.py` | Today's funground code (project venv, read-only) draws six lines in six fonts and saves a PDF (`out/exp5_multi_font.pdf` and `.png`) |
| `exp6_system_fonts.py` | Scans this machine's fonts with fontTools (read only), coverage, `fsType`, timing |
| `exp7_determinism_load.py` | Load time per font; the same line under three chains gives three different outputs |
| `exp8_colour_emoji_sizes.py` | Subset sizes of the two colour emoji fonts |

### 2.1 Itemisation (S-102.0 point 1)

Two strategies, same fonts, same strings (`out/exp2_itemise.txt`):

* **A. Cluster first** (recommended): per grapheme cluster, the first chain font with a cmap entry for every
  character of the cluster (ZWJ, variation selectors, tag characters ignored for the test, since fallback fonts
  rarely map them). Spaces and punctuation stay with the previous run when that font is a text font and has them.
* **B. HarfBuzz-style**: shape everything with the primary, find `.notdef` glyph ids (gid 0), re-shape those clusters
  with the next font, repeat.

Both give the same runs on 12 of 16 strings. The other four differ only in where a space or comma lands (B returns
more, smaller runs, A keeps `नमस्ते दुनिया, ` as one run). They agree on everything that matters: ZWJ family, skin
tone, flag, rainbow flag, keycap, conjuncts and combining marks stay in one font. A is simpler to reason about
(only cmap, no shaping needed to decide), never splits a cluster, and does not depend on a font drawing a visible
`.notdef`; B needs a full extra shaping pass per fallback level and would treat a font that maps a character to a
blank glyph as "present". B's one advantage: it needs no cmap lookups for text the primary can shape.

Cost, median of 300 runs, microseconds, one line (`out/exp2_itemise.txt`):

| Line | Today (one shape) | Cmap check only (the fast path) | A: itemise + shape | B: notdef retry |
|---|---|---|---|---|
| Latin, 60 chars (nothing missing) | 16 | 7 | 23 (fast path 7 + shape) | 19 |
| Latin, 60 chars + 1 emoji | 14 | 5 | 110 | 56 |
| Mixed Latin, emoji, Hindi, CJK (30 chars) | 9 | 2 | 81 | 79 |
| CJK 30 chars | 9 | 0.6 | 151 | 136 |

`itemise` itself (cluster splitting plus lookups) is 50 to 60 us of the mixed line; the stdlib cluster splitter
is 16 us against 9 us for `regex`. These are Windows 11, Python 3.14, unwarmed fonts. Conclusion: a line without
missing characters pays 0.1 microsecond per character; a line that uses fallback pays about 0.1 ms. That is fine
for static text; for text redrawn every frame, memoise by `(text, chain)` (itemisation and shaping are pure).
Loading a fallback font once costs 3 to 7 ms for the small Noto fonts, 61 ms for the 4.5 MB Japanese OTF, and
224 ms for the 19 MB TTC (`out/exp7_determinism_load.txt`), so fallback fonts must be loaded lazily, on first use.

### 2.2 Emoji (point 3)

* **Monochrome Noto Emoji: yes.** It is plain `glyf` outlines, and funground draws it like any font
  (`out/exp5_multi_font.png` row 5, `out/exp4_emoji.png` top row). It shipped as variable (wght 300 to 700); a
  build-time `instancer` at 400 gives 0.86 MB (see a1). 98% coverage of default-emoji characters. One colour only
  (the text colour). Sequences: 1 glyph for ZWJ people, skin tones, flags and the England tag flag; 2 glyphs for
  the rainbow flag, keycap 1 and heart + VS16 (the font has no ligature for them, so they draw as two glyphs).
* **DejaVu already has 98 emoji** (e.g. U+1F600), in a different, thinner style. If the primary has the character
  it wins, so a line such as `Hello 🚀 world 😀` mixes two styles. Making the emoji font win for Emoji_Presentation
  characters needs a table (80 ranges, 1,228 characters, derived from Unicode data) and changes today's output for
  those 98 characters; see D6.
* **COLRv0 (layers of solid colours): feasible and small.** `exp4_emoji.py` draws Twemoji Mozilla (COLR v0, 3,689
  glyphs, 1,063 palette entries) with 25 lines: look up `colr.ColorLayers[glyph]`, fill each layer glyph with its
  `CPAL` colour (`0xFFFF` means the text colour). Eight emoji took 39 layer fills (`out/exp4_emoji.png`, bottom
  row). In funground this means `outline_ops` returns one `FillPath` per layer instead of one per glyph, with
  fixed colours: a story of about 100 lines plus tests (**S to M**). Segoe UI Emoji on Windows also carries 3,487
  COLRv0 records inside its COLRv1 table, so a v0-only renderer can show it too.
* **COLRv1: large.** Noto Color Emoji needs, over its first 400 emoji: 11,144 `PaintGlyph`, 8,545 `PaintSolid`,
  3,850 `PaintTransform`, 1,704 `PaintColrLayers`, 1,690 `PaintLinearGradient`, 909 `PaintRadialGradient`, plus
  scale and translate nodes. No `PaintComposite` showed up in that sample. A renderer for those means a paint-graph
  walker, gradient fills with an affine transform per glyph (the IR has gradients, but extend modes and transforms
  would need checking), clip boxes, and byte-identical output across Cairo versions. I estimate **L**, plus
  an 8 MB (zlib) bundle for a full set. Not recommended now.
* **CBDT (Android and Linux Noto), sbix (Apple Color Emoji)** are bitmaps; an outline renderer cannot draw them,
  and bitmaps at one size would break the vector promise. Not pursued.

### 2.3 PDF text, T15 (point 4)

`exp5_pdf_embed.py` saves one page with six `f.text` calls, each after `f.text_font(...)` to a different font
(DejaVu, Noto Devanagari, Arabic, Symbols 2, Emoji, Noto Sans JP). Today's code produced **six Type0 subset fonts**
(`FUNAAA+DejaVuSans` ... `FUNAAF+NotoSansJP-Regular`), including a CFF font (the JP OTF); the page renders correctly
(`out/exp5_multi_font.png`). pdfium (Chrome's engine) reads every line back correctly. pypdf reads the Devanagari
line as `हिXन्दी` (a stray `X`; pypdf only, not investigated, a single-font line so not a fallback effect) and the
Arabic line reversed, which is the same pypdf RTL quirk spike 09 recorded.

So **no change to `pdf_text.py` is needed for fallback if each run is its own `Text` run**: the collector already
keys fonts by file and variation location. What fallback must do is hand the collector one run per font, with
`cluster` indexes relative to that run's text (already how `Glyph.cluster` works). `fsType` is **0 (installable) on every Noto font
tested** (Emoji, Symbols 2, Devanagari, Arabic, Hebrew, CJK) and on DejaVu; system fonts here are 8 (editable
embedding allowed) except one with the restricted bit, which `_prepare` already refuses (it falls back to
outlines). Two gaps:

* A character nobody has draws `.notdef` (gid 0); several different missing characters share it. pdfium still
  copied them back correctly here (it reads ActualText on the cluster), pypdf showed `🎲 🎲` for two different characters.
* A COLR colour emoji run cannot use the clip-mode text trick (`7 Tr` fills one paint); it should stay outlines (no
  real text), or carry `ActualText` on marked content. A decision for when colour emoji arrive.

### 2.4 Determinism (point 5)

`exp7_determinism_load.py` hashes the itemised, shaped glyph ids and advances of the same lines under three chains
(all on this PC):

| Line | Bundled Noto subsets | Windows system fonts | No fallback (today) |
|---|---|---|---|
| `नमस्ते दुनिया` | `5e71523d2c45` (Noto Devanagari) | `db98c7f39992` (Nirmala) | `7bb90d0a412a` (tofu) |
| `日本語のテキスト` | `cb9bfeed223a` (Noto Sans JP) | `6c2eac2f6e1e` (MS Gothic) | `376cb1c67255` (tofu) |
| `go 🚀 now` | `83af296dcef6` (Noto Emoji) | `40944f86e634` (Segoe UI Emoji) | `acaa19ab07ce` (tofu) |

With system fonts the picture changes with the machine; a golden test that contains a character only a system font
has will pass on Windows and fail on a Linux runner with different fonts, or fail on a CI image with none. Therefore:

1. Golden and IR tests use **bundled fonts or fonts generated in the test** (`tests/fontmaker.py` already makes
   tiny TrueType fonts), never the system lookup. A bundled Noto Emoji or Devanagari makes the real-script goldens
   possible at all.
2. The system lookup is opt-in and not part of the default chain, so nobody gets machine-dependent output by
   accident; when a requested system font is missing, the call should raise (like `load_font`), not silently drop it.
3. If nothing is bundled, tests that need a fallback script use a generated font with that script's code points
   (a few lines, as `fontmaker` does), which tests the mechanism but not the real look.
4. Existing snapshots are unaffected: the fast path calls today's `shape` unchanged when the primary has every
   character. The one exception is characters the primary lacks that existing goldens happen to contain, as
   tofu. I grepped `tests/`: only `test_font_info.py` mentions a missing glyph (`not font.contains("中")`), and
   `Font.contains` is unchanged by this design.
5. One residual determinism risk: the cluster splitter uses `unicodedata` categories, which change with the
   Python version's Unicode tables (3.14 has Unicode 16.0). An unassigned code point today can get a category tomorrow.
   Negligible for fonts, but worth a line in the contract (or pin the few ranges used).

### 2.5 Integration notes found while prototyping

* **Baseline.** `TextRun.placements` and `outline_ops` use `self.font.ascent`. Fallback fonts have different ascents
  at the same em (Arabic 1.37, Japanese 1.16, DejaVu 0.93, Devanagari 0.90), so sub-runs must be placed on **the
  primary font's baseline**, and line height must come from the primary. Sub-run scale is `size / own units_per_em`
  (Noto is 1,000 per em, DejaVu 2,048), which `TextRun.scale` already does.
* **Where to hook.** `FontResource.shape` is called from three places (`cairo2d.py:609`, `sketch.py:1513, 1521`) plus
  `text_width`/`wrap_lines`. The clean change: `effective_font(style).shape(...)` returns a composite with
  `.runs` (each a `TextRun`), `.advance`, `.outline_ops`, `.placements`; the PDF collector loops over `.runs`.
* **Wrapping and width** just sum run advances; `wrap_lines` needs no cluster knowledge beyond what it has.
* **Bidi.** funground shapes one direction per run and does no bidi (spike 09 note 6). Splitting an RTL phrase into runs
  by font keeps each run's own direction, but runs are laid out left to right, so an RTL phrase that needs two fonts
  would come out with its runs in the wrong order. The prototype's rule (spaces stay with the previous
  run) keeps a normal Hebrew or Arabic phrase in a single run, and DejaVu already covers those scripts, so the
  problem appears only for a rare mix; worth a known-limitation line, not a blocker.
* **Spaces.** Noto Emoji's space is 1.27 em; DejaVu's is 0.32 em. So spaces and punctuation must come from the
  primary (or a text font), never from an emoji font. In the prototype this is a name test; the real design needs an
  explicit flag on the chain entry (`exp7` shows the name test misses `seguiemj.ttf`).

## 3. Recommendation

**Adopt the cluster-itemised fallback chain with a small bundled emoji font and an opt-in API (option c).**

1. **Mechanism (story M):** `FontResource.shape_with_fallback(text, chain, ...)` returns a composite of `TextRun`s.
   Fast path when the primary has every character; stdlib cluster splitter; lazy font loading; memoise by
   `(text, chain, settings)`; baseline and line height from the primary. A new contract row (T18) and a graphics-state
   field for the chain so `push_style/pop_style` restore it, like the other T-rows. PDF: no change beyond the loop over runs.
2. **API:** `f.text_fallback(*fonts)` sets the chain after the primary (fonts from `f.load_font`; `f.text_fallback()`
   resets to the default; `f.text_fallback(None)` turns fallback off and gives today's tofu). A reviewable extra:
   `f.system_font("Noto Sans CJK JP")` returns a font object from the OS fonts (opt-in, raises when missing, documented as
   not reproducible).
3. **Bundled:** Noto Emoji static (0.86 MB; 0.57 MB compressed). Optionally Noto Sans Devanagari (0.17) and Noto Sans Symbols 2 (0.65) if
   the maintainer wants Hindi and Games/arrow symbols working out of the box. Total 0.86 to 1.88 MB, against 2.74 MB of DejaVu today.
4. **CJK:** not in the base install. Ship it as an optional extra, e.g. a separate wheel `funground-fonts-cjk`
   with kana + JIS level 1 (1.4 MB compressed), or document `f.text_fallback(f.load_font("NotoSansJP.otf"))`. Pick
   JP, SC, KR or TC per learner; never guess from the text.
5. **Colour emoji later, as COLRv0:** one story (S to M) once a COLRv0 emoji font is chosen. Not COLRv1.
6. **Tests:** goldens only with bundled or generated fonts; one test that the fast path leaves every existing snapshot
   byte-identical; one that the PDF contains one embedded subset per fallback font.

Risks to keep in view: Han unification, emoji style mixing with DejaVu's own 98 emoji, RTL run order, and
the non-reproducibility of anything from the OS.

## 4. Decisions the maintainer must make

Adding a font to the base install is a base-install change, which D-034 reserves for the maintainer.

1. **D1. Which fonts, if any, go into the base install?** Choices: (A) none, API only; (B) Noto Emoji only
   (+0.86 MB installed); (C) B + Noto Devanagari, Symbols 2 (+1.7 MB); (D) C + a CJK cut (+1.7 MB per language).
   I advise B, or C if Hindi is a priority. Also confirm the `package-data` globs (`fonts/*.ttf` today; the JP subset is `.otf`).
2. **D2. CJK: separate wheel, system only, or bundled?** And which language is the default (JP, SC, KR, TC)?
   I advise a separate optional wheel and no default.
3. **D3. Is fallback on by default?** Proposal: the default chain (bundled fonts only) is on for every text call, because it
   only changes characters that would be tofu. The alternative is off until `f.text_fallback()` is called.
4. **D4. May funground look up OS fonts at all?** Proposal: only through an explicit, named call that raises when the
   font is missing; never in the default chain; documented as machine-dependent; goldens never use it.
5. **D5. Emoji look for 0.1:** monochrome Noto Emoji (one colour, the text colour) only, or also a colour font (COLRv0 via Twemoji
   Mozilla, CC BY 4.0 attribution, +0.5 MB compressed; an extra story)? COLRv1 I advise against.
6. **D6. Emoji font wins over the primary for default-emoji characters?** Yes gives a consistent look (and a table of
   80 ranges) but changes today's output for the 98 emoji DejaVu already has; no keeps every snapshot identical but mixes two emoji styles in one line.
7. **D7. New dependency?** None needed (stdlib cluster splitter, tested against `regex`). If the maintainer prefers exact
   Unicode segmentation, `regex` is the choice (a new base dependency; the wheel is a compiled one).
8. **D8. Licences.** OFL 1.1 text for each bundled font goes beside it, a row each in `THIRD_PARTY_LICENSES.md`, and the OFL "may not be
   sold on its own" line (the same kind of note DejaVu has). A subset is a modified version: the OFL requires renaming it if the
   font declares a Reserved Font Name (the Noto Sans CJK variable file declares "Source"; the OTF and TTC name fields I read did not,
   the Noto Emoji and script fonts did not) so subsets should be given distinct names anyway. Also the funground licence is LGPL-2.1 and the fonts
   are OFL: mere aggregation, same as DejaVu today. Confirm.
9. **D9. Known limitations to accept in the contract:** RTL phrases that need two fonts, Han unification, mixed emoji styles (if D6 = no), tofu for characters nobody has.

## 5. What I could not test

* **macOS and Linux.** Only Windows 11, Python 3.14, pycairo 1.29.1. The system lookup for macOS
  (`/System/Library/Fonts`, `/System/Library/Fonts/Supplemental`, Apple Color Emoji as sbix, PingFang and Hiragino as `.ttc`)
  and Linux (`fc-match`, `/usr/share/fonts`) is from knowledge, not run, and CI images differ.
* Real viewers beyond pdfium and pypdf (Acrobat, Preview, pdf.js).
* A real change to funground: the prototype (`fb.py`) shapes with HarfBuzz directly; funground's pipeline, layout (`wrap_lines`) and
  the Cairo renderer were not modified. Pixel rendering of mixed-font lines was drawn only via the existing multi-call `exp5` page.
* Memoisation effects, and mixed-direction lines.
* Vertical text, Noto Sans Symbols and Math in practice, Bengali/Tamil/Thai/other Indic fonts (not downloaded; the OS here has them via Nirmala and Leelawadee).
* The licences of `Noto Sans CJK` Reserved Font Name beyond the name fields I read; read each `OFL.txt` before bundling.
* An exact Unicode grapheme-break implementation: the splitter matched `regex` on 16 strings, not on the Unicode conformance file.

## 6. Tools and downloads

Throwaway venv `.venv/` (git-ignored by `spikes/.gitignore`): fonttools 4.66, uharfbuzz 0.56, regex, brotli, pycairo, pillow, lxml
(lxml only so fontTools can subset the SVG table of Noto Color Emoji). The project venv was only used read-only to run `exp5` against the funground
package, with `PYTHONDONTWRITEBYTECODE=1`. Fonts were downloaded into `fonts/` only (53 MB, git-ignored): Noto script fonts from
`notofonts/notofonts.github.io`, Noto Emoji and Noto Color Emoji from `google/fonts`, Noto Sans CJK from `notofonts/noto-cjk`, Twemoji Mozilla v0.7.0
from `mozilla/twemoji-colr`. No font was opened, installed or started: files were read with fontTools only.
