# Design note: text as outlines, `TextRun` reserved

**Status:** agreed direction (D-006), 24 September 2026. Validated by Spike 06 (S-031) before implementation (S-029).

## Why not Cairo's text API

pycairo exposes only the "toy" text API: it resolves a *family name* through the platform font
system and documents its FreeType font-face support as not implemented. A bundled `.ttf` cannot be
loaded into a Cairo font face, so text would render differently on every machine and could never be
golden-tested.

## The route

```
bundled OFL font file
        │
   uharfbuzz  ──► shaped glyphs: (glyph id, x-advance, x/y offset), Unicode-capable
        │
   fontTools  ──► glyph outlines (glyph set + pen) → immutable Path per glyph id (cached)
        │
   Playground IR: translate/scale + DrawPath ops
        │
   any renderer / exporter (Cairo raster, PDF, SVG; later Skia)
```

Text stops being a renderer-specific primitive: every backend sees the same geometry, so text is
deterministic across platforms and renderers.

## Shape of the implementation (S-029)

```
FontResource
  ├── HarfBuzz face/font (uharfbuzz)
  ├── fontTools glyph set
  └── glyph-outline cache: glyph id → Path        (built once per glyph, never per frame)

TextRun
  ├── semantic text, font, size                  (kept — see "reserved")
  ├── shaped glyphs (ids + positions)
  └── materialise_outlines() → list of IR ops    (what Phase 1–2 renderers consume)
```

Anchor stays top-left (contract T1): the run's origin is offset by the font ascent.

## Reserved: don't bake "text is paths forever" into the IR

Outlines cost: PDF text is not searchable or selectable; text extraction/accessibility is lost; file
size grows; no hinting at small sizes. The maintainer accepted this for now (D-006). To keep the way
out open, the IR carries a **`TextRun` op** that renderers *may* materialise into outlines (Phase 1–2
does, always) — so a later PDF exporter (S-032) can instead embed/subset the font and emit real text
without changing learner code or the IR.

## What Spike 06 must answer

Single line only, no layout or wrapping: quality at 12–48 px versus pygame and Cairo toy text;
baseline/anchor correctness; per-frame cost with and without the outline cache; byte-identical output
across runs and platforms; that shaping is genuinely Unicode (one non-Latin sample, kerning `AVATAR`,
ligature `office`); PDF/SVG output. Then pick the font.
