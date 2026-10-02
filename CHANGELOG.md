# Changelog

What changed in funground, newest first. Release numbers follow the
[roadmap](docs/Roadmap.md). Decisions are cited as D-nnn from the
[decision log](docs/design/Decision_Log.md).

## Unreleased — will become 0.1

The first public release. It starts from *playground* v0.5, a small teaching wrapper around
pygame-ce that was never published.

### Renamed
- The library is now **funground**: `pip install funground`, `import funground as f` (D-020).
- `PlaygroundWarning` and `PlaygroundError` are `FungroundWarning` and `FungroundError`.
- Environment variables are `FUNGROUND_*`, for example `FUNGROUND_HEADLESS=1`.

### Changed from v0.5
- **A single number is a grey, not a packed colour.** `fill(0xFF0000FF)` is no longer a colour; use
  `"0xFF0000"` or a tuple (D-032).
- **Drawing is done by Cairo** and is anti-aliased. Fractional coordinates are honoured (D-005).
- **The fourth colour value (alpha) now works**: translucent fills and strokes (D-003).
- **Strokes are centred on the shape's edge**, with round ends and corners by default (D-004).
- **Text uses the bundled DejaVu Sans font** and looks the same on every computer.
  `text_size(n)` is an n-pixel em, so text is about 1.4 times larger than in v0.5 (D-012).
- **`mouse_pressed` is now `is_mouse_pressed`**, because `mouse_pressed()` is a callback you can
  define (D-016). The old name gives an error that names the new one.
- **Crisp on scaled displays**: coordinates are logical pixels, rendering is at full resolution.

