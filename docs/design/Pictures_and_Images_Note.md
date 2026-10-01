# Design note: pictures, images and pixels

**Status:** decided (D-021, 26 Sept 2026; D-028 and ADR-004, 1 Oct 2026; D-035, 1 Oct 2026). Built in
Sprint 6 (S-052) and Sprint 7 (S-077 to S-080). Contract rows P1 to P10 in
[Semantic_Contract.md](Semantic_Contract.md); P11 (SVG) has its own note,
[SVG_Import_Note.md](SVG_Import_Note.md). Code: `funground/picture.py`, `funground/imaging.py`,
`CairoRenderer` in `funground/renderers/cairo2d.py`, `funground/export/__init__.py`.

## The problem

A learner needs three things that look alike but are not:
- an off-screen canvas to draw on (`create_graphics`);
- a picture from a file (`load_image`);
- the canvas's own pixels, read and written one by one (`get`, `set`, `pixels`, `filter`).

They must also keep working in PDF and SVG, where a drawing should stay vector if it can.

## The route: one picture type

D-021 chose one type for all of them. A picture is a small sketch with its own surface.

```
f.create_graphics(w, h) ──┐
f.load_image(path)  ──────┼──►  Picture  ──►  f.image(pic, x, y)  ──►  ir.Image op
f.get(x, y, w, h)   ──────┘     │   ▲                                    (carries a Snapshot)
                                │   └── g.circle(), g.fill() ... forwarded to the inner Sketch
                                ▼
              inner Sketch  +  its own CairoRenderer  +  one persistent Cairo surface
```

- `Picture` (`picture.py`) owns a private `Sketch` with a `_PictureBacking` platform. The backing
  reports the window's scale and never opens a window.
- Drawing methods are forwarded by `Picture.__getattr__`, but only names in `ALLOWED_METHODS`
  (P2). Window-only functions and pure helpers give an `AttributeError` that explains why.
- `g.save` and `g.image` are real methods. They act at once instead of queuing.

## Persistent rendering through `draw_batch`

A window clears its state every frame. A picture must not (P2). Ops pile up in the inner sketch's
`frame`. They are drawn only when the picture is flushed: drawn with `image()`, saved, read, copied,
resized or masked.

- `Picture._flush_ops` calls `CairoRenderer.draw_batch(ctx, frame, depth)`. Unlike `draw()`, it has
  no Save/Restore wrapper and no unwind. The open Save depth is kept in `_persistent_depth`.
- The base matrix (the HiDPI scale that `reset_matrix()` returns to) is fixed once in
  `Picture.__init__`. So transform, clip and `push` nesting survive between flushes like pixels do.
- Each flush adds one to `_version` and empties `_snapshot_cache`.
- `Picture._snapshot()` makes an immutable `Snapshot`: a byte copy of the pixels plus the history.
  It is cached per version, so drawing one unchanged picture many times copies it once.
