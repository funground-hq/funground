# S-165 spike: CMYK / PDF/X output for print shops

## Question

Can funground produce a file that a print shop accepts as CMYK (or PDF/X), without a heavy
dependency, on Windows, macOS, Linux and in the browser (Pyodide)?

## Pass / fail criteria (written before measuring)

1. Print-workflow fit: the PDF uses only CMYK/Gray colour spaces for what we draw (checkable by
   walking the content streams and resources), and for PDF/X it carries an OutputIntent with an
   embedded ICC profile plus TrimBox/BleedBox. Anything we cannot verify without Acrobat or
   Ghostscript is stated as unverified, not claimed.
2. Install and platform: needs no native tool on the learner's machine, and runs in Pyodide.
   If it does not, say exactly what does not.
3. Colour honesty: say whether the conversion is a naive formula or ICC-managed, and what the
   learner sees change (RGB-to-CMYK always shifts bright colours).
4. Licence and size: any dependency or profile must be compatible with LGPL-2.1-only and be
   redistributable; size noted.
5. Breakage list: what the approach breaks (gradients, transparency, blend modes, images,
   text colour) on a real funground PDF.

Pass for 0.2 = at least one option meets 2 and 4 and is honest on 3. PDF/X conformance is a
separate bar: pass only if every PDF/X requirement can be met and checked.

Date: 11 Oct 2026. Tools used: pycairo 1.29.1, pypdf 6.19, Pillow 12.3 (with littleCMS 2.19), pypdfium2 5.13 (only to
look at the results), fonttools. No Ghostscript, Acrobat, veraPDF or other PDF/X validator was available or installed, so
no conformance is claimed anywhere below; "PASS" means my own checklist, nothing more.

## What was measured