### Added
- **GIF and MP4:** a script saves every page as a frame with `f.save("x.gif")` or `f.save("x.mp4")`; `f.frame_duration(seconds)` sets how long a page and the pages after it are shown. An animated sketch records itself with `f.save_gif(path, seconds)` or `f.save_movie(path, seconds)`. A GIF is written with Pillow (`pip install funground[extras]`) or ffmpeg; an MP4 needs ffmpeg on the PATH, and the error says how to install it (S-100, contract M1, D-048; how ffmpeg is supplied is D-045).
- **Controls:** `f.create_slider(low, high, value=None, step=None, label=None)`, `f.create_checkbox(label, checked=False)` and `f.create_button(label)` make a slider, a tick box and a button in a panel below the canvas. Read them with `slider.value()`, `box.checked()` and `button.clicked()`; `slider.value(v)` and `box.checked(b)` set them. The panel is not part of the canvas, so it is not in the size, saves, pixels or the mouse position, and clicks on it do not reach the sketch's mouse callbacks. Make controls in `setup()`, not in `draw()` or in a script (S-101, D-047).
- **Path shapes and booleans:** a path from `f.path()` gets `rect`, `ellipse`, `circle` and `polygon`, and `union`, `intersection`, `difference`, `xor` (also `|`, `&`, `-`, `^`) and `remove_overlap`, each giving a new path (S-086). **New dependency:** `skia-pathops`, a small Skia library, now installs with funground (D-037, ADR-005).
- **Path outlines, queries and moves:** a path gets `expand_stroke` (cap, join, miter limit and dash, open lines too), `bounds`, `contains`, `translate`, `scale`, `rotate` and `copy` (S-087).
- **Sound:** `f.load_sound(path)` reads a WAV, OGG or MP3 file and returns a sound with `play()`, `loop()`, `stop()`, `pause()`, `set_volume()`, `is_playing()` and `duration()`. `level()` (loudness) and `spectrum(bands)` (strength by pitch, from a built-in FFT) let a sketch follow the music. With no sound device a sound plays silently and keeps time, so a sketch behaves the same (S-098, S-099, contract A1, A2, D-046).
- **SVG files:** `f.load_svg(path)` reads an SVG file into a picture made of its shapes, so it stays sharp at any size and stays vector in a saved PDF or SVG; `f.svg_paths(path)` gives the shapes as paths, for booleans and clips. Paths, basic shapes, groups, `<use>`, transforms, colours with opacity, strokes, dashes and `fill-rule` are read; gradients paint with their first colour; text, images, filters and masks are ignored (S-092, contract P11). **New dependency:** `svgelements`, a small pure-Python SVG reader, now installs with funground (D-041).
- **Rounded corners:** `f.rect(x, y, w, h, *radii)` and `f.square(x, y, size, *radii)` take one radius for all corners, or four in p5's order (top-left, top-right, bottom-right, bottom-left); the path builder's `rect` takes them too (S-089). This is an approved change to the v0.5 `rect` signature (D-040): calls without a radius draw exactly as before.
- **Letters as a path:** `f.text_path(message, x, y)` returns the outlines of the text as a path, set exactly like `f.text()`, so you can cut them out of a shape, outline them, fill them with a gradient or clip with them (S-088).
- **Text as points:** `f.text_to_points(message, x, y, spacing=5)` returns `(x, y)` points along the outlines of the text, one every `spacing` pixels, for dotted and particle looks (D-050).
- **Font information:** `f.current_font()` returns the font text is set in; `font.family()`, `font.style()`, `font.variations()`, `font.features()` and `font.contains(text)` answer questions about it (D-050).
- **Tracking, OpenType features, variable fonts:** `f.text_tracking(pixels)` adds space after every letter, `f.text_features(liga=False)` turns OpenType features on or off, and `f.font_variations(wght=700)` sets a variable font's axes. They apply to `f.text`, `f.text_box`, `f.text_width` and `f.text_path`, and a saved state and a picture each keep their own (S-090).
- **Real text in PDFs:** every PDF funground saves (`f.save("x.pdf")`, a document of several pages,
  a picture's `g.save("x.pdf")`, and pictures drawn into any of these) holds its text as real text
  that can be selected, searched and copied. Each font used is put into the file once, as a subset
  of the letters used, and the page looks the same as before. A font that forbids being put in a
  file is still saved as letter shapes, and so is all text in SVG files. Text-heavy PDFs are about
  ten times smaller (S-094). **New dependency:** `pypdf`, a small pure-Python PDF library, now
  installs with funground (D-043).
- **Mixed styles in one text:** `f.FormattedString()` holds runs of text, and `append(text, size=, style=, color=, font=, tracking=, features=, variations=)` gives a run its own look; settings left out follow the drawing state. `f.text`, `f.text_box`, `f.text_width` and `f.text_path` take one, a line is as tall as its tallest run, and `f.text_box` returns the overflow as a FormattedString (S-091).
- **Full screen in scripts:** `f.full_screen()` at the top of a script makes the canvas the screen's size, and `f.show()` shows it full screen (S-085).
- **Pages:** in a script, `f.new_page()` starts a new page (a size, or a name such as `"A5"`);
  `f.page_count()` counts them and `f.page_size("A4")` gives a name's size. `f.save("x.pdf")` writes
  every page into one PDF, PNG and SVG write `x_1.png`, `x_2.png`, …, and `f.show()` turns pages with
  the arrow keys (S-084).
- **Pixels:** `f.get(x, y)` reads a colour, `f.get(x, y, w, h)` copies a region into a new picture,
  `f.set(x, y, color)` writes one pixel, and `f.load_pixels()`, `f.pixels` and `f.update_pixels()`
  read and write them all at once, as in p5 (pixel density 1; also on pictures). Reading sees the
  drawing so far, this frame included.
- **Copy, resize, mask and filters:** `g.copy()`, `g.resize(w, h)` (a 0 keeps the shape) and
  `g.mask(other)` change pictures; `f.filter(kind, value)` and `g.filter(...)` apply `"threshold"`,
  `"gray"`, `"opaque"`, `"invert"`, `"blur"`, `"posterize"`, `"erode"` or `"dilate"` to the canvas or
  a picture. `pip install funground[extras]` makes `"posterize"`, `"erode"` and `"dilate"` faster;
  the results are the same without it.
- **Crisp pixel art:** under `f.no_smooth()`, `f.image()` scales pictures with the nearest pixel.
- **Tint and parts of a picture:** `f.tint(color)` / `f.no_tint()` multiply the colour and alpha of
  pictures drawn with `f.image()`, and `f.image(picture, x, y, w, h, sx, sy, sw, sh)` draws only a
  part of a picture, as in p5 (also on `g.image`).
- **Gallery browser:** `python tools/gallery_browser.py` browses every example by topic, with its
  picture, description and code, and runs it in its own window. It is itself a funground app.
- **Scripts:** a file can be a script instead of an animated sketch: no `draw()`, no `f.run()`.
  `f.size()` makes a canvas with no window, `f.save()` writes at once, and the new `f.show()` opens a
  window to look at it. A file that mixes the two styles gets a clear error, and a program that has
  a `draw()` but never calls `f.run()` gets a one-line hint when it ends (D-029).
- **Shapes:** `square`, `triangle`, `quad`, `polygon`, `arc`; `begin_shape` … `end_shape` with
  `vertex`, `bezier_vertex`, `quadratic_vertex`, `curve_vertex`, contours for holes; `bezier`,
  `curve` and their point and tangent helpers; reusable paths with `path()` and `draw_path`.
- **Clipping:** `clip`, `no_clip`. **Transparent canvas:** `clear`.
- **Strokes:** `stroke_cap`, `stroke_join`, `miter_limit`, `stroke_dash`, `no_dash`;
  `no_smooth` / `smooth` for pixel art.
- **Colour mode:** `color_mode(mode, max1, max2, max3, max_alpha)` as in p5, with modes `"rgb"`,
  `"hsb"` and `"hsl"`; `color_mode("rgb", 1)` reads DrawBot's 0–1 colours (D-031).
- **Separate colour numbers:** `fill(255, 0, 0)`, `stroke(128)`, `background(30, 30, 60)` work as well as
  tuples, read in the current colour mode (D-032).
- **Grey numbers:** one number is a grey and two are a grey and an opacity, as in p5:
  `fill(128)`, `fill(128, 100)` (D-032).
- **Colour:** `hsb`, `hsl`, `color` objects, `lerp_color`; `linear_gradient` and
  `radial_gradient`, usable wherever a colour goes; `blend_mode`, `opacity`, `shadow`.
- **Transforms:** `translate`, `rotate` (degrees), `scale`, `shear_x`, `shear_y`, `apply_matrix`,
  `reset_matrix`; `push` / `pop` and `with f.saved_state():`.
- **Text:** `text_width`, `text_align`, `text_ascent`, `text_descent`, several lines with
  `text_leading`, `text_box` with word wrap and overflow, `load_font`, `text_font`, `text_style`
  with bundled bold and italic.
- **Animation and time:** `no_loop`, `loop`, `redraw`, `is_looping`, `exit`, `millis`,
  `frame_rate`, `second` … `year`; `run(max_frames=n)`.
- **Input:** callbacks `mouse_pressed`, `mouse_released`, `mouse_moved`, `mouse_dragged`,
  `mouse_clicked`, `mouse_wheel`, `key_pressed`, `key_released`, `key_typed`; live values
  `pmouse_x`, `pmouse_y`, `mouse_button`, `key`, `key_code`, `is_key_pressed`.
- **Maths and randomness:** `map_range`, `lerp`, `norm`, `mag`, `radians`, `degrees`,
  `random_seed`, `random_gaussian`, `random_choice`, `noise` (the same values as p5.js),
  `noise_seed`, `noise_detail`, `Vector`.
- **Drawing modes:** `rect_mode`, `ellipse_mode` and `image_mode` place shapes and pictures by their corner, opposite corners, centre or radius, as in p5.js. The defaults are unchanged (D-030).
- **Off-screen pictures:** `create_graphics` and `image`.
- **Image files:** `load_image` reads PNG, JPEG, GIF, BMP and TGA files into a picture. Phone photos are turned the right way up (ADR-004).
- **Saving:** `save` to PNG, PDF or SVG; `save_frames` for numbered frames; PDF and SVG output is
  true vector.
- **Window:** `resize_canvas`, `full_screen`, `cursor`, `no_cursor`.
- **Running without a window:** `FUNGROUND_HEADLESS=1`.
- **Teaching material:** a [User Guide](docs/guide/README.md), an
  [Examples Gallery](docs/gallery/README.md) with an example for every function, and a Quick
  Reference.

### Licence
- funground is LGPL-2.1-or-later (D-025). Example code is CC0 (D-026). Dependencies keep their own
  licences; see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

### Still to come before 0.1
- Images, pages and multi-page documents, more path tools, richer typography, SVG import, sound,
  GIF and video export, and controls (Phase 3, D-027).
