# Design note: colour for print (CMYK and sRGB in PDFs)

**Status:** built in Sprint 21 (S-170). Decision D-087 (e, with b): the maintainer asked for a CMYK colour model
the sketch writes in. Evidence: spike S-165 (`spikes/11_cmyk/RESULTS.md`). Contract rows S17, D4 and D5 in
[Semantic_Contract.md](Semantic_Contract.md); D2 is amended.
Code: `funground/color.py` (`Color.cmyk`, `Color.from_cmyk`), `funground/export/cmyk.py` (the stand-ins),
`funground/export/pdf_colour.py` (the PDF step), the `cmyk_standins` hook and `rgb_of` in
`funground/renderers/cairo2d.py`, `_write_pdf` in `funground/export/__init__.py`, the marks in
`funground/export/printing.py`, the profile `funground/data/sRGB.icc` made by `tools/make_srgb_profile.py`.
Tests: `tests/test_cmyk.py`, with the reader `tests/pdfcolour.py`.

## The problem

A print shop wants ink: cyan, magenta, yellow and black. A learner who writes `f.cmyk(0, 80, 100, 0)` should get exactly
those numbers in the PDF. Cairo, our renderer, writes only red, green and blue (`DeviceRGB`). The spike showed that a
finished PDF can be rewritten with pypdf. It also showed the hard part: after Cairo, an RGB colour is only three numbers, so
a rewrite cannot know which colours were meant as ink.

## The route

```text
 f.cmyk(c, m, y, k) ──► Color(r, g, b, a, cmyk=(c, m, y, k))        r, g, b by the screen formula
 IR keeps the Color, cmyk included (snapshots write {"cmyk": [...], "alpha": a})
 PDF export:   renderer.cmyk_standins = CmykStandins()
     every colour with .cmyk is drawn in a stand-in RGB, one per distinct set of inks
 surface.finish() ──► text step ──► layer step ──► colour step (pdf_colour) ──► page boxes
 colour step (pypdf), one walk over page, forms, patterns, soft-mask groups, shadings:
     stand-in `r g b rg`   ──►  `c m y k k`            (and RG ──► K)
     any other `r g b rg`  ──►  `/FunSRGB cs r g b sc`  (an ICCBased sRGB space)
     gradient functions    ──►  four-number C0 and C1 in a /DeviceCMYK shading
     image, shading, group ──►  /ICCBased sRGB (unless the file is only CMYK, see below)
     RGB in the file?      ──►  yes: sRGB output intent;  no: groups become /DeviceCMYK, no intent
```

Opacity stays what it was: Cairo writes it as an `ExtGState` alpha (`/CA`, `/ca`), which works with any colour space. A
gradient with see-through stops has a soft mask in Cairo's PDF; the mask is gray, the colour shading is CMYK.

## Why stand-ins can be trusted