Two PDFs made with funground itself (`make_test_pdf.py`, `make_test_pdf2.py`): live text, linear gradients (one with
transparent stops, so a soft mask), a photo, multiply and overlay blend modes, opacity, a shadow, three layers.
Cairo writes everything in `DeviceRGB`: 9 and 41 `rg`/`RG` operators, RGB shadings with Type 2/3 functions, an RGB
image, and `/Group /CS /DeviceRGB` on the page and on every transparency group (14 in the second file). The header is
`%PDF-1.3` (Cairo's own).

| Script | What it does |
|---|---|
| `inspect_pdf.py`, `leftover_rgb.py` | list colour operators, spaces, shadings, images, groups; scan every object for leftover RGB |
| `rgb_to_cmyk.py` | rewrite a PDF to DeviceCMYK, `naive` formula or `icc` (littleCMS) |
| `probe_icc_values.py` | what each route does to key colours; speed |
| `make_pdfx_probe.py` | add OutputIntent, XMP, Info, /ID, TrimBox/BleedBox, PDF 1.6 header; self-made checklist |
| `tag_srgb.py` | keep RGB but tag it as ICCBased sRGB (PDF/X-4 style) |
| `pure_icc.py` | pure-Python ICC (CMYK profile, B2A1 lut16 table) compared with littleCMS |
| `compare_render.py` | render with pdfium to see that nothing structural broke |

## Option a: leave RGB

Print shops split, so there is no single answer:

- Printful asks for RGB in sRGB IEC61966-2.1 and advises against converting to CMYK first: its systems convert, and an
  early conversion can lose colour information
  ([help.printful.com](https://help.printful.com/hc/en-us/articles/28491774495772-Should-I-use-RGB-or-CMYK-for-Printful-print-files)).
- Avery accepts RGB or CMYK, recommends CMYK, converts RGB in house and warns the change can be dramatic for bright
  colours ([avery.ca](https://www.avery.ca/en/artwork-guidelines-html.html)).
- MOO prints CMYK and says it converts RGB images itself, but its preferred upload is a PDF/X-1a:2001 in Coated GRACOL 2006
  ([support.moo.com](https://support.moo.com/hc/en-us/articles/202941410-Design-Color-Settings)).
- University and offset print shops commonly ask for CMYK (search results, e.g. carleton.ca, uwrf.edu). I could not read
  Vistaprint's current page (only second-hand reports), so I make no claim about it.

Verdict: RGB is acceptable for digital and print-on-demand shops that convert, and is sometimes what they prefer. It is
not acceptable where a CMYK or PDF/X file is demanded. Cost to us: nothing. Today's files are already this.

## Option b: rewrite the funground PDF to DeviceCMYK with pypdf

Works on both test files. The converter walks page and Form XObject streams, rewrites `rg`/`RG` to `k`/`K`, converts
shading dictionaries and their functions, the image, and every `/Group /CS`. Afterwards `leftover_rgb.py` found zero
DeviceRGB and zero `rg`/`RG` in any object. Live text, layers, opacity, soft masks, multiply/overlay and shadows all
survived (pdfium renders them; the side-by-side pictures were looked at).

What breaks or needs care, found by doing it:

1. **Gradients are not linear in CMYK.** The naive formula (K = 1 - max) is piecewise, so converting only the end colours
   changes the middle. I resample each gradient into 16 segments (`convert_function`); it costs a few hundred bytes.
2. **Blend modes give a different result.** PDF blends in the group's colour space, so multiply/overlay in CMYK is not the
   same picture as in RGB (the overlay overlap visibly differs). Not fixable by conversion, and the learner's RGB preview
   will not match the print.
3. **Black becomes rich black unless handled.** Naive: 0,0,0 gives K 100 only (good for text). Via ICC: 0,0,0 gives
   C2 M3 Y2 K96, and mid greys get CMY as well (grey 128 gives 25/21/20/35). Four-colour small text risks mis-registration.
   Rule needed: keep neutral greys (r = g = b) as K-only or DeviceGray.
4. **Images** need per-pixel work. Pure Python naive: about 2 s per megapixel on this PC (worst case, noise), so a
   300 dpi A4 image (8.7 Mpx) is roughly 17 s here and probably one to two minutes in Pyodide (an estimate: Pyodide was not
   run). JPEG (DCT) images would need decode and re-encode; Cairo wrote Flate RGB here. Image soft masks stay gray.
5. **Soft-mask and pattern groups** need the same walk (done); a missed group leaves RGB in a "CMYK" file. The
   leftover scan is a good test to keep.
6. **Naive CMYK looks flat.** pdfium draws formula CMYK duller than the RGB (mean difference per channel 10, 21, 32 on the
   first file). The formula is not what a press does, so the shop's RIP will still shift or clip it.
7. Viewers draw DeviceCMYK with their own formula, so the screen is not a soft proof.

Size: +7 KB on the first file (formula route). Dependencies: none beyond pypdf (pure Python, works in Pyodide).

## Option c: PDF/X-style (OutputIntent, boxes, claim)

Built `icc_x.pdf` and `tag_x.pdf` (`make_pdfx_probe.py`). My checklist passes: OutputIntent (GTS_PDFX, embedded CMYK
profile), XMP `pdfxid:GTSPDFXVersion`, Info (`GTS_PDFXVersion`, `Title`, `Trapped`), trailer `/ID`, no encryption,
TrimBox and BleedBox present, all fonts embedded, header raised to 1.6 (Cairo writes 1.3, and uses transparency anyway).

What conformance needs that I could not verify (no validator): exact XMP and Info consistency, font and CID rules for our
live-text fonts, the optional-content (layers) rules, no OPI or JavaScript, OutputIntent text, box nesting (TrimBox inside
BleedBox inside MediaBox), colour-space rules for every object. Do not claim PDF/X until a validator (veraPDF in CI, or a
shop's preflight) says so.

Facts that shape the claim (from the standards as I know them; to be confirmed by a validator):

- **PDF/X-1a** forbids transparency and RGB (CMYK and spot only). funground uses transparency (opacity, blend modes,
  shadows), so X-1a needs flattening, which turns parts of the page into bitmaps. Ghostscript does exactly that: PDF/X
  forces compatibility level 1.3 ([Ghostscript docs](https://ghostscript.readthedocs.io/en/latest/VectorDevices.html)).
- **PDF/X-4** allows live transparency, layers and ICC-managed RGB, so it fits funground far better.
- **Colour-managed RGB route (`tag_srgb.py`)**: instead of converting, tag every RGB as `ICCBased` sRGB (a 588-byte
  profile) and add the OutputIntent. No colour maths of ours; the shop's RIP converts. pdfium renders it within 0.4 per
  channel of the original, so tagging changes nothing visible. It still needs an OutputIntent profile (below).
- **Profiles.** Windows ships `RSWOP.icm` ("Swop Standard", Agfa, copyright Microsoft, 218 KB). I used it only to measure;
  it is not ours to redistribute. Free press profiles:
  - ECI/Heidelberg (ISO Coated v2, FOGRA39 family, PSO): the ICC registry says PSO Coated v3 "may be used, embedded and
    exchanged without restriction. It may not be distributed, sold or altered without written permission of ECI"
    ([registry.color.org](https://registry.color.org/profile-registry/PSOcoated_v3)). Debian's copyright file quotes the
    Heidelberg licence: free distribution, no charge for it, no editing
    ([Debian copyright](https://metadata.ftp-master.debian.org/changelogs/non-free/i/icc-profiles/stable_copyright)).
    Size is about 1.7 to 2 MB each (from memory, not measured).
  - IDEAlliance (SWOP, GRACoL): "may not be altered, or sold without written permission" (same Debian file). Adobe's
    profiles: I did not read their terms; treat as not redistributable.
  - Result: no profile I found has an open licence like LGPL or CC0. Bundling a 2 MB non-free file into an LGPL package is
    a licence and size problem. Cleaner: funground ships none; the user supplies the path to a profile, and the docs say
    where to download one. Or ask ECI for written permission later.

## Option d: colour-managed conversion with littleCMS (Pillow ImageCms)

- Works on Windows here: Pillow 12.3 has littleCMS 2.19. Image conversion is fast: 8.7 Mpx in 0.22 s.
- Accuracy: the ICC route gives press-realistic values (red 0/100/99/1; blue 99/64/0/15; naive gives 100/100/0/0).
- **Pillow is only an optional extra in funground** (`extras = ["pillow>=11"]`). In the browser: Pyodide 0.28.3 ships
  Pillow 11.3.0. I downloaded that wheel and listed it: there is **no `_imagingcms` module** (only `_imaging`,
  `_imagingft`, `_imagingmath`, `_imagingmorph`, `_imagingtk`, `_webp`) and no `lcms2` package in the Pyodide package
  list. So `ImageCms` does not work in Pyodide: a hard no for the browser unless the Pyodide build changes.
  Licences: Pillow is HPND (MIT-like), lcms2 is MIT: compatible with LGPL-2.1.
- **Pure Python fallback, measured** (`pure_icc.py`): reading a lut16 (mft2) CMYK press profile and converting
  sRGB to Lab to B2A1 with trilinear interpolation took about 60 lines and matched littleCMS within 0.2 percentage
  points of ink on 9 test colours (black, grey, primaries, gold, tomato, navy, skin). It takes 12.7 microseconds per
  colour: fine for vector colours and gradient stops, too slow for megapixel images (about 13 s per Mpx). It uses relative
  colorimetric without black point compensation. Caveats: only lut16 with Lab PCS (the one profile tested); lut8,
  lutAtoB, XYZ-PCS and matrix profiles need more code; trilinear is less precise than lcms's tetrahedral.
- In Pyodide, images are better left as tagged sRGB (route c2) than converted per pixel.

## Option e: external tools (handoff route, documentation only; not run here)

- **Ghostscript** (command line): `gs -dPDFX=3 -dBATCH -dNOPAUSE -sColorConversionStrategy=CMYK -sDEVICE=pdfwrite
  -sOutputFile=out.pdf PDFX_def.ps in.pdf`, after editing `lib/PDFX_def.ps` so `/ICCProfile` points at the shop's
  profile. Its docs say `-dPDFX` forces PDF 1.3 (so transparency is flattened) and that RGB is not allowed for PDF/X.
  The only free tool that makes X-1a/X-3.
- **Scribus** (GPL, free): place or open the file, turn colour management on, File > Export as PDF > Color: choose
  PDF/X-3 or X-1a and the shop's output profile (same flattening limit). Menu names from memory.
- **Acrobat Pro** (paid): Print Production > Preflight > convert to PDF/X-4 with the shop's profile; best fidelity for X-4.
  **Affinity** (paid): Export > PDF > "PDF (for print)" > PDF/X-4 or X-1a. Menu names from memory.
- **Ghostscript licence**: AGPL-3 or a commercial licence from Artifex. If funground only documents the command and the
  learner installs and runs it, funground neither distributes, links nor runs it, so the AGPL puts no obligation on us
  (my reading, not legal advice). Bundling or calling it would reach us and does not suit LGPL-2.1 or a browser build. Do not.

## Comparison

| Option | Print-shop fit | Native tool | Pyodide | Colour honesty | Licence / size | Verdict |
|---|---|---|---|---|---|---|
| a RGB as now | digital and POD shops that convert; not CMYK-only shops | no | yes | RGB, shop converts (often best) | none | keep as default |
| b naive CMYK (pypdf) | passes "is CMYK"; not PDF/X | no | yes, images slow | formula, not press-accurate, looks flat | none, small | do in 0.2, labelled |
| c1 CMYK + OutputIntent profile | closest to PDF/X-4 | no | yes | depends on profile | profile non-free, up to 2 MB | later, user-supplied profile |
| c2 tagged sRGB + OutputIntent | X-4-aware shops | no | yes | shop's RIP converts | 588-byte profile + OutputIntent profile | later |
| d lcms (ImageCms) | accurate | no (Pillow wheel) | no (no _imagingcms) | ICC-managed | MIT/HPND; Pillow optional | desktop-only, later |
| d' pure-Python ICC | accurate for vectors (0.2 pt) | no | yes | ICC-managed | about 60 lines ours; profile user-supplied | later; images stay tagged RGB |
| e Ghostscript, Scribus, Acrobat | true X-1a/X-3/X-4 | yes | no | managed | AGPL only if bundled; fine if documented | document as handoff |

## Recommendation

**0.2 (do):**

1. Keep RGB PDF as the default and say so plainly: many shops convert (Printful prefers sRGB; Avery and MOO convert). Add a
   guide section "which route for which shop" with the option e steps for shops that demand CMYK or PDF/X.
2. Offer an explicit opt-in CMYK PDF (for example a `color="cmyk"` choice on save) built from `rgb_to_cmyk.py` (naive
   mode), in a module next to `pdf_text.py`: pypdf only, no new dependency, works in Pyodide. Rules learned here: neutral
   greys and black to K only; resample gradients; convert every `/Group /CS`, soft-mask and pattern group; convert images
   with the per-pixel loop (warn on big ones). Fail safe like `_write_pdf` does (fall back to the RGB file). Label it
   "simple conversion, not colour-managed, ask your shop", and never call it PDF/X.
3. Add the leftover-RGB scan to the tests (zero DeviceRGB, zero rg/RG in the output) plus a soft-mask and blend case.
4. S-164's TrimBox/BleedBox stay as they are: PDF/X ingredients, not a claim.

**Later (0.3+):**

- ICC-managed CMYK with a user-supplied profile: littleCMS when Pillow is present (desktop), the pure-Python B2A reader
  (`pure_icc.py`) for vectors everywhere including the browser. Ask ECI for written permission before bundling any profile.
- PDF/X-4 output (OutputIntent, XMP, /ID, 1.6 header; route c1 or c2), only after a validator (veraPDF in CI, one real shop
  preflight) agrees. Prefer X-4 over X-1a because of transparency.
- Browser image conversion: ICC per pixel is too slow in pure Python; options are an lcms build in funground-cairo-wasm, or
  tagged sRGB (c2).

## Risks

- Naive CMYK may print duller than the shop's own conversion of RGB: for POD shops it can be worse than doing nothing.
  The docs must say so.
- Claiming PDF/X without a validator would be wrong; X-1a is out of reach without flattening.
- Pyodide timings are estimates (Pyodide was not run); the "no ImageCms in Pyodide" finding comes from the published
  wheel contents.
- No ICC profile found has an open licence; get a legal check before bundling anything.
- Shop behaviour was sampled from a few help pages; Vistaprint's could not be read.
- Blend modes behave differently in CMYK; the screen preview will not match the print.
- Every new PDF rewrite step (after text and layers) is another place that must fail safe.