- `draw_image` puts the `Snapshot` on `ir.Image.snapshot`. That is how P3 ("as it is at the moment
  of the call") holds: later drawing cannot change what was placed.

## Loading, tint and parts

- `imaging.decode` reads a file with pygame-ce (ADR-004) into premultiplied BGRA, which is Cairo's
  own layout. `Picture.from_pixels` copies the bytes onto the surface with no conversion.
- It checks that Cairo's stride is `width * 4`. `imaging.py` may not import Cairo, so the check
  lives in `from_pixels`.
- JPEG orientation is read by funground (`exif_orientation`, plain Python, never raises) and
  applied with `_orient`.
- `f.load_image` works before `size()` because it needs no window.
- Tint (P5) is `imaging.tint_pixels`: a pygame multiply on premultiplied pixels, then alpha
  through Cairo. Cairo operators would mis-colour soft edges (found in review, S-078).
- Parts (P6) clip the source rectangle to the picture in `draw_image`, then the renderer clips to
  the destination box and scales (`_draw_image`).

## Pixel access

```
f.set(x, y, c) ─► _pending_pixels ─┐
                                    ├─► one ir.Pixels op (region + CRC32; bytes ride on .data)
f.update_pixels() ─────────────────┘
f.get / load_pixels / filter ─► _sync_canvas ─► read_logical (logical pixels) ─► bgra_to_rgba
```

- Reading renders what is recorded so far (`_render_so_far`). A window frame is drawn in steps
  with `begin_frame`, `draw_batch` and `end_frame`. `_frame_drawn` counts what is already done.
- Many `set()` calls become one `Pixels` op (`patch_op`). `_append` flushes waiting writes first,
  so order is kept.
- A logical pixel covers `ceil(x*scale)` up to `ceil((x+1)*scale)` physical pixels. `get` reads
  the first one and `set` paints all of them (`_sample`, `block_from_logical`).
- The surface is premultiplied. `bgra_to_rgba` and `rgba_to_bgra` do the arithmetic only for
  partly transparent pixels, with rounding chosen so `load_pixels` then `update_pixels` changes
  nothing.
- `_draw_pixels` ignores transform, clip, tint, opacity and blend mode. On PDF and SVG it uses
  OVER, because those surfaces cannot replace.

## Filters, with and without Pillow

`filter_bgra` runs on plain RGBA at logical resolution. Blur is the exception: it runs on
premultiplied pixels with pygame-ce `gaussian_blur`, so see-through edges get no fringe.

- `threshold`, `gray`, `opaque`, `invert` use lookup tables and slicing in plain Python on bytes
  that pygame-ce has already reordered. P10 says "use pygame-ce"; only blur does so directly.
- `posterize`, `erode`, `dilate` use Pillow when `_pillow()` finds it, else plain Python
  (`_map_channels`, `_extreme_plain`). The results are the same bytes; a test checks it.
- The result goes back as one `Pixels` op, so a filter is a raster step in PDF and SVG.

## PDF and SVG: the history-replay rule (P3)

Raster targets paint the snapshot's pixels. PDF and SVG targets replay the picture's drawing:

1. `_update_history` keeps ops since the last `Clear` of alpha 0 or 255 (`_resets_history`).
2. Any `Pixels` op sets `_history = None`. `resize` and `mask` do the same.
3. When `len(history) > HISTORY_LIMIT` (10 000) the history is dropped. A new full `Clear`
   starts one again. This bounds memory.
4. `_draw_image` replays with `_replay_image_history` when the target is not an `ImageSurface`,
   history exists and there is no tint. It clips to the picture's bounds and paints the result as
   one group so opacity applies once.
5. Otherwise it embeds pixels (`paint_picture_pixels`). `Picture.save` and `save_picture` follow
   the same rule, so a save never fails because a picture drew a lot.

A loaded image has `_history = None`. It embeds pixels until a full `background` or `clear` on it
starts a history.

## Alternatives rejected

- **Two types (D-021 B)** and **defer (C)**: more to learn, and a rename risk after release.
- **Pillow in the base install (D-028 B)**: about 6 MB for every learner. Pillow stays an extra.
- **PNG only through Cairo (D)**: learners bring JPEG photos.
- **numpy arrays for pixels**: not installed. Hence the per-pixel loops over soft edges only.

## Invariants and edge cases

- A picture can be drawn onto another, never onto itself (`ValueError`).
- `shadow` never applies to pictures (`_composite_of` has no shadow field for `Image`).
- Snapshots never hold pixels. A JSON round trip leaves `Image.snapshot` and `Pixels.data` at
  `None`, and drawing such an op raises `RuntimeError`.
- `resize` unwinds the picture's pushes and re-attaches the surface. `copy` starts with default
  state.
- Under `no_smooth()` the renderer scales pictures with the nearest filter.

## Limits and open questions

- **Name clash.** `_graphics_counter` is reset by `_begin_script` and `run_namespace`. A picture
  loaded *before* `f.size()` is named `graphics-1`, and so is the first `create_graphics` after.
  Pixels are unaffected (they travel in the snapshot), but IR snapshots become ambiguous.
  P3 and P4 promise numbering "in creation order within a run".
- P3 says history starts at an "opaque" `background` or `clear`. `clear()` is alpha 0, and the
  code resets on 0 or 255. The behaviour is right; the wording is loose.
- P3 cites `no_smooth` as "S11"; the row is C6a.
- Tinted and pixel-written pictures are never vector in PDF/SVG. Loaded images have no finer data
  than their own pixels on a HiDPI screen.

## Tests

`tests/test_pictures.py` (P1 to P3, history, the 10 000 limit), `test_images.py` (P4, EXIF),
`test_tint_and_parts.py` (P5, P6), `test_pixels.py` (P7, P8), `test_filters.py` (P9, P10, with and
without Pillow), `test_boundaries.py` (pygame only in `imaging.py` and `platform/`). Gallery
examples: `tests/test_gallery.py`.