Every RGB colour in funground is three whole numbers from 0 to 255, so Cairo writes it as `n / 255`. Cairo also keeps a
colour as a 16-bit number (the spike's `0.000015259` is 1/65535), so `n / 255` is `257 n / 65535`: 0, or 257 and up. A stand-in
is `k / 65535` with `k` from 1 to 255, so **no real colour can equal a stand-in**. There is nothing to search for in the
frame's ops, and no way to run out of free colours by luck. The three `k` values carry the number of the colour: the first two
count from 1 to 250 and the third is 251 to 255 (so a stand-in is never a grey). That is 312 500 different inks in one
document; more is a `ValueError`. Reading back, a number must be within 0.02 of a whole `k`; Cairo prints about nine digits.

The colour step is built to refuse, not to guess:

- A colour that is part-stand-in, or a stand-in this document never made, is an error.
- A gradient function that is not an exponential (Type 2) or a stitching (Type 3) function is an error. Cairo writes only
  these for funground's gradients.
- After writing, the file is read back and every content stream is scanned, whether or not the walk reached it. No `rg` or
  `RG` may remain, and no shading may still be `DeviceRGB`.
- If the document has cmyk() colours and any of this fails, the file is **removed** and `ColourError` says why. A print file with a
  wrong colour is worse than none. If it has none, a failure leaves the file as Cairo wrote it (untagged RGB, as before S-170).

## What is CMYK and what is not

| In the PDF | Colour space |
|---|---|
| fills, strokes, text, background, shadow, crop marks made with `f.cmyk()` | `DeviceCMYK` (`k`, `K`) |
| gradient stops made with `f.cmyk()` | `DeviceCMYK` shading, exact four-number stops |
| every other colour | `ICCBased` sRGB, by `/FunSRGB cs r g b sc` |
| pictures, `set()` pixels, filters, tinted pictures | RGB pixels, tagged sRGB. A picture is pixels; funground does not convert pixels to ink |
| the page and each transparency group | `DeviceCMYK` if the file has nothing RGB; else sRGB |

A **tint** is a colour, but it multiplies pixels, so it works as its screen RGB on the picture. **Erase** strokes and fills write an
opaque black that is never seen; it is RGB. A shape with **alpha 0** is written by Cairo in black (it throws the colour away), so it
also counts as RGB. Neither changes anything you can see.

A gradient that mixes cmyk() stops and RGB stops is a CMYK gradient: its RGB stops are turned into inks by the opposite of the
screen formula, and the colours between stops are mixed in CMYK by the viewer.

**Blend modes and groups.** PDF mixes colours in the colour space of the group. A file that is only CMYK is mixed in CMYK, a mixed
file in sRGB. `multiply` and `overlay` can therefore look different from the screen's RGB picture. The screen is an approximation.

## RGB tagging and the output intent

Every RGB colour in a PDF is now tagged: the file says "this red is sRGB red". The profile is `funground/data/sRGB.icc`, 588 bytes,
made once by littleCMS through Pillow (`tools/make_srgb_profile.py`) and saved as package data. Pillow stays optional, and the
browser's Pillow has no `ImageCms`, so the product never makes it at run time. It says "No copyright, use freely"
(see THIRD_PARTY_LICENSES.md). A file with RGB in it also gets an **output intent** naming sRGB IEC61966-2.1, as the spike's
tag_srgb probe did. This is not PDF/X: the file has no `GTS_PDFXVersion` and nothing is claimed (the spike's rule stands: no validator, no claim).
The intent uses the subtype `GTS_PDFX` because it is the one print software looks for.

A file that is **only CMYK** has no sRGB colour space and no output intent. An RGB intent on a CMYK file would say the wrong thing.
A mixed file has the intent; its CMYK colours stay DeviceCMYK. (To be checked with a print shop's preflight: the spike had none.)

What changes in a PDF written without any cmyk() colour: its `rg` and `RG` operators become `/FunSRGB cs ... sc` and `/FunSRGB CS ... SC`;
its shadings, images and transparency groups name the sRGB space; it gains one 588-byte profile stream (compressed) and an
`/OutputIntents` entry; pypdf writes it again, so object numbers and the cross-reference table change. The header version is kept (the
steps before and after used to lower it to 1.3). Nothing is drawn differently, except that pdfium, which colour-manages tagged colours,
can move a channel by one step. The bytes stay the same from run to run.

## Crop marks

With `marks=True` the marks are drawn in registration colour: `f.cmyk(100, 100, 100, 100)`. Printers use it so the marks appear on every
plate, and a plate that is out of register shows. In a PDF that is `1 1 1 1 K`. (On screen, in a PNG and in an SVG the formula
makes it black, but marks are only in PDFs.) A file with marks therefore holds a CMYK colour, even when the drawing is all RGB.

## Limits (said plainly)

- The CMYK is **not colour-managed**. Nothing converts `f.color("red")` to ink, and funground ships no CMYK profile (the licences, in
  the spike). The sRGB tag lets the print shop convert the RGB colours itself.
- The screen shows an approximation: R = 255 x (1 - C) x (1 - K). A press mixes ink in its own way, so the screen will not match the print exactly (the spike found a formula looks flat in viewers).
- No spot colours, no total-ink limit, no PDF/X.
- Pictures stay RGB.
