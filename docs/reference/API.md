# funground API reference

Every public name in funground, with its signature, arguments and an example. This page is generated from the docstrings in the code, so `help(f.name)` in Python shows the same text. Do not edit it by hand: change the docstring and run `python tools/make_api_reference.py`.

Related pages: the [Quick Reference](Quick_Reference.md) (every function by topic, with pictures), the [guide](../guide/README.md) (learn step by step), [When something goes wrong](../guide/errors.md), the [glossary](../guide/glossary.md), [funground compared with p5 and DrawBot](Compared_with_p5_and_DrawBot.md) and the [documentation front door](../README.md).

In the examples, `import funground as f` is understood.

## Contents

- [Sketch and loop](#sketch-and-loop): [`size`](#fn-size), [`resize_canvas`](#fn-resize_canvas), [`full_screen`](#fn-full_screen), [`run`](#fn-run), [`loop`](#fn-loop), [`no_loop`](#fn-no_loop), [`redraw`](#fn-redraw), [`is_looping`](#fn-is_looping), [`exit`](#fn-exit), [`stop`](#fn-stop), [`frame_rate`](#fn-frame_rate), [`show`](#fn-show), [`smooth`](#fn-smooth), [`no_smooth`](#fn-no_smooth)
- [Shapes](#shapes): [`point`](#fn-point), [`line`](#fn-line), [`rect`](#fn-rect), [`square`](#fn-square), [`ellipse`](#fn-ellipse), [`circle`](#fn-circle), [`triangle`](#fn-triangle), [`quad`](#fn-quad), [`polygon`](#fn-polygon), [`arc`](#fn-arc), [`rect_mode`](#fn-rect_mode), [`ellipse_mode`](#fn-ellipse_mode)
- [Curves and custom shapes](#curves-and-custom-shapes): [`bezier`](#fn-bezier), [`bezier_point`](#fn-bezier_point), [`bezier_tangent`](#fn-bezier_tangent), [`curve`](#fn-curve), [`curve_point`](#fn-curve_point), [`curve_tangent`](#fn-curve_tangent), [`curve_tightness`](#fn-curve_tightness), [`begin_shape`](#fn-begin_shape), [`end_shape`](#fn-end_shape), [`vertex`](#fn-vertex), [`bezier_vertex`](#fn-bezier_vertex), [`quadratic_vertex`](#fn-quadratic_vertex), [`curve_vertex`](#fn-curve_vertex), [`begin_contour`](#fn-begin_contour), [`end_contour`](#fn-end_contour)
- [Colour](#colour): [`background`](#fn-background), [`clear`](#fn-clear), [`color`](#fn-color), [`color_mode`](#fn-color_mode), [`hsb`](#fn-hsb), [`hsl`](#fn-hsl), [`lerp_color`](#fn-lerp_color), [`linear_gradient`](#fn-linear_gradient), [`radial_gradient`](#fn-radial_gradient)
- [Fill and stroke](#fill-and-stroke): [`fill`](#fn-fill), [`no_fill`](#fn-no_fill), [`stroke`](#fn-stroke), [`no_stroke`](#fn-no_stroke), [`stroke_width`](#fn-stroke_width), [`stroke_cap`](#fn-stroke_cap), [`stroke_join`](#fn-stroke_join), [`miter_limit`](#fn-miter_limit), [`stroke_dash`](#fn-stroke_dash), [`no_dash`](#fn-no_dash), [`shadow`](#fn-shadow), [`no_shadow`](#fn-no_shadow), [`opacity`](#fn-opacity), [`blend_mode`](#fn-blend_mode), [`erase`](#fn-erase), [`no_erase`](#fn-no_erase), [`tint`](#fn-tint), [`no_tint`](#fn-no_tint)
- [Text and fonts](#text-and-fonts): [`text`](#fn-text), [`text_align`](#fn-text_align), [`text_ascent`](#fn-text_ascent), [`text_descent`](#fn-text_descent), [`text_leading`](#fn-text_leading), [`text_box`](#fn-text_box), [`text_path`](#fn-text_path), [`text_to_points`](#fn-text_to_points), [`current_font`](#fn-current_font), [`text_size`](#fn-text_size), [`text_style`](#fn-text_style), [`text_tracking`](#fn-text_tracking), [`text_fallback`](#fn-text_fallback), [`system_font`](#fn-system_font), [`text_features`](#fn-text_features), [`font_variations`](#fn-font_variations), [`text_width`](#fn-text_width), [`text_font`](#fn-text_font), [`load_font`](#fn-load_font)
- [Transforms and the state stack](#transforms-and-the-state-stack): [`translate`](#fn-translate), [`rotate`](#fn-rotate), [`scale`](#fn-scale), [`shear_x`](#fn-shear_x), [`shear_y`](#fn-shear_y), [`apply_matrix`](#fn-apply_matrix), [`reset_matrix`](#fn-reset_matrix), [`push`](#fn-push), [`pop`](#fn-pop), [`saved_state`](#fn-saved_state)
- [Paths and clipping](#paths-and-clipping): [`path`](#fn-path), [`draw_path`](#fn-draw_path), [`clip`](#fn-clip), [`no_clip`](#fn-no_clip)
- [Marks](#marks): [`mark`](#fn-mark)
- [Play](#play): [`variations`](#fn-variations), [`keep`](#fn-keep)
- [Pictures and layers](#pictures-and-layers): [`create_graphics`](#fn-create_graphics), [`layer`](#fn-layer), [`hide_layer`](#fn-hide_layer), [`show_layer`](#fn-show_layer)
- [Images and SVG](#images-and-svg): [`image`](#fn-image), [`image_mode`](#fn-image_mode), [`load_image`](#fn-load_image), [`load_svg`](#fn-load_svg), [`svg_paths`](#fn-svg_paths)
- [Pixels and filters](#pixels-and-filters): [`get`](#fn-get), [`set`](#fn-set), [`load_pixels`](#fn-load_pixels), [`update_pixels`](#fn-update_pixels), [`filter`](#fn-filter)
- [Randomness and noise](#randomness-and-noise): [`random`](#fn-random), [`random_choice`](#fn-random_choice), [`random_gaussian`](#fn-random_gaussian), [`random_seed`](#fn-random_seed), [`noise`](#fn-noise), [`noise_detail`](#fn-noise_detail), [`noise_seed`](#fn-noise_seed)
- [Maths](#maths): [`constrain`](#fn-constrain), [`distance`](#fn-distance), [`lerp`](#fn-lerp), [`map_range`](#fn-map_range), [`mag`](#fn-mag), [`norm`](#fn-norm), [`degrees`](#fn-degrees), [`radians`](#fn-radians)
- [Time](#time): [`year`](#fn-year), [`month`](#fn-month), [`day`](#fn-day), [`hour`](#fn-hour), [`minute`](#fn-minute), [`second`](#fn-second), [`millis`](#fn-millis)
- [Interaction and controls](#interaction-and-controls): [`key_down`](#fn-key_down), [`cursor`](#fn-cursor), [`no_cursor`](#fn-no_cursor), [`create_button`](#fn-create_button), [`create_checkbox`](#fn-create_checkbox), [`create_slider`](#fn-create_slider)
- [Saving](#saving): [`save`](#fn-save), [`save_frames`](#fn-save_frames), [`save_gif`](#fn-save_gif), [`save_movie`](#fn-save_movie)
- [Ground](#ground): [`area`](#fn-area), [`grid`](#fn-grid), [`mm`](#fn-mm), [`inch`](#fn-inch), [`ground`](#fn-ground)
- [Motion and pages](#motion-and-pages): [`frame_duration`](#fn-frame_duration), [`new_page`](#fn-new_page), [`page_size`](#fn-page_size), [`page_count`](#fn-page_count)
- [Sound](#sound): [`load_sound`](#fn-load_sound), [`create_sound`](#fn-create_sound), [`tone`](#fn-tone), [`note`](#fn-note), [`pluck`](#fn-pluck), [`melody`](#fn-melody), [`sequence`](#fn-sequence), [`mix`](#fn-mix), [`drone`](#fn-drone), [`note_to_frequency`](#fn-note_to_frequency), [`frequency_to_note`](#fn-frequency_to_note), [`chord_notes`](#fn-chord_notes)
- [Music analysis and the microphone](#music-analysis-and-the-microphone): [`microphone`](#fn-microphone), [`microphones`](#fn-microphones)
- [Drawing sound](#drawing-sound): [`draw_wave`](#fn-draw_wave), [`draw_spectrum`](#fn-draw_spectrum), [`spectrogram`](#fn-spectrogram), [`draw_pitch_line`](#fn-draw_pitch_line)
- [Ragas and talas](#ragas-and-talas): [`ragas`](#fn-ragas), [`raga`](#fn-raga), [`talas`](#fn-talas), [`tala_info`](#fn-tala_info), [`tala`](#fn-tala), [`match_ragas`](#fn-match_ragas)
- [Classes](#classes): [`Vector`](#cls-Vector), [`FormattedString`](#cls-FormattedString)
- [Live values](#live-values): [`delta_time`](#live-delta_time), [`frame_count`](#live-frame_count), [`ground`](#live-ground), [`height`](#live-height), [`is_key_pressed`](#live-is_key_pressed), [`is_mouse_pressed`](#live-is_mouse_pressed), [`key`](#live-key), [`key_code`](#live-key_code), [`mouse_button`](#live-mouse_button), [`mouse_x`](#live-mouse_x), [`mouse_y`](#live-mouse_y), [`pixels`](#live-pixels), [`pmouse_x`](#live-pmouse_x), [`pmouse_y`](#live-pmouse_y), [`width`](#live-width)
- [Classes in detail](#classes-in-detail): [`Sound`](#cls-Sound), [`Microphone`](#cls-Microphone), [`Picture`](#cls-Picture), [`Vector`](#cls-Vector), [`FormattedString`](#cls-FormattedString), [`Run`](#cls-Run), [`PathBuilder`](#cls-PathBuilder), [`Mark`](#cls-Mark), [`Area`](#cls-Area), [`Ground`](#cls-Ground), [`Cell`](#cls-Cell), [`Grid`](#cls-Grid), [`Path`](#cls-Path), [`Font`](#cls-Font), [`Control`](#cls-Control), [`Slider`](#cls-Slider), [`Checkbox`](#cls-Checkbox), [`Button`](#cls-Button), [`Color`](#cls-Color), [`Gradient`](#cls-Gradient), [`Raga`](#cls-Raga), [`Tala`](#cls-Tala)
- [Constants and reference tables](#constants-and-reference-tables)

<a id="sketch-and-loop"></a>
## Sketch and loop

<a id="fn-size"></a>
### `f.size`

```py
f.size(width: 'int | str', height: 'int | None' = None, *, title: 'str' = 'funground', fps: 'int' = 60, margin: 'float | tuple' = 0, landscape: 'bool' = False) -> 'None'
```

Create the canvas, or change its size.

Call it once, at the start of setup(). In an animated sketch it opens the window. In a script (a file with no draw()) it makes a canvas with no window; use show() to look at it. If setup() never calls size(), run() opens a 640 by 480 window for you. Instead of numbers you can give a page name, such as size("A4") (see page_size). The margin is a guide for your drawing: read it back with f.ground.content, or use grid(). It does not clip anything.

| Argument | Meaning |
|---|---|
| `width` | the canvas width in pixels (above 0), or a page name such as "A4". |
| `height` | the canvas height in pixels (above 0). Leave it out when width is a page name. |
| `title` | the text in the window's title bar. The default is "funground". |
| `fps` | the target frames per second. The default is 60. It must be above 0. |
| `margin` | the space kept free around the edge. One number is used on all four sides. A tuple of four numbers is (top, right, bottom, left). The default is 0. It stays when the canvas changes size or a new page starts. |
| `landscape` | True turns a named page on its side, as in size("A4", landscape=True). The default is False. It only goes with a page name. |

**Raises.**

- `ValueError`: the width, height or fps is 0 or less, a page name has a height, the name is unknown, a margin is negative, or the margins leave no room.

```py
f.size("A4", margin=f.mm(15))
```

See also: [`ground`](#fn-ground), [`grid`](#fn-grid), [`run`](#fn-run), [`resize_canvas`](#fn-resize_canvas), [`full_screen`](#fn-full_screen), [`page_size`](#fn-page_size).

<a id="fn-resize_canvas"></a>
### `f.resize_canvas`

```py
f.resize_canvas(width: 'int', height: 'int') -> 'None'
```

Change the canvas size while the sketch runs.

f.width and f.height follow the new size.

| Argument | Meaning |
|---|---|
| `width`, `height` | the new size in pixels. |

```py
f.resize_canvas(800, 600)
```

See also: [`size`](#fn-size), [`full_screen`](#fn-full_screen).

<a id="fn-full_screen"></a>
### `f.full_screen`

```py
f.full_screen() -> 'None'
```

Fill the whole screen with the canvas.

Use it instead of size(), in setup(). f.width and f.height become the screen's size. Escape still ends the sketch. In a script it makes the canvas the screen's size, and show() then shows it full screen.

```py
def setup():
    f.full_screen()
```

See also: [`size`](#fn-size), [`resize_canvas`](#fn-resize_canvas).

<a id="fn-run"></a>
### `f.run`

```py
f.run(*, fps: 'int | None' = None, max_frames: 'int | None' = None) -> 'None'
```

Start the sketch: call setup() once, then draw() again and again.

Put it as the last line of your file. It finds the functions called setup() and draw() in your file, so you do not pass them in. setup() is optional. draw() is required. The window closes with its close button, the Escape key or stop().

| Argument | Meaning |
|---|---|
| `fps` | the frames per second, replacing the one given to size(). The default None keeps it. |
| `max_frames` | stop by itself after this many frames. The default None runs until the window closes. It is mostly for tests and for runs with no window. |

**Raises.**

- `RuntimeError`: f.run() cannot find the file that called it, or the file mixes the script style with run().

```py
f.run(max_frames=300)
```

See also: [`size`](#fn-size), [`stop`](#fn-stop), [`no_loop`](#fn-no_loop).

<a id="fn-loop"></a>
### `f.loop`

```py
f.loop() -> 'None'
```

Call draw() every frame again, after no_loop().

See also: [`no_loop`](#fn-no_loop), [`redraw`](#fn-redraw).

<a id="fn-no_loop"></a>
### `f.no_loop`

```py
f.no_loop() -> 'None'
```

Stop calling draw() every frame. The window stays open.

draw() still runs once at the start, and after redraw(). Use loop() to start again.

```py
f.no_loop()
```

See also: [`loop`](#fn-loop), [`redraw`](#fn-redraw), [`is_looping`](#fn-is_looping).

<a id="fn-redraw"></a>
### `f.redraw`

```py
f.redraw() -> 'None'
```

Call draw() once more.

Use it, for example, after a key press when the sketch is not looping.

```py
def key_pressed():
    f.redraw()
```

See also: [`no_loop`](#fn-no_loop), [`loop`](#fn-loop).

<a id="fn-is_looping"></a>
### `f.is_looping`

```py
f.is_looping() -> 'bool'
```

Return whether draw() is called every frame.

**Returns.** True while the sketch is looping. False after no_loop().

See also: [`no_loop`](#fn-no_loop), [`loop`](#fn-loop).

<a id="fn-exit"></a>
### `f.exit`

```py
f.exit() -> 'None'
```

End the sketch after this frame.

It is the same as stop(). It shadows Python's own exit() only inside funground.

```py
f.exit()
```

See also: [`stop`](#fn-stop).

<a id="fn-stop"></a>
### `f.stop`

```py
f.stop() -> 'None'
```

Ask the sketch to stop.

The sketch ends after the current frame. It is the same as exit().

```py
if f.frame_count > 600:
    f.stop()
```

See also: [`exit`](#fn-exit), [`run`](#fn-run), [`no_loop`](#fn-no_loop).

<a id="fn-frame_rate"></a>
### `f.frame_rate`

```py
f.frame_rate() -> 'float'
```

Return the frames per second that the sketch is really achieving.

The number is smoothed over a few frames. It is 0.0 until the second frame.

**Returns.** A number of frames a second.

```py
f.text(round(f.frame_rate()), 10, 10)
```

See also: [`size`](#fn-size), [`millis`](#fn-millis).

<a id="fn-show"></a>
### `f.show`

```py
f.show() -> 'None'
```

Open a window on what a script has drawn, and wait until it is closed.

This is for the script style (a file with no draw()). Call size() first. The window also closes with the Escape key. With a document of several pages, the arrow keys turn the pages. With no window (FUNGROUND_HEADLESS=1) it returns at once.

```py
f.size(400, 300)
f.circle(200, 150, 100)
f.show()
```

See also: [`size`](#fn-size), [`new_page`](#fn-new_page), [`save`](#fn-save).

<a id="fn-smooth"></a>
### `f.smooth`

```py
f.smooth() -> 'None'
```

Draw smooth (anti-aliased) edges again.

This is the start. Use it after no_smooth().

See also: [`no_smooth`](#fn-no_smooth).

<a id="fn-no_smooth"></a>
### `f.no_smooth`

```py
f.no_smooth() -> 'None'
```

Draw hard, pixel-sharp edges from now on.

There is no anti-aliasing, which suits pixel art. It is a setting of the sketch, so pop() does not undo it. Use smooth() to go back.

```py
f.no_smooth()
```

See also: [`smooth`](#fn-smooth).

<a id="shapes"></a>
## Shapes

<a id="fn-point"></a>
### `f.point`

```py
f.point(x: 'float', y: 'float') -> 'None'
```

Draw a dot.

The dot has the stroke colour and is about stroke_width pixels across.

| Argument | Meaning |
|---|---|
| `x`, `y` | the position, in pixels. |

```py
f.stroke_width(6)
f.point(400, 100)
```

See also: [`line`](#fn-line), [`stroke`](#fn-stroke), [`stroke_width`](#fn-stroke_width).

<a id="fn-line"></a>
### `f.line`

```py
f.line(x1: 'float', y1: 'float', x2: 'float', y2: 'float') -> 'None'
```

Draw a straight line between two points.

A line uses the stroke only. The fill does not matter.

| Argument | Meaning |
|---|---|
| `x1`, `y1` | where the line starts. |
| `x2`, `y2` | where the line ends. |

```py
f.line(220, 160, 340, 220)
```

See also: [`stroke`](#fn-stroke), [`stroke_width`](#fn-stroke_width), [`point`](#fn-point).

<a id="fn-rect"></a>
### `f.rect`

```py
f.rect(x: 'float', y: 'float', width: 'float', height: 'float', *radii: 'float') -> 'None'
```

Draw a rectangle.

It uses the current fill and stroke. By default (x, y) is the top-left corner. rect_mode() can change that. Corner radii cannot be negative, and big ones are cut to half the shorter side.

| Argument | Meaning |
|---|---|
| `x`, `y` | the corner, in pixels from the top-left of the canvas. |
| `width` | the width, in pixels. |
| `height` | the height, in pixels. |
| `radii` | optional corner rounding. Give one number to round all four corners, or four numbers (top-left, top-right, bottom-right, bottom-left). |

```py
f.rect(40, 160, 120, 60)
f.rect(40, 240, 120, 60, 12)
```

See also: [`square`](#fn-square), [`rect_mode`](#fn-rect_mode), [`fill`](#fn-fill), [`stroke`](#fn-stroke).

<a id="fn-square"></a>
### `f.square`

```py
f.square(x: 'float', y: 'float', size: 'float', *radii: 'float') -> 'None'
```

Draw a square.

It is placed like rect(): by its top-left corner, unless rect_mode() says otherwise.

| Argument | Meaning |
|---|---|
| `x`, `y` | the corner, in pixels. |
| `size` | the length of each side, in pixels. |
| `radii` | optional corner rounding, as for rect(): one number, or four. |

```py
f.square(40, 40, 60, 10)
```

See also: [`rect`](#fn-rect), [`rect_mode`](#fn-rect_mode).

<a id="fn-ellipse"></a>
### `f.ellipse`

```py
f.ellipse(x: 'float', y: 'float', width: 'float', height: 'float') -> 'None'
```

Draw an ellipse.

It uses the current fill and stroke. By default (x, y) is the centre. ellipse_mode() can change that.

| Argument | Meaning |
|---|---|
| `x`, `y` | the centre, in pixels from the top-left corner. |
| `width` | the width across, in pixels. |
| `height` | the height, in pixels. |

```py
f.ellipse(220, 80, 100, 50)
```

See also: [`circle`](#fn-circle), [`ellipse_mode`](#fn-ellipse_mode), [`arc`](#fn-arc).

<a id="fn-circle"></a>
### `f.circle`

```py
f.circle(x: 'float', y: 'float', diameter: 'float') -> 'None'
```

Draw a circle.

The circle uses the current fill and stroke. By default (x, y) is the centre. ellipse_mode() can change that. The last number is the diameter, not the radius.

| Argument | Meaning |
|---|---|
| `x`, `y` | the centre, in pixels from the top-left corner. |
| `diameter` | the width across, in pixels. |

```py
f.circle(200, 150, 80)
```

See also: [`ellipse`](#fn-ellipse), [`ellipse_mode`](#fn-ellipse_mode), [`fill`](#fn-fill), [`stroke`](#fn-stroke).

<a id="fn-triangle"></a>
### `f.triangle`

```py
f.triangle(x1: 'float', y1: 'float', x2: 'float', y2: 'float', x3: 'float', y3: 'float') -> 'None'
```

Draw a triangle through three corners.

It uses the current fill and stroke.

| Argument | Meaning |
|---|---|
| `x1`, `y1` | the first corner. |
| `x2`, `y2` | the second corner. |
| `x3`, `y3` | the third corner. |

```py
f.triangle(10, 90, 90, 90, 50, 10)
```

See also: [`quad`](#fn-quad), [`polygon`](#fn-polygon).

<a id="fn-quad"></a>
### `f.quad`

```py
f.quad(x1: 'float', y1: 'float', x2: 'float', y2: 'float', x3: 'float', y3: 'float', x4: 'float', y4: 'float') -> 'None'
```

Draw a four-sided shape through four corners.

The corners are joined in the order you give them. It uses the current fill and stroke.

| Argument | Meaning |
|---|---|
| `x1`, `y1` | the first corner. |
| `x2`, `y2` | the second corner. |
| `x3`, `y3` | the third corner. |
| `x4`, `y4` | the fourth corner. |

```py
f.quad(20, 20, 80, 20, 80, 80, 20, 80)
```

See also: [`triangle`](#fn-triangle), [`polygon`](#fn-polygon).

<a id="fn-polygon"></a>
### `f.polygon`

```py
f.polygon(points: 'list[tuple[float, float]]') -> 'None'
```

Draw a closed shape through a list of points.

It uses the current fill and stroke. The last point is joined back to the first.

| Argument | Meaning |
|---|---|
| `points` | a list of (x, y) pairs, at least two. |

**Raises.**

- `ValueError`: an item is not an (x, y) pair, or there are fewer than two points.

```py
f.polygon([(0, 0), (50, 20), (20, 60)])
```

See also: [`triangle`](#fn-triangle), [`quad`](#fn-quad), [`begin_shape`](#fn-begin_shape).

<a id="fn-arc"></a>
### `f.arc`

```py
f.arc(x: 'float', y: 'float', width: 'float', height: 'float', start: 'float', stop: 'float', mode: 'str' = 'open') -> 'None'
```

Draw part of an ellipse.

Angles are in degrees and go clockwise, starting from the right (3 o'clock). If stop is less than start, 360 is added to it. An arc is never more than one full turn. ellipse_mode() changes how x, y, width and height are read.

| Argument | Meaning |
|---|---|
| `x`, `y` | the centre of the whole ellipse. |
| `width`, `height` | the size of the whole ellipse, in pixels. |
| `start`, `stop` | the first and last angle, in degrees. |
| `mode` | "open" (the default: the area is filled, but only the curve is outlined), "chord" (closed by a straight line) or "pie" (closed through the centre, like a slice). |

**Raises.**

- `ValueError`: the mode is not one of those words.

```py
f.arc(100, 100, 80, 80, 0, 270, "pie")
```

See also: [`ellipse`](#fn-ellipse), [`ellipse_mode`](#fn-ellipse_mode).

<a id="fn-rect_mode"></a>
### `f.rect_mode`

```py
f.rect_mode(mode: 'str') -> 'None'
```

Choose how rect() and square() read their numbers.

The choice is saved by push() and brought back by pop().

| Argument | Meaning |
|---|---|
| `mode` | "corner" (the default: x, y is the top-left corner, then the size), "corners" (two opposite corners), "center" (x, y is the middle, then the size) or "radius" (x, y is the middle, then half-sizes). |

**Raises.**

- `ValueError`: the mode is not one of those words.

```py
f.rect_mode("center")
f.rect(200, 150, 80, 40)
```

See also: [`rect`](#fn-rect), [`square`](#fn-square), [`ellipse_mode`](#fn-ellipse_mode), [`image_mode`](#fn-image_mode).

<a id="fn-ellipse_mode"></a>
### `f.ellipse_mode`

```py
f.ellipse_mode(mode: 'str') -> 'None'
```

Choose how ellipse(), circle() and arc() read their numbers.

The choice is saved by push() and brought back by pop().

| Argument | Meaning |
|---|---|
| `mode` | "center" (the default: x, y is the middle), "radius" (x, y is the middle, then half-sizes), "corner" (x, y is the top-left of the box around the shape) or "corners" (two opposite corners of that box). |

**Raises.**

- `ValueError`: the mode is not one of those words.

```py
f.ellipse_mode("corner")
f.ellipse(20, 20, 100, 60)
```

See also: [`ellipse`](#fn-ellipse), [`circle`](#fn-circle), [`arc`](#fn-arc), [`rect_mode`](#fn-rect_mode).

<a id="curves-and-custom-shapes"></a>
## Curves and custom shapes

<a id="fn-bezier"></a>
### `f.bezier`

```py
f.bezier(x1: 'float', y1: 'float', cx1: 'float', cy1: 'float', cx2: 'float', cy2: 'float', x2: 'float', y2: 'float') -> 'None'
```

Draw a Bezier curve from one point to another.

Two control points pull the curve. It is stroked only, never filled.

| Argument | Meaning |
|---|---|
| `x1`, `y1` | where the curve starts. |
| `cx1`, `cy1` | the first control point. |
| `cx2`, `cy2` | the second control point. |
| `x2`, `y2` | where the curve ends. |

```py
f.bezier(20, 80, 20, 0, 180, 0, 180, 80)
```

See also: [`curve`](#fn-curve), [`bezier_vertex`](#fn-bezier_vertex), [`bezier_point`](#fn-bezier_point).

<a id="fn-bezier_point"></a>
### `f.bezier_point`

```py
f.bezier_point(a: 'float', b: 'float', c: 'float', d: 'float', t: 'float') -> 'float'
```

Return one coordinate of a Bezier curve at a place along it.

Call it once for x and once for y.

| Argument | Meaning |
|---|---|
| `a` | the start coordinate. |
| `b` | the first control coordinate. |
| `c` | the second control coordinate. |
| `d` | the end coordinate. |
| `t` | the place along the curve, 0 (start) to 1 (end). |

**Returns.** The coordinate at t.

```py
x = f.bezier_point(20, 20, 180, 180, 0.5)
y = f.bezier_point(80, 0, 0, 80, 0.5)
```

See also: [`bezier`](#fn-bezier), [`bezier_tangent`](#fn-bezier_tangent).

<a id="fn-bezier_tangent"></a>
### `f.bezier_tangent`

```py
f.bezier_tangent(a: 'float', b: 'float', c: 'float', d: 'float', t: 'float') -> 'float'
```

Return the slope of one coordinate of a Bezier curve at a place along it.

Call it once for x and once for y, then use math.atan2 to get the direction.

| Argument | Meaning |
|---|---|
| `a` | the start coordinate. |
| `b` | the first control coordinate. |
| `c` | the second control coordinate. |
| `d` | the end coordinate. |
| `t` | the place along the curve, 0 (start) to 1 (end). |

**Returns.** The rate of change of the coordinate at t.

See also: [`bezier`](#fn-bezier), [`bezier_point`](#fn-bezier_point).

<a id="fn-curve"></a>
### `f.curve`

```py
f.curve(x1: 'float', y1: 'float', x2: 'float', y2: 'float', x3: 'float', y3: 'float', x4: 'float', y4: 'float') -> 'None'
```

Draw a smooth curve from point 2 to point 3.

Points 1 and 4 only steer it. It is stroked only, never filled. curve_tightness() changes how tight it is.

| Argument | Meaning |
|---|---|
| `x1`, `y1` | the first steering point. |
| `x2`, `y2` | where the curve starts. |
| `x3`, `y3` | where the curve ends. |
| `x4`, `y4` | the last steering point. |

```py
f.curve(0, 100, 40, 40, 160, 40, 200, 100)
```

See also: [`bezier`](#fn-bezier), [`curve_vertex`](#fn-curve_vertex), [`curve_tightness`](#fn-curve_tightness).

<a id="fn-curve_point"></a>
### `f.curve_point`

```py
f.curve_point(a: 'float', b: 'float', c: 'float', d: 'float', t: 'float') -> 'float'
```

Return one coordinate of a curve() segment at a place along it.

It uses the current curve_tightness(). Call it once for x and once for y.

| Argument | Meaning |
|---|---|
| `a`, `b`, `c`, `d` | the four coordinates, as for curve(): the first and last steer, and the curve runs from b to c. |
| `t` | the place along the segment, 0 (at b) to 1 (at c). |

**Returns.** The coordinate at t.

See also: [`curve`](#fn-curve), [`curve_tangent`](#fn-curve_tangent), [`curve_tightness`](#fn-curve_tightness).

<a id="fn-curve_tangent"></a>
### `f.curve_tangent`

```py
f.curve_tangent(a: 'float', b: 'float', c: 'float', d: 'float', t: 'float') -> 'float'
```

Return the slope of one coordinate of a curve() segment at a place along it.

| Argument | Meaning |
|---|---|
| `a`, `b`, `c`, `d` | the four coordinates, as for curve(). |
| `t` | the place along the segment, 0 to 1. |

**Returns.** The rate of change of the coordinate at t.

See also: [`curve`](#fn-curve), [`curve_point`](#fn-curve_point).

<a id="fn-curve_tightness"></a>
### `f.curve_tightness`

```py
f.curve_tightness(tightness: 'float') -> 'None'
```

Set how tight curve_vertex() and curve() curves are.

| Argument | Meaning |
|---|---|
| `tightness` | 0 is smooth (the default). 1 gives straight lines. |

```py
f.curve_tightness(0.5)
```

See also: [`curve_vertex`](#fn-curve_vertex), [`curve`](#fn-curve).

<a id="fn-begin_shape"></a>
### `f.begin_shape`

```py
f.begin_shape() -> 'None'
```

Start a shape that you build from its corners.

Call vertex() for each corner, then end_shape(). Calling it twice without end_shape() is an error. A shape still open when draw() ends is dropped with a warning.

**Raises.**

- `RuntimeError`: a shape is already being built.

```py
f.begin_shape()
f.vertex(100, 20)
f.vertex(180, 80)
f.vertex(60, 90)
f.end_shape(close=True)
```

See also: [`vertex`](#fn-vertex), [`end_shape`](#fn-end_shape), [`begin_contour`](#fn-begin_contour).

<a id="fn-end_shape"></a>
### `f.end_shape`

```py
f.end_shape(close: 'bool' = False) -> 'None'
```

Draw the shape that you built from corners.

It uses the current fill and stroke. An open shape is only stroked, never filled. A shape that crosses itself, like a five-pointed star, is filled right through its centre.

| Argument | Meaning |
|---|---|
| `close` | True joins the last corner to the first, then fills and strokes it. The default False leaves the shape open. |

**Raises.**

- `RuntimeError`: there is no begin_shape() before it.

```py
f.end_shape(close=True)
```

See also: [`begin_shape`](#fn-begin_shape), [`vertex`](#fn-vertex).

<a id="fn-vertex"></a>
### `f.vertex`

```py
f.vertex(x: 'float', y: 'float') -> 'None'
```

Add a corner to the shape begun by begin_shape().

| Argument | Meaning |
|---|---|
| `x`, `y` | the corner, in pixels. |

**Raises.**

- `RuntimeError`: there is no begin_shape() before it.

See also: [`begin_shape`](#fn-begin_shape), [`end_shape`](#fn-end_shape), [`bezier_vertex`](#fn-bezier_vertex).

<a id="fn-bezier_vertex"></a>
### `f.bezier_vertex`

```py
f.bezier_vertex(cx1: 'float', cy1: 'float', cx2: 'float', cy2: 'float', x: 'float', y: 'float') -> 'None'
```

Add a Bezier curve segment to the shape being built.

It goes from the last point to (x, y). It needs a vertex() before it.

| Argument | Meaning |
|---|---|
| `cx1`, `cy1` | the first control point, which pulls the start of the curve. |
| `cx2`, `cy2` | the second control point, which pulls the end of the curve. |
| `x`, `y` | where the curve ends. |

**Raises.**

- `RuntimeError`: there is no begin_shape() or no earlier vertex().

```py
f.begin_shape()
f.vertex(20, 80)
f.bezier_vertex(20, 0, 180, 0, 180, 80)
f.end_shape()
```

See also: [`quadratic_vertex`](#fn-quadratic_vertex), [`curve_vertex`](#fn-curve_vertex), [`bezier`](#fn-bezier).

<a id="fn-quadratic_vertex"></a>
### `f.quadratic_vertex`

```py
f.quadratic_vertex(cx: 'float', cy: 'float', x: 'float', y: 'float') -> 'None'
```

Add a quadratic curve segment to the shape being built.

It goes from the last point to (x, y), pulled by one control point.

| Argument | Meaning |
|---|---|
| `cx`, `cy` | the control point. |
| `x`, `y` | where the curve ends. |

**Raises.**

- `RuntimeError`: there is no begin_shape() or no earlier vertex().

```py
f.quadratic_vertex(100, 0, 180, 80)
```

See also: [`bezier_vertex`](#fn-bezier_vertex), [`curve_vertex`](#fn-curve_vertex).

<a id="fn-curve_vertex"></a>
### `f.curve_vertex`

```py
f.curve_vertex(x: 'float', y: 'float') -> 'None'
```

Add a point for a smooth curve that passes through the points.

Give at least four in a row. The first and last only steer the curve. curve_tightness() changes how tight it is.

| Argument | Meaning |
|---|---|
| `x`, `y` | the point, in pixels. |

```py
f.begin_shape()
f.curve_vertex(0, 100)
f.curve_vertex(40, 40)
f.curve_vertex(160, 40)
f.curve_vertex(200, 100)
f.end_shape()
```

See also: [`curve`](#fn-curve), [`curve_tightness`](#fn-curve_tightness), [`bezier_vertex`](#fn-bezier_vertex).

<a id="fn-begin_contour"></a>
### `f.begin_contour`

```py
f.begin_contour() -> 'None'
```

Start a hole inside the shape being built.

List the hole's corners with vertex(), then call end_contour().

See also: [`end_contour`](#fn-end_contour), [`begin_shape`](#fn-begin_shape).

<a id="fn-end_contour"></a>
### `f.end_contour`

```py
f.end_contour() -> 'None'
```

Finish the hole started by begin_contour().

See also: [`begin_contour`](#fn-begin_contour), [`end_shape`](#fn-end_shape).

<a id="colour"></a>
## Colour

<a id="fn-background"></a>
### `f.background`

```py
f.background(color: 'Color', *more: 'float') -> 'None'
```

Fill the whole canvas with one colour.

It ignores the fill, the stroke, the transform and any clip. Call it near the start of draw() to clear the last frame. Leave it out when you want trails. Inside a ``with f.layer(...)`` block it clears that layer. Inside a function drawn by variations(), it paints that version's whole picture.

| Argument | Meaning |
|---|---|
| `color` | a colour name such as "white", a hex string such as "#F05A45", an (r, g, b) or (r, g, b, a) tuple, a colour from f.color(), or a gradient. One number is a grey. |
| `more` | extra numbers, so that background(30, 30, 60) works like background((30, 30, 60)). They follow the colour mode. A name, hex string or gradient takes no extra numbers. |

**Raises.**

- `ValueError`: the colour is not understood, or numbers follow a name or gradient.

```py
f.background("white")
f.background(30, 30, 60)
```

See also: [`clear`](#fn-clear), [`fill`](#fn-fill), [`color_mode`](#fn-color_mode).

<a id="fn-clear"></a>
### `f.clear`

```py
f.clear() -> 'None'
```

Make the whole canvas transparent.

A PNG saved afterwards keeps the transparency. The window shows it as black.

See also: [`background`](#fn-background), [`erase`](#fn-erase), [`save`](#fn-save).

<a id="fn-color"></a>
### `f.color`

```py
f.color(*values)
```

Make a colour that you can read and reuse.

You can pass it to fill(), stroke(), background() and so on. It has these parts: red, green, blue and alpha (each 0 to 255), hue (0 to 360), and saturation, brightness and lightness (each 0 to 100). Numbers follow the colour mode. A tuple always means red, green, blue. Use hsb() or hsl() to give a hue.

| Argument | Meaning |
|---|---|
| `values` | one colour (a name, a hex string, a tuple or another colour), or one grey number, or a grey and alpha, or three or four numbers (red, green, blue and optional alpha). |

**Returns.** A colour with parts such as .red, .green, .blue, .alpha, .hue, .saturation, .brightness and .lightness.

**Raises.**

- `ValueError`: there are no values, or more than four, or the colour is not understood.

```py
c = f.color("tomato")
print(c.red, c.hue)
```

See also: [`hsb`](#fn-hsb), [`hsl`](#fn-hsl), [`lerp_color`](#fn-lerp_color), [`color_mode`](#fn-color_mode).

<a id="fn-color_mode"></a>
### `f.color_mode`

```py
f.color_mode(mode: 'str', max1: 'float | None' = None, max2: 'float | None' = None, max3: 'float | None' = None, max_alpha: 'float | None' = None) -> 'None'
```

Choose how numbers become a colour.

It affects colours given as numbers. Names, hex strings and colour objects are not affected. Each mode remembers its own ranges. The choice is saved by push() and brought back by pop().

| Argument | Meaning |
|---|---|
| `mode` | "rgb" (the default; ranges 255), "hsb" or "hsl" (ranges 360, 100, 100, and opacity 0 to 1). |
| `max1` | with only this one, it sets the top of all four ranges. With max2 and max3 as well, it is the top of the first (red or hue). |
| `max2` | the top of the second range (green or saturation). |
| `max3` | the top of the third range (blue, brightness or lightness). |
| `max_alpha` | the top of the opacity range. Leave it out to keep the opacity range. |

**Raises.**

- `ValueError`: the mode is unknown, a range is not a number above 0, or exactly two ranges are given.

```py
f.color_mode("hsb", 360, 100, 100)
f.fill(200, 80, 90)
```

See also: [`color`](#fn-color), [`hsb`](#fn-hsb), [`hsl`](#fn-hsl), [`fill`](#fn-fill).

<a id="fn-hsb"></a>
### `f.hsb`

```py
f.hsb(hue: 'float', saturation: 'float', brightness: 'float', alpha: 'float' = 255)
```

Make a colour from hue, saturation and brightness.

The ranges are always these, whatever the colour mode is.

| Argument | Meaning |
|---|---|
| `hue` | the colour wheel position, 0 to 360. It wraps round. |
| `saturation` | how strong the colour is, 0 to 100. |
| `brightness` | how light it is, 0 to 100. |
| `alpha` | the opacity, 0 (invisible) to 255 (solid). The default is 255. |

**Returns.** A colour, as from color().

```py
f.fill(f.hsb(200, 80, 90))
```

See also: [`hsl`](#fn-hsl), [`color`](#fn-color), [`color_mode`](#fn-color_mode).

<a id="fn-hsl"></a>
### `f.hsl`

```py
f.hsl(hue: 'float', saturation: 'float', lightness: 'float', alpha: 'float' = 255)
```

Make a colour from hue, saturation and lightness.

The ranges are always these, whatever the colour mode is.

| Argument | Meaning |
|---|---|
| `hue` | the colour wheel position, 0 to 360. It wraps round. |
| `saturation` | how strong the colour is, 0 to 100. |
| `lightness` | how light it is, 0 to 100. |
| `alpha` | the opacity, 0 (invisible) to 255 (solid). The default is 255. |

**Returns.** A colour, as from color().

```py
f.fill(f.hsl(30, 90, 60))
```

See also: [`hsb`](#fn-hsb), [`color`](#fn-color), [`color_mode`](#fn-color_mode).

<a id="fn-lerp_color"></a>
### `f.lerp_color`

```py
f.lerp_color(c1: 'Color', c2: 'Color', amount: 'float')
```

Return a colour part of the way between two colours.

It mixes red, green, blue and alpha.

| Argument | Meaning |
|---|---|
| `c1` | the first colour, in any form that fill() takes. |
| `c2` | the second colour. |
| `amount` | from 0 to 1. 0 gives c1, 1 gives c2 and 0.5 is halfway. |

**Returns.** A colour, as from color().

```py
f.fill(f.lerp_color("red", "blue", 0.5))
```

See also: [`color`](#fn-color), [`lerp`](#fn-lerp), [`linear_gradient`](#fn-linear_gradient).

<a id="fn-linear_gradient"></a>
### `f.linear_gradient`

```py
f.linear_gradient(x1: 'float', y1: 'float', x2: 'float', y2: 'float', colors, stops=None)
```

Make a gradient: colours blended along a line.

Use it like a colour in fill(), stroke() or background().

| Argument | Meaning |
|---|---|
| `x1`, `y1` | where the line starts (the first colour). |
| `x2`, `y2` | where the line ends (the last colour). |
| `colors` | a list of colours, in any form that fill() takes. |
| `stops` | where each colour sits along the line, from 0 to 1. The default None spaces them evenly. |

**Returns.** A gradient. Give it to fill(), stroke() or background().

```py
f.fill(f.linear_gradient(0, 0, 200, 0, ["red", "blue"]))
f.rect(0, 0, 200, 100)
```

See also: [`radial_gradient`](#fn-radial_gradient), [`fill`](#fn-fill), [`lerp_color`](#fn-lerp_color).

<a id="fn-radial_gradient"></a>
### `f.radial_gradient`

```py
f.radial_gradient(x: 'float', y: 'float', radius: 'float', colors, stops=None)
```

Make a gradient: colours blended outward from a point.

The first colour is at the centre. Use it like a colour in fill(), stroke() or background().

| Argument | Meaning |
|---|---|
| `x`, `y` | the centre. |
| `radius` | the distance where the last colour is reached, in pixels. |
| `colors` | a list of colours, in any form that fill() takes. |
| `stops` | where each colour sits, from 0 (centre) to 1 (the radius). The default None spaces them evenly. |

**Returns.** A gradient. Give it to fill(), stroke() or background().

```py
f.background(f.radial_gradient(320, 200, 300, ["white", "navy"]))
```

See also: [`linear_gradient`](#fn-linear_gradient), [`fill`](#fn-fill).

<a id="fill-and-stroke"></a>
## Fill and stroke

<a id="fn-fill"></a>
### `f.fill`

```py
f.fill(color: 'Color', *more: 'float') -> 'None'
```

Set the colour that shapes are filled with.

It applies to the shapes you draw after the call. The start is white. The choice is saved by push() and brought back by pop().

| Argument | Meaning |
|---|---|
| `color` | a colour name such as "gold", a hex string such as "#F05A45", an (r, g, b) or (r, g, b, a) tuple, a colour from f.color(), or a gradient. One number is a grey. |
| `more` | extra numbers, so that fill(255, 99, 71) works like fill((255, 99, 71)). They follow the colour mode. A name, hex string or gradient takes no extra numbers. |

**Raises.**

- `ValueError`: the colour is not understood, or numbers follow a name or gradient.

```py
f.fill("gold")
f.fill(255, 99, 71, 128)
```

See also: [`no_fill`](#fn-no_fill), [`stroke`](#fn-stroke), [`color_mode`](#fn-color_mode), [`linear_gradient`](#fn-linear_gradient).

<a id="fn-no_fill"></a>
### `f.no_fill`

```py
f.no_fill() -> 'None'
```

Do not fill shapes drawn after this.

Only their outlines are drawn. Use fill() to start filling again.

```py
f.no_fill()
f.circle(100, 100, 50)
```

See also: [`fill`](#fn-fill), [`no_stroke`](#fn-no_stroke).

<a id="fn-stroke"></a>
### `f.stroke`

```py
f.stroke(color: 'Color', *more: 'float') -> 'None'
```

Set the colour of outlines and lines.

It applies to what you draw after the call. The start is black. The choice is saved by push() and brought back by pop().

| Argument | Meaning |
|---|---|
| `color` | a colour name such as "black", a hex string, an (r, g, b) or (r, g, b, a) tuple, a colour from f.color(), or a gradient. One number is a grey. |
| `more` | extra numbers, so that stroke(0, 0, 255) works like stroke((0, 0, 255)). They follow the colour mode. A name, hex string or gradient takes no extra numbers. |

**Raises.**

- `ValueError`: the colour is not understood, or numbers follow a name or gradient.

```py
f.stroke("navy")
```

See also: [`no_stroke`](#fn-no_stroke), [`stroke_width`](#fn-stroke_width), [`fill`](#fn-fill).

<a id="fn-no_stroke"></a>
### `f.no_stroke`

```py
f.no_stroke() -> 'None'
```

Do not draw outlines or lines after this.

Use stroke() to start again.

```py
f.no_stroke()
f.circle(100, 100, 50)
```

See also: [`stroke`](#fn-stroke), [`no_fill`](#fn-no_fill).

<a id="fn-stroke_width"></a>
### `f.stroke_width`

```py
f.stroke_width(pixels: 'int') -> 'None'
```

Set how thick outlines and lines are.

The stroke is centred on the edge of the shape: half of it lies outside and half inside. The start is 1. The choice is saved by push() and brought back by pop().

| Argument | Meaning |
|---|---|
| `pixels` | the thickness, in pixels. It must be 1 or more. Fractions such as 2.5 are kept. |

**Raises.**

- `ValueError`: pixels is less than 1.

```py
f.stroke_width(3)
```

See also: [`stroke`](#fn-stroke), [`stroke_cap`](#fn-stroke_cap), [`stroke_join`](#fn-stroke_join), [`stroke_dash`](#fn-stroke_dash).

<a id="fn-stroke_cap"></a>
### `f.stroke_cap`

```py
f.stroke_cap(cap: 'str') -> 'None'
```

Choose how the ends of lines look.

| Argument | Meaning |
|---|---|
| `cap` | "round" (the default), "square" (extends past the end by half the width) or "butt" (stops flat at the end). |

**Raises.**

- `ValueError`: the cap is not one of those words.

```py
f.stroke_cap("butt")
```

See also: [`stroke_join`](#fn-stroke_join), [`stroke_width`](#fn-stroke_width).

<a id="fn-stroke_join"></a>
### `f.stroke_join`

```py
f.stroke_join(join: 'str') -> 'None'
```

Choose how corners of outlines look.

| Argument | Meaning |
|---|---|
| `join` | "round" (the default), "miter" (sharp) or "bevel" (cut off). |

**Raises.**

- `ValueError`: the join is not one of those words.

```py
f.stroke_join("miter")
```

See also: [`miter_limit`](#fn-miter_limit), [`stroke_cap`](#fn-stroke_cap), [`stroke_width`](#fn-stroke_width).

<a id="fn-miter_limit"></a>
### `f.miter_limit`

```py
f.miter_limit(limit: 'float') -> 'None'
```

Set how far a sharp "miter" corner may stick out.

Past that limit the corner is cut off (bevelled). It matters only when stroke_join is "miter".

| Argument | Meaning |
|---|---|
| `limit` | the ratio of the point's length to the stroke width. The default is 10. It must be 1 or more. |

**Raises.**

- `ValueError`: limit is less than 1.

```py
f.miter_limit(4)
```

See also: [`stroke_join`](#fn-stroke_join).

<a id="fn-stroke_dash"></a>
### `f.stroke_dash`

```py
f.stroke_dash(pattern: 'float | list[float]', offset: 'float' = 0) -> 'None'
```

Draw outlines and lines as dashes.

Use no_dash() for solid lines again.

| Argument | Meaning |
|---|---|
| `pattern` | one length, or a list of lengths that alternate dash, gap, dash, gap and so on. Lengths are in pixels, 0 or more, and not all 0. |
| `offset` | how far into the pattern to start, in pixels. The default is 0. |

**Raises.**

- `ValueError`: the pattern is empty, has a negative length, or is all zeros.

```py
f.stroke_dash([12, 4])
f.line(20, 50, 300, 50)
```

See also: [`no_dash`](#fn-no_dash), [`stroke_width`](#fn-stroke_width).

<a id="fn-no_dash"></a>
### `f.no_dash`

```py
f.no_dash() -> 'None'
```

Draw solid outlines and lines again.

See also: [`stroke_dash`](#fn-stroke_dash).

<a id="fn-shadow"></a>
### `f.shadow`

```py
f.shadow(x_offset: 'float', y_offset: 'float', blur: 'float' = 5, color: 'Color' = (0, 0, 0, 128)) -> 'None'
```

Give everything drawn after this a soft shadow.

Stop it with no_shadow(). The choice is saved by push() and brought back by pop().

| Argument | Meaning |
|---|---|
| `x_offset`, `y_offset` | how far the shadow moves from the shape, in pixels. |
| `blur` | how soft the edge is, in pixels, 0 or more. The default is 5. |
| `color` | the shadow colour. The default is black at half strength. |

**Raises.**

- `ValueError`: blur is negative.

```py
f.shadow(4, 6, blur=8)
```

See also: [`no_shadow`](#fn-no_shadow), [`opacity`](#fn-opacity).

<a id="fn-no_shadow"></a>
### `f.no_shadow`

```py
f.no_shadow() -> 'None'
```

Stop drawing shadows.

See also: [`shadow`](#fn-shadow).

<a id="fn-opacity"></a>
### `f.opacity`

```py
f.opacity(amount: 'float') -> 'None'
```

Make everything drawn after this see-through.

The choice is saved by push() and brought back by pop().

| Argument | Meaning |
|---|---|
| `amount` | from 0 (invisible) to 255 (solid, the default). |

**Raises.**

- `ValueError`: amount is not a number from 0 to 255.

```py
f.opacity(128)
```

See also: [`blend_mode`](#fn-blend_mode), [`fill`](#fn-fill), [`tint`](#fn-tint).

<a id="fn-blend_mode"></a>
### `f.blend_mode`

```py
f.blend_mode(mode: 'str') -> 'None'
```

Choose how what you draw next mixes with what is already there.

The choice is saved by push() and brought back by pop().

| Argument | Meaning |
|---|---|
| `mode` | "normal" (the default), "multiply", "screen", "overlay", "darken", "lighten", "add", "difference", "exclusion", "dodge", "burn", "hard_light", "soft_light", "hue", "saturation", "color" or "luminosity". |

**Raises.**

- `ValueError`: the mode is not one of those words.

```py
f.blend_mode("multiply")
```

See also: [`opacity`](#fn-opacity), [`tint`](#fn-tint), [`erase`](#fn-erase).

<a id="fn-erase"></a>
### `f.erase`

```py
f.erase(fill_strength: 'float' = 255, stroke_strength: 'float' = 255) -> 'None'
```

Make everything drawn after this remove what is under it, instead of painting.

Colours, gradients, tint, blend mode, opacity and shadow are ignored. Use it to cut holes in a picture from create_graphics(). Stop it with no_erase().

| Argument | Meaning |
|---|---|
| `fill_strength` | how much shape fills remove. 255 (the default) removes completely, making it see-through. 128 removes about half. 0 removes nothing. |
| `stroke_strength` | the same for outlines. |

**Raises.**

- `ValueError`: a strength is not a number from 0 to 255.

```py
f.erase()
f.circle(50, 50, 40)
f.no_erase()
```

See also: [`no_erase`](#fn-no_erase), [`clear`](#fn-clear), [`create_graphics`](#fn-create_graphics).

<a id="fn-no_erase"></a>
### `f.no_erase`

```py
f.no_erase() -> 'None'
```

Go back to painting.

See also: [`erase`](#fn-erase).

<a id="fn-tint"></a>
### `f.tint`

```py
f.tint(color, *more: 'float') -> 'None'
```

Colour every picture drawn with image() from now on.

Red, green and blue of each pixel are multiplied by the tint's, and the alpha is multiplied in. Shapes and text are not tinted. The choice is saved by push() and brought back by pop().

| Argument | Meaning |
|---|---|
| `color` | any colour that fill() takes, except a gradient. One number is a grey. |
| `more` | extra numbers, as for fill(). tint(255, 128) draws pictures half see-through. |

```py
f.tint("gold")
f.image(photo, 0, 0)
```

See also: [`no_tint`](#fn-no_tint), [`image`](#fn-image), [`opacity`](#fn-opacity).

<a id="fn-no_tint"></a>
### `f.no_tint`

```py
f.no_tint() -> 'None'
```

Stop tinting pictures.

See also: [`tint`](#fn-tint).

<a id="text-and-fonts"></a>
## Text and fonts

<a id="fn-text"></a>
### `f.text`

```py
f.text(message: 'object', x: 'float', y: 'float', color: 'Color | None' = None) -> 'None'
```

Draw text.

By default (x, y) is the top-left corner of the text; text_align() can change that. The text uses the fill colour. If there is no fill it uses the stroke colour, and if there is neither it is white. A new line in the message starts a new line of text. The default size is 20 (see text_size).

| Argument | Meaning |
|---|---|
| `message` | what to write. Any value works: str() is applied. A FormattedString gives each part its own look. |
| `x`, `y` | the position, in pixels. |
| `color` | a colour for this text only, in any form that fill() takes. The default None uses the fill. |

```py
f.fill("black")
f.text("Hello", 30, 40)
f.text(f.frame_count, 30, 80, color="navy")
```

See also: [`text_size`](#fn-text_size), [`text_align`](#fn-text_align), [`text_width`](#fn-text_width), [`text_box`](#fn-text_box), [`text_font`](#fn-text_font), [`FormattedString`](#cls-FormattedString).

<a id="fn-text_align"></a>
### `f.text_align`

```py
f.text_align(horizontal: 'str', vertical: 'str | None' = None) -> 'None'
```

Choose which point of the text (x, y) means.

The default is left and top. The choice is saved by push() and brought back by pop().

| Argument | Meaning |
|---|---|
| `horizontal` | "left" (the default), "center" or "right". |
| `vertical` | "top" (the default), "center", "baseline" or "bottom". Leave it out to keep the current choice. |

**Raises.**

- `ValueError`: a word is not one of those.

```py
f.text_align("center", "center")
f.text("Middle", f.width / 2, f.height / 2)
```

See also: [`text`](#fn-text), [`text_width`](#fn-text_width).

<a id="fn-text_ascent"></a>
### `f.text_ascent`

```py
f.text_ascent() -> 'float'
```

Return how far letters reach above the baseline, in pixels.

It is measured at the current text size and font.

See also: [`text_descent`](#fn-text_descent), [`text_size`](#fn-text_size).

<a id="fn-text_descent"></a>
### `f.text_descent`

```py
f.text_descent() -> 'float'
```

Return how far letters such as g and y reach below the baseline, in pixels.

It is measured at the current text size and font.

See also: [`text_ascent`](#fn-text_ascent), [`text_size`](#fn-text_size).

<a id="fn-text_leading"></a>
### `f.text_leading`

```py
f.text_leading(leading: 'float | None') -> 'None'
```

Set the distance from one line's baseline to the next.

It matters when a message has several lines, and in text_box().

| Argument | Meaning |
|---|---|
| `leading` | the distance in pixels, 0 or more. None (the default behaviour) means automatic: 1.25 times the text size. |

**Raises.**

- `ValueError`: leading is negative.

```py
f.text_leading(30)
```

See also: [`text_size`](#fn-text_size), [`text`](#fn-text), [`text_box`](#fn-text_box).

<a id="fn-text_box"></a>
### `f.text_box`

```py
f.text_box(message: 'object', x: 'float', y: 'float', width: 'float', height: 'float | None' = None, color: 'Color | None' = None) -> 'str | FormattedString'
```

Draw text wrapped inside a box, and return whatever did not fit.

Words are moved to a new line when they would pass the right edge. With a height, only the lines that fit are drawn. Give the returned text to another box to flow a story across columns.

| Argument | Meaning |
|---|---|
| `message` | the text, a string or a FormattedString. |
| `x`, `y` | the top-left corner of the box. |
| `width` | the width of the box, in pixels. It must be above 0. |
| `height` | the height of the box, in pixels, 0 or more. None (the default) means no limit. |
| `color` | a colour for this text only. The default None uses the fill, as text() does. |

**Returns.** The text that did not fit: a string, or a FormattedString if you gave one. It is "" when everything fitted.

**Raises.**

- `ValueError`: the width is not above 0, or the height is negative.

```py
rest = f.text_box("A long story that wraps inside a box.", 20, 60, 280, 100)
```

See also: [`text`](#fn-text), [`text_width`](#fn-text_width), [`text_leading`](#fn-text_leading), [`FormattedString`](#cls-FormattedString).

<a id="fn-text_path"></a>
### `f.text_path`

```py
f.text_path(message: 'object', x: 'float', y: 'float') -> 'PathBuilder'
```

Return the outlines of some text as a path.

It is set with the current font, style, size, alignment and leading, just like text(). The path has no colour, and it is not moved by the current transform until you draw it. You can cut it, outline it, fill it, or clip with it.

| Argument | Meaning |
|---|---|
| `message` | what to write. Any value works, or a FormattedString. |
| `x`, `y` | the position, as for text(). |

**Returns.** A path (like f.path()). Draw it with draw_path(), or use union(), intersection(), expand_stroke() and so on.

```py
f.draw_path(f.text_path("Hi", 20, 20))
```

See also: [`text`](#fn-text), [`text_to_points`](#fn-text_to_points), [`draw_path`](#fn-draw_path), [`clip`](#fn-clip).

<a id="fn-text_to_points"></a>
### `f.text_to_points`

```py
f.text_to_points(message: 'object', x: 'float', y: 'float', spacing: 'float' = 5) -> 'list[tuple[float, float]]'
```

Return points along the outlines of some text.

It draws nothing. Each outline starts at its first point, and curves are measured along the curve. An empty message gives an empty list.

| Argument | Meaning |
|---|---|
| `message` | what to write, as for text(). |
| `x`, `y` | the position, as for text(). |
| `spacing` | the distance between points, in pixels. The default is 5. It must be above 0. |

**Returns.** A list of (x, y) tuples.

**Raises.**

- `ValueError`: spacing is 0 or less.
- `TypeError`: spacing is not a number.

```py
for x, y in f.text_to_points("hi", 20, 20, 6):
    f.circle(x, y, 3)
```

See also: [`text_path`](#fn-text_path), [`text`](#fn-text).

<a id="fn-current_font"></a>
### `f.current_font`

```py
f.current_font() -> 'Font'
```

Return the font that text is set in now.

It works for the built-in font too.

**Returns.** A Font. Ask it font.family(), font.style(), font.variations() (axis tag to (minimum, default, maximum); empty if the font is not variable), font.features() (a sorted list of OpenType tags) and font.contains(text) (True when every character has a glyph).

```py
print(f.current_font().contains("e"))
```

See also: [`text_font`](#fn-text_font), [`load_font`](#fn-load_font), [`system_font`](#fn-system_font).

<a id="fn-text_size"></a>
### `f.text_size`

```py
f.text_size(size: 'int') -> 'None'
```

Set the size of text.

The size is an em of that many pixels, as in CSS. Capital letters come out about three-quarters of it. The start is 20. The choice is saved by push() and brought back by pop().

| Argument | Meaning |
|---|---|
| `size` | the size in pixels, above 0. A fraction is cut to a whole number. |

**Raises.**

- `ValueError`: size is 0 or less.

```py
f.text_size(28)
```

See also: [`text`](#fn-text), [`text_width`](#fn-text_width), [`text_font`](#fn-text_font), [`text_leading`](#fn-text_leading).

<a id="fn-text_style"></a>
### `f.text_style`

```py
f.text_style(style: 'str') -> 'None'
```

Choose one of the four styles of the built-in font.

It is ignored once you have chosen a font with text_font(), but remembered for when you go back to the built-in one.

| Argument | Meaning |
|---|---|
| `style` | "normal", "bold", "italic" or "bold_italic". |

**Raises.**

- `ValueError`: the style is not one of those words.

```py
f.text_style("bold")
```

See also: [`text_font`](#fn-text_font), [`text_size`](#fn-text_size).

<a id="fn-text_tracking"></a>
### `f.text_tracking`

```py
f.text_tracking(pixels: 'float') -> 'None'
```

Add space after every letter.

The space is added after the last letter too. It changes text_width(), alignment, text_box() and text_path(). The start is 0. The choice is saved by push() and brought back by pop().

| Argument | Meaning |
|---|---|
| `pixels` | the extra space in pixels. A negative number tightens the text. |

```py
f.text_tracking(4)
```

See also: [`text_width`](#fn-text_width), [`text_size`](#fn-text_size).

<a id="fn-text_fallback"></a>
### `f.text_fallback`

```py
f.text_fallback(*fonts) -> 'None'
```

Choose fonts to use for letters that the current font does not have.

They are tried before funground's built-in fallbacks (emoji, symbols and Devanagari). Emoji are drawn in one colour, the fill. Part of the drawing state, so push() and pop() keep it.

| Argument | Meaning |
|---|---|
| `fonts` | fonts from load_font() or system_font(). Give none to use only the built-in fallbacks. Give None on its own to turn fallback off, so a missing letter is an empty box. |

```py
f.text_fallback(f.system_font("Arial"))
```

See also: [`system_font`](#fn-system_font), [`load_font`](#fn-load_font), [`text_font`](#fn-text_font).

<a id="fn-system_font"></a>
### `f.system_font`

```py
f.system_font(name: 'str')
```

Find a font installed on this computer.

A sketch that uses it can look different on another computer. Font collections (.ttc files) are read too.

| Argument | Meaning |
|---|---|
| `name` | the family name, such as "Arial" (capitals do not matter; the Regular face is used when there are several), or a family with a style, such as "Nirmala UI Bold". |

**Returns.** A Font, for text_font() or text_fallback().

**Raises.**

- `FileNotFoundError`: no installed font has that name.

```py
f.text_font(f.system_font("Arial"))
```

See also: [`load_font`](#fn-load_font), [`text_font`](#fn-text_font), [`text_fallback`](#fn-text_fallback).

<a id="fn-text_features"></a>
### `f.text_features`

```py
f.text_features(**features: 'bool') -> 'None'
```

Turn OpenType features of the font on or off.

Calls add to each other. With no arguments it goes back to the font's defaults.

| Argument | Meaning |
|---|---|
| `features` | each name is a four-letter feature tag, and each value is True or False. For example liga=False turns ligatures off. |

**Raises.**

- `TypeError`: a value is not True or False.

```py
f.text_features(liga=False)
```

See also: [`font_variations`](#fn-font_variations), [`current_font`](#fn-current_font).

<a id="fn-font_variations"></a>
### `f.font_variations`

```py
f.font_variations(**axes: 'float') -> 'None'
```

Set the axes of a variable font.

An axis that the font does not have is ignored, so it is harmless with an ordinary font. With no arguments it goes back to the font's defaults.

| Argument | Meaning |
|---|---|
| `axes` | each name is an axis tag, and each value is a number. For example wght=700 is bold. |

**Raises.**

- `TypeError`: a value is not a number.

```py
f.font_variations(wght=700)
```

See also: [`text_features`](#fn-text_features), [`current_font`](#fn-current_font).

<a id="fn-text_width"></a>
### `f.text_width`

```py
f.text_width(message: 'object') -> 'float'
```

Return how wide some text will be, in pixels.

It is measured at the current text size and font, and it is the exact distance text() advances. Use it to centre or right-align text.

| Argument | Meaning |
|---|---|
| `message` | what to measure. Any value works, or a FormattedString. |

**Returns.** The width in pixels.

```py
msg = "Hello"
f.text(msg, (f.width - f.text_width(msg)) / 2, 100)
```

See also: [`text`](#fn-text), [`text_size`](#fn-text_size), [`text_align`](#fn-text_align).

<a id="fn-text_font"></a>
### `f.text_font`

```py
f.text_font(font, size: 'float | None' = None) -> 'None'
```

Choose the font for the text you draw after this.

The choice is saved by push() and brought back by pop().

| Argument | Meaning |
|---|---|
| `font` | a font from load_font() or system_font(), a path to a font file, or None for the built-in family. |
| `size` | a text size to set at the same time. The default None keeps the size. |

**Raises.**

- `TypeError`: font is not a Font, a path or None.

```py
f.text_font(f.load_font("fonts/MyFont.ttf"), 24)
f.text_font(None)
```

See also: [`load_font`](#fn-load_font), [`system_font`](#fn-system_font), [`text_size`](#fn-text_size), [`text_style`](#fn-text_style).

<a id="fn-load_font"></a>
### `f.load_font`

```py
f.load_font(path: 'str', face: 'int | str' = 0)
```

Load a font file.

Pass the result to text_font(), text_fallback() and so on. A relative path is looked for next to your sketch file first, then in the current folder.

| Argument | Meaning |
|---|---|
| `path` | a .ttf or .otf font file, or a .ttc collection. |
| `face` | for a .ttc collection, which font to use: its number (0 is the first) or its style as a word, such as "Bold". The default is 0. |

**Returns.** A Font. Ask it font.family(), font.style(), font.variations(), font.features() and font.contains(text).

**Raises.**

- `FileNotFoundError`: the file is not found in either place.

```py
mono = f.load_font("fonts/DejaVuSansMono.ttf")
f.text_font(mono)
```

See also: [`text_font`](#fn-text_font), [`system_font`](#fn-system_font), [`current_font`](#fn-current_font).

<a id="transforms-and-the-state-stack"></a>
## Transforms and the state stack

<a id="fn-translate"></a>
### `f.translate`

```py
f.translate(dx: 'float', dy: 'float') -> 'None'
```

Move the origin.

Everything drawn after this is shifted by (dx, dy). Transforms add up, and they apply to shapes, text, paths and clips. Order matters: translate then rotate turns about the new origin. The stack is reset at the start of every draw().

| Argument | Meaning |
|---|---|
| `dx` | how far to move to the right, in pixels. |
| `dy` | how far to move down, in pixels. |

```py
f.translate(f.width / 2, f.height / 2)
```

See also: [`rotate`](#fn-rotate), [`scale`](#fn-scale), [`push`](#fn-push), [`pop`](#fn-pop).

<a id="fn-rotate"></a>
### `f.rotate`

```py
f.rotate(degrees: 'float') -> 'None'
```

Turn later drawing about the current origin.

Degrees are used. 90 is a quarter turn clockwise on the screen. Each call adds to the turns before it.

| Argument | Meaning |
|---|---|
| `degrees` | the angle, in degrees. Use radians() or degrees() to convert if you work in radians. |

```py
f.translate(200, 150)
f.rotate(45)
f.rect(-40, -25, 80, 50)
```

See also: [`translate`](#fn-translate), [`scale`](#fn-scale), [`radians`](#fn-radians), [`push`](#fn-push).

<a id="fn-scale"></a>
### `f.scale`

```py
f.scale(sx: 'float', sy: 'float | None' = None) -> 'None'
```

Grow or shrink later drawing about the origin.

Each call multiplies the scale already in force.

| Argument | Meaning |
|---|---|
| `sx` | the factor sideways. 2 doubles, 0.5 halves. If sy is left out it is used both ways. |
| `sy` | the factor up and down. The default None means the same as sx. |

**Raises.**

- `ValueError`: a factor is 0.

```py
f.scale(2)
f.scale(2, 1)
```

See also: [`translate`](#fn-translate), [`rotate`](#fn-rotate), [`push`](#fn-push).

<a id="fn-shear_x"></a>
### `f.shear_x`

```py
f.shear_x(degrees: 'float') -> 'None'
```

Slant later drawing sideways.

Each point moves along x by tan(degrees) times its y.

| Argument | Meaning |
|---|---|
| `degrees` | the slant, in degrees. |

```py
f.shear_x(20)
```

See also: [`shear_y`](#fn-shear_y), [`apply_matrix`](#fn-apply_matrix).

<a id="fn-shear_y"></a>
### `f.shear_y`

```py
f.shear_y(degrees: 'float') -> 'None'
```

Slant later drawing up or down.

Each point moves along y by tan(degrees) times its x.

| Argument | Meaning |
|---|---|
| `degrees` | the slant, in degrees. |

See also: [`shear_x`](#fn-shear_x), [`apply_matrix`](#fn-apply_matrix).

<a id="fn-apply_matrix"></a>
### `f.apply_matrix`

```py
f.apply_matrix(a: 'float', b: 'float', c: 'float', d: 'float', e: 'float', f: 'float') -> 'None'
```

Multiply a whole transform into later drawing.

A point (x, y) goes to x' = a*x + c*y + e and y' = b*x + d*y + f.

| Argument | Meaning |
|---|---|
| `a`, `b`, `c`, `d` | the four numbers that stretch, turn and slant. a and d are the sideways and up-and-down scale. |
| `e`, `f` | how far to move along x and y, in pixels. |

```py
f.apply_matrix(1, 0, 0.5, 1, 0, 0)
```

See also: [`translate`](#fn-translate), [`rotate`](#fn-rotate), [`scale`](#fn-scale), [`shear_x`](#fn-shear_x), [`reset_matrix`](#fn-reset_matrix).

<a id="fn-reset_matrix"></a>
### `f.reset_matrix`

```py
f.reset_matrix() -> 'None'
```

Forget every translate, rotate, scale and shear so far.

It lasts until the enclosing pop().

See also: [`translate`](#fn-translate), [`push`](#fn-push), [`pop`](#fn-pop).

<a id="fn-push"></a>
### `f.push`

```py
f.push() -> 'None'
```

Save the current transform and style.

pop() brings them back. The style includes fill, stroke, stroke width, text settings, modes and clip. If you forget a pop(), funground pops for you at the end of draw() and prints a warning.

```py
f.push()
f.rotate(30)
f.rect(0, 0, 80, 40)
f.pop()
```

See also: [`pop`](#fn-pop), [`saved_state`](#fn-saved_state).

<a id="fn-pop"></a>
### `f.pop`

```py
f.pop() -> 'None'
```

Restore the transform and style saved by the last push().

A pop() with nothing to restore prints a warning and is ignored.

See also: [`push`](#fn-push), [`saved_state`](#fn-saved_state).

<a id="fn-saved_state"></a>
### `f.saved_state`

```py
f.saved_state() -> 'AbstractContextManager[None]'
```

Return a ``with`` block that saves and restores the transform and style.

It does push() on entry and pop() on exit, even if the block raises an error.

**Returns.** A context manager. Use it as ``with f.saved_state():``.

```py
with f.saved_state():
    f.rotate(30)
    f.rect(0, 0, 80, 40)
```

See also: [`push`](#fn-push), [`pop`](#fn-pop).

<a id="paths-and-clipping"></a>
## Paths and clipping

<a id="fn-path"></a>
### `f.path`

```py
f.path() -> 'PathBuilder'
```

Make a new, empty path that you can reuse.

Chain its methods, each of which returns the builder: move_to(x, y), line_to(x, y), curve_to(cx1, cy1, cx2, cy2, x, y), quad_to(cx, cy, x, y), close(), rect(), ellipse(), circle() and polygon(). Draw it with draw_path(), or use it with clip(). Only closed paths are filled.

**Returns.** A path builder. It also has union(), intersection(), difference(), xor(), expand_stroke(), bounds(), contains(), translate(), scale(), rotate() and copy().

```py
tri = f.path().move_to(0, 0).line_to(40, 0).line_to(20, -30).close()
f.draw_path(tri)
```

See also: [`draw_path`](#fn-draw_path), [`clip`](#fn-clip), [`text_path`](#fn-text_path), [`svg_paths`](#fn-svg_paths).

<a id="fn-draw_path"></a>
### `f.draw_path`

```py
f.draw_path(path: 'PathBuilder') -> 'None'
```

Draw a path made with path().

It is filled (if it is closed) and then stroked, with the current style and transform.

| Argument | Meaning |
|---|---|
| `path` | the path to draw. |

```py
f.draw_path(f.path().circle(50, 50, 40))
```

See also: [`path`](#fn-path), [`clip`](#fn-clip), [`text_path`](#fn-text_path).

<a id="fn-clip"></a>
### `f.clip`

```py
f.clip(path: 'PathBuilder') -> 'None'
```

Limit later drawing to the inside of a path.

The path is treated as closed and follows the current transform. The clip lasts until the enclosing pop() or the end of the saved_state() block, so put it inside one. background() ignores the clip.

| Argument | Meaning |
|---|---|
| `path` | a path made with path() or text_path(). |

```py
with f.saved_state():
    f.clip(f.path().circle(100, 100, 80))
    f.background("gold")
```

See also: [`no_clip`](#fn-no_clip), [`path`](#fn-path), [`saved_state`](#fn-saved_state).

<a id="fn-no_clip"></a>
### `f.no_clip`

```py
f.no_clip() -> 'None'
```

Remove clipping.

It lasts until the enclosing pop() or the end of the saved_state() block, which brings the previous clip back.

See also: [`clip`](#fn-clip), [`saved_state`](#fn-saved_state).

<a id="marks"></a>
## Marks

<a id="fn-mark"></a>
### `f.mark`

```py
f.mark(path: 'PathBuilder | str | None' = None, *, fill: 'Color | None' = <not given>, stroke: 'Color | None' = <not given>, stroke_width: 'float | None' = None) -> 'Mark'
```

Make a mark: a drawing kept as a value, to place as often as you like.

Use it with ``with``: ``with f.mark() as m:`` records the drawing calls in the block instead of drawing them. Each part keeps the fill, stroke and font it was drawn with. The block starts with the current style and no transform, so (0, 0) is the mark's own origin. When it ends, the transform, style and clip are exactly as before, even after an error. Then m.place(x, y) draws the mark. Inside the block you cannot open a layer, make controls, save files, or read or change pixels.

Give a path instead to make a mark from it at once. It is filled (if closed) and stroked with the current style, changed by fill, stroke and stroke_width when you give them.

Give the name of an SVG file to make a mark of its shapes, each with the file's own colours. A name that is not a full path is looked for next to the sketch first, as load_svg() does. The mark's origin is the file's top-left corner.

A mark stays sharp at any size, and stays real shapes and text in a saved PDF or SVG. It cannot be changed once it is made.

| Argument | Meaning |
|---|---|
| `path` | a path made with f.path(), or the name of an .svg file. Leave it out to record a block. |
| `fill` | the fill for a path, as fill() takes it. None means no fill. Left out, it is the current fill. |
| `stroke` | the stroke for a path, as stroke() takes it. None means no stroke. Left out, it is the current stroke. |
| `stroke_width` | the stroke width for a path. Left out (None), it is the current width. |

**Returns.** A Mark, with place(), bounds(), width, height and is_empty.

**Raises.**

- `TypeError`: path is not a path or a file name, or fill, stroke or stroke_width is given without a path.
- `ValueError`: the file name does not end in ".svg", or the file is not an SVG file.
- `FileNotFoundError`: the SVG file is not there.

```py
leaf = f.mark(f.path().ellipse(0, 0, 40, 16), fill="olive", stroke=None)
badge = f.mark("badge.svg")
with f.mark() as flower:
    f.fill("gold")
    f.circle(0, 0, 24)
flower.place(100, 100)
```

See also: [`path`](#fn-path), [`load_svg`](#fn-load_svg), [`saved_state`](#fn-saved_state), [`layer`](#fn-layer).

<a id="play"></a>
## Play

<a id="fn-variations"></a>
### `f.variations`

```py
f.variations(fn, *, columns: 'int | None' = None, **values) -> 'list'
```

Draw several versions of a drawing side by side, as a labelled contact sheet.

Write the drawing as a function with a parameter, then give a list of values to try. variations() calls the function once for each value, and draws each result in its own cell over f.ground.content, with a thin frame and a label such as "gap = 35".

With one parameter the versions go in one row while every cell stays readable: each picture at least 100 units wide, with its label fitting on one line under it. When they do not fit, they wrap into the grid that makes the cells largest (near-square on a square canvas). columns= chooses the number of columns yourself. With two parameters it tries every pair: one row for each value of the first, one column for each value of the second, so columns= is not allowed.

Each version is drawn as if on the whole canvas, then made smaller to fit its cell. Every cell is made smaller by the same amount and keeps the canvas's coordinates, so a change of size or position shows. Each cell shows only the canvas's rectangle: drawing outside the canvas is cut off in the sheet, but kept in the returned mark. Each version starts from the style you have when you call variations() and no transform, so one version's fill() cannot change the next. Each version also starts from the same random seed, so the versions differ only in the parameter. background() in the function paints only that version's cell; in the returned mark it is a rectangle the size of the canvas.

It works in a script, in setup(), and in draw(), where it draws the sheet again every frame.

| Argument | Meaning |
|---|---|
| `fn` | the function that draws one version. It is called with the parameters by name, such as fn(gap=35). |
| `columns` | with one parameter, how many columns the sheet has, a whole number above 0. The default None chooses: one row while it stays readable, otherwise a grid. A parameter of your function cannot be called columns. |
| `values` | one or two parameters, each with a list of values to try, such as gap=[10, 20, 35]. |

**Returns.** A list with one (values, mark) pair for each version, in order. values is a dictionary such as {"gap": 35}; mark is that version as a Mark, without its frame or label, so chosen.place(0, 0) draws it full size.

**Raises.**

- `TypeError`: fn cannot be called, a parameter is given one value instead of a list, or columns is not a whole number.
- `ValueError`: there is no parameter, more than two, a list is empty, columns is 0 or less or given with two parameters, or the cells do not fit in the canvas.

```py
def study(gap):
    for i in range(12):
        f.circle(f.ground.content.left + i * gap, f.ground.content.cy, 20)

f.variations(study, gap=[10, 20, 35, 60])
```

See also: [`keep`](#fn-keep), [`mark`](#fn-mark), [`random_seed`](#fn-random_seed).

<a id="fn-keep"></a>
### `f.keep`

```py
f.keep(note: 'str' = '', *, pdf: 'bool' = False, **settings) -> 'str'
```

Save this version of your picture in a studio folder, with what made it.

The files go in a folder called studio next to your sketch file (or in the current folder when there is no file). They are numbered in order, after any already there: 001.png, 002.png and so on. Each kept version has a picture (.png), a copy of your sketch (.py), and a record (.json). The record holds your note, the settings you give, every control's value, the random and noise seeds, the size and margin, the page or frame, the date, the versions of funground and Python, the fonts used and the files read. It also lists what it could not keep, such as fonts installed on this computer. It prints one line saying where it saved. Grid guides from show() are not in the picture.

In a script it keeps the canvas as drawn so far, at once. In an animated sketch it keeps the next frame that is drawn: the frame being drawn when you call it from draw(), or the next one when you call it from key_pressed() or another event. The picture, the copy and the record are all written when that frame is complete, so the frame number, the controls, the seeds and the fonts in the record are that frame's. If no frame is drawn (after no_loop()), it keeps the frame on the screen.

The seeds make funground's random() and noise() repeatable: f.random_seed(n) and f.noise_seed(n) with the recorded numbers give the same values again. A recorded seed makes funground's randomness repeatable; it does not make every sketch reproducible. The record's lists of fonts, files read and what it could not keep say what else the picture depends on.

| Argument | Meaning |
|---|---|
| `note` | a few words about this version, such as "gap 35 reads as a rhythm". |
| `pdf` | True also saves a .pdf, a vector drawing that stays sharp when printed. The default is False. |
| `settings` | any values you want to remember with it, such as gap=35. |

**Returns.** The path of the files without their ending, such as "studio/007". In an animated sketch the files appear there when the frame is complete.

**Raises.**

- `RuntimeError`: it is used inside a ``with f.mark()`` block, or before f.size().
- `TypeError`: the note is not text.

```py
f.keep("gap 35 reads as a rhythm", gap=35)
f.keep("for printing", pdf=True)
```

See also: [`variations`](#fn-variations), [`save`](#fn-save), [`random_seed`](#fn-random_seed).

<a id="pictures-and-layers"></a>
## Pictures and layers

<a id="fn-create_graphics"></a>
### `f.create_graphics`

```py
f.create_graphics(width: 'int', height: 'int') -> 'Picture'
```

Make a picture: an off-screen canvas.

It starts transparent. It has the same drawing commands as f (fill, circle, text, push, pop, transforms, clip and more) but its own state, transform and pixels. Nothing about it resets between frames. Draw it on the canvas with image().

| Argument | Meaning |
|---|---|
| `width`, `height` | the size in pixels. |

**Returns.** A Picture, with width and height, the drawing commands, get(), set(), copy(), resize(w, h), mask(other), filter(), load_pixels(), pixels, update_pixels() and save(path).

```py
g = f.create_graphics(200, 100)
g.fill("tomato")
g.circle(100, 50, 80)
f.image(g, 20, 20)
```

See also: [`image`](#fn-image), [`layer`](#fn-layer), [`load_image`](#fn-load_image).

<a id="fn-layer"></a>
### `f.layer`

```py
f.layer(name: 'str') -> 'Picture'
```

Return the layer with a given name, and make it if it is new.

A layer is a see-through picture the size of the canvas. Use it with ``with``: everything drawn inside the block goes to the layer. Layers are put over the canvas in the order they were first made. A layer keeps its drawing from frame to frame until you call background() or clear() inside it. Inside the block, f.width, f.mouse_x, random() and the like keep their canvas meaning. Layers do not nest. In a saved PDF or SVG each layer is a real, named layer.

| Argument | Meaning |
|---|---|
| `name` | a name in quotes. It must not be empty. |

**Returns.** A Picture, so ``with f.layer("sky") as sky:`` gives you sky.get(), sky.filter() and sky.save().

**Raises.**

- `RuntimeError`: a layer block is already open.
- `ValueError`: the name is empty.

```py
with f.layer("sky"):
    f.background("skyblue")
```

See also: [`hide_layer`](#fn-hide_layer), [`show_layer`](#fn-show_layer), [`create_graphics`](#fn-create_graphics).

<a id="fn-hide_layer"></a>
### `f.hide_layer`

```py
f.hide_layer(name: 'str') -> 'None'
```

Stop showing a layer.

It keeps its drawing, and show_layer() brings it back. A hidden layer is left out of the window, a PNG and get(). It is kept in a PDF or SVG, switched off.

| Argument | Meaning |
|---|---|
| `name` | the layer's name. |

**Raises.**

- `ValueError`: there is no layer with that name.

See also: [`show_layer`](#fn-show_layer), [`layer`](#fn-layer).

<a id="fn-show_layer"></a>
### `f.show_layer`

```py
f.show_layer(name: 'str') -> 'None'
```

Show a layer that hide_layer() hid.

| Argument | Meaning |
|---|---|
| `name` | the layer's name. |

**Raises.**

- `ValueError`: there is no layer with that name.

See also: [`hide_layer`](#fn-hide_layer), [`layer`](#fn-layer).

<a id="images-and-svg"></a>
## Images and SVG

<a id="fn-image"></a>
### `f.image`

```py
f.image(picture, x: 'float', y: 'float', width: 'float | None' = None, height: 'float | None' = None, sx: 'float | None' = None, sy: 'float | None' = None, sw: 'float | None' = None, sh: 'float | None' = None) -> 'None'
```

Draw a picture.

It is drawn as it is at this moment: later drawing on the picture does not change what was placed. image_mode() changes how x, y, width and height are read. tint() colours it.

| Argument | Meaning |
|---|---|
| `picture` | a Picture, from load_image(), load_svg(), create_graphics(), get() or spectrogram(). |
| `x`, `y` | where to put it, by default the top-left corner. |
| `width`, `height` | the size to stretch it to. The default None uses the picture's own size. |
| `sx`, `sy`, `sw`, `sh` | give all four to draw only that part of the picture (in its own pixels) into the box. A part that reaches outside the picture is clipped and keeps its place. sw and sh must be above 0. |

**Raises.**

- `ValueError`: only some of sx, sy, sw and sh were given, or sw or sh is not above 0.

```py
f.image(photo, 0, 0)
f.image(photo, 0, 0, 200, 150, 40, 30, 100, 75)
```

See also: [`load_image`](#fn-load_image), [`create_graphics`](#fn-create_graphics), [`image_mode`](#fn-image_mode), [`tint`](#fn-tint).

<a id="fn-image_mode"></a>
### `f.image_mode`

```py
f.image_mode(mode: 'str') -> 'None'
```

Choose how image() reads its numbers.

The choice is saved by push() and brought back by pop().

| Argument | Meaning |
|---|---|
| `mode` | "corner" (the default: x, y is the top-left corner), "center" (x, y is the middle) or "corners" (x, y and the opposite corner; it needs a width and height). |

**Raises.**

- `ValueError`: the mode is not one of those words.

```py
f.image_mode("center")
```

See also: [`image`](#fn-image), [`rect_mode`](#fn-rect_mode).

<a id="fn-load_image"></a>
### `f.load_image`

```py
f.load_image(path: 'str') -> 'Picture'
```

Read an image file and return it as a picture.

Draw it with image(). A relative path is looked for next to your sketch file first, then in the current folder. Photos from phones are turned the right way up. Transparency is kept. You can draw on the picture like any other.

| Argument | Meaning |
|---|---|
| `path` | the file name: PNG, JPEG, GIF, BMP, TGA and others. |

**Returns.** A Picture, with width and height in pixels.

**Raises.**

- `FileNotFoundError`: the file is not found in either place.
- `ValueError`: the file is not an image.

```py
photo = f.load_image("photo.jpg")
f.image(photo, 0, 0)
```

See also: [`image`](#fn-image), [`load_svg`](#fn-load_svg), [`create_graphics`](#fn-create_graphics).

<a id="fn-load_svg"></a>
### `f.load_svg`

```py
f.load_svg(path: 'str') -> 'Picture'
```

Read an SVG file and return a picture of its shapes.

It stays sharp at any size, and stays vector in a saved PDF or SVG. The size is the file's width and height (96 to the inch), or its viewBox. It reads paths, rect, circle, ellipse, line, polyline, polygon, groups, use, transforms, fill and stroke colours, stroke width, caps, joins, dashes and fill-rule. A gradient or pattern uses its first colour. Text, images, filters, masks and animation are ignored. A relative path is looked for next to your sketch file first, then in the current folder.

| Argument | Meaning |
|---|---|
| `path` | the SVG file name. |

**Returns.** A Picture. Draw it with image().

**Raises.**

- `FileNotFoundError`: the file is not found.
- `ValueError`: the file is not an SVG.

```py
badge = f.load_svg("badge.svg")
f.image(badge, 20, 20)
```

See also: [`svg_paths`](#fn-svg_paths), [`load_image`](#fn-load_image), [`image`](#fn-image).

<a id="fn-svg_paths"></a>
### `f.svg_paths`

```py
f.svg_paths(path: 'str') -> 'list[PathBuilder]'
```

Read an SVG file and return its shapes as paths.

There is one path for each shape, in the file's own coordinates. Use them for booleans, clips or your own colours.

| Argument | Meaning |
|---|---|
| `path` | the SVG file name. A relative path is looked for next to your sketch file first, then in the current folder. |

**Returns.** A list of path builders, as from path().

**Raises.**

- `FileNotFoundError`: the file is not found.
- `ValueError`: the file is not an SVG.

```py
shapes = f.svg_paths("badge.svg")
f.draw_path(shapes[0])
```

See also: [`load_svg`](#fn-load_svg), [`path`](#fn-path), [`draw_path`](#fn-draw_path).

<a id="pixels-and-filters"></a>
## Pixels and filters

<a id="fn-get"></a>
### `f.get`

```py
f.get(x: 'float', y: 'float', w: 'float | None' = None, h: 'float | None' = None)
```

Read a pixel, or copy a region of the canvas.

It sees what has been drawn so far, this frame included. Outside the canvas is transparent. Coordinates are rounded down. On a high-resolution screen it reads the top-left real pixel of a logical one.

| Argument | Meaning |
|---|---|
| `x`, `y` | the pixel, or the top-left corner of the region. |
| `w`, `h` | the size of the region. Give both to copy a region. Leave them out (None) to read one pixel. |

**Returns.** With no w and h: a colour with .red, .green, .blue and .alpha. With w and h: a new Picture copied from that region.

```py
c = f.get(10, 20)
part = f.get(0, 0, 50, 50)
```

See also: [`set`](#fn-set), [`load_pixels`](#fn-load_pixels), [`image`](#fn-image).

<a id="fn-set"></a>
### `f.set`

```py
f.set(x: 'float', y: 'float', color, *more: 'float') -> 'None'
```

Make one pixel exactly one colour.

Fill, stroke, transform, clip, tint, opacity and blend mode do not apply. Outside the canvas, nothing happens.

| Argument | Meaning |
|---|---|
| `x`, `y` | the pixel. |
| `color` | any colour that fill() takes. |
| `more` | extra numbers, as for fill(). |

```py
f.set(10, 20, "red")
```

See also: [`get`](#fn-get), [`update_pixels`](#fn-update_pixels).

<a id="fn-load_pixels"></a>
### `f.load_pixels`

```py
f.load_pixels() -> 'None'
```

Copy the canvas into f.pixels.

f.pixels is then a bytearray with red, green, blue and alpha (0 to 255, not premultiplied) for every pixel, row by row from the top left. The pixel at (x, y) starts at index (y * f.width + x) * 4. Change the numbers in place, then call update_pixels(). A Python loop over a whole 640 by 400 canvas takes seconds.

```py
f.load_pixels()
f.pixels[(10 * f.width + 20) * 4] = 255
f.update_pixels()
```

See also: [`update_pixels`](#fn-update_pixels), [`get`](#fn-get), [`set`](#fn-set).

<a id="fn-update_pixels"></a>
### `f.update_pixels`

```py
f.update_pixels() -> 'None'
```

Write f.pixels back onto the canvas.

It works like a set() of every pixel.

**Raises.**

- `RuntimeError`: load_pixels() was not called first.

See also: [`load_pixels`](#fn-load_pixels), [`set`](#fn-set).

<a id="fn-filter"></a>
### `f.filter`

```py
f.filter(kind: 'str', value: 'float | None' = None) -> 'None'
```

Change everything drawn so far, in place.

Alpha is kept, except by "opaque". "posterize", "erode" and "dilate" are faster with funground[extras] installed, but the result is the same.

| Argument | Meaning |
|---|---|
| `kind` | "threshold", "gray", "opaque", "invert", "blur", "posterize", "erode" or "dilate". |
| `value` | for "threshold", a level from 0 to 1 (default 0.5). For "blur", a radius in pixels (default 1). For "posterize", the number of levels, 2 to 255 (required). The others take none. |

**Raises.**

- `ValueError`: the kind is unknown, or the value is out of range.

```py
f.filter("blur", 3)
```

See also: [`get`](#fn-get), [`create_graphics`](#fn-create_graphics).

<a id="randomness-and-noise"></a>
## Randomness and noise

<a id="fn-random"></a>
### `f.random`

```py
f.random(low: 'float' = 1.0, high: 'float | None' = None) -> 'float'
```

Return a random number.

random(10) gives a number from 0 up to 10. random(5, 10) gives a number from 5 up to 10. random() gives a number from 0 up to 1. It uses its own generator and never touches Python's own random module.

| Argument | Meaning |
|---|---|
| `low` | with one argument, the top of the range (it starts at 0). With high as well, the bottom. |
| `high` | the top of the range. The default None means low is the top. |

**Returns.** A floating-point number.

```py
x = f.random(f.width)
d = f.random(10, 40)
```

See also: [`random_seed`](#fn-random_seed), [`random_choice`](#fn-random_choice), [`random_gaussian`](#fn-random_gaussian), [`noise`](#fn-noise).

<a id="fn-random_choice"></a>
### `f.random_choice`

```py
f.random_choice(items)
```

Return one item picked at random.

It can be repeated with random_seed().

| Argument | Meaning |
|---|---|
| `items` | a list, a tuple or a string. It must not be empty. |

**Returns.** One of the items. For a string, one letter.

**Raises.**

- `ValueError`: there are no items.

```py
f.fill(f.random_choice(["red", "gold", "skyblue"]))
```

See also: [`random`](#fn-random), [`random_seed`](#fn-random_seed).

<a id="fn-random_gaussian"></a>
### `f.random_gaussian`

```py
f.random_gaussian(mean: 'float' = 0.0, sd: 'float' = 1.0) -> 'float'
```

Return a random number from a bell curve.

Most values are near the mean. About two thirds are within one sd of it.

| Argument | Meaning |
|---|---|
| `mean` | the middle of the bell. The default is 0.0. |
| `sd` | the spread. The default is 1.0. It cannot be negative. |

**Returns.** A floating-point number.

**Raises.**

- `ValueError`: sd is negative.

```py
f.random_gaussian(200, 30)
```

See also: [`random`](#fn-random), [`random_seed`](#fn-random_seed).

<a id="fn-random_seed"></a>
### `f.random_seed`

```py
f.random_seed(seed: 'int | None' = None) -> 'None'
```

Make random() repeatable.

The same seed gives the same sequence. It also covers random_gaussian(), random_choice() and the random parts of sounds. Any whole number works, however large or negative, and f.keep() records it exactly as you gave it.

When you do not call random_seed(), funground picks a seed at the start of the run (a number below 1,000,000) and f.keep() records it, so f.random_seed(that number) gives the same random numbers again. A recorded seed makes funground's randomness repeatable; it does not make every sketch reproducible, because a sketch can also depend on the mouse, the clock, files or Python's own random module.

| Argument | Meaning |
|---|---|
| `seed` | a whole number. The default None starts from a different, unpredictable place each time, and records where. |

```py
f.random_seed(7)
```

See also: [`random`](#fn-random), [`noise_seed`](#fn-noise_seed).

<a id="fn-noise"></a>
### `f.noise`

```py
f.noise(x: 'float', y: 'float' = 0.0, z: 'float' = 0.0) -> 'float'
```

Return a smooth random number from 0 to 1.

Nearby inputs give nearby outputs, so it makes gentle wandering. Take small steps through the input, such as x * 0.01. noise_detail() changes how bumpy it is.

| Argument | Meaning |
|---|---|
| `x` | the place along a line. |
| `y` | a second direction. The default is 0.0. |
| `z` | a third direction, often used for time. The default is 0.0. |

**Returns.** A number from 0 to 1.

```py
y = f.height * f.noise(f.frame_count * 0.01)
```

See also: [`noise_seed`](#fn-noise_seed), [`noise_detail`](#fn-noise_detail), [`random`](#fn-random).

<a id="fn-noise_detail"></a>
### `f.noise_detail`

```py
f.noise_detail(octaves: 'int', falloff: 'float | None' = None) -> 'None'
```

Choose how much detail noise() has.

| Argument | Meaning |
|---|---|
| `octaves` | how many layers of detail to add. The default is 4. It must be 1 or more. Fewer is smoother and faster. |
| `falloff` | how much each layer fades, above 0 and below 1. The default None keeps the current one (0.5 at the start). |

**Raises.**

- `ValueError`: octaves is less than 1, or falloff is not between 0 and 1.

```py
f.noise_detail(2)
```

See also: [`noise`](#fn-noise), [`noise_seed`](#fn-noise_seed).

<a id="fn-noise_seed"></a>
### `f.noise_seed`

```py
f.noise_seed(seed: 'int') -> 'None'
```

Make noise() repeatable.

The same seed gives the same values as p5.js's noiseSeed. Any whole number works, and f.keep() records it exactly as you gave it. Without noise_seed(), funground picks one the first time noise() is used, and f.keep() records that.

| Argument | Meaning |
|---|---|
| `seed` | a whole number. |

```py
f.noise_seed(1)
```

See also: [`noise`](#fn-noise), [`random_seed`](#fn-random_seed).

<a id="maths"></a>
## Maths

<a id="fn-constrain"></a>
### `f.constrain`

```py
f.constrain(value: 'float', low: 'float', high: 'float') -> 'float'
```

Keep a number inside a minimum and a maximum.

| Argument | Meaning |
|---|---|
| `value` | the number to limit. |
| `low` | the smallest answer. |
| `high` | the largest answer. |

**Returns.** low if value is below it, high if value is above it, otherwise value.

```py
x = f.constrain(x, 20, f.width - 20)
```

See also: [`map_range`](#fn-map_range), [`lerp`](#fn-lerp).

<a id="fn-distance"></a>
### `f.distance`

```py
f.distance(x1: 'float', y1: 'float', x2: 'float', y2: 'float') -> 'float'
```

Return the straight-line distance between two points.

| Argument | Meaning |
|---|---|
| `x1`, `y1` | the first point. |
| `x2`, `y2` | the second point. |

**Returns.** The distance, in the same units as the points.

```py
d = f.distance(x, y, f.mouse_x, f.mouse_y)
```

See also: [`mag`](#fn-mag), [`constrain`](#fn-constrain).

<a id="fn-lerp"></a>
### `f.lerp`

```py
f.lerp(start: 'float', stop: 'float', amount: 'float') -> 'float'
```

Return the number that is part of the way from start to stop.

| Argument | Meaning |
|---|---|
| `start` | the first number. |
| `stop` | the second number. |
| `amount` | how far to go. 0 gives start, 1 gives stop, and 0.5 is halfway. It may go beyond 0 and 1. |

**Returns.** start + (stop - start) * amount.

```py
print(f.lerp(0, 100, 0.25))
```

See also: [`norm`](#fn-norm), [`map_range`](#fn-map_range), [`lerp_color`](#fn-lerp_color).

<a id="fn-map_range"></a>
### `f.map_range`

```py
f.map_range(value: 'float', start1: 'float', stop1: 'float', start2: 'float', stop2: 'float', clamp: 'bool' = False) -> 'float'
```

Re-scale a number from one range to another.

| Argument | Meaning |
|---|---|
| `value` | the number to convert. |
| `start1`, `stop1` | the range it is in now. |
| `start2`, `stop2` | the range to convert it to. |
| `clamp` | True keeps the answer inside the second range. The default False lets it go beyond. |

**Returns.** The converted number.

**Raises.**

- `ValueError`: start1 and stop1 are the same.

```py
grey = f.map_range(f.mouse_x, 0, f.width, 0, 255)
```

See also: [`lerp`](#fn-lerp), [`norm`](#fn-norm), [`constrain`](#fn-constrain).

<a id="fn-mag"></a>
### `f.mag`

```py
f.mag(x: 'float', y: 'float') -> 'float'
```

Return the length of the arrow (x, y).

That is the distance from (0, 0).

| Argument | Meaning |
|---|---|
| `x`, `y` | the sideways and up-and-down parts. |

**Returns.** The length. mag(3, 4) is 5.

```py
print(f.mag(3, 4))
```

See also: [`distance`](#fn-distance).

<a id="fn-norm"></a>
### `f.norm`

```py
f.norm(value: 'float', start: 'float', stop: 'float') -> 'float'
```

Return where a number sits between two others, as 0 to 1.

| Argument | Meaning |
|---|---|
| `value` | the number to place. |
| `start` | the number that gives 0. |
| `stop` | the number that gives 1. |

**Returns.** (value - start) / (stop - start).

**Raises.**

- `ValueError`: start and stop are the same.

```py
print(f.norm(25, 0, 100))
```

See also: [`lerp`](#fn-lerp), [`map_range`](#fn-map_range).

<a id="fn-degrees"></a>
### `f.degrees`

```py
f.degrees(radians: 'float') -> 'float'
```

Convert radians to degrees.

Use it, for example, to give rotate() an angle from math.atan2.

| Argument | Meaning |
|---|---|
| `radians` | an angle in radians. |

**Returns.** The angle in degrees.

```py
import math
f.rotate(f.degrees(math.atan2(1, 1)))
```

See also: [`radians`](#fn-radians), [`rotate`](#fn-rotate).

<a id="fn-radians"></a>
### `f.radians`

```py
f.radians(degrees: 'float') -> 'float'
```

Convert degrees to radians.

Use it with math.sin and math.cos. rotate() itself takes degrees.

| Argument | Meaning |
|---|---|
| `degrees` | an angle in degrees. |

**Returns.** The angle in radians.

```py
import math
y = math.sin(f.radians(45))
```

See also: [`degrees`](#fn-degrees), [`rotate`](#fn-rotate).

<a id="time"></a>
## Time

<a id="fn-year"></a>
### `f.year`

```py
f.year() -> 'int'
```

Return the year, for example 2026.

See also: [`month`](#fn-month), [`day`](#fn-day).

<a id="fn-month"></a>
### `f.month`

```py
f.month() -> 'int'
```

Return the month, from 1 to 12.

See also: [`day`](#fn-day), [`year`](#fn-year).

<a id="fn-day"></a>
### `f.day`

```py
f.day() -> 'int'
```

Return the day of the month, from 1 to 31.

See also: [`month`](#fn-month), [`year`](#fn-year).

<a id="fn-hour"></a>
### `f.hour`

```py
f.hour() -> 'int'
```

Return the clock's hour, from 0 to 23.

```py
print(f.hour(), f.minute(), f.second())
```

See also: [`minute`](#fn-minute), [`second`](#fn-second).

<a id="fn-minute"></a>
### `f.minute`

```py
f.minute() -> 'int'
```

Return the clock's minutes, from 0 to 59.

See also: [`second`](#fn-second), [`hour`](#fn-hour).

<a id="fn-second"></a>
### `f.second`

```py
f.second() -> 'int'
```

Return the clock's seconds, from 0 to 59.

See also: [`minute`](#fn-minute), [`hour`](#fn-hour).

<a id="fn-millis"></a>
### `f.millis`

```py
f.millis() -> 'int'
```

Return the milliseconds since the sketch started running.

**Returns.** A whole number of thousandths of a second.

```py
seconds = f.millis() / 1000
```

See also: [`frame_rate`](#fn-frame_rate).

<a id="interaction-and-controls"></a>
## Interaction and controls

<a id="fn-key_down"></a>
### `f.key_down`

```py
f.key_down(key: 'str | int') -> 'bool'
```

Return whether a key is held down right now.

Escape also closes the sketch. With no window, no key is ever down.

| Argument | Meaning |
|---|---|
| `key` | "left", "right", "up", "down", "space", "enter", "escape", or a single character such as "a" or "7". Capitals do not matter. |

**Returns.** True while the key is held.

**Raises.**

- `ValueError`: the name is not one of those.

```py
if f.key_down("left"):
    x -= 3
```

See also: `is_key_pressed`, `key`, `key_code`.

<a id="fn-cursor"></a>
### `f.cursor`

```py
f.cursor(kind: 'str' = 'arrow') -> 'None'
```

Choose the shape of the mouse pointer over the canvas.

| Argument | Meaning |
|---|---|
| `kind` | "arrow" (the default), "cross", "hand", "move", "text" or "wait". |

**Raises.**

- `ValueError`: the kind is not one of those names.

```py
f.cursor("hand")
```

See also: [`no_cursor`](#fn-no_cursor).

<a id="fn-no_cursor"></a>
### `f.no_cursor`

```py
f.no_cursor() -> 'None'
```

Hide the mouse pointer over the canvas.

Use cursor() to show it again.

See also: [`cursor`](#fn-cursor).

<a id="fn-create_button"></a>
### `f.create_button`

```py
f.create_button(label: 'str') -> 'Button'
```

Make a button in the panel below the canvas.

Make it in setup(), and read it in draw().

| Argument | Meaning |
|---|---|
| `label` | the text on the button. |

**Returns.** A Button. button.clicked() is True once for each click since it was last asked.

```py
reset = f.create_button("reset")
if reset.clicked():
    f.background("white")
```

See also: [`create_slider`](#fn-create_slider), [`create_checkbox`](#fn-create_checkbox).

<a id="fn-create_checkbox"></a>
### `f.create_checkbox`

```py
f.create_checkbox(label: 'str', checked: 'bool' = False) -> 'Checkbox'
```

Make a tick box in the panel below the canvas.

Make it in setup(), and read it in draw().

| Argument | Meaning |
|---|---|
| `label` | the text beside the box. |
| `checked` | whether it starts ticked. The default is False. |

**Returns.** A Checkbox. box.checked() reads it. box.checked(True) sets it.

```py
grid = f.create_checkbox("grid")
if grid.checked():
    f.line(0, 0, f.width, f.height)
```

See also: [`create_slider`](#fn-create_slider), [`create_button`](#fn-create_button).

<a id="fn-create_slider"></a>
### `f.create_slider`

```py
f.create_slider(low: 'float', high: 'float', value: 'float | None' = None, step: 'float | None' = None, label: 'str | None' = None) -> 'Slider'
```

Make a slider in a panel below the canvas.

Make it in setup() (or at the top of the file) and keep it in a variable. Read it in draw(). The panel is not part of the picture: it is not in f.width or f.height, saves, or get(). Making a control inside draw(), or in a script, is a RuntimeError. Without a window the slider keeps its value.

| Argument | Meaning |
|---|---|
| `low`, `high` | the smallest and largest value. low must be below high. |
| `value` | where the slider starts. The default None starts at low. |
| `step` | the size of each move. The default None moves smoothly. It must be above 0. |
| `label` | the text beside the slider. The default None has no label. |

**Returns.** A Slider. slider.value() reads the value. slider.value(v) sets it.

**Raises.**

- `ValueError`: low is not below high, or step is 0 or less.

```py
size = f.create_slider(10, 100, 40, step=5, label="size")
f.circle(200, 150, size.value())
```

See also: [`create_checkbox`](#fn-create_checkbox), [`create_button`](#fn-create_button).

<a id="saving"></a>
## Saving

<a id="fn-save"></a>
### `f.save`

```py
f.save(path: 'str', *, text: 'str' = 'live') -> 'None'
```

Save this frame to a picture or document file.

The file is written when the frame is complete, and it holds everything that frame drew, including what comes after the call. In a script, it writes at once. A .png holds pixels. A .pdf or .svg holds a true vector drawing. A .gif or .mp4 records an animation (see save_gif and save_movie). Any other extension is an error that names the choices. In a document of several pages, a PDF holds every page.

A PNG is written at the screen's real resolution, so on a 2x display a 640 by 400 window gives a 1280 by 800 file.

| Argument | Meaning |
|---|---|
| `path` | the file name. Its ending decides the kind: ".png", ".pdf" or ".svg". |
| `text` | for a PDF or SVG only. "live" (the default) keeps text real and editable. "shapes" draws every letter as a shape, so the file looks right without the font. A PNG ignores it. |

**Raises.**

- `ValueError`: the file ending is not one that save() knows, or text is not "live" or "shapes".

```py
if f.key_down("s"):
    f.save("my_sketch.png")
```

See also: [`save_frames`](#fn-save_frames), [`save_gif`](#fn-save_gif), [`save_movie`](#fn-save_movie), [`new_page`](#fn-new_page).

<a id="fn-save_frames"></a>
### `f.save_frames`

```py
f.save_frames(pattern: 'str', count: 'int') -> 'None'
```

Save this frame and the next ones as numbered picture files.

| Argument | Meaning |
|---|---|
| `pattern` | the file name with a run of # signs, which becomes the frame number. "frames/####.png" gives frames/0001.png, frames/0002.png and so on. |
| `count` | how many frames to save in all, this one included. |

```py
f.save_frames("frames/####.png", 60)
```

See also: [`save`](#fn-save), [`save_gif`](#fn-save_gif), [`save_movie`](#fn-save_movie).

<a id="fn-save_gif"></a>
### `f.save_gif`

```py
f.save_gif(path: 'str', seconds: 'float') -> 'None'
```

Record the next few seconds of an animated sketch into a GIF.

The GIF loops for ever. Each frame lasts 1 divided by the frame rate. It needs Pillow (install funground[extras]) or ffmpeg. It is an error to call it again while recording, or in a script (use frame_duration() and save() for a script).

| Argument | Meaning |
|---|---|
| `path` | the file name. It must end in ".gif". |
| `seconds` | how long to record, starting from the next frame. |

```py
f.save_gif("spin.gif", 2)
```

See also: [`save_movie`](#fn-save_movie), [`save_frames`](#fn-save_frames), [`frame_duration`](#fn-frame_duration).

<a id="fn-save_movie"></a>
### `f.save_movie`

```py
f.save_movie(path: 'str', seconds: 'float') -> 'None'
```

Record the next few seconds of an animated sketch into an MP4 movie.

It needs ffmpeg on your PATH. A canvas with an odd width or height is padded by one pixel.

| Argument | Meaning |
|---|---|
| `path` | the file name. It must end in ".mp4". |
| `seconds` | how long to record, starting from the next frame. |

```py
f.save_movie("spin.mp4", 2)
```

See also: [`save_gif`](#fn-save_gif), [`save_frames`](#fn-save_frames), [`frame_duration`](#fn-frame_duration).

<a id="ground"></a>
## Ground

<a id="fn-area"></a>
### `f.area`

```py
f.area(x: 'float', y: 'float', w: 'float', h: 'float') -> 'Area'
```

Make an area: a rectangle kept as a value.

An area has left, top, right, bottom, width, height, cx and cy (its centre). inset() gives a smaller area inside it, and grid() divides it into cells. f.ground, f.ground.content and every grid cell are areas too. An area may be 0 wide or 0 high, but not less. It draws nothing by itself.

| Argument | Meaning |
|---|---|
| `x` | the left edge. |
| `y` | the top edge. |
| `w` | the width, 0 or more. |
| `h` | the height, 0 or more. |

**Returns.** A new Area.

**Raises.**

- `TypeError`: a value is not a number.
- `ValueError`: w or h is negative, or a value is not finite.

```py
panel = f.area(40, 40, 320, 200)
f.rect(panel.left, panel.top, panel.width, panel.height)
for cell in panel.inset(10).grid(4, 2, gutter=6):
    f.circle(cell.cx, cell.cy, 20)
```

See also: [`grid`](#fn-grid), [`ground`](#fn-ground).

<a id="fn-grid"></a>
### `f.grid`

```py
f.grid(cols: 'int', rows: 'int', *, gutter: 'float | tuple' = 0, area: 'object' = None) -> 'Grid'
```

Divide an area into a grid of equal cells.

The cells cover f.ground.content (the canvas inside the margins), or the area you give. The grid works like a list of its cells, row by row, left to right: a for loop goes through them, len() counts them, g[0] is the top-left cell, g[-1] the last, and g[1:3] gives a list. Each cell is an area (left, top, right, bottom, width, height, cx, cy) with col, row and index, all counted from 0, so a cell can be the area of another grid.

The grid also has g.cell(col, row), g.span(col, row, cols, rows) for one area over several cells and the gutters between them, g.column_count and g.row_count, g.columns and g.rows as lists of areas, and g.show() to draw guide lines in the window.

| Argument | Meaning |
|---|---|
| `cols` | how many columns. A whole number above 0. |
| `rows` | how many rows. A whole number above 0. |
| `gutter` | the gap between cells. One number is used both across and down. A tuple (column_gutter, row_gutter) sets them apart. The default is 0. |
| `area` | what to divide: an area such as f.ground, a cell or f.area(...), or any object with left, top, width and height. The default None is f.ground.content. |

**Returns.** A Grid of cols times rows cells.

**Raises.**

- `TypeError`: cols or rows is not a whole number, a gutter is not a number, or area has no edges.
- `ValueError`: cols or rows is 0 or less, a gutter is negative, or the gutters leave no room for the cells.

```py
g = f.grid(3, 2, gutter=10)
for cell in g:
    f.circle(cell.cx, cell.cy, cell.width * 0.8)
g.show()
```

See also: [`area`](#fn-area), [`ground`](#fn-ground), [`size`](#fn-size), [`mm`](#fn-mm).

<a id="fn-mm"></a>
### `f.mm`

```py
f.mm(n: 'float') -> 'float'
```

Convert millimetres to funground units.

One unit is one point, as in a PDF: 72 to the inch, so 1 mm is about 2.83 units. It is a plain conversion. It does not change the canvas.

| Argument | Meaning |
|---|---|
| `n` | a length in millimetres. |

**Returns.** The length in funground units, as a float.

```py
f.size("A4", margin=f.mm(15))
```

See also: [`inch`](#fn-inch), [`size`](#fn-size), [`grid`](#fn-grid).

<a id="fn-inch"></a>
### `f.inch`

```py
f.inch(n: 'float') -> 'float'
```

Convert inches to funground units.

One unit is one point, as in a PDF: 72 to the inch. It is a plain conversion. It does not change the canvas.

| Argument | Meaning |
|---|---|
| `n` | a length in inches. |

**Returns.** The length in funground units, as a float. inch(1) is 72.0.

```py
f.size(f.inch(6), f.inch(4))
```

See also: [`mm`](#fn-mm), [`size`](#fn-size), [`grid`](#fn-grid).

<a id="fn-ground"></a>
### `f.ground`

```py
f.ground
```

The canvas as an area, with its margins.

f.ground is the whole canvas and f.ground.content is the part inside the margins. Both are areas, so they have left, top, right, bottom, width, height, cx and cy, and inset() and grid(). f.ground is made fresh each time you read it, so it always matches the canvas. You do not make a Ground yourself: set the margins with f.size(..., margin=...).

```py
f.size("A5", margin=f.mm(12))
f.background("linen")
c = f.ground.content
f.rect(c.left, c.top, c.width, c.height)
```

See also: [`area`](#fn-area), [`grid`](#fn-grid), [`size`](#fn-size).

<a id="motion-and-pages"></a>
## Motion and pages

<a id="fn-frame_duration"></a>
### `f.frame_duration`

```py
f.frame_duration(seconds: 'float') -> 'None'
```

Set how long each page is shown in a saved GIF or MP4.

This is for scripts. It applies to this page and the pages after it, until you call it again. The start is 0.1 seconds. Then save("x.gif") or save("x.mp4") writes every page as a frame, all of the same size.

| Argument | Meaning |
|---|---|
| `seconds` | how long to show the page. It must be above 0. |

**Raises.**

- `ValueError`: seconds is 0 or less.

```py
f.frame_duration(0.2)
```

See also: [`new_page`](#fn-new_page), [`save`](#fn-save), [`save_gif`](#fn-save_gif).

<a id="fn-new_page"></a>
### `f.new_page`

```py
f.new_page(width: 'int | str | None' = None, height: 'int | None' = None) -> 'None'
```

End this page and start a blank one.

This is for scripts (a file with no draw()). Colours, text settings and other styles carry over. The transform starts afresh. After a few pages, save("x.pdf") writes every page. PNG and SVG write x_1.png, x_2.png and so on. In a window, the arrow keys turn the pages.

| Argument | Meaning |
|---|---|
| `width` | a page width in points, or a page name such as "A4" (see page_size). Leave it out to keep the size. |
| `height` | the page height in points. Leave it out when width is a name or None. |

**Raises.**

- `RuntimeError`: an animated sketch has one canvas, so it cannot start a new page.
- `ValueError`: a page name was given together with a height, or the name is unknown.

```py
f.new_page("A5")
```

See also: [`page_count`](#fn-page_count), [`page_size`](#fn-page_size), [`save`](#fn-save).

<a id="fn-page_size"></a>
### `f.page_size`

```py
f.page_size(name: 'str', landscape: 'bool' = False) -> 'tuple[int, int]'
```

Return the size of a named page, in points.

Add "Landscape" to the name, or give landscape=True, to turn the page on its side.

| Argument | Meaning |
|---|---|
| `name` | "A3", "A4", "A5", "B5", "Letter", "Legal", "Tabloid" or "Square". Capitals do not matter. "A4Landscape" is also allowed. |
| `landscape` | True turns the page on its side. The default False keeps it upright. |

**Returns.** A (width, height) tuple of whole numbers. page_size("A4") is (595, 842).

**Raises.**

- `ValueError`: the name is not one of the page names.

```py
f.size(*f.page_size("A4"))
```

See also: [`new_page`](#fn-new_page), [`size`](#fn-size).

<a id="fn-page_count"></a>
### `f.page_count`

```py
f.page_count() -> 'int'
```

Return how many pages the document has so far.

**Returns.** A whole number, 1 or more.

```py
print(f.page_count())
```

See also: [`new_page`](#fn-new_page).

<a id="sound"></a>
## Sound

<a id="fn-load_sound"></a>
### `f.load_sound`

```py
f.load_sound(path: 'str')
```

Read a sound file and return a sound.

A relative path is looked for next to your sketch file first, then in the current folder. With no sound device (or FUNGROUND_HEADLESS=1) it plays silently and keeps time.

| Argument | Meaning |
|---|---|
| `path` | a WAV, OGG or MP3 file. |

**Returns.** A Sound: play(), loop(), stop(), pause(), set_volume(v), is_playing(), duration(), current_time(), level(), spectrum(bands), pitch(), pan(p), reverb(amount), samples() and save(path).

**Raises.**

- `FileNotFoundError`: the file is not found in either place.
- `ValueError`: the file is not sound.

```py
beep = f.load_sound("beep.wav")
beep.play()
```

See also: [`create_sound`](#fn-create_sound), [`tone`](#fn-tone), [`note`](#fn-note), [`draw_wave`](#fn-draw_wave).

<a id="fn-create_sound"></a>
### `f.create_sound`

```py
f.create_sound(samples, rate: 'int' = 44100)
```

Make a sound from a list of numbers.

It is an ordinary sound. sound.samples() gives the numbers back.

| Argument | Meaning |
|---|---|
| `samples` | a list of numbers from -1 to 1, one channel. Numbers outside that range are clipped. |
| `rate` | how many numbers make one second. The default is 44100. |

**Returns.** A Sound: play(), loop(), stop(), level(), spectrum(bands), samples() and so on.

**Raises.**

- `ValueError`: the list is empty or has things that are not numbers.

```py
import math
s = f.create_sound([math.sin(i / 9) for i in range(44100)])
s.play()
```

See also: [`tone`](#fn-tone), [`load_sound`](#fn-load_sound), [`mix`](#fn-mix).

<a id="fn-tone"></a>
### `f.tone`

```py
f.tone(frequency: 'float', seconds: 'float', wave: 'str' = 'sine', volume: 'float' = 0.5, attack: 'float' = 0.01, release: 'float' = 0.15, decay: 'float' = 0.15, sustain: 'float' = 0.7)
```

Make a sound that is one steady tone.

The loudness follows an envelope. It rises to full over the attack, falls to the sustain level over the decay, holds, and fades out over the last release seconds. If attack and release do not fit, they are made shorter. Noise repeats after random_seed().

| Argument | Meaning |
|---|---|
| `frequency` | the pitch, in hertz. |
| `seconds` | how long the sound lasts. |
| `wave` | "sine" (the default), "soft", "triangle", "square", "saw" or "noise". |
| `volume` | from 0 to 1. The default 0.5 is half, so sounds can play together without clipping. |
| `attack` | seconds to rise to full. The default is 0.01. |
| `release` | seconds to fade out at the end. The default is 0.15. |
| `decay` | seconds to fall to the sustain level. The default is 0.15. |
| `sustain` | the level held after the decay, 0 to 1. The default is 0.7. |

**Returns.** A Sound: play(), loop(), stop(), level() and so on.

```py
f.tone(440, 1, "square").play()
```

See also: [`note`](#fn-note), [`pluck`](#fn-pluck), [`melody`](#fn-melody), [`create_sound`](#fn-create_sound).

<a id="fn-note"></a>
### `f.note`

```py
f.note(name: 'str', seconds: 'float', wave: 'str' = 'sine', volume: 'float' = 0.5, attack: 'float' = 0.01, release: 'float' = 0.15, decay: 'float' = 0.15, sustain: 'float' = 0.7)
```

Make a sound that is one named note.

It takes the same options as tone().

| Argument | Meaning |
|---|---|
| `name` | a note name such as "A4" (440 hertz), "C#5" or "Bb3". |
| `seconds` | how long the sound lasts. |
| `wave` | "sine" (the default), "soft", "triangle", "square", "saw" or "noise". |
| `volume` | from 0 to 1. The default is 0.5. |
| `attack` | seconds to rise to full. The default is 0.01. |
| `release` | seconds to fade out at the end. The default is 0.15. |
| `decay` | seconds to fall to the sustain level. The default is 0.15. |
| `sustain` | the level held after the decay, 0 to 1. The default is 0.7. |

**Returns.** A Sound: play(), loop(), stop(), level() and so on.

**Raises.**

- `ValueError`: the note name is not understood.

```py
f.note("C4", 2, attack=0.5, sustain=1).play()
```

See also: [`tone`](#fn-tone), [`melody`](#fn-melody), [`note_to_frequency`](#fn-note_to_frequency).

<a id="fn-pluck"></a>
### `f.pluck`

```py
f.pluck(name_or_frequency, seconds: 'float', volume: 'float' = 0.5)
```

Make a sound like a plucked string.

It dies away by itself. It repeats after random_seed().

| Argument | Meaning |
|---|---|
| `name_or_frequency` | a note name such as "E3", or a frequency in hertz. |
| `seconds` | how long the sound lasts. |
| `volume` | from 0 to 1. The default is 0.5. |

**Returns.** A Sound: play(), loop(), stop(), reverb() and so on.

```py
f.pluck("E3", 2).play()
```

See also: [`tone`](#fn-tone), [`note`](#fn-note), [`drone`](#fn-drone).

<a id="fn-melody"></a>
### `f.melody`

```py
f.melody(text: 'str', tempo: 'float' = 120, wave: 'str' = 'soft', sa: 'str | None' = None, tuning: 'str' = 'equal', volume: 'float' = 0.5)
```

Make a sound from a string of notes.

Separate the tokens with spaces. A token is a note name, "-" for a rest, or "[C4 E4 G4]" for a chord. Add ":2" after a token for how many beats it lasts (1 if left off). Notes are smooth: each one fades out over 0.15 seconds while the next begins, so the sound lasts that much longer than its beats when it ends on a note. With sa given, the notes are sargam: S r R g G m M P d D n N, with ' for the octave above and a comma for the octave below. In sargam, "S~G" glides from S to G over the token's beats, and "(R)G" touches R for about 60 milliseconds and then plays G.

| Argument | Meaning |
|---|---|
| `text` | the notes, such as "C4 E4 G4:2 - [C4 E4 G4]:4". |
| `tempo` | beats a minute. The default is 120. |
| `wave` | the tone, as for tone(). The default is "soft". |
| `sa` | a note name such as "C4" that makes the notes sargam, with that note as Sa. The default None reads note names. |
| `tuning` | "equal" (the default) or "just". "just" uses just-intonation ratios from Sa, and needs sa. |
| `volume` | from 0 to 1. The default is 0.5. |

**Returns.** A Sound: play(), loop(), stop() and so on.

**Raises.**

- `ValueError`: a token cannot be read. The message names it.

```py
f.melody("C4 E4 G4:2 -", tempo=100).play()
```

See also: [`note`](#fn-note), [`sequence`](#fn-sequence), [`mix`](#fn-mix), [`raga`](#fn-raga).

<a id="fn-sequence"></a>
### `f.sequence`

```py
f.sequence(*sounds)
```

Make a new sound that plays the given sounds one after another.

| Argument | Meaning |
|---|---|
| `sounds` | the sounds to join, in order. |

**Returns.** A Sound that lasts as long as all of them together.

```py
f.sequence(f.note("C4", 1), f.note("E4", 1)).play()
```

See also: [`mix`](#fn-mix), [`melody`](#fn-melody).

<a id="fn-mix"></a>
### `f.mix`

```py
f.mix(*sounds)
```

Make a new sound that plays the given sounds together.

A soft limiter keeps the loudest moments at or below 0.9, so the sum never clips. Quiet sums are not changed.

| Argument | Meaning |
|---|---|
| `sounds` | the sounds to play together. |

**Returns.** A Sound as long as the longest of them.

```py
f.mix(f.note("C4", 2), f.note("E4", 2), f.note("G4", 2)).play()
```

See also: [`sequence`](#fn-sequence), [`chord_notes`](#fn-chord_notes).

<a id="fn-drone"></a>
### `f.drone`

```py
f.drone(sa, seconds: 'float', pattern: 'str' = "P S' S' S", volume: 'float' = 0.5)
```

Make a tanpura-like drone.

It is plucked strings that ring on, played in turn over and over. It loops smoothly with sound.loop(). It repeats after random_seed().

| Argument | Meaning |
|---|---|
| `sa` | the base note: a note name such as "D3", or a frequency in hertz. |
| `seconds` | how long the sound lasts. |
| `pattern` | the strings to pluck, as swaras. The default is "P S' S' S". It may start with m or N instead of P. |
| `volume` | its loudest point, 0 to 1. The default is 0.5. |

**Returns.** A Sound: loop(), play(), reverb() and so on.

```py
f.drone("D3", 8).loop()
```

See also: [`pluck`](#fn-pluck), [`tala`](#fn-tala), [`raga`](#fn-raga).

<a id="fn-note_to_frequency"></a>
### `f.note_to_frequency`

```py
f.note_to_frequency(name: 'str', sa: 'str | None' = None) -> 'float'
```

Return the frequency of a note, in hertz.

| Argument | Meaning |
|---|---|
| `name` | a note name such as "A4". With sa given, a swara such as "G" or "N,". |
| `sa` | a note name such as "C4" that the swara is counted from. The default None reads an ordinary note name. |

**Returns.** The frequency in hertz. note_to_frequency("A4") is 440.

**Raises.**

- `ValueError`: the name is not understood.

```py
print(f.note_to_frequency("A4"))
```

See also: [`frequency_to_note`](#fn-frequency_to_note), [`note`](#fn-note), [`tone`](#fn-tone).

<a id="fn-frequency_to_note"></a>
### `f.frequency_to_note`

```py
f.frequency_to_note(hz: 'float', sa: 'str | None' = None) -> 'str'
```

Return the name of the note nearest to a frequency.

Sharps are used, such as "C#5".

| Argument | Meaning |
|---|---|
| `hz` | the frequency, in hertz. |
| `sa` | a note name such as "C4". With it, the answer is the nearest swara, such as "G'". The default None gives an ordinary note name. |

**Returns.** A note name, such as "A4".

```py
print(f.frequency_to_note(440))
```

See also: [`note_to_frequency`](#fn-note_to_frequency).

<a id="fn-chord_notes"></a>
### `f.chord_notes`

```py
f.chord_notes(name: 'str') -> 'list[str]'
```

Return the note names in a chord.

| Argument | Meaning |
|---|---|
| `name` | a note (with # or b), followed by nothing, m, dim, aug, 7, maj7 or m7. For example "C", "Am" or "Bdim". |

**Returns.** A list of note names, with sharps. chord_notes("C") is ["C", "E", "G"], and chord_notes("Am") is ["A", "C", "E"].

**Raises.**

- `ValueError`: the chord name is not understood.

```py
print(f.chord_notes("Am"))
```

See also: [`mix`](#fn-mix), [`note`](#fn-note).

<a id="music-analysis-and-the-microphone"></a>
## Music analysis and the microphone

<a id="fn-microphone"></a>
### `f.microphone`

```py
f.microphone(name: 'str | None' = None)
```

Make a microphone object for the computer's default input.

Call mic.start() to listen. While it listens, mic.level(), mic.spectrum(bands) and mic.pitch() work as they do on a sound. mic.capture(seconds) returns the last few seconds as a sound. It is never played back. With FUNGROUND_HEADLESS=1 it is silent and hears nothing. On a Mac, allow microphone access in System Settings.

| Argument | Meaning |
|---|---|
| `name` | part of the name of the input to use. The default None uses the default input. See microphones(). |

**Returns.** A Microphone: start(), stop(), is_listening(), level(), spectrum(bands), pitch(), capture(seconds), is_onset(), chroma() and chord().

**Raises.**

- `RuntimeError`: there is no microphone, or access is refused.

```py
mic = f.microphone()
mic.start()
```

See also: [`microphones`](#fn-microphones), [`draw_wave`](#fn-draw_wave), [`draw_spectrum`](#fn-draw_spectrum), [`draw_pitch_line`](#fn-draw_pitch_line).

<a id="fn-microphones"></a>
### `f.microphones`

```py
f.microphones() -> 'list[str]'
```

Return the names of the computer's microphones (inputs).

**Returns.** A list of names. Give part of one to microphone().

```py
print(f.microphones())
```

See also: [`microphone`](#fn-microphone).

<a id="drawing-sound"></a>
## Drawing sound

<a id="fn-draw_wave"></a>
### `f.draw_wave`

```py
f.draw_wave(source, x: 'float', y: 'float', w: 'float', h: 'float') -> 'None'
```

Draw the wave of a sound, a microphone or a list of numbers.

It is drawn inside a box, with the current fill, stroke and transform. For a sound it shows the whole sound, with a line at the place it is playing. For a microphone it shows the last half second. A sound's shape is worked out once for each width, so it is quick.

| Argument | Meaning |
|---|---|
| `source` | a Sound, a Microphone or a list of numbers. |
| `x`, `y` | the top-left corner of the box. |
| `w`, `h` | the width and height of the box, in pixels. |

```py
f.draw_wave(song, 20, 20, 400, 80)
```

See also: [`draw_spectrum`](#fn-draw_spectrum), [`spectrogram`](#fn-spectrogram), [`draw_pitch_line`](#fn-draw_pitch_line).

<a id="fn-draw_spectrum"></a>
### `f.draw_spectrum`

```py
f.draw_spectrum(source, x: 'float', y: 'float', w: 'float', h: 'float', bands: 'int' = 32) -> 'None'
```

Draw bars for a spectrum, as it is now.

The bars stand on the bottom of a box, in the current style.

| Argument | Meaning |
|---|---|
| `source` | a Sound or a Microphone. |
| `x`, `y` | the top-left corner of the box. |
| `w`, `h` | the width and height of the box, in pixels. |
| `bands` | how many bars. The default is 32. |

```py
f.draw_spectrum(mic, 20, 120, 400, 80)
```

See also: [`draw_wave`](#fn-draw_wave), [`spectrogram`](#fn-spectrogram).

<a id="fn-spectrogram"></a>
### `f.spectrogram`

```py
f.spectrogram(sound, width: 'int', height: 'int') -> 'Picture'
```

Make a picture of a whole sound.

Time goes across. Pitch goes up (about 40 hertz to 16 kilohertz, spaced like notes). Louder is brighter. The brightest colour is the current fill. It takes a moment (about a second for 10 seconds of sound at 400 by 200), so make it once, in setup().

| Argument | Meaning |
|---|---|
| `sound` | the Sound to look at. |
| `width`, `height` | the size of the picture, in pixels. |

**Returns.** A Picture. Draw it with image(), or save it.

```py
pic = f.spectrogram(song, 400, 200)
f.image(pic, 20, 20)
```

See also: [`draw_wave`](#fn-draw_wave), [`draw_spectrum`](#fn-draw_spectrum), [`image`](#fn-image).

<a id="fn-draw_pitch_line"></a>
### `f.draw_pitch_line`

```py
f.draw_pitch_line(source, x: 'float', y: 'float', w: 'float', h: 'float', seconds: 'float' = 5, low: 'str' = 'C3', high: 'str' = 'C6', sa: 'str | None' = None) -> 'None'
```

Draw the pitch of a sound or microphone as a scrolling line.

Call it once in every frame, because it reads source.pitch() each time. The line scrolls left. Faint guide lines are labelled with note names, or with swaras when sa is given. The line has a gap where pitch() is None.

| Argument | Meaning |
|---|---|
| `source` | a Sound or a Microphone. |
| `x`, `y` | the top-left corner of the box. |
| `w`, `h` | the width and height of the box, in pixels. |
| `seconds` | how much time the box shows. The default is 5. |
| `low` | the note at the bottom. The default is "C3". |
| `high` | the note at the top. The default is "C6". |
| `sa` | a note name such as "C4". With it the guide lines are swaras. The default None uses note names. |

```py
f.draw_pitch_line(mic, 20, 20, 400, 150)
```

See also: [`draw_wave`](#fn-draw_wave), [`microphone`](#fn-microphone), [`frequency_to_note`](#fn-frequency_to_note).

<a id="ragas-and-talas"></a>
## Ragas and talas

<a id="fn-ragas"></a>
### `f.ragas`

```py
f.ragas() -> 'list[str]'
```

Return the names of the ragas in funground's small built-in table.

For example "Yaman" and "Bhupali".

**Returns.** A list of names.

See also: [`raga`](#fn-raga), [`match_ragas`](#fn-match_ragas), [`talas`](#fn-talas).

<a id="fn-raga"></a>
### `f.raga`

```py
f.raga(name: 'str')
```

Return one raga from the built-in table.

| Argument | Meaning |
|---|---|
| `name` | the raga's name. Capitals do not matter. |

**Returns.** A read-only record with name, thaat, swaras, aroha, avaroha and pakad (sargam strings for melody(sa=...)), vadi, samvadi, time, notes and sources.

**Raises.**

- `ValueError`: the name is not in the table. The message lists the table.

```py
f.melody(f.raga("Yaman").aroha, sa="D4").play()
```

See also: [`ragas`](#fn-ragas), [`melody`](#fn-melody), [`match_ragas`](#fn-match_ragas).

<a id="fn-talas"></a>
### `f.talas`

```py
f.talas() -> 'list[str]'
```

Return the names of the talas in the built-in table.

They are Teentaal, Ektaal, Jhaptaal, Rupak, Dadra and Keherwa.

**Returns.** A list of names.

See also: [`tala_info`](#fn-tala_info), [`tala`](#fn-tala), [`ragas`](#fn-ragas).

<a id="fn-tala_info"></a>
### `f.tala_info`

```py
f.tala_info(name: 'str')
```

Return one tala from the built-in table.

| Argument | Meaning |
|---|---|
| `name` | the tala's name. Capitals do not matter. |

**Returns.** A read-only record with name, beats, vibhag (the divisions), tali (claps) and khali (waves) as beat numbers, sam (beat 1), bols (the theka, one bol a beat), notes and sources.

**Raises.**

- `ValueError`: the name is not in the table.

```py
print(f.tala_info("Rupak").khali)
```

See also: [`talas`](#fn-talas), [`tala`](#fn-tala).

<a id="fn-tala"></a>
### `f.tala`

```py
f.tala(name: 'str', tempo: 'float' = 80, cycles: 'int' = 1)
```

Make a sound of a tala's theka played with simple drum sounds.

The sam is accented, and the khali part is softer. The sound is exactly beats * 60 / tempo * cycles seconds long.

| Argument | Meaning |
|---|---|
| `name` | the tala's name, such as "Teentaal". See talas(). |
| `tempo` | beats a minute. The default is 80. |
| `cycles` | how many times round the tala. The default is 1. |

**Returns.** A Sound: play(), loop() and so on.

**Raises.**

- `ValueError`: the name is not in the table.

```py
f.tala("Teentaal", tempo=100).loop()
```

See also: [`talas`](#fn-talas), [`tala_info`](#fn-tala_info), [`drone`](#fn-drone).

<a id="fn-match_ragas"></a>
### `f.match_ragas`

```py
f.match_ragas(histogram) -> 'list[tuple[str, float]]'
```

Rank the table's ragas by how well their swaras fit a histogram.

It compares note sets only, so ragas with the same swaras score almost the same (for example Bhupali and Deshkar). It is a learning aid, not a judge.

| Argument | Meaning |
|---|---|
| `histogram` | twelve numbers, as from sound.swara_histogram(sa). |

**Returns.** A list of (name, score) pairs, best first, with scores from 0 to 1.

```py
h = song.swara_histogram("C#4")
print(f.match_ragas(h)[0])
```

See also: [`ragas`](#fn-ragas), [`raga`](#fn-raga).

<a id="classes"></a>
## Classes

- `Vector`: see [the Vector class](#cls-Vector).

- `FormattedString`: see [the FormattedString class](#cls-FormattedString).

<a id="live-values"></a>
## Live values

These look like variables. Read them as `f.width`, `f.mouse_x` and so on. They always hold the current value, and you cannot set them.

<a id="live-delta_time"></a>
### `f.delta_time`

The seconds that the previous frame took.

It is a number, such as 0.016 at 60 frames a second. It is 0.0 in the first frame. It is updated once a frame. Use it to move at the same speed on any computer.

```py
x += 120 * f.delta_time
```

<a id="live-frame_count"></a>
### `f.frame_count`

How many frames have been completed since the sketch started.

It is a whole number. It is 0 during the first draw(), 1 during the second, and so on. It goes up by one after each draw().

```py
f.rotate(f.frame_count * 3)
```

<a id="live-ground"></a>
### `f.ground`

The canvas as an area, with its margins.

It is a read-only value, always up to date, like width. It is an Area, so it has left, top, right, bottom, width, height, cx and cy (the centre), and inset() and grid(). It also has margin, a tuple (top, right, bottom, left) from size(). It starts at (0, 0), so left and top are 0, and right and bottom are the canvas width and height. Its content is the area inside the margins: a value of the same kind, whose own margin is (0, 0, 0, 0) and whose own content is itself. With no margin, ground.content is ground. It follows size(), resize_canvas() and new_page(). The margin stays when the canvas changes size. Margins are a guide: drawing outside them is allowed. Inside a ``with f.layer(...)`` block it is still the canvas.

```py
f.size(400, 300, margin=20)
f.rect(f.ground.content.left, f.ground.content.top, f.ground.content.width, f.ground.content.height)
```

<a id="live-height"></a>
### `f.height`

The height of the canvas, in pixels.

It is a whole number, exactly what you gave to size(). It is 480 until you call size(). It changes with resize_canvas() and full_screen().

```py
f.line(0, f.height, f.width, 0)
```

<a id="live-is_key_pressed"></a>
### `f.is_key_pressed`

Whether any key is held down now.

It is True or False. It is updated before every call to draw(). It is always False with no window.

```py
if f.is_key_pressed:
    f.fill("gold")
```

<a id="live-is_mouse_pressed"></a>
### `f.is_mouse_pressed`

Whether a mouse button is held down now.

It is True or False. It is True while any of the first three mouse buttons is held. It is updated before every call to draw(). To act once when a click starts, define a mouse_pressed() function instead.

```py
if f.is_mouse_pressed:
    f.fill("tomato")
```

<a id="live-key"></a>
### `f.key`

The last key that was pressed or released.

It is a one-character string such as "a" or " ", or a name such as "left", "right", "up", "down", "enter" or "escape". It is None before any key has been used. It changes when a key goes down or up, and it stays after the key is let go. To ask whether a key is held right now, use key_down().

```py
if f.key == "r":
    f.background("white")
```

<a id="live-key_code"></a>
### `f.key_code`

The code of the last key that was pressed or released.

It is a whole number, or None before any key has been used. It changes at the same time as key. Most programs use key instead, which is easier to read.

```py
print(f.key_code)
```

<a id="live-mouse_button"></a>
### `f.mouse_button`

The last mouse button that was pressed or released.

It is the word "left", "center" or "right", or None before any button has been used. It changes when a button goes down or up, and it stays after the button is let go.

```py
if f.mouse_button == "right":
    f.background("white")
```

<a id="live-mouse_x"></a>
### `f.mouse_x`

The mouse's x position over the canvas, in pixels from the left edge.

It is a number. It is updated before every call to draw(). It is 0 with no window.

```py
f.circle(f.mouse_x, f.mouse_y, 30)
```

<a id="live-mouse_y"></a>
### `f.mouse_y`

The mouse's y position over the canvas, in pixels from the top edge.

It is a number. It is updated before every call to draw(). It is 0 with no window. The panel of controls below the canvas is not counted.

```py
f.circle(f.mouse_x, f.mouse_y, 30)
```

<a id="live-pixels"></a>
### `f.pixels`

The canvas pixels, after load_pixels().

It is a bytearray with red, green, blue and alpha (0 to 255, not premultiplied) for every pixel, row by row from the top left. The pixel at (x, y) starts at index (y * f.width + x) * 4. It is None until you call load_pixels(). Change the numbers in place, then call update_pixels(). Inside a ``with f.layer(...)`` block it holds the layer's pixels.

```py
f.load_pixels()
f.pixels[0] = 255
f.update_pixels()
```

<a id="live-pmouse_x"></a>
### `f.pmouse_x`

Where the mouse's x was in the previous frame, in pixels.

It is a number. It is updated before every call to draw(), together with mouse_x. Use it with mouse_x to draw a line that follows the mouse.

```py
f.line(f.pmouse_x, f.pmouse_y, f.mouse_x, f.mouse_y)
```

<a id="live-pmouse_y"></a>
### `f.pmouse_y`

Where the mouse's y was in the previous frame, in pixels.

It is a number. It is updated before every call to draw(), together with mouse_y.

```py
f.line(f.pmouse_x, f.pmouse_y, f.mouse_x, f.mouse_y)
```

<a id="live-width"></a>
### `f.width`

The width of the canvas, in pixels.

It is a whole number, exactly what you gave to size(). It is 640 until you call size(). It changes with resize_canvas() and full_screen(). On a high-resolution screen it is still the number you asked for.

```py
f.circle(f.width / 2, f.height / 2, 80)
```

<a id="classes-in-detail"></a>
## Classes in detail

<a id="cls-Sound"></a>
### `Sound`

```py
Sound(device_sound, mixer, silent: 'bool', frame_source=None, made=None)
```

A sound that you can play, listen to and change.

You get one from f.load_sound() (a file), f.create_sound() (a list of numbers), f.tone(), f.note(),
f.pluck(), f.melody(), f.drone() and f.tala() (made for you), f.sequence() and f.mix() (made from
other sounds), and mic.capture() (made from what a microphone heard). All of them are the same kind
of object.

A sound keeps its own place and state (playing, paused or stopped), kept by a clock. So is_playing()
and the listening methods behave the same with or without a sound device. With no device, or with
FUNGROUND_HEADLESS=1, a sound plays silently and keeps time.

Methods that change a sound's state (play, loop, stop, pause, set_volume, pan) change this sound.
Methods that make something new (reverb) give you a new sound and leave this one alone.

```py
beep = f.tone(440, 1)
beep.play()
f.circle(200, 200, 50 + 300 * beep.level())
```

<a id="cls-Sound-beats"></a>
#### `Sound.beats`

```py
Sound.beats() -> 'list[float]'
```

The times of the beats, at the sound's tempo.

They are lined up with the onsets. It looks at the whole sound.

**Returns.** a list of times in seconds from the start, or an empty list when there is no clear pulse.

```py
song = f.melody("C4 E4 G4 E4 A3 C4 E4 C4", tempo=100, wave="triangle")
beats = song.beats()
song.play()
```

See also: [`tempo`](#cls-Sound-tempo), [`onsets`](#cls-Sound-onsets), [`is_onset`](#cls-Sound-is_onset).

<a id="cls-Sound-chord"></a>
#### `Sound.chord`

```py
Sound.chord() -> 'str | None'
```

The chord sounding now, as a name.

The name is a note followed by nothing (major), m, dim, aug, 7, maj7 or m7, such as "C", "Am", "G7",
"Fmaj7" or "Bdim". One voice on its own is not a chord. It is meant for clear chords on a piano, a
guitar or a synth, not for a busy band.

**Returns.** the chord name, or None when no chord stands out.

```py
f.text(song.chord() or "-", 150, 100)
```

See also: [`chroma`](#cls-Sound-chroma), [`key`](#cls-Sound-key), [`chord_notes`](#fn-chord_notes).

<a id="cls-Sound-chroma"></a>
#### `Sound.chroma`

```py
Sound.chroma() -> 'list[float]'
```

How strong each of the twelve note names is right now, whatever the octave.

The numbers are for C, C#, D, D#, E, F, F#, G, G#, A, A# and B, in that order. The strongest is 1.
All of them are 0 when nothing is playing or listening, or when it is quiet.

**Returns.** a list of 12 numbers from 0 to 1.

```py
notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
for i, strength in enumerate(song.chroma()):
    f.text(notes[i], 20 + i * 30, 380 - 200 * strength)
```

See also: [`chord`](#cls-Sound-chord), [`pitch`](#cls-Sound-pitch), [`key`](#cls-Sound-key).

<a id="cls-Sound-current_time"></a>
#### `Sound.current_time`

```py
Sound.current_time() -> 'float'
```

Where the sound is now.

A sound that is stopped is at 0. A paused sound stays where it stopped.

**Returns.** the time in seconds from the start of the sound.

```py
snd = f.melody("C4 E4 G4")
snd.loop()
f.rect(0, 190, 400 * snd.current_time() / snd.duration(), 20)
```

See also: [`duration`](#cls-Sound-duration), [`pause`](#cls-Sound-pause).

<a id="cls-Sound-duration"></a>
#### `Sound.duration`

```py
Sound.duration() -> 'float'
```

The length of the sound.

**Returns.** the length in seconds.

```py
snd = f.tone(440, 2)
print(snd.duration())     # 2.0 or a little more
```

See also: [`current_time`](#cls-Sound-current_time).

<a id="cls-Sound-get_volume"></a>
#### `Sound.get_volume`

```py
Sound.get_volume() -> 'float'
```

The loudness set by set_volume().

**Returns.** a number from 0 to 1. It is 1 until you change it.

```py
snd = f.tone(440, 1)
snd.set_volume(0.5)
print(snd.get_volume())
```

See also: [`set_volume`](#cls-Sound-set_volume).

<a id="cls-Sound-is_onset"></a>
#### `Sound.is_onset`

```py
Sound.is_onset() -> 'bool'
```

Whether a new note or hit is heard in this frame.

Use it to flash a light on each beat or note. It looks at the last 0.3 seconds. It is False
when nothing is playing or listening.

**Returns.** True in the frame where a new note or hit begins, otherwise False.

```py
if song.is_onset():
    f.background("white")
```

See also: [`onsets`](#cls-Sound-onsets), [`level`](#cls-Sound-level).

<a id="cls-Sound-is_playing"></a>
#### `Sound.is_playing`

```py
Sound.is_playing() -> 'bool'
```

Whether the sound is playing now.

A paused sound is not playing. A sound that has reached its end is not playing.

**Returns.** True while the sound is playing, otherwise False.

```py
if not song.is_playing():
    song.play()
```

See also: [`play`](#cls-Sound-play), [`pause`](#cls-Sound-pause), [`stop`](#cls-Sound-stop).

<a id="cls-Sound-key"></a>
#### `Sound.key`

```py
Sound.key() -> 'str | None'
```

The key of the whole sound.

It adds up the chroma over the whole sound and says which key fits best. It is worked out once.

**Returns.** a name like "G major" or "E minor", or None when no key stands out.

```py
song = f.melody("C4 E4 G4 C5 G4 E4 C4")
print(song.key())
```

See also: [`chord`](#cls-Sound-chord), [`chroma`](#cls-Sound-chroma).

<a id="cls-Sound-level"></a>
#### `Sound.level`

```py
Sound.level() -> 'float'
```

How loud the sound is right now, from 0 (silent) to 1.

It is the root mean square of the last 1/30 of a second, so it follows the music. It is 0 when the
sound is not playing, or the microphone is not listening.

**Returns.** a number from 0 to 1.

```py
snd = f.load_sound("song.wav")   # your own file
snd.loop()
f.circle(200, 200, 50 + 300 * snd.level())
```

See also: [`spectrum`](#cls-Sound-spectrum), [`pitch`](#cls-Sound-pitch), [`is_onset`](#cls-Sound-is_onset).

<a id="cls-Sound-loop"></a>
#### `Sound.loop`

```py
Sound.loop() -> 'None'
```

Play the sound over and over, until you call stop() or pause().

```py
drone = f.drone("D3", 8)
drone.loop()
```

See also: [`play`](#cls-Sound-play), [`stop`](#cls-Sound-stop), [`pause`](#cls-Sound-pause).

<a id="cls-Sound-onsets"></a>
#### `Sound.onsets`

```py
Sound.onsets() -> 'list[float]'
```

The times where a note or a hit begins.

It looks at the whole sound. It is worked out once, then remembered. A three-minute song takes a few
seconds the first time. A microphone has no whole sound, so use mic.capture(seconds).onsets().

**Returns.** a list of times in seconds from the start, earliest first.

```py
song = f.melody("C4 E4 G4 C5")
print(song.onsets())
```

See also: [`is_onset`](#cls-Sound-is_onset), [`tempo`](#cls-Sound-tempo), [`beats`](#cls-Sound-beats).

<a id="cls-Sound-pan"></a>
#### `Sound.pan`

```py
Sound.pan(position: 'float') -> 'None'
```

Move the sound between the left and right speakers.

It works on any sound. level() and spectrum() do not change with pan. save() keeps the pan.

| Argument | Meaning |
|---|---|
| `position` | a number from -1 (all left) to 1 (all right). 0 is the middle. |

**Raises.**

- `ValueError`: if position is not a number from -1 to 1.

```py
snd = f.tone(440, 1)
snd.pan(-1)     # left speaker only
snd.play()
```

See also: [`set_volume`](#cls-Sound-set_volume), [`play`](#cls-Sound-play).

<a id="cls-Sound-pause"></a>
#### `Sound.pause`

```py
Sound.pause() -> 'None'
```

Stop the sound and keep the place, so that play() carries on from there.

Nothing happens if the sound is not playing.

```py
snd = f.tone(440, 5)
snd.play()
snd.pause()
snd.play()     # carries on
```

See also: [`play`](#cls-Sound-play), [`stop`](#cls-Sound-stop), [`current_time`](#cls-Sound-current_time).

<a id="cls-Sound-pitch"></a>
#### `Sound.pitch`

```py
Sound.pitch() -> 'float | None'
```

The frequency of the one voice or instrument heard right now.

It looks at the last 2 048 samples. It is for one note at a time, not for chords. It looks for
pitches from 50 to 2000 Hz. It gives None when the sound is quiet, when it has no clear pitch (noise
has none), or when nothing is playing or listening.

**Returns.** the frequency in hertz, or None.

```py
mic = f.microphone()
mic.start()
hz = mic.pitch()
if hz:
    f.text(f.frequency_to_note(hz), 20, 40)
```

See also: [`chroma`](#cls-Sound-chroma), [`chord`](#cls-Sound-chord), [`level`](#cls-Sound-level).

<a id="cls-Sound-play"></a>
#### `Sound.play`

```py
Sound.play() -> 'None'
```

Play the sound from the start, or from where pause() left it.

Playing a sound that is already playing starts it again from the start. A sound that is not
looping stops by itself at the end.

```py
beep = f.tone(440, 1)
beep.play()
```

See also: [`loop`](#cls-Sound-loop), [`pause`](#cls-Sound-pause), [`stop`](#cls-Sound-stop), [`is_playing`](#cls-Sound-is_playing).

<a id="cls-Sound-reverb"></a>
#### `Sound.reverb`

```py
Sound.reverb(amount: 'float' = 0.3) -> "'Sound'"
```

Make a new sound that is this sound played in a room.

The room's echoes ring on after the end, so the new sound is longer, by up to 1.5 seconds at 1. The
new sound has one channel. The volume and pan are not carried over. This sound is not changed.

It takes a moment to work out: about a twentieth of a second for each second of sound. Make the new
sound once, at the start, not in draw().

| Argument | Meaning |
|---|---|
| `amount` | the size of the room, from 0 (no room, the sound is unchanged) to 1 (a large hall). It is 0.3 at first. |

**Returns.** a new Sound.

**Raises.**

- `ValueError`: if amount is not a number from 0 to 1.

```py
dry = f.pluck("G3", 1.5)
wet = dry.reverb(0.5)
wet.play()
```

See also: [`mix`](#fn-mix), [`sequence`](#fn-sequence).

<a id="cls-Sound-samples"></a>
#### `Sound.samples`

```py
Sound.samples() -> 'list[float]'
```

The sound as a list of numbers.

A sound is a long list of numbers, one for each tiny slice of time. A mono sound has 44 100 of them
a second. If the sound has more than one channel, they are mixed into one. Draw them to see the wave.
The pan and the volume are not in the numbers.

**Returns.** a list of numbers from -1 to 1.

```py
wave = f.tone(220, 1).samples()
for x in range(399):
    f.line(x, 100 - 80 * wave[x * 4], x + 1, 100 - 80 * wave[x * 4 + 4])
```

See also: [`create_sound`](#fn-create_sound), [`save`](#cls-Sound-save).

<a id="cls-Sound-save"></a>
#### `Sound.save`

```py
Sound.save(path: 'str') -> 'None'
```

Write the sound to a 16-bit WAV file.

The pan is kept in the file. The volume is not.

| Argument | Meaning |
|---|---|
| `path` | the file name, such as "tune.wav". |

**Raises.**

- `ValueError`: if path is empty or not text, or the file cannot be written.

```py
f.melody("C4 E4 G4").save("tune.wav")    # writes a new file
```

See also: [`samples`](#cls-Sound-samples), [`create_sound`](#fn-create_sound).

<a id="cls-Sound-set_volume"></a>
#### `Sound.set_volume`

```py
Sound.set_volume(volume: 'float') -> 'None'
```

Set how loud the sound plays.

It does not change the numbers inside the sound, so level() and samples() are not affected.

| Argument | Meaning |
|---|---|
| `volume` | a number from 0 (silent) to 1 (full). It is 1 at first. |

**Raises.**

- `ValueError`: if volume is not a number from 0 to 1.

```py
snd = f.tone(440, 1)
snd.set_volume(0.3)
snd.play()
```

See also: [`get_volume`](#cls-Sound-get_volume), [`pan`](#cls-Sound-pan).

<a id="cls-Sound-spectrum"></a>
#### `Sound.spectrum`

```py
Sound.spectrum(bands: 'int' = 32) -> 'list[float]'
```

How strong the sound is now in each of several ranges of pitch, from low notes to high notes.

The ranges are called bands. They are spaced evenly in pitch, from 40 Hz to 16 kHz, so each one is
about the same number of notes wide. A band is strong when the sound has a lot of that pitch. You get
a list of zeros when the sound is not playing, or the microphone is not listening.

| Argument | Meaning |
|---|---|
| `bands` | how many ranges to split the sound into, a whole number from 1 to 256. It is 32 at first. |

**Returns.** a list of `bands` numbers from 0 to 1, lowest pitch first.

**Raises.**

- `ValueError`: if bands is not a whole number from 1 to 256.

```py
snd = f.tone(220, 2)
snd.play()
for i, strength in enumerate(snd.spectrum(16)):
    f.rect(20 + i * 24, 380, 20, -300 * strength)
```

See also: [`level`](#cls-Sound-level), [`pitch`](#cls-Sound-pitch), [`chroma`](#cls-Sound-chroma).

<a id="cls-Sound-stop"></a>
#### `Sound.stop`

```py
Sound.stop() -> 'None'
```

Stop the sound and go back to its start.

```py
snd = f.tone(440, 5)
snd.play()
snd.stop()
```

See also: [`pause`](#cls-Sound-pause), [`play`](#cls-Sound-play).

<a id="cls-Sound-swara_histogram"></a>
#### `Sound.swara_histogram`

```py
Sound.swara_histogram(sa) -> 'list[float]'
```

How much of the singing was on each swara.

Each number is the share of the time with a clear pitch that was spent within 50 cents (half a
semitone) of that swara, in any octave. The twelve swaras above Sa are S, r, R, g, G, m, M, P, d, D,
n and N. The numbers add up to 1, or are all 0 if nothing had a pitch.

| Argument | Meaning |
|---|---|
| `sa` | the note that Sa is, as a note name like "D4" or as a number of hertz. |

**Returns.** a list of 12 numbers, the first for S and the last for N.

```py
hist = recording.swara_histogram("D4")
print(f.match_ragas(hist)[0])
```

See also: [`tonic`](#cls-Sound-tonic), [`match_ragas`](#fn-match_ragas).

<a id="cls-Sound-tempo"></a>
#### `Sound.tempo`

```py
Sound.tempo() -> 'float | None'
```

The speed of the music.

It looks at the whole sound, and is worked out once. A sound with no clear pulse has no tempo.

**Returns.** the speed in beats a minute, from 60 to 200, or None when there is no clear pulse.

```py
song = f.melody("C4 E4 G4 E4 A3 C4 E4 C4", tempo=100, wave="triangle")
print(song.tempo())
```

See also: [`beats`](#cls-Sound-beats), [`onsets`](#cls-Sound-onsets).

<a id="cls-Sound-tonic"></a>
#### `Sound.tonic`

```py
Sound.tonic() -> 'float | None'
```

A guess at Sa, the starting note of a singer, in hertz.

It counts how long each pitch was heard, folded into one octave. It then picks the pitch that best
explains a strong Sa and Pa. It is a rough guide, not an answer. For a microphone it uses the last
10 seconds. For a sound it uses the whole sound.

**Returns.** the frequency of Sa in hertz, or None when too little had a clear pitch.

```py
sa = recording.tonic()
if sa:
    print(f.frequency_to_note(sa))
```

See also: [`swara_histogram`](#cls-Sound-swara_histogram), [`pitch`](#cls-Sound-pitch), [`match_ragas`](#fn-match_ragas).

<a id="cls-Microphone"></a>
### `Microphone`

```py
Microphone(device_name: 'str | None', frame_source=None, silent: 'bool' = False)
```

A microphone that your sketch can listen to.

You get one from f.microphone(). Call start() to begin listening and stop() to end. While it listens,
level(), spectrum(), pitch(), is_onset(), chroma(), chord(), tonic() and swara_histogram() work as they
do on a Sound. They tell you about the last fraction of a second. When it is not listening they give 0,
a list of zeros, None or False.

capture(seconds) gives you a Sound made of the last few seconds it heard (up to 10), so you can play
it, save it, draw it or look at its whole-sound features such as tempo().

The microphone is never played back, so there is no squeal from the speakers. Nothing is recorded to a
file unless you call save() on a capture. With FUNGROUND_HEADLESS=1 it is silent and hears nothing.

```py
mic = f.microphone()
mic.start()
f.circle(200, 200, 20 + 400 * mic.level())
```

<a id="cls-Microphone-beats"></a>
#### `Microphone.beats`

```py
Microphone.beats()
```

Not for a microphone, because it looks at a whole sound.

Use mic.capture(seconds).beats() to look at what was heard.

**Raises.**

- `ValueError`: always, with a message that points to capture().

See also: [`capture`](#cls-Microphone-capture).

<a id="cls-Microphone-capture"></a>
#### `Microphone.capture`

```py
Microphone.capture(seconds: 'float')
```

Make a new sound from the last few seconds the microphone heard.

If it has heard less than that, the start is silence, so the sound is always as long as you asked.
It is an ordinary Sound: play it, save it, or draw its wave with samples().

| Argument | Meaning |
|---|---|
| `seconds` | how much to keep, more than 0 and at most 10. |

**Returns.** a new Sound that is `seconds` long.

**Raises.**

- `ValueError`: if seconds is not more than 0 and at most 10.

```py
mic = f.microphone()
mic.start()
recording = mic.capture(1)   # use it after about a second
recording.save("heard.wav")  # writes a new file
```

See also: [`start`](#cls-Microphone-start), [`stop`](#cls-Microphone-stop).

<a id="cls-Microphone-chord"></a>
#### `Microphone.chord`

```py
Microphone.chord() -> 'str | None'
```

The chord sounding now, as a name.

The name is a note followed by nothing (major), m, dim, aug, 7, maj7 or m7, such as "C", "Am", "G7",
"Fmaj7" or "Bdim". One voice on its own is not a chord. It is meant for clear chords on a piano, a
guitar or a synth, not for a busy band.

**Returns.** the chord name, or None when no chord stands out.

```py
f.text(song.chord() or "-", 150, 100)
```

See also: [`chroma`](#cls-Microphone-chroma), [`key`](#cls-Microphone-key), [`chord_notes`](#fn-chord_notes).

<a id="cls-Microphone-chroma"></a>
#### `Microphone.chroma`

```py
Microphone.chroma() -> 'list[float]'
```

How strong each of the twelve note names is right now, whatever the octave.

The numbers are for C, C#, D, D#, E, F, F#, G, G#, A, A# and B, in that order. The strongest is 1.
All of them are 0 when nothing is playing or listening, or when it is quiet.

**Returns.** a list of 12 numbers from 0 to 1.

```py
notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
for i, strength in enumerate(song.chroma()):
    f.text(notes[i], 20 + i * 30, 380 - 200 * strength)
```

See also: [`chord`](#cls-Microphone-chord), [`pitch`](#cls-Microphone-pitch), [`key`](#cls-Microphone-key).

<a id="cls-Microphone-close"></a>
#### `Microphone.close`

```py
Microphone.close() -> 'None'
```

Stop listening and let go of the microphone.

funground calls it when a sketch ends, so you do not need to.

```py
mic.close()
```

See also: [`stop`](#cls-Microphone-stop).

<a id="cls-Microphone-is_listening"></a>
#### `Microphone.is_listening`

```py
Microphone.is_listening() -> 'bool'
```

Whether the microphone is listening.

**Returns.** True between start() and stop(), otherwise False.

```py
if not mic.is_listening():
    mic.start()
```

See also: [`start`](#cls-Microphone-start), [`stop`](#cls-Microphone-stop).

<a id="cls-Microphone-is_onset"></a>
#### `Microphone.is_onset`

```py
Microphone.is_onset() -> 'bool'
```

Whether a new note or hit is heard in this frame.

Use it to flash a light on each beat or note. It looks at the last 0.3 seconds. It is False
when nothing is playing or listening.

**Returns.** True in the frame where a new note or hit begins, otherwise False.

```py
if song.is_onset():
    f.background("white")
```

See also: [`onsets`](#cls-Microphone-onsets), [`level`](#cls-Microphone-level).

<a id="cls-Microphone-key"></a>
#### `Microphone.key`

```py
Microphone.key()
```

Not for a microphone, because it looks at a whole sound.

Use mic.capture(seconds).key() to look at what was heard.

**Raises.**

- `ValueError`: always, with a message that points to capture().

See also: [`capture`](#cls-Microphone-capture), [`chroma`](#cls-Microphone-chroma).

<a id="cls-Microphone-level"></a>
#### `Microphone.level`

```py
Microphone.level() -> 'float'
```

How loud the sound is right now, from 0 (silent) to 1.

It is the root mean square of the last 1/30 of a second, so it follows the music. It is 0 when the
sound is not playing, or the microphone is not listening.

**Returns.** a number from 0 to 1.

```py
snd = f.load_sound("song.wav")   # your own file
snd.loop()
f.circle(200, 200, 50 + 300 * snd.level())
```

See also: [`spectrum`](#cls-Microphone-spectrum), [`pitch`](#cls-Microphone-pitch), [`is_onset`](#cls-Microphone-is_onset).

<a id="cls-Microphone-onsets"></a>
#### `Microphone.onsets`

```py
Microphone.onsets()
```

Not for a microphone, because it looks at a whole sound.

Use mic.capture(seconds).onsets() to look at what was heard.

**Raises.**

- `ValueError`: always, with a message that points to capture().

See also: [`capture`](#cls-Microphone-capture), [`is_onset`](#cls-Microphone-is_onset).

<a id="cls-Microphone-pitch"></a>
#### `Microphone.pitch`

```py
Microphone.pitch() -> 'float | None'
```

The frequency of the one voice or instrument heard right now.

It looks at the last 2 048 samples. It is for one note at a time, not for chords. It looks for
pitches from 50 to 2000 Hz. It gives None when the sound is quiet, when it has no clear pitch (noise
has none), or when nothing is playing or listening.

**Returns.** the frequency in hertz, or None.

```py
mic = f.microphone()
mic.start()
hz = mic.pitch()
if hz:
    f.text(f.frequency_to_note(hz), 20, 40)
```

See also: [`chroma`](#cls-Microphone-chroma), [`chord`](#cls-Microphone-chord), [`level`](#cls-Microphone-level).

<a id="cls-Microphone-spectrum"></a>
#### `Microphone.spectrum`

```py
Microphone.spectrum(bands: 'int' = 32) -> 'list[float]'
```

How strong the sound is now in each of several ranges of pitch, from low notes to high notes.

The ranges are called bands. They are spaced evenly in pitch, from 40 Hz to 16 kHz, so each one is
about the same number of notes wide. A band is strong when the sound has a lot of that pitch. You get
a list of zeros when the sound is not playing, or the microphone is not listening.

| Argument | Meaning |
|---|---|
| `bands` | how many ranges to split the sound into, a whole number from 1 to 256. It is 32 at first. |

**Returns.** a list of `bands` numbers from 0 to 1, lowest pitch first.

**Raises.**

- `ValueError`: if bands is not a whole number from 1 to 256.

```py
snd = f.tone(220, 2)
snd.play()
for i, strength in enumerate(snd.spectrum(16)):
    f.rect(20 + i * 24, 380, 20, -300 * strength)
```

See also: [`level`](#cls-Microphone-level), [`pitch`](#cls-Microphone-pitch), [`chroma`](#cls-Microphone-chroma).

<a id="cls-Microphone-start"></a>
#### `Microphone.start`

```py
Microphone.start() -> 'None'
```

Start listening.

It forgets what it heard before. Calling it when it is already listening does nothing.

**Raises.**

- `RuntimeError`: if there is no microphone, or the computer will not let funground use it.

```py
mic = f.microphone()
mic.start()
```

See also: [`stop`](#cls-Microphone-stop), [`is_listening`](#cls-Microphone-is_listening), [`capture`](#cls-Microphone-capture).

<a id="cls-Microphone-stop"></a>
#### `Microphone.stop`

```py
Microphone.stop() -> 'None'
```

Stop listening, but keep what was heard, so that capture() still works.

```py
recording = mic.capture(2)
mic.stop()
```

See also: [`start`](#cls-Microphone-start), [`capture`](#cls-Microphone-capture).

<a id="cls-Microphone-swara_histogram"></a>
#### `Microphone.swara_histogram`

```py
Microphone.swara_histogram(sa) -> 'list[float]'
```

How much of the singing was on each swara.

Each number is the share of the time with a clear pitch that was spent within 50 cents (half a
semitone) of that swara, in any octave. The twelve swaras above Sa are S, r, R, g, G, m, M, P, d, D,
n and N. The numbers add up to 1, or are all 0 if nothing had a pitch.

| Argument | Meaning |
|---|---|
| `sa` | the note that Sa is, as a note name like "D4" or as a number of hertz. |

**Returns.** a list of 12 numbers, the first for S and the last for N.

```py
hist = recording.swara_histogram("D4")
print(f.match_ragas(hist)[0])
```

See also: [`tonic`](#cls-Microphone-tonic), [`match_ragas`](#fn-match_ragas).

<a id="cls-Microphone-tempo"></a>
#### `Microphone.tempo`

```py
Microphone.tempo()
```

Not for a microphone, because it looks at a whole sound.

Use mic.capture(seconds).tempo() to look at what was heard.

**Raises.**

- `ValueError`: always, with a message that points to capture().

See also: [`capture`](#cls-Microphone-capture).

<a id="cls-Microphone-tonic"></a>
#### `Microphone.tonic`

```py
Microphone.tonic() -> 'float | None'
```

A guess at Sa, the starting note of a singer, in hertz.

It counts how long each pitch was heard, folded into one octave. It then picks the pitch that best
explains a strong Sa and Pa. It is a rough guide, not an answer. For a microphone it uses the last
10 seconds. For a sound it uses the whole sound.

**Returns.** the frequency of Sa in hertz, or None when too little had a clear pitch.

```py
sa = recording.tonic()
if sa:
    print(f.frequency_to_note(sa))
```

See also: [`swara_histogram`](#cls-Microphone-swara_histogram), [`pitch`](#cls-Microphone-pitch), [`match_ragas`](#fn-match_ragas).

<a id="cls-Picture"></a>
### `Picture`

```py
Picture(width: 'int', height: 'int', backing_scale: 'float', name: 'str') -> 'None'
```

A surface that you can draw on and then draw onto the canvas, save, copy or use as a mask.

You get one from f.create_graphics(width, height) (an empty, see-through canvas), f.layer(name) (a
layer that sits over the canvas), f.load_image(path) (a picture file), f.load_svg(path) (a vector
file), f.get(x, y, w, h) (a copy of part of the canvas) and f.spectrogram() (a picture of a sound).

A picture has its own state and its own transform, and nothing about it is cleared between frames. It
starts see-through. Draw on it with the same commands as f.: fill, stroke, circle, rect, line, text,
push, pop, translate, rotate, scale, begin_shape, path, clip, background, clear, get, set, filter and
so on. For example, g.circle(50, 50, 20) draws on the picture g. Window-only commands such as size(),
run() and cursor(), and plain helpers such as random() and noise(), are not on a picture.

The picture's width and height, in pixels, are g.width and g.height. Its name is g.name.

A layer made by f.layer() is a picture too. Use it with with: everything drawn inside the block goes to
the layer.

```py
g = f.create_graphics(100, 100)
g.fill("tomato")
g.circle(50, 50, 80)
f.image(g, 10, 10)
f.image(g, 120, 10, 50, 50)    # the same picture, smaller
```

<a id="cls-Picture-copy"></a>
#### `Picture.copy`

```py
Picture.copy() -> "'Picture'"
```

Make a new picture with the same pixels and drawing history.

Changing one picture never changes the other. The copy starts with the default drawing state and
transform, like any new picture.

**Returns.** a new Picture.

```py
g = f.create_graphics(100, 100)
g.circle(50, 50, 80)
h = g.copy()
h.background("black")    # g is not changed
```

See also: [`resize`](#cls-Picture-resize), [`mask`](#cls-Picture-mask).

<a id="cls-Picture-from_pixels"></a>
#### `Picture.from_pixels`

```py
Picture.from_pixels(width: 'int', height: 'int', bgra: 'bytes', name: 'str') -> "'Picture'"
```

Make a picture from decoded image pixels.

f.load_image() uses it. You do not need to call it.

| Argument | Meaning |
|---|---|
| `width`, `height` | the size of the image in pixels. |
| `bgra` | the pixels as bytes: blue, green, red and alpha for each pixel, with the colour already multiplied by the alpha. |
| `name` | the name for the picture. |

**Returns.** a new Picture whose scale is 1.

**Raises.**

- `RuntimeError`: if bgra is not the right length for the size.

See also: [`copy`](#cls-Picture-copy).

<a id="cls-Picture-image"></a>
#### `Picture.image`

```py
Picture.image(picture: "'Picture'", x: 'float', y: 'float', width: 'float | None' = None, height: 'float | None' = None, sx: 'float | None' = None, sy: 'float | None' = None, sw: 'float | None' = None, sh: 'float | None' = None) -> 'None'
```

Draw another picture onto this one, the same as f.image() does on the canvas.

You can give a box to fit it in, and a part of the picture to use. It uses this picture's current
transform, clip, blend mode and opacity.

| Argument | Meaning |
|---|---|
| `picture` | the Picture to draw. It cannot be this picture. |
| `x`, `y` | where to put it (the top left corner, unless image_mode() says otherwise). |
| `width`, `height` | the size to draw it, in pixels. They are the picture's own size if left out. |
| `sx`, `sy`, `sw`, `sh` | the part of the picture to use, as a box in its own pixels. Give all four or none. |

**Raises.**

- `TypeError`: if picture is not a Picture.
- `ValueError`: if picture is this picture, if only some of sx, sy, sw and sh are given, or if sw or sh is 0 or less.

```py
g = f.create_graphics(200, 200)
stamp = f.create_graphics(20, 20)
stamp.fill("gold")
stamp.circle(10, 10, 18)
g.image(stamp, 50, 50)
```

See also: [`copy`](#cls-Picture-copy), [`save`](#cls-Picture-save).

<a id="cls-Picture-mask"></a>
#### `Picture.mask`

```py
Picture.mask(other: "'Picture'") -> 'None'
```

Make this picture see-through where another picture is see-through, in place.

Each pixel's alpha is multiplied by the alpha of the other picture, which is scaled to this picture's
size first. Only how see-through the mask is matters, not its colours. Draw a shape on a see-through picture to use it as a stencil.

| Argument | Meaning |
|---|---|
| `other` | the Picture to use as the mask. |

**Raises.**

- `TypeError`: if other is not a Picture.

```py
photo = f.load_image("photo.png")           # your own file
stencil = f.create_graphics(photo.width, photo.height)
stencil.circle(photo.width / 2, photo.height / 2, photo.width)
photo.mask(stencil)                         # now it is a circle
```

See also: [`copy`](#cls-Picture-copy), [`image`](#cls-Picture-image).

<a id="cls-Picture-pixels"></a>
#### `Picture.pixels`

```py
Picture.pixels  # property
```

The colour of every pixel, after load_pixels().

It is a list of numbers, four for each pixel (red, green, blue, alpha, each from 0 to 255), row by row
from the top left. Change the numbers, then call update_pixels() to put them back on the picture.

**Returns.** the numbers, or None before g.load_pixels() has been called.

```py
g = f.create_graphics(10, 10)
g.background("white")
g.load_pixels()
g.pixels[0] = 0       # no red in the first pixel
g.update_pixels()
```

See also: [`copy`](#cls-Picture-copy), [`mask`](#cls-Picture-mask).

<a id="cls-Picture-resize"></a>
#### `Picture.resize`

```py
Picture.resize(width: 'int', height: 'int') -> 'None'
```

Change the size of the picture, in place, scaling its pixels smoothly.

Put a 0 for one side to keep the shape of the picture. The drawing history is dropped. The transform,
the clip and any open push() start again.

| Argument | Meaning |
|---|---|
| `width`, `height` | the new size in pixels, whole numbers. One of them may be 0 to keep the shape. Both may not be 0. |

**Raises.**

- `ValueError`: if a side is not a whole number, is negative, or both are 0.

```py
photo = f.load_image("photo.png")    # your own file
photo.resize(200, 0)                 # 200 wide, with the height to match
```

See also: [`copy`](#cls-Picture-copy), [`mask`](#cls-Picture-mask).

<a id="cls-Picture-save"></a>
#### `Picture.save`

```py
Picture.save(path: 'str', *, text: 'str' = 'live') -> 'None'
```

Write the picture to a file straight away.

The file type comes from the name. A PNG file gets the picture's pixels. A PDF or SVG file replays the
drawing as shapes when it can. It cannot when the picture drew more than 10 000 things since its last
opaque background or clear, or when its pixels were changed directly. Then the pixels are put in the
file as an image instead, so saving never fails for being too big.

| Argument | Meaning |
|---|---|
| `path` | the file name, such as "art.png", "art.pdf" or "art.svg". |
| `text` | for PDF and SVG files only. "live" keeps text as text. "shapes" draws every letter as a shape. It is "live" at first. |

```py
g = f.create_graphics(200, 200)
g.circle(100, 100, 150)
g.save("circle.png")    # writes a new file
```

See also: [`copy`](#cls-Picture-copy), [`image`](#cls-Picture-image).

<a id="cls-Vector"></a>
### `Vector`

```py
Vector(x: 'float' = 0.0, y: 'float' = 0.0) -> 'None'
```

A 2D vector: two numbers, x and y, that you can add, scale, turn and measure.

Make one with f.Vector(3, 4). Read and change its parts as v.x and v.y. Use it for a position, a speed
or a push. Angles are in degrees, like every angle in funground. y grows downward, so 90 degrees points
down.

The methods add, sub, mult, div, normalize, limit, set_mag, set_heading, rotate, lerp and set change
the vector in place and give it back, so calls can be chained: position.add(velocity). The operators
+, -, * and / make a new vector instead, and leave the first one alone. A vector can be unpacked like a
pair, as in x, y = v, and compared with == against another vector or an (x, y) pair. It is changeable,
so it cannot be a dictionary key.

| Argument | Meaning |
|---|---|
| `x`, `y` | the two parts of the vector. Both are 0 at first. |

```py
v = f.Vector(3, 4)
print(v.mag())            # 5.0
v.add(1, 1).mult(2)       # now (8, 10)
w = v + f.Vector(1, 0)    # a new vector, v is not changed
```

<a id="cls-Vector-add"></a>
#### `Vector.add`

```py
Vector.add(x, y=None) -> 'Vector'
```

Add to the vector, in place.

| Argument | Meaning |
|---|---|
| `x`, `y` | either two numbers, or x can be a Vector or an (x, y) pair with y left out. |

**Returns.** this vector, changed.

**Raises.**

- `TypeError`: if the values are not numbers, a Vector or an (x, y) pair.

```py
position = f.Vector(100, 100)
velocity = f.Vector(2, 1)
position.add(velocity)
```

See also: [`sub`](#cls-Vector-sub), [`mult`](#cls-Vector-mult).

<a id="cls-Vector-angle_between"></a>
#### `Vector.angle_between`

```py
Vector.angle_between(other) -> 'float'
```

The angle that turns this vector's direction onto another's.

| Argument | Meaning |
|---|---|
| `other` | a Vector or an (x, y) pair. Neither vector may be zero. |

**Returns.** the signed angle in degrees.

**Raises.**

- `ValueError`: if either vector is zero.

```py
print(f.Vector(1, 0).angle_between(f.Vector(0, 1)))    # 90.0
```

See also: [`heading`](#cls-Vector-heading), [`dot`](#cls-Vector-dot), [`cross`](#cls-Vector-cross).

<a id="cls-Vector-copy"></a>
#### `Vector.copy`

```py
Vector.copy() -> 'Vector'
```

Make a new vector with the same x and y.

Changing the copy does not change the original.

**Returns.** a new Vector.

```py
a = f.Vector(1, 2)
b = a.copy()
b.add(5, 5)       # a is still (1, 2)
```

See also: [`set`](#cls-Vector-set).

<a id="cls-Vector-cross"></a>
#### `Vector.cross`

```py
Vector.cross(other) -> 'float'
```

The 2D cross product of this vector and another.

It is positive when the other vector is clockwise from this one on the screen.

| Argument | Meaning |
|---|---|
| `other` | a Vector or an (x, y) pair. |

**Returns.** a number.

```py
print(f.Vector(1, 0).cross(f.Vector(0, 1)))    # 1.0
```

See also: [`dot`](#cls-Vector-dot), [`angle_between`](#cls-Vector-angle_between).

<a id="cls-Vector-dist"></a>
#### `Vector.dist`

```py
Vector.dist(other) -> 'float'
```

The distance from this point to another.

| Argument | Meaning |
|---|---|
| `other` | a Vector or an (x, y) pair. |

**Returns.** the distance, as a number that is 0 or more.

```py
if position.dist(target) < 5:
    print("arrived")
```

See also: [`mag`](#cls-Vector-mag), [`sub`](#cls-Vector-sub).

<a id="cls-Vector-div"></a>
#### `Vector.div`

```py
Vector.div(n: 'float') -> 'Vector'
```

Divide both parts by a number, in place.

| Argument | Meaning |
|---|---|
| `n` | the number to divide by. |

**Returns.** this vector, changed.

**Raises.**

- `ZeroDivisionError`: if n is 0.

```py
v = f.Vector(10, 20).div(2)    # (5, 10)
```

See also: [`mult`](#cls-Vector-mult).

<a id="cls-Vector-dot"></a>
#### `Vector.dot`

```py
Vector.dot(other) -> 'float'
```

The dot product of this vector and another.

It is x * other.x + y * other.y. It is 0 when the two are at right angles.

| Argument | Meaning |
|---|---|
| `other` | a Vector or an (x, y) pair. |

**Returns.** a number.

```py
print(f.Vector(1, 0).dot(f.Vector(0, 1)))    # 0.0
```

See also: [`cross`](#cls-Vector-cross), [`angle_between`](#cls-Vector-angle_between).

<a id="cls-Vector-from_angle"></a>
#### `Vector.from_angle`

```py
Vector.from_angle(angle: 'float', length: 'float' = 1.0) -> 'Vector'
```

Make a vector that points at an angle.

0 degrees points right and 90 degrees points down, as on the screen.

| Argument | Meaning |
|---|---|
| `angle` | the direction in degrees. |
| `length` | how long the vector is. It is 1 at first. |

**Returns.** a new Vector.

```py
v = f.Vector.from_angle(90, 10)    # (0, 10): ten pixels down
```

See also: [`heading`](#cls-Vector-heading), [`random_2d`](#cls-Vector-random_2d).

<a id="cls-Vector-heading"></a>
#### `Vector.heading`

```py
Vector.heading() -> 'float'
```

The direction the vector points in.

**Returns.** the angle in degrees, from -180 to 180. 0 is right and 90 is down.

```py
print(f.Vector(0, 1).heading())    # 90.0
```

See also: [`set_heading`](#cls-Vector-set_heading), [`angle_between`](#cls-Vector-angle_between), [`from_angle`](#cls-Vector-from_angle).

<a id="cls-Vector-lerp"></a>
#### `Vector.lerp`

```py
Vector.lerp(target, amount: 'float') -> 'Vector'
```

Move part of the way towards another vector, in place.

| Argument | Meaning |
|---|---|
| `target` | the vector to move towards, or an (x, y) pair. |
| `amount` | how much of the way to go, from 0 (stay) to 1 (arrive). Numbers outside 0 to 1 go past. |

**Returns.** this vector, changed.

```py
position.lerp(f.Vector(f.mouse_x, f.mouse_y), 0.1)    # follow the mouse
```

See also: [`add`](#cls-Vector-add), [`dist`](#cls-Vector-dist).

<a id="cls-Vector-limit"></a>
#### `Vector.limit`

```py
Vector.limit(maximum: 'float') -> 'Vector'
```

Shorten the vector, in place, if it is longer than a maximum length.

A vector that is already short enough is not changed.

| Argument | Meaning |
|---|---|
| `maximum` | the longest the vector may be. |

**Returns.** this vector, changed.

```py
velocity.add(acceleration).limit(8)
```

See also: [`set_mag`](#cls-Vector-set_mag), [`normalize`](#cls-Vector-normalize).

<a id="cls-Vector-mag"></a>
#### `Vector.mag`

```py
Vector.mag() -> 'float'
```

The length of the vector.

**Returns.** the length, as a number that is 0 or more.

```py
print(f.Vector(3, 4).mag())    # 5.0
```

See also: [`mag_sq`](#cls-Vector-mag_sq), [`set_mag`](#cls-Vector-set_mag), [`normalize`](#cls-Vector-normalize).

<a id="cls-Vector-mag_sq"></a>
#### `Vector.mag_sq`

```py
Vector.mag_sq() -> 'float'
```

The length of the vector, squared.

It is quicker than mag(), because it needs no square root. Use it to compare lengths.

**Returns.** x * x + y * y.

```py
print(f.Vector(3, 4).mag_sq())    # 25.0
```

See also: [`mag`](#cls-Vector-mag).

<a id="cls-Vector-mult"></a>
#### `Vector.mult`

```py
Vector.mult(n: 'float') -> 'Vector'
```

Multiply both parts by a number, in place.

| Argument | Meaning |
|---|---|
| `n` | the number to multiply by. A negative number turns the vector round. |

**Returns.** this vector, changed.

```py
velocity.mult(0.99)    # slow down a little
```

See also: [`div`](#cls-Vector-div), [`set_mag`](#cls-Vector-set_mag), [`limit`](#cls-Vector-limit).

<a id="cls-Vector-normalize"></a>
#### `Vector.normalize`

```py
Vector.normalize() -> 'Vector'
```

Make the length 1, keeping the direction, in place.

A zero vector stays zero.

**Returns.** this vector, changed.

```py
direction = f.Vector(3, 4).normalize()    # (0.6, 0.8)
```

See also: [`set_mag`](#cls-Vector-set_mag), [`limit`](#cls-Vector-limit), [`mag`](#cls-Vector-mag).

<a id="cls-Vector-random_2d"></a>
#### `Vector.random_2d`

```py
Vector.random_2d() -> 'Vector'
```

Make a vector of length 1 that points in a random direction.

f.random_seed() makes the choice repeatable.

**Returns.** a new Vector of length 1.

```py
push = f.Vector.random_2d().mult(5)
```

See also: [`from_angle`](#cls-Vector-from_angle), [`set_mag`](#cls-Vector-set_mag).

<a id="cls-Vector-rotate"></a>
#### `Vector.rotate`

```py
Vector.rotate(angle: 'float') -> 'Vector'
```

Turn the vector by an angle, in place.

A positive angle turns clockwise on the screen, like f.rotate().

| Argument | Meaning |
|---|---|
| `angle` | how far to turn, in degrees. |

**Returns.** this vector, changed.

```py
v = f.Vector(1, 0).rotate(90)    # about (0, 1)
```

See also: [`set_heading`](#cls-Vector-set_heading), [`heading`](#cls-Vector-heading).

<a id="cls-Vector-set"></a>
#### `Vector.set`

```py
Vector.set(x, y=None) -> 'Vector'
```

Give the vector new x and y values, in place.

| Argument | Meaning |
|---|---|
| `x`, `y` | either two numbers, or x can be a Vector or an (x, y) pair with y left out. |

**Returns.** this vector, changed.

**Raises.**

- `TypeError`: if the values are not numbers, a Vector or an (x, y) pair.

```py
v = f.Vector(1, 2)
v.set(10, 20)
v.set((3, 4))
```

See also: [`copy`](#cls-Vector-copy), [`add`](#cls-Vector-add).

<a id="cls-Vector-set_heading"></a>
#### `Vector.set_heading`

```py
Vector.set_heading(angle: 'float') -> 'Vector'
```

Turn the vector to point at an angle, in place, keeping its length.

| Argument | Meaning |
|---|---|
| `angle` | the new direction in degrees. 0 is right and 90 is down. |

**Returns.** this vector, changed.

```py
v = f.Vector(5, 0).set_heading(90)    # about (0, 5)
```

See also: [`heading`](#cls-Vector-heading), [`rotate`](#cls-Vector-rotate).

<a id="cls-Vector-set_mag"></a>
#### `Vector.set_mag`

```py
Vector.set_mag(length: 'float') -> 'Vector'
```

Give the vector a new length, in place, keeping its direction.

A zero vector stays zero, because it has no direction.

| Argument | Meaning |
|---|---|
| `length` | the new length. |

**Returns.** this vector, changed.

```py
v = f.Vector(3, 4).set_mag(10)    # (6, 8)
```

See also: [`mag`](#cls-Vector-mag), [`normalize`](#cls-Vector-normalize), [`limit`](#cls-Vector-limit).

<a id="cls-Vector-sub"></a>
#### `Vector.sub`

```py
Vector.sub(x, y=None) -> 'Vector'
```

Take away from the vector, in place.

| Argument | Meaning |
|---|---|
| `x`, `y` | either two numbers, or x can be a Vector or an (x, y) pair with y left out. |

**Returns.** this vector, changed.

**Raises.**

- `TypeError`: if the values are not numbers, a Vector or an (x, y) pair.

```py
to_mouse = f.Vector(f.mouse_x, f.mouse_y).sub(position)
```

See also: [`add`](#cls-Vector-add), [`dist`](#cls-Vector-dist).

<a id="cls-FormattedString"></a>
### `FormattedString`

```py
FormattedString() -> 'None'
```

Text made of runs, where each run can have its own font, size, style, colour and so on.

Make an empty one with f.FormattedString(), then add runs with append(). Draw it with f.text() or
f.text_box() in place of an ordinary string. f.text_box() gives back what did not fit as a
FormattedString, and its runs keep their settings.

A setting that you leave out for a run is not fixed. It follows the drawing state when the text is
drawn, so a push() or a text_size() still reaches it.

str(line) is the plain text, len(line) is the number of characters, and a + b joins two formatted
strings (or a formatted string and an ordinary string) into a new one.

```py
line = f.FormattedString()
line.append("big ", size=60, color="tomato")
line.append("and small", size=20)
f.text(line, 20, 100)
```

<a id="cls-FormattedString-append"></a>
#### `FormattedString.append`

```py
FormattedString.append(text: 'object', font=None, size: 'float | None' = None, style: 'str | None' = None, color=None, tracking: 'float | None' = None, features: 'dict | None' = None, variations: 'dict | None' = None) -> "'FormattedString'"
```

Add a run of text to the end.

Every setting you give belongs to this run. A setting you leave out follows the drawing state when
the text is drawn. Numbers for the colour are read in the colour mode of the moment you call append().

| Argument | Meaning |
|---|---|
| `text` | what to add. It is turned into text with str(). Empty text adds no run. |
| `font` | a font from f.load_font(), or the path of a font file. |
| `size` | the text size in pixels, more than 0. |
| `style` | "normal", "bold", "italic" or "bold_italic". It is for the built-in font only. |
| `color` | the colour of this run. Any colour that f.fill() takes. |
| `tracking` | the extra space after every letter, in pixels. |
| `features` | a dictionary of OpenType features to turn on or off, like {"liga": False}. |
| `variations` | a dictionary of axes of a variable font, like {"wght": 700}. |

**Returns.** this same FormattedString, so calls can chain.

**Raises.**

- `TypeError`: if font, size, tracking, features or variations is of the wrong kind.
- `ValueError`: if size is 0 or less, or style is not one of the four.

```py
line = f.FormattedString()
line.append("Hello ", size=40).append("world", style="bold", color="navy")
```

See also: [`runs`](#cls-FormattedString-runs), [`text`](#fn-text).

<a id="cls-FormattedString-lines"></a>
#### `FormattedString.lines`

```py
FormattedString.lines() -> 'list[list[tuple[str, int | None]]]'
```

Split the text at every new line.

funground uses it when it draws text. You do not need to call it.

**Returns.** a list of lines. Each line is a list of (text, run index) pieces.

See also: [`wrap`](#cls-FormattedString-wrap).

<a id="cls-FormattedString-runs"></a>
#### `FormattedString.runs`

```py
FormattedString.runs  # property
```

The runs, in order.

**Returns.** a tuple of Run objects.

```py
line = f.FormattedString().append("a").append("b", size=30)
print(len(line.runs))    # 2
```

See also: [`append`](#cls-FormattedString-append).

<a id="cls-FormattedString-wrap"></a>
#### `FormattedString.wrap`

```py
FormattedString.wrap(fits) -> 'tuple[list[list[tuple[str, int | None]]], list[int]]'
```

Break the text into lines that fit, at spaces.

funground uses it when it draws text in a box. You do not need to call it. A word that is wider than
the box is broken between letters. A blank line keeps one empty piece, so that it still has a height.

| Argument | Meaning |
|---|---|
| `fits` | a function that takes a candidate line, a list of (text, run index) pieces, and says whether it is narrow enough. None means no wrapping, only new lines. |

**Returns.** (lines, starts). lines is a list of lines, each a list of (text, run index) pieces. starts[i] is the character where line i begins.

See also: [`lines`](#cls-FormattedString-lines).

<a id="cls-Run"></a>
### `Run`

```py
Run(text: 'str', font: 'str | None' = None, size: 'int | None' = None, style: 'str | None' = None, color: 'Color | None' = None, tracking: 'float | None' = None, features: 'tuple | None' = None, variations: 'tuple | None' = None) -> None
```

One piece of a FormattedString: some text and the settings that were given for it.

You get the runs of a FormattedString from its runs property. A run is read-only. The fields are
text, font (the name of the font, or None), size, style, color, tracking, features and variations. A
field that is None was not given, so it follows the drawing state when the text is drawn.

```py
line = f.FormattedString().append("Hello ", size=40).append("world", style="bold")
for run in line.runs:
    print(run.text, run.size)
```

<a id="cls-Run-apply"></a>
#### `Run.apply`

```py
Run.apply(state)
```

Work out the drawing state for this run.

funground uses it when it draws formatted text. You do not need to call it.

| Argument | Meaning |
|---|---|
| `state` | a drawing state, the current settings for fill, text and so on. |

**Returns.** a drawing state: the one you gave, with this run's own settings put on top.

See also: [`with_text`](#cls-Run-with_text).

<a id="cls-Run-with_text"></a>
#### `Run.with_text`

```py
Run.with_text(text: 'str') -> "'Run'"
```

Make a new run with the same settings and different text.

funground uses it when it breaks text into lines. You do not need to call it.

| Argument | Meaning |
|---|---|
| `text` | the new text. |

**Returns.** a new Run.

See also: [`apply`](#cls-Run-apply).

<a id="cls-PathBuilder"></a>
### `PathBuilder`

```py
PathBuilder(path: 'Path | None' = None) -> 'None'
```

A path that you build step by step, then draw, clip with, cut, outline or measure.

You get one from f.path(), f.text_path() and f.svg_paths(). Draw it with f.draw_path(p) or use it as
a clip with f.clip(p). A path does not draw anything until you do that, so you can reuse it as often
as you like.

Most methods change the path and give it back, so you can chain calls: f.path().move_to(0, 0).line_to(50, 0).
The building methods are move_to, line_to, curve_to, quad_to, close, rect, ellipse, circle and
polygon. They change this builder. The methods that make a new shape (union, intersection, difference,
xor, remove_overlap, expand_stroke, translate, scale, rotate and copy) give you a new builder and leave
this one alone. The operators do the same: a | b is union, a & b is intersection, a - b and a % b are
difference, and a ^ b is xor.

Only closed paths are filled. An open path is stroked.

```py
star = f.path().polygon([(0, -50), (15, -15), (50, -10), (22, 10), (30, 45), (0, 25), (-30, 45), (-22, 10), (-50, -10), (-15, -15)])
f.translate(200, 200)
f.draw_path(star)
```

<a id="cls-PathBuilder-bounds"></a>
#### `PathBuilder.bounds`

```py
PathBuilder.bounds()
```

The box that exactly holds the path.

**Returns.** (x, y, w, h), the top left corner and the size, or None when the path has no lines or curves.

```py
x, y, w, h = f.path().circle(50, 50, 60).bounds()
```

See also: [`contains`](#cls-PathBuilder-contains).

<a id="cls-PathBuilder-circle"></a>
#### `PathBuilder.circle`

```py
PathBuilder.circle(x: 'float', y: 'float', d: 'float') -> "'PathBuilder'"
```

Add a circle as a closed part of the path.

| Argument | Meaning |
|---|---|
| `x`, `y` | the centre. |
| `d` | the diameter, which is the distance across. |

**Returns.** this builder, changed.

```py
p = f.path().circle(50, 50, 60)
```

See also: [`ellipse`](#cls-PathBuilder-ellipse), [`rect`](#cls-PathBuilder-rect).

<a id="cls-PathBuilder-close"></a>
#### `PathBuilder.close`

```py
PathBuilder.close() -> "'PathBuilder'"
```

Join the current point back to where the part of the path began.

Only closed paths are filled.

**Returns.** this builder, changed.

**Raises.**

- `ValueError`: if the path has no starting point yet. Begin with move_to().

```py
p = f.path().move_to(10, 10).line_to(90, 10).line_to(50, 80).close()
```

See also: [`move_to`](#cls-PathBuilder-move_to), [`line_to`](#cls-PathBuilder-line_to), [`is_closed`](#cls-PathBuilder-is_closed).

<a id="cls-PathBuilder-contains"></a>
#### `PathBuilder.contains`

```py
PathBuilder.contains(x: 'float', y: 'float') -> 'bool'
```

Whether a point is inside the shape that the path fills.

| Argument | Meaning |
|---|---|
| `x`, `y` | the point. |

**Returns.** True when the point is inside what is filled, otherwise False.

```py
button = f.path().rect(10, 10, 80, 30)
if button.contains(f.mouse_x, f.mouse_y):
    f.fill("gold")
```

See also: [`bounds`](#cls-PathBuilder-bounds).

<a id="cls-PathBuilder-copy"></a>
#### `PathBuilder.copy`

```py
PathBuilder.copy() -> "'PathBuilder'"
```

Make a new builder with the same path.

Building on the copy does not change the original.

**Returns.** a new PathBuilder.

```py
a = f.path().move_to(0, 0).line_to(50, 0)
b = a.copy().line_to(50, 50)    # a is not changed
```

See also: [`translate`](#cls-PathBuilder-translate).

<a id="cls-PathBuilder-curve_to"></a>
#### `PathBuilder.curve_to`

```py
PathBuilder.curve_to(cx1: 'float', cy1: 'float', cx2: 'float', cy2: 'float', x: 'float', y: 'float') -> "'PathBuilder'"
```

Add a smooth curve from the current point to a new point (a cubic Bezier curve).

The two control points pull the curve towards them.

| Argument | Meaning |
|---|---|
| `cx1`, `cy1` | the first control point. |
| `cx2`, `cy2` | the second control point. |
| `x`, `y` | the end of the curve. |

**Returns.** this builder, changed.

**Raises.**

- `ValueError`: if the path has no starting point yet. Begin with move_to().

```py
p = f.path().move_to(10, 90).curve_to(10, 10, 90, 10, 90, 90)
```

See also: [`quad_to`](#cls-PathBuilder-quad_to), [`line_to`](#cls-PathBuilder-line_to).

<a id="cls-PathBuilder-difference"></a>
#### `PathBuilder.difference`

```py
PathBuilder.difference(other: "'PathBuilder'") -> "'PathBuilder'"
```

Make a new path of what this path covers, minus what another path covers.

| Argument | Meaning |
|---|---|
| `other` | another path made with f.path(). |

**Returns.** a new PathBuilder. Neither original is changed.

**Raises.**

- `TypeError`: if other is not a path from f.path().

```py
ring = f.path().circle(50, 50, 80).difference(f.path().circle(50, 50, 40))
```

See also: [`union`](#cls-PathBuilder-union), [`intersection`](#cls-PathBuilder-intersection), [`xor`](#cls-PathBuilder-xor).

<a id="cls-PathBuilder-ellipse"></a>
#### `PathBuilder.ellipse`

```py
PathBuilder.ellipse(x: 'float', y: 'float', w: 'float', h: 'float') -> "'PathBuilder'"
```

Add an ellipse as a closed part of the path.

| Argument | Meaning |
|---|---|
| `x`, `y` | the centre. |
| `w`, `h` | the width and the height. |

**Returns.** this builder, changed.

```py
p = f.path().ellipse(50, 50, 80, 40)
```

See also: [`circle`](#cls-PathBuilder-circle), [`rect`](#cls-PathBuilder-rect).

<a id="cls-PathBuilder-expand_stroke"></a>
#### `PathBuilder.expand_stroke`

```py
PathBuilder.expand_stroke(width: 'float', cap: 'str' = 'round', join: 'str' = 'round', miter_limit: 'float' = 10, dash=None) -> "'PathBuilder'"
```

Make a new path that is the outline a stroke would paint, so you can fill, cut or clip with it.

Open parts of the path are included. Overlaps are removed.

| Argument | Meaning |
|---|---|
| `width` | how thick the stroke is. It must be more than 0. |
| `cap` | the ends of open parts: "round", "square" or "butt". It is "round" at first. |
| `join` | the corners: "round", "miter" or "bevel". It is "round" at first. |
| `miter_limit` | how long a pointed corner may get, at least 1. It is 10 at first. |
| `dash` | None for a solid line, or a length, or a list of lengths for dashes and gaps, such as [10, 5]. It is None at first. |

**Returns.** a new closed PathBuilder.

**Raises.**

- `ValueError`: if width, cap, join, miter_limit or dash is not allowed.

```py
line = f.path().move_to(10, 50).line_to(90, 50)
outline = line.expand_stroke(8, cap="butt", dash=[10, 5])
```

See also: [`remove_overlap`](#cls-PathBuilder-remove_overlap), [`contains`](#cls-PathBuilder-contains).

<a id="cls-PathBuilder-geometry"></a>
#### `PathBuilder.geometry`

```py
PathBuilder.geometry  # property
```

The plain path data built so far.

It cannot be changed. It is what funground draws.

**Returns.** a Path (from funground.geometry).

See also: [`is_empty`](#cls-PathBuilder-is_empty), [`is_closed`](#cls-PathBuilder-is_closed).

<a id="cls-PathBuilder-intersection"></a>
#### `PathBuilder.intersection`

```py
PathBuilder.intersection(other: "'PathBuilder'") -> "'PathBuilder'"
```

Make a new path of only what both paths cover.

| Argument | Meaning |
|---|---|
| `other` | another path made with f.path(). |

**Returns.** a new PathBuilder. Neither original is changed.

**Raises.**

- `TypeError`: if other is not a path from f.path().

```py
lens = f.path().circle(40, 50, 60).intersection(f.path().circle(70, 50, 60))
```

See also: [`union`](#cls-PathBuilder-union), [`difference`](#cls-PathBuilder-difference), [`xor`](#cls-PathBuilder-xor).

<a id="cls-PathBuilder-is_closed"></a>
#### `PathBuilder.is_closed`

```py
PathBuilder.is_closed  # property
```

Whether every part of the path that draws something is closed.

Only closed paths are filled. Open ones are stroked.

**Returns.** True when the path is closed, otherwise False. An empty path is not closed.

```py
print(f.path().circle(50, 50, 60).is_closed)    # True
```

See also: [`close`](#cls-PathBuilder-close), [`is_empty`](#cls-PathBuilder-is_empty).

<a id="cls-PathBuilder-is_empty"></a>
#### `PathBuilder.is_empty`

```py
PathBuilder.is_empty  # property
```

Whether nothing has been added to the path.

**Returns.** True when the path has no parts, otherwise False.

```py
print(f.path().is_empty)    # True
```

See also: [`is_closed`](#cls-PathBuilder-is_closed).

<a id="cls-PathBuilder-line_to"></a>
#### `PathBuilder.line_to`

```py
PathBuilder.line_to(x: 'float', y: 'float') -> "'PathBuilder'"
```

Add a straight line from the current point to a new point.

| Argument | Meaning |
|---|---|
| `x`, `y` | the end of the line. |

**Returns.** this builder, changed.

**Raises.**

- `ValueError`: if the path has no starting point yet. Begin with move_to().

```py
p = f.path().move_to(10, 10).line_to(90, 10).line_to(50, 80).close()
```

See also: [`move_to`](#cls-PathBuilder-move_to), [`curve_to`](#cls-PathBuilder-curve_to), [`close`](#cls-PathBuilder-close).

<a id="cls-PathBuilder-move_to"></a>
#### `PathBuilder.move_to`

```py
PathBuilder.move_to(x: 'float', y: 'float') -> "'PathBuilder'"
```

Start a new part of the path at a point, without drawing.

| Argument | Meaning |
|---|---|
| `x`, `y` | the point. |

**Returns.** this builder, changed.

```py
p = f.path().move_to(10, 10).line_to(90, 10)
```

See also: [`line_to`](#cls-PathBuilder-line_to), [`close`](#cls-PathBuilder-close).

<a id="cls-PathBuilder-polygon"></a>
#### `PathBuilder.polygon`

```py
PathBuilder.polygon(points) -> "'PathBuilder'"
```

Add a closed shape through a list of corners.

| Argument | Meaning |
|---|---|
| `points` | a list of at least 3 (x, y) pairs. |

**Returns.** this builder, changed.

**Raises.**

- `ValueError`: if there are fewer than 3 points.

```py
p = f.path().polygon([(50, 10), (90, 80), (10, 80)])
```

See also: [`rect`](#cls-PathBuilder-rect), [`line_to`](#cls-PathBuilder-line_to).

<a id="cls-PathBuilder-quad_to"></a>
#### `PathBuilder.quad_to`

```py
PathBuilder.quad_to(cx: 'float', cy: 'float', x: 'float', y: 'float') -> "'PathBuilder'"
```

Add a curve from the current point to a new point, pulled towards one control point (a quadratic Bezier curve).

| Argument | Meaning |
|---|---|
| `cx`, `cy` | the control point. |
| `x`, `y` | the end of the curve. |

**Returns.** this builder, changed.

**Raises.**

- `ValueError`: if the path has no starting point yet. Begin with move_to().

```py
p = f.path().move_to(10, 90).quad_to(50, 10, 90, 90)
```

See also: [`curve_to`](#cls-PathBuilder-curve_to), [`line_to`](#cls-PathBuilder-line_to).

<a id="cls-PathBuilder-rect"></a>
#### `PathBuilder.rect`

```py
PathBuilder.rect(x: 'float', y: 'float', w: 'float', h: 'float', *radii: 'float') -> "'PathBuilder'"
```

Add a rectangle as a closed part of the path.

| Argument | Meaning |
|---|---|
| `x`, `y` | the top left corner. |
| `w`, `h` | the width and the height. |
| `radii` | no radius, one radius for all four corners, or four radii (top left, top right, bottom right, bottom left). A radius is cut down to half the shorter side. |

**Returns.** this builder, changed.

**Raises.**

- `ValueError`: if the number of radii is not 0, 1 or 4, or a radius is negative.

```py
p = f.path().rect(10, 10, 80, 50, 8)
```

See also: [`ellipse`](#cls-PathBuilder-ellipse), [`circle`](#cls-PathBuilder-circle), [`polygon`](#cls-PathBuilder-polygon).

<a id="cls-PathBuilder-remove_overlap"></a>
#### `PathBuilder.remove_overlap`

```py
PathBuilder.remove_overlap() -> "'PathBuilder'"
```

Make a new path that fills the same area, drawn as one clean outline with no overlapping parts.

**Returns.** a new PathBuilder. This one is not changed.

```py
clean = f.path().circle(40, 50, 60).circle(70, 50, 60).remove_overlap()
```

See also: [`union`](#cls-PathBuilder-union), [`expand_stroke`](#cls-PathBuilder-expand_stroke).

<a id="cls-PathBuilder-rotate"></a>
#### `PathBuilder.rotate`

```py
PathBuilder.rotate(degrees: 'float', cx: 'float' = 0, cy: 'float' = 0) -> "'PathBuilder'"
```

Make a new path that is this path turned about a point.

| Argument | Meaning |
|---|---|
| `degrees` | how far to turn it. A positive angle turns clockwise on the screen. |
| `cx`, `cy` | the point to turn about. It is (0, 0) at first. |

**Returns.** a new PathBuilder. This one is not changed.

```py
bar = f.path().rect(-40, -5, 80, 10).rotate(45)
```

See also: [`translate`](#cls-PathBuilder-translate), [`scale`](#cls-PathBuilder-scale).

<a id="cls-PathBuilder-scale"></a>
#### `PathBuilder.scale`

```py
PathBuilder.scale(sx: 'float', sy: 'float | None' = None) -> "'PathBuilder'"
```

Make a new path that is this path scaled about the point (0, 0).

| Argument | Meaning |
|---|---|
| `sx` | how much to scale across. 2 makes it twice as wide. |
| `sy` | how much to scale down. If you leave it out, it is the same as sx. |

**Returns.** a new PathBuilder. This one is not changed.

```py
big = f.path().circle(0, 0, 40).scale(2)
```

See also: [`translate`](#cls-PathBuilder-translate), [`rotate`](#cls-PathBuilder-rotate).

<a id="cls-PathBuilder-translate"></a>
#### `PathBuilder.translate`

```py
PathBuilder.translate(dx: 'float', dy: 'float') -> "'PathBuilder'"
```

Make a new path that is this path moved.

| Argument | Meaning |
|---|---|
| `dx`, `dy` | how far to move it across and down. |

**Returns.** a new PathBuilder. This one is not changed.

```py
moved = f.path().circle(0, 0, 40).translate(100, 100)
```

See also: [`scale`](#cls-PathBuilder-scale), [`rotate`](#cls-PathBuilder-rotate).

<a id="cls-PathBuilder-union"></a>
#### `PathBuilder.union`

```py
PathBuilder.union(other: "'PathBuilder'") -> "'PathBuilder'"
```

Make a new path of everything that either path covers.

| Argument | Meaning |
|---|---|
| `other` | another path made with f.path(). |

**Returns.** a new PathBuilder. Neither original is changed.

**Raises.**

- `TypeError`: if other is not a path from f.path().

```py
both = f.path().circle(40, 50, 60).union(f.path().circle(70, 50, 60))
```

See also: [`intersection`](#cls-PathBuilder-intersection), [`difference`](#cls-PathBuilder-difference), [`xor`](#cls-PathBuilder-xor).

<a id="cls-PathBuilder-xor"></a>
#### `PathBuilder.xor`

```py
PathBuilder.xor(other: "'PathBuilder'") -> "'PathBuilder'"
```

Make a new path of what exactly one of the two paths covers.

| Argument | Meaning |
|---|---|
| `other` | another path made with f.path(). |

**Returns.** a new PathBuilder. Neither original is changed.

**Raises.**

- `TypeError`: if other is not a path from f.path().

```py
p = f.path().circle(40, 50, 60).xor(f.path().circle(70, 50, 60))
```

See also: [`union`](#cls-PathBuilder-union), [`intersection`](#cls-PathBuilder-intersection), [`difference`](#cls-PathBuilder-difference).

<a id="cls-Mark"></a>
### `Mark`

```py
Mark() -> 'None'
```

A drawing kept as a value, which you can place as often as you like.

Make one with a block: ``with f.mark() as m:``. The drawing calls inside the block are recorded, not
drawn, each with the fill, stroke and font it was drawn with. Or make one from a path with
f.mark(path, fill=..., stroke=...). Then m.place(x, y) draws it, with its own origin (0, 0) at
(x, y), and with any scale, rotation and opacity.

A mark keeps the drawing steps, not pixels. It is sharp at any size on screen, and real shapes and
text in a saved PDF or SVG. A finished mark cannot be changed, and placing it never changes it. To
make a variation, make a new mark, for example in a function that takes the parts that vary.

A mark's block starts with the current style and with no transform, so its coordinates are its own.
When the block ends, the transform, style and clip are exactly as before it, even if the block
raised an error. Inside the block you cannot open a layer, make controls, save files or read pixels.

```py
with f.mark() as flower:
    for a in range(0, 360, 60):
        with f.saved_state():
            f.rotate(a)
            f.fill("tomato")
            f.ellipse(0, -30, 18, 40)
    f.fill("gold")
    f.circle(0, 0, 24)
flower.place(150, 200)
flower.place(400, 200, scale=0.5, rotate=15, opacity=0.6)
```

<a id="cls-Mark-bounds"></a>
#### `Mark.bounds`

```py
Mark.bounds() -> 'tuple[float, float, float, float] | None'
```

Return the area the mark covers, in its own coordinates.

The area includes stroke widths, joins and caps, and text. It is never smaller than what the mark
paints, and at most a tiny bit larger. The mark's origin (0, 0) is where place() puts (x, y), so x
and y are often negative.

**Returns.** (x, y, w, h): the left, the top, the width and the height. None for an empty mark.

**Raises.**

- `RuntimeError`: the mark is unfinished.

```py
x, y, w, h = flower.bounds()
```

See also: [`width`](#cls-Mark-width), [`height`](#cls-Mark-height), [`is_empty`](#cls-Mark-is_empty), [`place`](#cls-Mark-place).

<a id="cls-Mark-height"></a>
#### `Mark.height`

```py
Mark.height  # property
```

The height of the area the mark covers, from bounds(); 0 for an empty mark.

**Raises.**

- `RuntimeError`: the mark is unfinished.

```py
f.size(400, int(flower.height) + 20)
```

See also: [`width`](#cls-Mark-width), [`bounds`](#cls-Mark-bounds).

<a id="cls-Mark-is_empty"></a>
#### `Mark.is_empty`

```py
Mark.is_empty  # property
```

Whether the mark paints nothing.

**Returns.** True when the mark paints nothing (and bounds() is None), otherwise False.

**Raises.**

- `RuntimeError`: the mark is unfinished.

```py
if not flower.is_empty:
    flower.place(100, 100)
```

See also: [`bounds`](#cls-Mark-bounds).

<a id="cls-Mark-place"></a>
#### `Mark.place`

```py
Mark.place(x: 'float', y: 'float', *, scale: 'float | tuple[float, float] | None' = None, rotate: 'float' = 0, opacity: 'float' = 1, anchor: 'str' = 'origin', width: 'float | None' = None, height: 'float | None' = None, style: 'str' = 'own') -> 'None'
```

Draw the mark now, with its origin at (x, y).

The mark follows the current transform and clip, so it works inside saved_state() and translate(), inside a layer block, and inside another mark's block (marks can be made of marks). The mark itself never changes.

The mark is moved to (x, y), then turned by rotate, then sized by scale, all around the anchor point. So with anchor="center" the centre of the mark lands on (x, y) and stays there.

width and height size the mark from its bounds, keeping its proportions. Give one of them, and the mark is scaled to that width or height. Give both, and the mark is scaled to fit inside a box of that size and centred in it; then anchor places the box ("origin" counts as "top-left"). This happens before rotate.

style="own" (the default) draws every part with the style it was recorded with. style="current" draws every part with the style in force now instead, so f.fill("black") then place(..., style="current") gives a black silhouette. It replaces, for each part: on closed shapes and paths, the fill, stroke, stroke width, caps, joins, miter limit and dash (a gradient fill too, and no_fill() or no_stroke() now take the fill or stroke away); on lines and open paths, the stroke, its width, caps and dash; on text, its colour, which comes from the fill as text() does (font, size and shaping stay). Pictures are unchanged. Marks inside the mark follow the same rules. Blend mode and opacity never come from the current style: opacity is the argument here.

| Argument | Meaning |
|---|---|
| `x`, `y` | where the anchor point lands. |
| `scale` | one number to size both ways, or two as (sx, sy). Left out (None), the mark keeps its own size. A negative number mirrors it. 0 is an error. |
| `rotate` | degrees to turn, clockwise on screen. |
| `opacity` | from 0 (invisible) to 1 (solid, the default). The whole mark fades as one piece, so its overlapping parts do not show through each other. |
| `anchor` | which point of the mark lands on (x, y). "origin" (the default) is the mark's own (0, 0). The others use bounds(): "center", "top-left", "top", "top-right", "left", "right", "bottom-left", "bottom" and "bottom-right". |
| `width`, `height` | the size to make the mark, in pixels, keeping its proportions (see above). They cannot be used with scale. |
| `style` | "own" (the default) or "current" (see above). |

**Raises.**

- `RuntimeError`: the mark is unfinished, or still being recorded.
- `ValueError`: the anchor or style is unknown, the mark is empty and the anchor is not "origin" or a width or height is given, opacity is outside 0 to 1, scale is 0, width or height is not above 0, or scale is given with width or height.
- `TypeError`: a number is not a number.

```py
flower.place(150, 200)
flower.place(400, 200, scale=0.5, rotate=15, opacity=0.6)
flower.place(200, 150, anchor="center", width=80)
f.fill("black")
flower.place(300, 200, style="current")
```

See also: [`mark`](#fn-mark), [`bounds`](#cls-Mark-bounds), [`saved_state`](#fn-saved_state).

<a id="cls-Mark-width"></a>
#### `Mark.width`

```py
Mark.width  # property
```

The width of the area the mark covers, from bounds(); 0 for an empty mark.

**Raises.**

- `RuntimeError`: the mark is unfinished.

```py
gap = flower.width + 10
```

See also: [`height`](#cls-Mark-height), [`bounds`](#cls-Mark-bounds).

<a id="cls-Area"></a>
### `Area`

```py
Area(left: 'float', top: 'float', width: 'float', height: 'float') -> 'None'
```

A rectangle on the canvas, kept as a value.

An area has a left edge, a top edge, a width and a height, in canvas units. It also gives its right and bottom edges and its centre. Make one with f.area(x, y, w, h). f.ground, f.ground.content and every cell of a grid are areas too, so anything that takes an area takes them.

An area never changes. inset() and grid() give new values. An area may be 0 wide or 0 high, but never less.

```py
panel = f.area(40, 40, 300, 200)
f.rect(panel.left, panel.top, panel.width, panel.height)
f.circle(panel.cx, panel.cy, 20)
```

<a id="cls-Area-bottom"></a>
#### `Area.bottom`

```py
Area.bottom  # property
```

The y of the area's bottom edge: top + height.

<a id="cls-Area-cx"></a>
#### `Area.cx`

```py
Area.cx  # property
```

The x of the area's centre.

<a id="cls-Area-cy"></a>
#### `Area.cy`

```py
Area.cy  # property
```

The y of the area's centre.

<a id="cls-Area-grid"></a>
#### `Area.grid`

```py
Area.grid(cols: 'int', rows: 'int', *, gutter: 'float | tuple' = 0) -> "'Grid'"
```

Return a grid of equal cells over this area.

It is the same as f.grid(cols, rows, gutter=gutter, area=this_area). A cell is an area too, so a cell can hold a grid of its own.

| Argument | Meaning |
|---|---|
| `cols` | how many columns. A whole number above 0. |
| `rows` | how many rows. A whole number above 0. |
| `gutter` | the gap between cells. One number is used both across and down. A tuple (column_gutter, row_gutter) sets them apart. The default is 0. |

**Returns.** A Grid. It goes row by row, left to right, like a list of cells.

**Raises.**

- `TypeError`: cols or rows is not a whole number, or a gutter is not a number.
- `ValueError`: cols or rows is 0 or less, a gutter is negative, or the gutters leave no room for the cells.

```py
for cell in f.ground.content.grid(4, 3, gutter=8):
    f.circle(cell.cx, cell.cy, cell.width * 0.5)
```

See also: [`inset`](#cls-Area-inset), [`area`](#fn-area).

<a id="cls-Area-height"></a>
#### `Area.height`

```py
Area.height  # property
```

How high the area is: 0 or more.

<a id="cls-Area-inset"></a>
#### `Area.inset`

```py
Area.inset(all: 'float | None' = None, *, top: 'float | None' = None, right: 'float | None' = None, bottom: 'float | None' = None, left: 'float | None' = None) -> "'Area'"
```

Return a smaller area inside this one.

One number moves every edge in by that much. top=, right=, bottom= and left= move one edge each, and a side you name wins over the one number. A side you leave out does not move. A negative number moves that edge out instead, which makes the area bigger, as for a bleed around a page. The area itself does not change.

| Argument | Meaning |
|---|---|
| `all` | how far to move every edge in. The default None moves none of them. |
| `top` | how far to move the top edge down. The default None uses all. |
| `right` | how far to move the right edge left. The default None uses all. |
| `bottom` | how far to move the bottom edge up. The default None uses all. |
| `left` | how far to move the left edge right. The default None uses all. |

**Returns.** A new Area. It may be 0 wide or 0 high.

**Raises.**

- `TypeError`: a side is not a number.
- `ValueError`: the insets are more than the width or the height, which would leave a negative size.

```py
page = f.ground.inset(20)
header = page.inset(bottom=page.height - 60)
```

See also: [`grid`](#cls-Area-grid), [`area`](#fn-area).

<a id="cls-Area-left"></a>
#### `Area.left`

```py
Area.left  # property
```

The x of the area's left edge.

<a id="cls-Area-right"></a>
#### `Area.right`

```py
Area.right  # property
```

The x of the area's right edge: left + width.

<a id="cls-Area-top"></a>
#### `Area.top`

```py
Area.top  # property
```

The y of the area's top edge.

<a id="cls-Area-width"></a>
#### `Area.width`

```py
Area.width  # property
```

How wide the area is: 0 or more.

<a id="cls-Ground"></a>
### `Ground`

```py
Ground(left: 'float', top: 'float', width: 'float', height: 'float', margin: 'tuple' = (0, 0, 0, 0)) -> 'None'
```

The canvas as an area, with its margins.

f.ground is the whole canvas and f.ground.content is the part inside the margins. Both are areas, so they have left, top, right, bottom, width, height, cx and cy, and inset() and grid(). f.ground is made fresh each time you read it, so it always matches the canvas. You do not make a Ground yourself: set the margins with f.size(..., margin=...).

```py
f.size("A5", margin=f.mm(12))
f.background("linen")
c = f.ground.content
f.rect(c.left, c.top, c.width, c.height)
```

<a id="cls-Ground-bottom"></a>
#### `Ground.bottom`

```py
Ground.bottom  # property
```

The y of the area's bottom edge: top + height.

<a id="cls-Ground-content"></a>
#### `Ground.content`

```py
Ground.content  # property
```

The area inside the margins. With no margin it is this same object, and its own margin is (0, 0, 0, 0).

<a id="cls-Ground-cx"></a>
#### `Ground.cx`

```py
Ground.cx  # property
```

The x of the area's centre.

<a id="cls-Ground-cy"></a>
#### `Ground.cy`

```py
Ground.cy  # property
```

The y of the area's centre.

<a id="cls-Ground-grid"></a>
#### `Ground.grid`

```py
Ground.grid(cols: 'int', rows: 'int', *, gutter: 'float | tuple' = 0) -> "'Grid'"
```

Return a grid of equal cells over this area.

It is the same as f.grid(cols, rows, gutter=gutter, area=this_area). A cell is an area too, so a cell can hold a grid of its own.

| Argument | Meaning |
|---|---|
| `cols` | how many columns. A whole number above 0. |
| `rows` | how many rows. A whole number above 0. |
| `gutter` | the gap between cells. One number is used both across and down. A tuple (column_gutter, row_gutter) sets them apart. The default is 0. |

**Returns.** A Grid. It goes row by row, left to right, like a list of cells.

**Raises.**

- `TypeError`: cols or rows is not a whole number, or a gutter is not a number.
- `ValueError`: cols or rows is 0 or less, a gutter is negative, or the gutters leave no room for the cells.

```py
for cell in f.ground.content.grid(4, 3, gutter=8):
    f.circle(cell.cx, cell.cy, cell.width * 0.5)
```

See also: [`inset`](#cls-Ground-inset), [`area`](#fn-area).

<a id="cls-Ground-height"></a>
#### `Ground.height`

```py
Ground.height  # property
```

How high the area is: 0 or more.

<a id="cls-Ground-inset"></a>
#### `Ground.inset`

```py
Ground.inset(all: 'float | None' = None, *, top: 'float | None' = None, right: 'float | None' = None, bottom: 'float | None' = None, left: 'float | None' = None) -> "'Area'"
```

Return a smaller area inside this one.

One number moves every edge in by that much. top=, right=, bottom= and left= move one edge each, and a side you name wins over the one number. A side you leave out does not move. A negative number moves that edge out instead, which makes the area bigger, as for a bleed around a page. The area itself does not change.

| Argument | Meaning |
|---|---|
| `all` | how far to move every edge in. The default None moves none of them. |
| `top` | how far to move the top edge down. The default None uses all. |
| `right` | how far to move the right edge left. The default None uses all. |
| `bottom` | how far to move the bottom edge up. The default None uses all. |
| `left` | how far to move the left edge right. The default None uses all. |

**Returns.** A new Area. It may be 0 wide or 0 high.

**Raises.**

- `TypeError`: a side is not a number.
- `ValueError`: the insets are more than the width or the height, which would leave a negative size.

```py
page = f.ground.inset(20)
header = page.inset(bottom=page.height - 60)
```

See also: [`grid`](#cls-Ground-grid), [`area`](#fn-area).

<a id="cls-Ground-left"></a>
#### `Ground.left`

```py
Ground.left  # property
```

The x of the area's left edge.

<a id="cls-Ground-margin"></a>
#### `Ground.margin`

```py
Ground.margin  # property
```

The margins as (top, right, bottom, left). (0, 0, 0, 0) when there are none.

<a id="cls-Ground-right"></a>
#### `Ground.right`

```py
Ground.right  # property
```

The x of the area's right edge: left + width.

<a id="cls-Ground-top"></a>
#### `Ground.top`

```py
Ground.top  # property
```

The y of the area's top edge.

<a id="cls-Ground-width"></a>
#### `Ground.width`

```py
Ground.width  # property
```

How wide the area is: 0 or more.

<a id="cls-Cell"></a>
### `Cell`

```py
Cell(left: 'float', top: 'float', width: 'float', height: 'float', col: 'int', row: 'int', index: 'int') -> 'None'
```

One cell of a grid: an area that knows its column, row and place in the grid.

A cell has everything an area has (left, top, width, height, cx, cy and so on), plus col, row and index, all counted from 0. A cell can be the area of another grid, so grids nest.

```py
for cell in f.grid(3, 2, gutter=10):
    if cell.row == 0:
        f.circle(cell.cx, cell.cy, cell.width * 0.5)
```

<a id="cls-Cell-bottom"></a>
#### `Cell.bottom`

```py
Cell.bottom  # property
```

The y of the area's bottom edge: top + height.

<a id="cls-Cell-col"></a>
#### `Cell.col`

```py
Cell.col  # property
```

The cell's column, counted from 0 at the left.

<a id="cls-Cell-cx"></a>
#### `Cell.cx`

```py
Cell.cx  # property
```

The x of the area's centre.

<a id="cls-Cell-cy"></a>
#### `Cell.cy`

```py
Cell.cy  # property
```

The y of the area's centre.

<a id="cls-Cell-grid"></a>
#### `Cell.grid`

```py
Cell.grid(cols: 'int', rows: 'int', *, gutter: 'float | tuple' = 0) -> "'Grid'"
```

Return a grid of equal cells over this area.

It is the same as f.grid(cols, rows, gutter=gutter, area=this_area). A cell is an area too, so a cell can hold a grid of its own.

| Argument | Meaning |
|---|---|
| `cols` | how many columns. A whole number above 0. |
| `rows` | how many rows. A whole number above 0. |
| `gutter` | the gap between cells. One number is used both across and down. A tuple (column_gutter, row_gutter) sets them apart. The default is 0. |

**Returns.** A Grid. It goes row by row, left to right, like a list of cells.

**Raises.**

- `TypeError`: cols or rows is not a whole number, or a gutter is not a number.
- `ValueError`: cols or rows is 0 or less, a gutter is negative, or the gutters leave no room for the cells.

```py
for cell in f.ground.content.grid(4, 3, gutter=8):
    f.circle(cell.cx, cell.cy, cell.width * 0.5)
```

See also: [`inset`](#cls-Cell-inset), [`area`](#fn-area).

<a id="cls-Cell-height"></a>
#### `Cell.height`

```py
Cell.height  # property
```

How high the area is: 0 or more.

<a id="cls-Cell-index"></a>
#### `Cell.index`

```py
Cell.index  # property
```

The cell's place in the grid, counted from 0, row by row: row * column_count + col.

<a id="cls-Cell-inset"></a>
#### `Cell.inset`

```py
Cell.inset(all: 'float | None' = None, *, top: 'float | None' = None, right: 'float | None' = None, bottom: 'float | None' = None, left: 'float | None' = None) -> "'Area'"
```

Return a smaller area inside this one.

One number moves every edge in by that much. top=, right=, bottom= and left= move one edge each, and a side you name wins over the one number. A side you leave out does not move. A negative number moves that edge out instead, which makes the area bigger, as for a bleed around a page. The area itself does not change.

| Argument | Meaning |
|---|---|
| `all` | how far to move every edge in. The default None moves none of them. |
| `top` | how far to move the top edge down. The default None uses all. |
| `right` | how far to move the right edge left. The default None uses all. |
| `bottom` | how far to move the bottom edge up. The default None uses all. |
| `left` | how far to move the left edge right. The default None uses all. |

**Returns.** A new Area. It may be 0 wide or 0 high.

**Raises.**

- `TypeError`: a side is not a number.
- `ValueError`: the insets are more than the width or the height, which would leave a negative size.

```py
page = f.ground.inset(20)
header = page.inset(bottom=page.height - 60)
```

See also: [`grid`](#cls-Cell-grid), [`area`](#fn-area).

<a id="cls-Cell-left"></a>
#### `Cell.left`

```py
Cell.left  # property
```

The x of the area's left edge.

<a id="cls-Cell-right"></a>
#### `Cell.right`

```py
Cell.right  # property
```

The x of the area's right edge: left + width.

<a id="cls-Cell-row"></a>
#### `Cell.row`

```py
Cell.row  # property
```

The cell's row, counted from 0 at the top.

<a id="cls-Cell-top"></a>
#### `Cell.top`

```py
Cell.top  # property
```

The y of the area's top edge.

<a id="cls-Cell-width"></a>
#### `Cell.width`

```py
Cell.width  # property
```

How wide the area is: 0 or more.

<a id="cls-Grid"></a>
### `Grid`

```py
Grid(area, cols: 'int', rows: 'int', gutter: 'float | tuple' = 0) -> 'None'
```

An area divided into equal cells, with gutters between them.

f.grid() and area.grid() make one. A grid works like a list of its cells, row by row, left to right: a for loop goes through them, len() counts them, g[0] is the top-left cell and g[-1] the last one, and g[2:5] gives a list. It also finds cells by column and row, joins cells into larger areas, and draws guide lines to help you see the layout.

A grid never changes. Columns, rows and cells are all counted from 0.

```py
g = f.grid(4, 3, gutter=10)
for cell in g:
    f.circle(cell.cx, cell.cy, cell.width * 0.6)
banner = g.span(0, 0, cols=4)
g.show()
```

<a id="cls-Grid-area"></a>
#### `Grid.area`

```py
Grid.area  # property
```

The area the grid divides.

<a id="cls-Grid-cell"></a>
#### `Grid.cell`

```py
Grid.cell(col: 'int', row: 'int') -> 'Cell'
```

Return the cell at a column and a row.

Both count from 0, so g.cell(0, 0) is the top-left cell. It is the same cell as g[row * g.column_count + col].

| Argument | Meaning |
|---|---|
| `col` | the column, from 0 at the left. |
| `row` | the row, from 0 at the top. |

**Returns.** The Cell.

**Raises.**

- `TypeError`: col or row is not a whole number.
- `IndexError`: there is no such column or row. The message says which ones there are.

```py
corner = f.grid(3, 3).cell(2, 0)
f.rect(corner.left, corner.top, corner.width, corner.height)
```

See also: [`span`](#cls-Grid-span), [`columns`](#cls-Grid-columns), [`rows`](#cls-Grid-rows).

<a id="cls-Grid-column_count"></a>
#### `Grid.column_count`

```py
Grid.column_count  # property
```

How many columns the grid has.

<a id="cls-Grid-columns"></a>
#### `Grid.columns`

```py
Grid.columns  # property
```

The columns as a list of areas, left to right, each as high as the whole grid.

<a id="cls-Grid-gutter"></a>
#### `Grid.gutter`

```py
Grid.gutter  # property
```

The gaps between cells, as (column_gutter, row_gutter).

<a id="cls-Grid-row_count"></a>
#### `Grid.row_count`

```py
Grid.row_count  # property
```

How many rows the grid has.

<a id="cls-Grid-rows"></a>
#### `Grid.rows`

```py
Grid.rows  # property
```

The rows as a list of areas, top to bottom, each as wide as the whole grid.

<a id="cls-Grid-show"></a>
#### `Grid.show`

```py
Grid.show(*, color='#1e90ff', in_files: 'bool' = False) -> 'None'
```

Draw thin guide lines that show the grid: the outline of its area and of every cell.

Guides help you see a layout while you work. They are drawn over everything else in the window, and they are not part of the picture: they are left out of every saved file (PNG, PDF, SVG, f.keep(), save_frames(), GIFs and movies), and get() and pixels do not see them. Give in_files=True to make them ordinary drawing instead, so they are saved too; then later drawing can cover them.

The lines are 1 unit wide and follow the current transform. show() does not change the fill, stroke, transform, clip or anything else. In an animated sketch the guides last one frame, so call show() in draw().

| Argument | Meaning |
|---|---|
| `color` | the colour of the lines. The default is a clear blue. |
| `in_files` | True draws the guides as ordinary drawing, so saved files have them. The default False shows them only in the window. |

**Raises.**

- `RuntimeError`: it is used inside a ``with f.mark()`` block without in_files=True, or before f.size().

```py
g = f.grid(4, 3, gutter=10)
g.show()
g.show(color="red", in_files=True)
```

See also: [`cell`](#cls-Grid-cell), [`span`](#cls-Grid-span).

<a id="cls-Grid-span"></a>
#### `Grid.span`

```py
Grid.span(col: 'int', row: 'int', cols: 'int' = 1, rows: 'int' = 1) -> 'Area'
```

Return one area that covers several cells, with the gutters between them.

The area starts at the cell (col, row) and is cols cells wide and rows cells high. The gutters inside it are part of it, so its edges line up with the cells around it.

| Argument | Meaning |
|---|---|
| `col` | the column of the top-left cell, from 0. |
| `row` | the row of the top-left cell, from 0. |
| `cols` | how many columns it covers. The default is 1. |
| `rows` | how many rows it covers. The default is 1. |

**Returns.** A new Area.

**Raises.**

- `TypeError`: a value is not a whole number.
- `ValueError`: cols or rows is less than 1.
- `IndexError`: the cells it would cover are not all in the grid. The message says which ones there are.

```py
g = f.grid(4, 3, gutter=10)
title = g.span(0, 0, cols=4)
f.rect(title.left, title.top, title.width, title.height)
```

See also: [`cell`](#cls-Grid-cell), [`columns`](#cls-Grid-columns), [`rows`](#cls-Grid-rows).

<a id="cls-Path"></a>
### `Path`

```py
Path(segments: 'tuple[Segment, ...]' = ()) -> None
```

The plain data of a path: a fixed list of moves, lines, curves and closes.

You get one from PathBuilder.geometry. Most sketches never need it, because f.path() gives you a
PathBuilder with friendlier methods. A Path cannot be changed. Every method that builds returns a new
Path and leaves the first alone.

The parts are in Path.segments, a tuple. Each part is a tuple: ("move", (x, y)), ("line", (x, y)),
("cubic", (cx1, cy1), (cx2, cy2), (x, y)) or ("close",). A Path is also a sequence: len(p)
counts the parts and you can loop over them. y grows downward and angles are in degrees.

```py
p = f.path().circle(50, 50, 60).geometry
print(len(p), p.is_closed)
```

<a id="cls-Path-arc_to"></a>
#### `Path.arc_to`

```py
Path.arc_to(cx: 'float', cy: 'float', rx: 'float', ry: 'float', start: 'float', stop: 'float') -> "'Path'"
```

Make a new path with an arc of an ellipse added.

The point at angle a is (cx + rx * cos a, cy + ry * sin a), so 0 degrees is right and 90 degrees is
straight down. The arc begins with a line from the current point to the start of the arc, or with a
move if the path is empty.

| Argument | Meaning |
|---|---|
| `cx`, `cy` | the centre of the ellipse. |
| `rx`, `ry` | the radii across and down. |
| `start`, `stop` | the angles where the arc begins and ends, in degrees, turning clockwise on the screen. If stop is not above start, only the line to the start is added. |

**Returns.** a new Path.

See also: [`ellipse`](#cls-Path-ellipse), [`line_to`](#cls-Path-line_to).

<a id="cls-Path-bounds"></a>
#### `Path.bounds`

```py
Path.bounds() -> 'tuple[float, float, float, float] | None'
```

The box that holds every point of the path, including curve control points.

Because it counts control points, a curved path may have a smaller real extent. PathBuilder.bounds()
gives the exact one.

**Returns.** (min_x, min_y, max_x, max_y), or None for an empty path.

See also: [`points`](#cls-Path-points).

<a id="cls-Path-close"></a>
#### `Path.close`

```py
Path.close() -> "'Path'"
```

Make a new path with the current part closed.

**Returns.** a new Path.

See also: [`move_to`](#cls-Path-move_to), [`is_closed`](#cls-Path-is_closed).

<a id="cls-Path-cubic_to"></a>
#### `Path.cubic_to`

```py
Path.cubic_to(c1x: 'float', c1y: 'float', c2x: 'float', c2y: 'float', x: 'float', y: 'float') -> "'Path'"
```

Make a new path with a cubic Bezier curve added.

| Argument | Meaning |
|---|---|
| `c1x`, `c1y` | the first control point. |
| `c2x`, `c2y` | the second control point. |
| `x`, `y` | the end of the curve. |

**Returns.** a new Path.

See also: [`quad_to`](#cls-Path-quad_to), [`line_to`](#cls-Path-line_to).

<a id="cls-Path-current_point"></a>
#### `Path.current_point`

```py
Path.current_point() -> 'Point'
```

The point where the path now ends.

**Returns.** an (x, y) pair.

**Raises.**

- `ValueError`: if the path is empty, so it has no current point.

See also: [`move_to`](#cls-Path-move_to), [`points`](#cls-Path-points).

<a id="cls-Path-ellipse"></a>
#### `Path.ellipse`

```py
Path.ellipse(cx: 'float', cy: 'float', rx: 'float', ry: 'float') -> "'Path'"
```

Make a new path that is one closed ellipse.

It is built from four curves, and is within about 0.03 per cent of a true ellipse.

| Argument | Meaning |
|---|---|
| `cx`, `cy` | the centre. |
| `rx`, `ry` | the radii across and down. |

**Returns.** a new Path.

See also: [`rect`](#cls-Path-rect).

<a id="cls-Path-is_closed"></a>
#### `Path.is_closed`

```py
Path.is_closed  # property
```

Whether every part that draws something ends with a close.

Only closed shapes are filled. A move at the end on its own draws nothing, and does not count.

**Returns.** True when the path is closed. An empty path is not closed.

See also: [`close`](#cls-Path-close), [`is_empty`](#cls-Path-is_empty).

<a id="cls-Path-is_empty"></a>
#### `Path.is_empty`

```py
Path.is_empty  # property
```

Whether the path has no parts.

**Returns.** True when there are no parts, otherwise False.

See also: [`is_closed`](#cls-Path-is_closed).

<a id="cls-Path-line_to"></a>
#### `Path.line_to`

```py
Path.line_to(x: 'float', y: 'float') -> "'Path'"
```

Make a new path with a straight line added.

| Argument | Meaning |
|---|---|
| `x`, `y` | the end of the line. |

**Returns.** a new Path.

See also: [`move_to`](#cls-Path-move_to), [`cubic_to`](#cls-Path-cubic_to).

<a id="cls-Path-move_to"></a>
#### `Path.move_to`

```py
Path.move_to(x: 'float', y: 'float') -> "'Path'"
```

Make a new path with a new part started at a point.

| Argument | Meaning |
|---|---|
| `x`, `y` | the point. |

**Returns.** a new Path.

See also: [`line_to`](#cls-Path-line_to), [`close`](#cls-Path-close).

<a id="cls-Path-points"></a>
#### `Path.points`

```py
Path.points() -> 'Iterator[Point]'
```

Every point in the path, including curve control points, in order.

**Returns.** an iterator of (x, y) pairs.

See also: [`bounds`](#cls-Path-bounds), [`current_point`](#cls-Path-current_point).

<a id="cls-Path-quad_to"></a>
#### `Path.quad_to`

```py
Path.quad_to(cx: 'float', cy: 'float', x: 'float', y: 'float') -> "'Path'"
```

Make a new path with a quadratic Bezier curve added.

It is stored as the same curve written as a cubic, so a path only needs one kind of curve.

| Argument | Meaning |
|---|---|
| `cx`, `cy` | the control point. |
| `x`, `y` | the end of the curve. |

**Returns.** a new Path.

**Raises.**

- `ValueError`: if the path has no current point.

See also: [`cubic_to`](#cls-Path-cubic_to).

<a id="cls-Path-rect"></a>
#### `Path.rect`

```py
Path.rect(x: 'float', y: 'float', w: 'float', h: 'float') -> "'Path'"
```

Make a new path that is one closed rectangle.

| Argument | Meaning |
|---|---|
| `x`, `y` | the top left corner. |
| `w`, `h` | the width and the height. |

**Returns.** a new Path.

See also: [`rounded_rect`](#cls-Path-rounded_rect), [`ellipse`](#cls-Path-ellipse).

<a id="cls-Path-rounded_rect"></a>
#### `Path.rounded_rect`

```py
Path.rounded_rect(x: 'float', y: 'float', w: 'float', h: 'float', radii: 'tuple[float, float, float, float]') -> "'Path'"
```

Make a new path that is one closed rectangle with rounded corners.

| Argument | Meaning |
|---|---|
| `x`, `y` | the top left corner. |
| `w`, `h` | the width and the height. |
| `radii` | four corner radii: top left, top right, bottom right, bottom left. They must already be no more than half the shorter side. A radius of 0 gives a sharp corner. |

**Returns.** a new Path.

See also: [`rect`](#cls-Path-rect).

<a id="cls-Path-transformed"></a>
#### `Path.transformed`

```py
Path.transformed(t: 'Transform') -> "'Path'"
```

Make a new path with every point moved by a transform.

| Argument | Meaning |
|---|---|
| `t` | a Transform from funground.geometry, which turns a point (x, y) into (a*x + c*y + e, b*x + d*y + f). |

**Returns.** a new Path. It is this path itself when the transform changes nothing.

See also: [`bounds`](#cls-Path-bounds).

<a id="cls-Font"></a>
### `Font`

```py
Font(name: 'str') -> 'None'
```

A font that you can pass to f.text_font(), or ask questions about.

You get one from f.load_font(path) (a font file), f.system_font(name) (a font installed on this
computer) or f.current_font() (the font in use now). The font's name, which funground uses to find it,
is font.name: the file name, or the file name with ~2, ~3 and so on when two files share a name. A
font from a collection (.ttc) file has # and the face number after the file name.

Two fonts are equal when they have the same name.

```py
face = f.load_font("MyFont.ttf")   # your own file
f.text_font(face)
print(face.family(), face.style())
```

<a id="cls-Font-contains"></a>
#### `Font.contains`

```py
Font.contains(text: 'str') -> 'bool'
```

Whether the font has a shape for every character of some text.

Spaces count. A new line is ignored.

| Argument | Meaning |
|---|---|
| `text` | the text to check. |

**Returns.** True when every character has a shape in the font, otherwise False.

```py
if not f.current_font().contains("hello"):
    print("some letters are missing")
```

See also: [`features`](#cls-Font-features), [`family`](#cls-Font-family).

<a id="cls-Font-family"></a>
#### `Font.family`

```py
Font.family() -> 'str'
```

The family name of the font, as written in the font file.

**Returns.** the name, such as "DejaVu Sans".

```py
print(f.current_font().family())
```

See also: [`style`](#cls-Font-style), [`variations`](#cls-Font-variations), [`features`](#cls-Font-features).

<a id="cls-Font-features"></a>
#### `Font.features`

```py
Font.features() -> 'list[str]'
```

The OpenType features that the font has.

Use f.text_features() to turn one on or off.

**Returns.** a sorted list of four-letter tags, such as ["kern", "liga"].

```py
print(f.current_font().features())
```

See also: [`variations`](#cls-Font-variations), [`contains`](#cls-Font-contains).

<a id="cls-Font-style"></a>
#### `Font.style`

```py
Font.style() -> 'str'
```

The style name of the font, as written in the font file.

**Returns.** the name, such as "Bold" or "Book".

```py
print(f.current_font().style())
```

See also: [`family`](#cls-Font-family).

<a id="cls-Font-variations"></a>
#### `Font.variations`

```py
Font.variations() -> 'dict[str, tuple[float, float, float]]'
```

The axes of a variable font and how far each one can go.

An ordinary font has none. Use f.font_variations() to set an axis.

**Returns.** a dictionary from the axis tag, such as "wght", to (minimum, default, maximum). It is {} for a font that is not variable.

```py
for tag, (low, normal, high) in f.current_font().variations().items():
    print(tag, low, normal, high)
```

See also: [`features`](#cls-Font-features), [`family`](#cls-Font-family).

<a id="cls-Control"></a>
### `Control`

```py
Control(label: 'str | None') -> 'None'
```

What a slider, a checkbox and a button share: a label.

You do not make a Control yourself. Use f.create_slider(), f.create_checkbox() and f.create_button().
They sit in a panel below the canvas, in the order you made them. Make them in setup() and read them
in draw().

<a id="cls-Control-label"></a>
#### `Control.label`

```py
Control.label  # property
```

The text shown beside the control.

**Returns.** the label, or "" when it has none.

```py
box = f.create_checkbox("Show grid")
print(box.label)    # Show grid
```

See also: [`create_slider`](#fn-create_slider), [`create_checkbox`](#fn-create_checkbox), [`create_button`](#fn-create_button).

<a id="cls-Control-visible"></a>
#### `Control.visible`

```py
Control.visible(flag=<not given>)
```

Read whether the control is shown, or hide or show it.

A hidden control is not drawn and cannot be pressed, dragged or clicked. Its space in the panel stays
blank, so the panel keeps its height and nothing moves when you show it again. It keeps its value.
value(), checked() and clicked() still work while it is hidden. You can call visible() in draw().

| Argument | Meaning |
|---|---|
| `flag` | True to show the control, False to hide it. Leave it out to read. |

**Returns.** True or False when you leave flag out. None when you set it.

```py
size = f.create_slider(10, 100, 50)
size.visible(False)
print(size.visible())    # False
```

See also: `value`, `checked`, [`create_slider`](#fn-create_slider).

<a id="cls-Slider"></a>
### `Slider`

```py
Slider(low, high, value=None, step=None, label=None) -> 'None'
```

A control that holds a number between a low and a high end. You drag it in the panel below the canvas.

You get one from f.create_slider(low, high, value, step, label). Make it in setup(). In draw(), read
it with slider.value(). It starts at value, or at low if you give none. If you give a step, the value
moves in jumps of that size from low. Whole numbers in give whole numbers out, when low and step are
both whole.

```py
size_slider = f.create_slider(10, 200, 50, label="size")

def draw():
    f.circle(200, 200, size_slider.value())
```

<a id="cls-Slider-high"></a>
#### `Slider.high`

```py
Slider.high  # property
```

The largest value the slider can have.

**Returns.** the high end, as given.

See also: [`low`](#cls-Slider-low), [`step`](#cls-Slider-step).

<a id="cls-Slider-label"></a>
#### `Slider.label`

```py
Slider.label  # property
```

The text shown beside the control.

**Returns.** the label, or "" when it has none.

```py
box = f.create_checkbox("Show grid")
print(box.label)    # Show grid
```

See also: [`create_slider`](#fn-create_slider), [`create_checkbox`](#fn-create_checkbox), [`create_button`](#fn-create_button).

<a id="cls-Slider-low"></a>
#### `Slider.low`

```py
Slider.low  # property
```

The smallest value the slider can have.

**Returns.** the low end, as given.

See also: [`high`](#cls-Slider-high), [`step`](#cls-Slider-step).

<a id="cls-Slider-step"></a>
#### `Slider.step`

```py
Slider.step  # property
```

The size of each jump of the slider.

**Returns.** the step as given, or None when the slider moves smoothly.

See also: [`low`](#cls-Slider-low), [`high`](#cls-Slider-high).

<a id="cls-Slider-text"></a>
#### `Slider.text`

```py
Slider.text() -> 'str'
```

The value as the panel shows it.

**Returns.** the value as text. A step of 0.1 gives one decimal place.

```py
s = f.create_slider(0, 1, 0.5, 0.1)
print(s.text())    # 0.5
```

See also: [`value`](#cls-Slider-value).

<a id="cls-Slider-value"></a>
#### `Slider.value`

```py
Slider.value(v=<not given>)
```

Read the slider's number, or set it.

With no argument it reads the value. With a number it sets the value, which is kept between low and
high and rounded to the step. It changes in the panel too.

| Argument | Meaning |
|---|---|
| `v` | the new value. Leave it out to read the value. |

**Returns.** the value when you leave v out. None when you set it.

**Raises.**

- `TypeError`: if v is not a number.
- `ValueError`: if v is infinity or nan.

```py
s = f.create_slider(0, 1, 0.5)
print(s.value())    # 0.5
s.value(0.8)
```

See also: [`text`](#cls-Slider-text), [`low`](#cls-Slider-low), [`high`](#cls-Slider-high).

<a id="cls-Slider-visible"></a>
#### `Slider.visible`

```py
Slider.visible(flag=<not given>)
```

Read whether the control is shown, or hide or show it.

A hidden control is not drawn and cannot be pressed, dragged or clicked. Its space in the panel stays
blank, so the panel keeps its height and nothing moves when you show it again. It keeps its value.
value(), checked() and clicked() still work while it is hidden. You can call visible() in draw().

| Argument | Meaning |
|---|---|
| `flag` | True to show the control, False to hide it. Leave it out to read. |

**Returns.** True or False when you leave flag out. None when you set it.

```py
size = f.create_slider(10, 100, 50)
size.visible(False)
print(size.visible())    # False
```

See also: [`value`](#cls-Slider-value), `checked`, [`create_slider`](#fn-create_slider).

<a id="cls-Checkbox"></a>
### `Checkbox`

```py
Checkbox(label, checked=False) -> 'None'
```

A box that is ticked or not. You click it in the panel below the canvas.

You get one from f.create_checkbox(label, checked). Make it in setup(). In draw(), read it with
box.checked().

```py
grid = f.create_checkbox("Show grid", True)

def draw():
    if grid.checked():
        f.line(0, 200, 400, 200)
```

<a id="cls-Checkbox-checked"></a>
#### `Checkbox.checked`

```py
Checkbox.checked(b=<not given>)
```

Read whether the box is ticked, or tick or untick it.

| Argument | Meaning |
|---|---|
| `b` | True to tick it, False to untick it. Leave it out to read. |

**Returns.** True or False when you leave b out. None when you set it.

```py
box = f.create_checkbox("Fill", True)
if box.checked():
    box.checked(False)
```

See also: [`create_checkbox`](#fn-create_checkbox).

<a id="cls-Checkbox-label"></a>
#### `Checkbox.label`

```py
Checkbox.label  # property
```

The text shown beside the control.

**Returns.** the label, or "" when it has none.

```py
box = f.create_checkbox("Show grid")
print(box.label)    # Show grid
```

See also: [`create_slider`](#fn-create_slider), [`create_checkbox`](#fn-create_checkbox), [`create_button`](#fn-create_button).

<a id="cls-Checkbox-visible"></a>
#### `Checkbox.visible`

```py
Checkbox.visible(flag=<not given>)
```

Read whether the control is shown, or hide or show it.

A hidden control is not drawn and cannot be pressed, dragged or clicked. Its space in the panel stays
blank, so the panel keeps its height and nothing moves when you show it again. It keeps its value.
value(), checked() and clicked() still work while it is hidden. You can call visible() in draw().

| Argument | Meaning |
|---|---|
| `flag` | True to show the control, False to hide it. Leave it out to read. |

**Returns.** True or False when you leave flag out. None when you set it.

```py
size = f.create_slider(10, 100, 50)
size.visible(False)
print(size.visible())    # False
```

See also: `value`, [`checked`](#cls-Checkbox-checked), [`create_slider`](#fn-create_slider).

<a id="cls-Button"></a>
### `Button`

```py
Button(label) -> 'None'
```

A button that you click in the panel below the canvas.

You get one from f.create_button(label). Make it in setup(). In draw(), ask button.clicked(). It is True
once for each click.

```py
again = f.create_button("Again")

def draw():
    if again.clicked():
        f.background("white")
```

<a id="cls-Button-clicked"></a>
#### `Button.clicked`

```py
Button.clicked() -> 'bool'
```

Whether the button was clicked since you last asked.

It is True once for each click. Asking again straight away gives False.

**Returns.** True if there was a click since the last time you asked, otherwise False.

```py
if again.clicked():
    f.background("white")
```

See also: [`create_button`](#fn-create_button).

<a id="cls-Button-label"></a>
#### `Button.label`

```py
Button.label  # property
```

The text shown beside the control.

**Returns.** the label, or "" when it has none.

```py
box = f.create_checkbox("Show grid")
print(box.label)    # Show grid
```

See also: [`create_slider`](#fn-create_slider), [`create_checkbox`](#fn-create_checkbox), [`create_button`](#fn-create_button).

<a id="cls-Button-visible"></a>
#### `Button.visible`

```py
Button.visible(flag=<not given>)
```

Read whether the control is shown, or hide or show it.

A hidden control is not drawn and cannot be pressed, dragged or clicked. Its space in the panel stays
blank, so the panel keeps its height and nothing moves when you show it again. It keeps its value.
value(), checked() and clicked() still work while it is hidden. You can call visible() in draw().

| Argument | Meaning |
|---|---|
| `flag` | True to show the control, False to hide it. Leave it out to read. |

**Returns.** True or False when you leave flag out. None when you set it.

```py
size = f.create_slider(10, 100, 50)
size.visible(False)
print(size.visible())    # False
```

See also: `value`, `checked`, [`create_slider`](#fn-create_slider).

<a id="cls-Color"></a>
### `Color`

```py
Color(r: 'int', g: 'int', b: 'int', a: 'int' = 255) -> None
```

A colour, as red, green, blue and alpha numbers.

You get one from f.color(), f.hsb(), f.hsl(), f.lerp_color() and f.get(x, y). You can give it to
fill(), stroke(), background() and every other command that takes a colour. A colour cannot be
changed.

Read its parts as c.red, c.green, c.blue and c.alpha (each a whole number from 0 to 255), c.hue (0 to
360) and c.saturation, c.brightness and c.lightness (each 0 to 100). The short names c.r, c.g, c.b and
c.a are the same as red, green, blue and alpha.

```py
c = f.color("tomato")
print(c.red, c.green, c.blue)    # 255 99 71
f.fill(c)
```

<a id="cls-Color-alpha"></a>
#### `Color.alpha`

```py
Color.alpha  # property
```

How solid the colour is.

**Returns.** a whole number from 0 (see-through) to 255 (solid).

```py
print(f.color(255, 0, 0, 128).alpha)    # 128
```

See also: [`rgba`](#cls-Color-rgba).

<a id="cls-Color-blue"></a>
#### `Color.blue`

```py
Color.blue  # property
```

How much blue the colour has.

**Returns.** a whole number from 0 to 255.

```py
print(f.color("tomato").blue)
```

See also: [`red`](#cls-Color-red), [`green`](#cls-Color-green).

<a id="cls-Color-brightness"></a>
#### `Color.brightness`

```py
Color.brightness  # property
```

How bright the colour is, in the HSB way of measuring.

**Returns.** a number from 0 (black) to 100 (full brightness).

```py
print(f.color("red").brightness)    # 100.0
```

See also: [`hue`](#cls-Color-hue), [`saturation`](#cls-Color-saturation), [`lightness`](#cls-Color-lightness).

<a id="cls-Color-from_hsb"></a>
#### `Color.from_hsb`

```py
Color.from_hsb(h: 'float', s: 'float', b: 'float', a: 'float' = 255) -> "'Color'"
```

Make a colour from hue, saturation and brightness.

f.hsb() does the same, and is the one to use in a sketch.

| Argument | Meaning |
|---|---|
| `h` | the hue in degrees. It wraps round, so 370 is the same as 10. |
| `s` | the saturation, from 0 to 100. Numbers outside are cut off. |
| `b` | the brightness, from 0 to 100. Numbers outside are cut off. |
| `a` | the alpha, from 0 to 255. It is 255 at first. |

**Returns.** a new Color.

**Raises.**

- `ValueError`: if a value is not a number.

See also: [`from_hsl`](#cls-Color-from_hsl), [`hue`](#cls-Color-hue).

<a id="cls-Color-from_hsl"></a>
#### `Color.from_hsl`

```py
Color.from_hsl(h: 'float', s: 'float', l: 'float', a: 'float' = 255) -> "'Color'"
```

Make a colour from hue, saturation and lightness.

f.hsl() does the same, and is the one to use in a sketch.

| Argument | Meaning |
|---|---|
| `h` | the hue in degrees. It wraps round, so 370 is the same as 10. |
| `s` | the saturation, from 0 to 100. Numbers outside are cut off. |
| `l` | the lightness, from 0 to 100. Numbers outside are cut off. |
| `a` | the alpha, from 0 to 255. It is 255 at first. |

**Returns.** a new Color.

**Raises.**

- `ValueError`: if a value is not a number.

See also: [`from_hsb`](#cls-Color-from_hsb), [`lightness`](#cls-Color-lightness).

<a id="cls-Color-green"></a>
#### `Color.green`

```py
Color.green  # property
```

How much green the colour has.

**Returns.** a whole number from 0 to 255.

```py
print(f.color("tomato").green)
```

See also: [`red`](#cls-Color-red), [`blue`](#cls-Color-blue).

<a id="cls-Color-hue"></a>
#### `Color.hue`

```py
Color.hue  # property
```

The hue of the colour: its place on the colour wheel.

**Returns.** a number from 0 to 360. Red is 0, green is 120 and blue is 240.

```py
print(f.color("blue").hue)    # 240.0
```

See also: [`saturation`](#cls-Color-saturation), [`brightness`](#cls-Color-brightness), [`lightness`](#cls-Color-lightness).

<a id="cls-Color-lerp"></a>
#### `Color.lerp`

```py
Color.lerp(other: "'Color'", amount: 'float') -> "'Color'"
```

Make a colour that is part of the way from this colour to another.

f.lerp_color() does the same. It mixes red, green, blue and alpha.

| Argument | Meaning |
|---|---|
| `other` | the Color to mix towards. |
| `amount` | how much of the way to go, from 0 (this colour) to 1 (the other). Numbers outside are cut off. |

**Returns.** a new Color.

```py
mid = f.color("red").lerp(f.color("blue"), 0.5)
```

See also: [`from_hsb`](#cls-Color-from_hsb).

<a id="cls-Color-lightness"></a>
#### `Color.lightness`

```py
Color.lightness  # property
```

How light the colour is, in the HSL way of measuring.

**Returns.** a number from 0 (black) to 100 (white). A pure colour such as red is 50.

```py
print(f.color("red").lightness)    # 50.0
```

See also: [`brightness`](#cls-Color-brightness), [`hue`](#cls-Color-hue).

<a id="cls-Color-parse"></a>
#### `Color.parse`

```py
Color.parse(value: 'ColorLike') -> "'Color'"
```

Read a colour from any of the forms that funground accepts.

Every command that takes a colour uses it. You do not need to call it.

| Argument | Meaning |
|---|---|
| `value` | a name like "tomato", a hex string like "#FF6347", a tuple of 2, 3 or 4 numbers, one grey number, or another Color. |

**Returns.** a Color. If you give a Color, you get the same one back.

**Raises.**

- `ValueError`: if the colour is not understood, or a part is not from 0 to 255.
- `TypeError`: if the value is True or False.

See also: [`from_hsb`](#cls-Color-from_hsb), [`from_hsl`](#cls-Color-from_hsl).

<a id="cls-Color-red"></a>
#### `Color.red`

```py
Color.red  # property
```

How much red the colour has.

**Returns.** a whole number from 0 to 255.

```py
print(f.color("tomato").red)
```

See also: [`green`](#cls-Color-green), [`blue`](#cls-Color-blue).

<a id="cls-Color-rgb"></a>
#### `Color.rgb`

```py
Color.rgb  # property
```

The red, green and blue parts together.

**Returns.** a tuple (red, green, blue), each a whole number from 0 to 255.

```py
r, g, b = f.color("tomato").rgb
```

See also: [`rgba`](#cls-Color-rgba).

<a id="cls-Color-rgba"></a>
#### `Color.rgba`

```py
Color.rgba  # property
```

The red, green, blue and alpha parts together.

**Returns.** a tuple (red, green, blue, alpha), each a whole number from 0 to 255.

```py
print(f.color("tomato").rgba)    # (255, 99, 71, 255)
```

See also: [`rgb`](#cls-Color-rgb).

<a id="cls-Color-saturation"></a>
#### `Color.saturation`

```py
Color.saturation  # property
```

How strong the colour is, in the HSB way of measuring.

**Returns.** a number from 0 (grey) to 100 (the strongest colour).

```py
print(f.color("red").saturation)    # 100.0
```

See also: [`hue`](#cls-Color-hue), [`brightness`](#cls-Color-brightness).

<a id="cls-Gradient"></a>
### `Gradient`

```py
Gradient(kind: 'str', points: 'tuple[float, ...]', stops: 'tuple[tuple[float, Color], ...]') -> None
```

A blend of colours that you can use in place of a colour.

You get one from f.linear_gradient() (colours along a line) and f.radial_gradient() (colours outward
from a centre). Give it to fill(), stroke() or background(). It is read in the drawing space of the
moment you draw the shape, so it follows translate(), rotate() and scale() like the shape does. In a
PDF or SVG file it stays a true gradient.

A gradient cannot be changed. Its parts are kind ("linear" or "radial"), points (x1, y1, x2, y2 for a
linear gradient, and x, y, radius for a radial one) and stops (a tuple of (position, colour) pairs,
with positions from 0 to 1).

```py
sky = f.linear_gradient(0, 0, 0, 400, ["navy", "skyblue"])
f.background(sky)
```

<a id="cls-Raga"></a>
### `Raga`

```py
Raga(name: 'str', thaat: 'str', swaras: 'tuple[str, ...]', aroha: 'str', avaroha: 'str', pakad: 'str', vadi: 'str', samvadi: 'str', time: 'str', notes: 'str' = '', sources: 'tuple[str, ...]' = ()) -> None
```

One raga from funground's small table. It is read-only.

You get one from f.raga(name). Its parts are:
name: the raga's name.
thaat: the parent scale it belongs to.
swaras: the notes it uses, as a tuple of letters such as ("S", "R", "G"). Small r, g, d and n are komal (flat). M is tivra (sharp) Ma.
aroha: the way up, as a sargam string that f.melody(text, sa=...) can play.
avaroha: the way down, as a sargam string.
pakad: a phrase that marks the raga, as a sargam string.
vadi: the most important swara.
samvadi: the second most important swara.
time: the traditional time of day to perform it.
notes: where the sources differ, and other things to know. It may be empty.
sources: a tuple of texts that say where each fact was checked.

str(raga) gives a short summary. A raga is much more than its notes, and the table gives a start, not
the raga.

```py
yaman = f.raga("Yaman")
print(yaman.thaat, yaman.swaras)
f.melody(yaman.aroha, sa="D4").play()
```

<a id="cls-Tala"></a>
### `Tala`

```py
Tala(name: 'str', beats: 'int', vibhag: 'tuple[int, ...]', tali: 'tuple[int, ...]', khali: 'tuple[int, ...]', sam: 'int', bols: 'tuple[str, ...]', notes: 'str' = '', sources: 'tuple[str, ...]' = ()) -> None
```

One tala from funground's small table. It is read-only.

You get one from f.tala_info(name). Beats are counted from 1, so the sam is beat 1. Its parts are:
name: the tala's name.
beats: how many beats in one cycle.
vibhag: the divisions, as a tuple of beat counts such as (4, 4, 4, 4).
tali: the beat numbers that are claps.
khali: the beat numbers that are waves (the empty beats).
sam: the first beat, always 1.
bols: the theka, the drum syllables, one for each beat.
notes: where the sources differ, and other things to know. It may be empty.
sources: a tuple of texts that say where each fact was checked.

str(tala) gives a short summary. Use f.tala(name) to hear the theka.

```py
teentaal = f.tala_info("Teentaal")
print(teentaal.beats, teentaal.bols)
```

<a id="constants-and-reference-tables"></a>
## Constants and reference tables

Every table here is generated from the funground source, so it cannot drift from the code.

### Fixed words

| Where it is used | Accepted words |
|---|---|
| `f.blend_mode(mode)` | `normal`, `multiply`, `screen`, `overlay`, `darken`, `lighten`, `add`, `difference`, `exclusion`, `dodge`, `burn`, `hard_light`, `soft_light`, `hue`, `saturation`, `color`, `luminosity` |
| `f.stroke_cap(cap)` | `round`, `square`, `butt` |
| `f.stroke_join(join)` | `round`, `miter`, `bevel` |
| `f.text_align(horizontal, vertical)`, horizontal | `left`, `center`, `right` |
| `f.text_align(horizontal, vertical)`, vertical | `top`, `center`, `baseline`, `bottom` |
| `f.text_style(style)` | `normal`, `bold`, `italic`, `bold_italic` |
| `f.color_mode(mode)` | `rgb`, `hsb`, `hsl` |
| `f.cursor(kind)` | `arrow`, `cross`, `hand`, `move`, `text`, `wait` |
| `f.filter(kind)` | `threshold`, `gray`, `opaque`, `invert`, `blur`, `posterize`, `erode`, `dilate` |
| `f.save(path, text=...)`, text | `live`, `shapes` |
| Sound waves | `sine`, `square`, `saw`, `triangle`, `soft`, `noise` |

### Colour modes and ranges

The default range of each colour channel in each mode (first, second, third, alpha).

| Mode | First | Second | Third | Alpha |
|---|---|---|---|---|
| `rgb` | 255 | 255 | 255 | 255 |
| `hsb` | 360 | 100 | 100 | 1 |
| `hsl` | 360 | 100 | 100 | 1 |

### Keys and the mouse

`f.key` is a single character such as `"a"`, or one of these names. `f.mouse_button` is one of the buttons below.

| Kind | Names |
|---|---|
| Key names | `left`, `right`, `up`, `down`, `space`, `enter`, `escape` |
| Mouse buttons | `left`, `center`, `right` |
| Callbacks you can define | `mouse_pressed`, `mouse_released`, `mouse_moved`, `mouse_dragged`, `mouse_clicked`, `mouse_wheel`, `key_pressed`, `key_released`, `key_typed` |

### Page sizes

For `f.page_size(name)`, in points (1/72 inch). Any capitals are accepted.

| Name | Width | Height |
|---|---|---|
| `A3` | 842 | 1191 |
| `A4` | 595 | 842 |
| `A5` | 420 | 595 |
| `B5` | 499 | 709 |
| `Letter` | 612 | 792 |
| `Legal` | 612 | 1008 |
| `Tabloid` | 792 | 1224 |
| `Square` | 600 | 600 |

### Files

| Function | Formats |
|---|---|
| `f.save(path)` | `.png`, `.pdf`, `.svg` |
| `f.save_gif`, `f.save_movie` | `.gif`, `.mp4` |

### Notes, sargam and chords

- **Note names:** a letter from `CDEFGAB`, an optional `#` or `b`, then an octave number, such as `C4`, `F#3` or `Bb2`. The twelve names in an octave are `C`, `C#`, `D`, `D#`, `E`, `F`, `F#`, `G`, `G#`, `A`, `A#`, `B`.
- **Sargam** (for `sa=`): a swara letter, then `'` for each octave up or `,` for each octave down. Lower-case letters are komal, and capital `M` is tivra Ma. The swaras, with their just-intonation ratio above Sa, are:

| Swara | Ratio from Sa |
|---|---|
| `S` | 1 |
| `r` | 16/15 |
| `R` | 9/8 |
| `g` | 6/5 |
| `G` | 5/4 |
| `m` | 4/3 |
| `M` | 45/32 |
| `P` | 3/2 |
| `d` | 8/5 |
| `D` | 5/3 |
| `n` | 9/5 |
| `N` | 15/8 |

- **Chord names** (for `f.chord_notes`): a note name then a suffix. Suffixes and their semitones:

| Suffix | Semitones above the root |
|---|---|
| `(none)` | 0 4 7 |
| `m` | 0 3 7 |
| `dim` | 0 3 6 |
| `aug` | 0 4 8 |
| `7` | 0 4 7 10 |
| `maj7` | 0 4 7 11 |
| `m7` | 0 3 7 10 |

### Ragas

From `f.ragas()` and `f.raga(name)`. See the [ragas and talas chapter](../guide/17_ragas_and_talas.md).

| Name | Thaat | Time |
|---|---|---|
| Yaman | Kalyan | evening: the first prahar of the night, about 6 to 9 pm |
| Bhupali | Kalyan | evening: the first prahar of the night, about 6 to 9 pm |
| Bilawal | Bilawal | morning: the first prahar of the day, about 6 to 9 am |
| Khamaj | Khamaj | night: the second prahar, about 9 pm to midnight |
| Kafi | Kafi | night: the second prahar, about 9 pm to midnight |
| Bhairav | Bhairav | dawn: the first prahar of the day, about 6 to 9 am |
| Asavari | Asavari | late morning: the second prahar of the day, about 9 am to noon |
| Bhairavi | Bhairavi | morning: the first prahar of the day, about 6 to 9 am; by custom it ends a concert, at any hour |
| Todi | Todi | late morning: the second prahar of the day, about 9 am to noon |
| Marwa | Marwa | sunset: the end of the fourth prahar of the day, about 4 to 7 pm |
| Durga | Bilawal | night: the second prahar, about 9 pm to midnight |
| Desh | Khamaj | night: the second prahar, about 9 pm to midnight |
| Deshkar | Bilawal | morning: the first prahar of the day, about 6 to 9 am |

### Talas

From `f.talas()` and `f.tala_info(name)`.

| Name | Beats | Vibhag (divisions) |
|---|---|---|
| Teentaal | 16 | 4+4+4+4 |
| Ektaal | 12 | 2+2+2+2+2+2 |
| Jhaptaal | 10 | 2+3+2+3 |
| Rupak | 7 | 3+2+2 |
| Dadra | 6 | 3+3 |
| Keherwa | 8 | 4+4 |

### Bundled fonts

Files in `funground/fonts`, always available with no install.

| File | Used for |
|---|---|
| `DejaVuSans-Bold.ttf` | `f.text_style("bold")` |
| `DejaVuSans-BoldOblique.ttf` | `f.text_style("bold_italic")` |
| `DejaVuSans-Oblique.ttf` | `f.text_style("italic")` |
| `DejaVuSans.ttf` | `f.text_style("normal")` |
| `NotoEmoji-Regular.ttf` | fallback for letters the font lacks |
| `NotoSansDevanagari-Regular.ttf` | fallback for letters the font lacks |
| `NotoSansSymbols2-Regular.ttf` | fallback for letters the font lacks |

### Environment variables

| Variable | Meaning |
|---|---|
| `FUNGROUND_BACKING_SCALE` | Force the pixel-density scale of the window's backing store (a number). |
| `FUNGROUND_HEADLESS` | Set to 1, true or yes to run with no window (tests, servers, saving pictures). |
| `FUNGROUND_HIGHDPI` | Set to 1, true or yes to ask for a sharper window on a high-density screen. |
| `FUNGROUND_RENDERER` | Which drawing engine to use. Only `cairo` exists today, and it is the default. |
| `LOCALAPPDATA` | (see the source) |
| `SDL_AUDIODRIVER` | (see the source) |
| `SDL_VIDEODRIVER` | Read from pygame's own setting. `dummy` means no real window. |
| `WAYLAND_DISPLAY` | Read to detect a Wayland desktop on Linux. |
| `WINDIR` | (see the source) |

### Named colours

All 665 names accepted wherever a colour is expected, such as `f.fill("tomato")`, with their hex values.

| Name | Hex | Name | Hex | Name | Hex | Name | Hex |
|---|---|---|---|---|---|---|---|
| `aliceblue` | `#f0f8ff` | `antiquewhite` | `#faebd7` | `antiquewhite1` | `#ffefdb` | `antiquewhite2` | `#eedfcc` |
| `antiquewhite3` | `#cdc0b0` | `antiquewhite4` | `#8b8378` | `aqua` | `#00ffff` | `aquamarine` | `#7fffd4` |
| `aquamarine1` | `#7fffd4` | `aquamarine2` | `#76eec6` | `aquamarine3` | `#66cdaa` | `aquamarine4` | `#458b74` |
| `azure` | `#f0ffff` | `azure1` | `#f0ffff` | `azure2` | `#e0eeee` | `azure3` | `#c1cdcd` |
| `azure4` | `#838b8b` | `beige` | `#f5f5dc` | `bisque` | `#ffe4c4` | `bisque1` | `#ffe4c4` |
| `bisque2` | `#eed5b7` | `bisque3` | `#cdb79e` | `bisque4` | `#8b7d6b` | `black` | `#000000` |
| `blanchedalmond` | `#ffebcd` | `blue` | `#0000ff` | `blue1` | `#0000ff` | `blue2` | `#0000ee` |
| `blue3` | `#0000cd` | `blue4` | `#00008b` | `blueviolet` | `#8a2be2` | `brown` | `#a52a2a` |
| `brown1` | `#ff4040` | `brown2` | `#ee3b3b` | `brown3` | `#cd3333` | `brown4` | `#8b2323` |
| `burlywood` | `#deb887` | `burlywood1` | `#ffd39b` | `burlywood2` | `#eec591` | `burlywood3` | `#cdaa7d` |
| `burlywood4` | `#8b7355` | `cadetblue` | `#5f9ea0` | `cadetblue1` | `#98f5ff` | `cadetblue2` | `#8ee5ee` |
| `cadetblue3` | `#7ac5cd` | `cadetblue4` | `#53868b` | `chartreuse` | `#7fff00` | `chartreuse1` | `#7fff00` |
| `chartreuse2` | `#76ee00` | `chartreuse3` | `#66cd00` | `chartreuse4` | `#458b00` | `chocolate` | `#d2691e` |
| `chocolate1` | `#ff7f24` | `chocolate2` | `#ee7621` | `chocolate3` | `#cd661d` | `chocolate4` | `#8b4513` |
| `coral` | `#ff7f50` | `coral1` | `#ff7256` | `coral2` | `#ee6a50` | `coral3` | `#cd5b45` |
| `coral4` | `#8b3e2f` | `cornflowerblue` | `#6495ed` | `cornsilk` | `#fff8dc` | `cornsilk1` | `#fff8dc` |
| `cornsilk2` | `#eee8cd` | `cornsilk3` | `#cdc8b1` | `cornsilk4` | `#8b8878` | `crimson` | `#dc143c` |
| `cyan` | `#00ffff` | `cyan1` | `#00ffff` | `cyan2` | `#00eeee` | `cyan3` | `#00cdcd` |
| `cyan4` | `#008b8b` | `darkblue` | `#00008b` | `darkcyan` | `#008b8b` | `darkgoldenrod` | `#b8860b` |
| `darkgoldenrod1` | `#ffb90f` | `darkgoldenrod2` | `#eead0e` | `darkgoldenrod3` | `#cd950c` | `darkgoldenrod4` | `#8b6508` |
| `darkgray` | `#a9a9a9` | `darkgreen` | `#006400` | `darkgrey` | `#a9a9a9` | `darkkhaki` | `#bdb76b` |
| `darkmagenta` | `#8b008b` | `darkolivegreen` | `#556b2f` | `darkolivegreen1` | `#caff70` | `darkolivegreen2` | `#bcee68` |
| `darkolivegreen3` | `#a2cd5a` | `darkolivegreen4` | `#6e8b3d` | `darkorange` | `#ff8c00` | `darkorange1` | `#ff7f00` |
| `darkorange2` | `#ee7600` | `darkorange3` | `#cd6600` | `darkorange4` | `#8b4500` | `darkorchid` | `#9932cc` |
| `darkorchid1` | `#bf3eff` | `darkorchid2` | `#b23aee` | `darkorchid3` | `#9a32cd` | `darkorchid4` | `#68228b` |
| `darkred` | `#8b0000` | `darksalmon` | `#e9967a` | `darkseagreen` | `#8fbc8f` | `darkseagreen1` | `#c1ffc1` |
| `darkseagreen2` | `#b4eeb4` | `darkseagreen3` | `#9bcd9b` | `darkseagreen4` | `#698b69` | `darkslateblue` | `#483d8b` |
| `darkslategray` | `#2f4f4f` | `darkslategray1` | `#97ffff` | `darkslategray2` | `#8deeee` | `darkslategray3` | `#79cdcd` |
| `darkslategray4` | `#528b8b` | `darkslategrey` | `#2f4f4f` | `darkturquoise` | `#00ced1` | `darkviolet` | `#9400d3` |
| `deeppink` | `#ff1493` | `deeppink1` | `#ff1493` | `deeppink2` | `#ee1289` | `deeppink3` | `#cd1076` |
| `deeppink4` | `#8b0a50` | `deepskyblue` | `#00bfff` | `deepskyblue1` | `#00bfff` | `deepskyblue2` | `#00b2ee` |
| `deepskyblue3` | `#009acd` | `deepskyblue4` | `#00688b` | `dimgray` | `#696969` | `dimgrey` | `#696969` |
| `dodgerblue` | `#1e90ff` | `dodgerblue1` | `#1e90ff` | `dodgerblue2` | `#1c86ee` | `dodgerblue3` | `#1874cd` |
| `dodgerblue4` | `#104e8b` | `firebrick` | `#b22222` | `firebrick1` | `#ff3030` | `firebrick2` | `#ee2c2c` |
| `firebrick3` | `#cd2626` | `firebrick4` | `#8b1a1a` | `floralwhite` | `#fffaf0` | `forestgreen` | `#228b22` |
| `fuchsia` | `#ff00ff` | `gainsboro` | `#dcdcdc` | `ghostwhite` | `#f8f8ff` | `gold` | `#ffd700` |
| `gold1` | `#ffd700` | `gold2` | `#eec900` | `gold3` | `#cdad00` | `gold4` | `#8b7500` |
| `goldenrod` | `#daa520` | `goldenrod1` | `#ffc125` | `goldenrod2` | `#eeb422` | `goldenrod3` | `#cd9b1d` |
| `goldenrod4` | `#8b6914` | `gray` | `#bebebe` | `gray0` | `#000000` | `gray1` | `#030303` |
| `gray10` | `#1a1a1a` | `gray100` | `#ffffff` | `gray11` | `#1c1c1c` | `gray12` | `#1f1f1f` |
| `gray13` | `#212121` | `gray14` | `#242424` | `gray15` | `#262626` | `gray16` | `#292929` |
| `gray17` | `#2b2b2b` | `gray18` | `#2e2e2e` | `gray19` | `#303030` | `gray2` | `#050505` |
| `gray20` | `#333333` | `gray21` | `#363636` | `gray22` | `#383838` | `gray23` | `#3b3b3b` |
| `gray24` | `#3d3d3d` | `gray25` | `#404040` | `gray26` | `#424242` | `gray27` | `#454545` |
| `gray28` | `#474747` | `gray29` | `#4a4a4a` | `gray3` | `#080808` | `gray30` | `#4d4d4d` |
| `gray31` | `#4f4f4f` | `gray32` | `#525252` | `gray33` | `#545454` | `gray34` | `#575757` |
| `gray35` | `#595959` | `gray36` | `#5c5c5c` | `gray37` | `#5e5e5e` | `gray38` | `#616161` |
| `gray39` | `#636363` | `gray4` | `#0a0a0a` | `gray40` | `#666666` | `gray41` | `#696969` |
| `gray42` | `#6b6b6b` | `gray43` | `#6e6e6e` | `gray44` | `#707070` | `gray45` | `#737373` |
| `gray46` | `#757575` | `gray47` | `#787878` | `gray48` | `#7a7a7a` | `gray49` | `#7d7d7d` |
| `gray5` | `#0d0d0d` | `gray50` | `#7f7f7f` | `gray51` | `#828282` | `gray52` | `#858585` |
| `gray53` | `#878787` | `gray54` | `#8a8a8a` | `gray55` | `#8c8c8c` | `gray56` | `#8f8f8f` |
| `gray57` | `#919191` | `gray58` | `#949494` | `gray59` | `#969696` | `gray6` | `#0f0f0f` |
| `gray60` | `#999999` | `gray61` | `#9c9c9c` | `gray62` | `#9e9e9e` | `gray63` | `#a1a1a1` |
| `gray64` | `#a3a3a3` | `gray65` | `#a6a6a6` | `gray66` | `#a8a8a8` | `gray67` | `#ababab` |
| `gray68` | `#adadad` | `gray69` | `#b0b0b0` | `gray7` | `#121212` | `gray70` | `#b3b3b3` |
| `gray71` | `#b5b5b5` | `gray72` | `#b8b8b8` | `gray73` | `#bababa` | `gray74` | `#bdbdbd` |
| `gray75` | `#bfbfbf` | `gray76` | `#c2c2c2` | `gray77` | `#c4c4c4` | `gray78` | `#c7c7c7` |
| `gray79` | `#c9c9c9` | `gray8` | `#141414` | `gray80` | `#cccccc` | `gray81` | `#cfcfcf` |
| `gray82` | `#d1d1d1` | `gray83` | `#d4d4d4` | `gray84` | `#d6d6d6` | `gray85` | `#d9d9d9` |
| `gray86` | `#dbdbdb` | `gray87` | `#dedede` | `gray88` | `#e0e0e0` | `gray89` | `#e3e3e3` |
| `gray9` | `#171717` | `gray90` | `#e5e5e5` | `gray91` | `#e8e8e8` | `gray92` | `#ebebeb` |
| `gray93` | `#ededed` | `gray94` | `#f0f0f0` | `gray95` | `#f2f2f2` | `gray96` | `#f5f5f5` |
| `gray97` | `#f7f7f7` | `gray98` | `#fafafa` | `gray99` | `#fcfcfc` | `green` | `#00ff00` |
| `green1` | `#00ff00` | `green2` | `#00ee00` | `green3` | `#00cd00` | `green4` | `#008b00` |
| `greenyellow` | `#adff2f` | `grey` | `#bebebe` | `grey0` | `#000000` | `grey1` | `#030303` |
| `grey10` | `#1a1a1a` | `grey100` | `#ffffff` | `grey11` | `#1c1c1c` | `grey12` | `#1f1f1f` |
| `grey13` | `#212121` | `grey14` | `#242424` | `grey15` | `#262626` | `grey16` | `#292929` |
| `grey17` | `#2b2b2b` | `grey18` | `#2e2e2e` | `grey19` | `#303030` | `grey2` | `#050505` |
| `grey20` | `#333333` | `grey21` | `#363636` | `grey22` | `#383838` | `grey23` | `#3b3b3b` |
| `grey24` | `#3d3d3d` | `grey25` | `#404040` | `grey26` | `#424242` | `grey27` | `#454545` |
| `grey28` | `#474747` | `grey29` | `#4a4a4a` | `grey3` | `#080808` | `grey30` | `#4d4d4d` |
| `grey31` | `#4f4f4f` | `grey32` | `#525252` | `grey33` | `#545454` | `grey34` | `#575757` |
| `grey35` | `#595959` | `grey36` | `#5c5c5c` | `grey37` | `#5e5e5e` | `grey38` | `#616161` |
| `grey39` | `#636363` | `grey4` | `#0a0a0a` | `grey40` | `#666666` | `grey41` | `#696969` |
| `grey42` | `#6b6b6b` | `grey43` | `#6e6e6e` | `grey44` | `#707070` | `grey45` | `#737373` |
| `grey46` | `#757575` | `grey47` | `#787878` | `grey48` | `#7a7a7a` | `grey49` | `#7d7d7d` |
| `grey5` | `#0d0d0d` | `grey50` | `#7f7f7f` | `grey51` | `#828282` | `grey52` | `#858585` |
| `grey53` | `#878787` | `grey54` | `#8a8a8a` | `grey55` | `#8c8c8c` | `grey56` | `#8f8f8f` |
| `grey57` | `#919191` | `grey58` | `#949494` | `grey59` | `#969696` | `grey6` | `#0f0f0f` |
| `grey60` | `#999999` | `grey61` | `#9c9c9c` | `grey62` | `#9e9e9e` | `grey63` | `#a1a1a1` |
| `grey64` | `#a3a3a3` | `grey65` | `#a6a6a6` | `grey66` | `#a8a8a8` | `grey67` | `#ababab` |
| `grey68` | `#adadad` | `grey69` | `#b0b0b0` | `grey7` | `#121212` | `grey70` | `#b3b3b3` |
| `grey71` | `#b5b5b5` | `grey72` | `#b8b8b8` | `grey73` | `#bababa` | `grey74` | `#bdbdbd` |
| `grey75` | `#bfbfbf` | `grey76` | `#c2c2c2` | `grey77` | `#c4c4c4` | `grey78` | `#c7c7c7` |
| `grey79` | `#c9c9c9` | `grey8` | `#141414` | `grey80` | `#cccccc` | `grey81` | `#cfcfcf` |
| `grey82` | `#d1d1d1` | `grey83` | `#d4d4d4` | `grey84` | `#d6d6d6` | `grey85` | `#d9d9d9` |
| `grey86` | `#dbdbdb` | `grey87` | `#dedede` | `grey88` | `#e0e0e0` | `grey89` | `#e3e3e3` |
| `grey9` | `#171717` | `grey90` | `#e5e5e5` | `grey91` | `#e8e8e8` | `grey92` | `#ebebeb` |
| `grey93` | `#ededed` | `grey94` | `#f0f0f0` | `grey95` | `#f2f2f2` | `grey96` | `#f5f5f5` |
| `grey97` | `#f7f7f7` | `grey98` | `#fafafa` | `grey99` | `#fcfcfc` | `honeydew` | `#f0fff0` |
| `honeydew1` | `#f0fff0` | `honeydew2` | `#e0eee0` | `honeydew3` | `#c1cdc1` | `honeydew4` | `#838b83` |
| `hotpink` | `#ff69b4` | `hotpink1` | `#ff6eb4` | `hotpink2` | `#ee6aa7` | `hotpink3` | `#cd6090` |
| `hotpink4` | `#8b3a62` | `indianred` | `#cd5c5c` | `indianred1` | `#ff6a6a` | `indianred2` | `#ee6363` |
| `indianred3` | `#cd5555` | `indianred4` | `#8b3a3a` | `indigo` | `#4b0082` | `ivory` | `#fffff0` |
| `ivory1` | `#fffff0` | `ivory2` | `#eeeee0` | `ivory3` | `#cdcdc1` | `ivory4` | `#8b8b83` |
| `khaki` | `#f0e68c` | `khaki1` | `#fff68f` | `khaki2` | `#eee685` | `khaki3` | `#cdc673` |
| `khaki4` | `#8b864e` | `lavender` | `#e6e6fa` | `lavenderblush` | `#fff0f5` | `lavenderblush1` | `#fff0f5` |
| `lavenderblush2` | `#eee0e5` | `lavenderblush3` | `#cdc1c5` | `lavenderblush4` | `#8b8386` | `lawngreen` | `#7cfc00` |
| `lemonchiffon` | `#fffacd` | `lemonchiffon1` | `#fffacd` | `lemonchiffon2` | `#eee9bf` | `lemonchiffon3` | `#cdc9a5` |
| `lemonchiffon4` | `#8b8970` | `lightblue` | `#add8e6` | `lightblue1` | `#bfefff` | `lightblue2` | `#b2dfee` |
| `lightblue3` | `#9ac0cd` | `lightblue4` | `#68838b` | `lightcoral` | `#f08080` | `lightcyan` | `#e0ffff` |
| `lightcyan1` | `#e0ffff` | `lightcyan2` | `#d1eeee` | `lightcyan3` | `#b4cdcd` | `lightcyan4` | `#7a8b8b` |
| `lightgoldenrod` | `#eedd82` | `lightgoldenrod1` | `#ffec8b` | `lightgoldenrod2` | `#eedc82` | `lightgoldenrod3` | `#cdbe70` |
| `lightgoldenrod4` | `#8b814c` | `lightgoldenrodyellow` | `#fafad2` | `lightgray` | `#d3d3d3` | `lightgreen` | `#90ee90` |
| `lightgrey` | `#d3d3d3` | `lightpink` | `#ffb6c1` | `lightpink1` | `#ffaeb9` | `lightpink2` | `#eea2ad` |
| `lightpink3` | `#cd8c95` | `lightpink4` | `#8b5f65` | `lightsalmon` | `#ffa07a` | `lightsalmon1` | `#ffa07a` |
| `lightsalmon2` | `#ee9572` | `lightsalmon3` | `#cd8162` | `lightsalmon4` | `#8b5742` | `lightseagreen` | `#20b2aa` |
| `lightskyblue` | `#87cefa` | `lightskyblue1` | `#b0e2ff` | `lightskyblue2` | `#a4d3ee` | `lightskyblue3` | `#8db6cd` |
| `lightskyblue4` | `#607b8b` | `lightslateblue` | `#8470ff` | `lightslategray` | `#778899` | `lightslategrey` | `#778899` |
| `lightsteelblue` | `#b0c4de` | `lightsteelblue1` | `#cae1ff` | `lightsteelblue2` | `#bcd2ee` | `lightsteelblue3` | `#a2b5cd` |
| `lightsteelblue4` | `#6e7b8b` | `lightyellow` | `#ffffe0` | `lightyellow1` | `#ffffe0` | `lightyellow2` | `#eeeed1` |
| `lightyellow3` | `#cdcdb4` | `lightyellow4` | `#8b8b7a` | `lime` | `#00ff00` | `limegreen` | `#32cd32` |
| `linen` | `#faf0e6` | `magenta` | `#ff00ff` | `magenta1` | `#ff00ff` | `magenta2` | `#ee00ee` |
| `magenta3` | `#cd00cd` | `magenta4` | `#8b008b` | `maroon` | `#b03060` | `maroon1` | `#ff34b3` |
| `maroon2` | `#ee30a7` | `maroon3` | `#cd2990` | `maroon4` | `#8b1c62` | `mediumaquamarine` | `#66cdaa` |
| `mediumblue` | `#0000cd` | `mediumorchid` | `#ba55d3` | `mediumorchid1` | `#e066ff` | `mediumorchid2` | `#d15fee` |
| `mediumorchid3` | `#b452cd` | `mediumorchid4` | `#7a378b` | `mediumpurple` | `#9370db` | `mediumpurple1` | `#ab82ff` |
| `mediumpurple2` | `#9f79ee` | `mediumpurple3` | `#8968cd` | `mediumpurple4` | `#5d478b` | `mediumseagreen` | `#3cb371` |
| `mediumslateblue` | `#7b68ee` | `mediumspringgreen` | `#00fa9a` | `mediumturquoise` | `#48d1cc` | `mediumvioletred` | `#c71585` |
| `midnightblue` | `#191970` | `mintcream` | `#f5fffa` | `mistyrose` | `#ffe4e1` | `mistyrose1` | `#ffe4e1` |
| `mistyrose2` | `#eed5d2` | `mistyrose3` | `#cdb7b5` | `mistyrose4` | `#8b7d7b` | `moccasin` | `#ffe4b5` |
| `navajowhite` | `#ffdead` | `navajowhite1` | `#ffdead` | `navajowhite2` | `#eecfa1` | `navajowhite3` | `#cdb38b` |
| `navajowhite4` | `#8b795e` | `navy` | `#000080` | `navyblue` | `#000080` | `oldlace` | `#fdf5e6` |
| `olive` | `#808000` | `olivedrab` | `#6b8e23` | `olivedrab1` | `#c0ff3e` | `olivedrab2` | `#b3ee3a` |
| `olivedrab3` | `#9acd32` | `olivedrab4` | `#698b22` | `orange` | `#ffa500` | `orange1` | `#ffa500` |
| `orange2` | `#ee9a00` | `orange3` | `#cd8500` | `orange4` | `#8b5a00` | `orangered` | `#ff4500` |
| `orangered1` | `#ff4500` | `orangered2` | `#ee4000` | `orangered3` | `#cd3700` | `orangered4` | `#8b2500` |
| `orchid` | `#da70d6` | `orchid1` | `#ff83fa` | `orchid2` | `#ee7ae9` | `orchid3` | `#cd69c9` |
| `orchid4` | `#8b4789` | `palegoldenrod` | `#eee8aa` | `palegreen` | `#98fb98` | `palegreen1` | `#9aff9a` |
| `palegreen2` | `#90ee90` | `palegreen3` | `#7ccd7c` | `palegreen4` | `#548b54` | `paleturquoise` | `#afeeee` |
| `paleturquoise1` | `#bbffff` | `paleturquoise2` | `#aeeeee` | `paleturquoise3` | `#96cdcd` | `paleturquoise4` | `#668b8b` |
| `palevioletred` | `#db7093` | `palevioletred1` | `#ff82ab` | `palevioletred2` | `#ee799f` | `palevioletred3` | `#cd6889` |
| `palevioletred4` | `#8b475d` | `papayawhip` | `#ffefd5` | `peachpuff` | `#ffdab9` | `peachpuff1` | `#ffdab9` |
| `peachpuff2` | `#eecbad` | `peachpuff3` | `#cdaf95` | `peachpuff4` | `#8b7765` | `peru` | `#cd853f` |
| `pink` | `#ffc0cb` | `pink1` | `#ffb5c5` | `pink2` | `#eea9b8` | `pink3` | `#cd919e` |
| `pink4` | `#8b636c` | `plum` | `#dda0dd` | `plum1` | `#ffbbff` | `plum2` | `#eeaeee` |
| `plum3` | `#cd96cd` | `plum4` | `#8b668b` | `powderblue` | `#b0e0e6` | `purple` | `#a020f0` |
| `purple1` | `#9b30ff` | `purple2` | `#912cee` | `purple3` | `#7d26cd` | `purple4` | `#551a8b` |
| `red` | `#ff0000` | `red1` | `#ff0000` | `red2` | `#ee0000` | `red3` | `#cd0000` |
| `red4` | `#8b0000` | `rosybrown` | `#bc8f8f` | `rosybrown1` | `#ffc1c1` | `rosybrown2` | `#eeb4b4` |
| `rosybrown3` | `#cd9b9b` | `rosybrown4` | `#8b6969` | `royalblue` | `#4169e1` | `royalblue1` | `#4876ff` |
| `royalblue2` | `#436eee` | `royalblue3` | `#3a5fcd` | `royalblue4` | `#27408b` | `saddlebrown` | `#8b4513` |
| `salmon` | `#fa8072` | `salmon1` | `#ff8c69` | `salmon2` | `#ee8262` | `salmon3` | `#cd7054` |
| `salmon4` | `#8b4c39` | `sandybrown` | `#f4a460` | `seagreen` | `#2e8b57` | `seagreen1` | `#54ff9f` |
| `seagreen2` | `#4eee94` | `seagreen3` | `#43cd80` | `seagreen4` | `#2e8b57` | `seashell` | `#fff5ee` |
| `seashell1` | `#fff5ee` | `seashell2` | `#eee5de` | `seashell3` | `#cdc5bf` | `seashell4` | `#8b8682` |
| `sienna` | `#a0522d` | `sienna1` | `#ff8247` | `sienna2` | `#ee7942` | `sienna3` | `#cd6839` |
| `sienna4` | `#8b4726` | `silver` | `#c0c0c0` | `skyblue` | `#87ceeb` | `skyblue1` | `#87ceff` |
| `skyblue2` | `#7ec0ee` | `skyblue3` | `#6ca6cd` | `skyblue4` | `#4a708b` | `slateblue` | `#6a5acd` |
| `slateblue1` | `#836fff` | `slateblue2` | `#7a67ee` | `slateblue3` | `#6959cd` | `slateblue4` | `#473c8b` |
| `slategray` | `#708090` | `slategray1` | `#c6e2ff` | `slategray2` | `#b9d3ee` | `slategray3` | `#9fb6cd` |
| `slategray4` | `#6c7b8b` | `slategrey` | `#708090` | `snow` | `#fffafa` | `snow1` | `#fffafa` |
| `snow2` | `#eee9e9` | `snow3` | `#cdc9c9` | `snow4` | `#8b8989` | `springgreen` | `#00ff7f` |
| `springgreen1` | `#00ff7f` | `springgreen2` | `#00ee76` | `springgreen3` | `#00cd66` | `springgreen4` | `#008b45` |
| `steelblue` | `#4682b4` | `steelblue1` | `#63b8ff` | `steelblue2` | `#5cacee` | `steelblue3` | `#4f94cd` |
| `steelblue4` | `#36648b` | `tan` | `#d2b48c` | `tan1` | `#ffa54f` | `tan2` | `#ee9a49` |
| `tan3` | `#cd853f` | `tan4` | `#8b5a2b` | `teal` | `#008080` | `thistle` | `#d8bfd8` |
| `thistle1` | `#ffe1ff` | `thistle2` | `#eed2ee` | `thistle3` | `#cdb5cd` | `thistle4` | `#8b7b8b` |
| `tomato` | `#ff6347` | `tomato1` | `#ff6347` | `tomato2` | `#ee5c42` | `tomato3` | `#cd4f39` |
| `tomato4` | `#8b3626` | `turquoise` | `#40e0d0` | `turquoise1` | `#00f5ff` | `turquoise2` | `#00e5ee` |
| `turquoise3` | `#00c5cd` | `turquoise4` | `#00868b` | `violet` | `#ee82ee` | `violetred` | `#d02090` |
| `violetred1` | `#ff3e96` | `violetred2` | `#ee3a8c` | `violetred3` | `#cd3278` | `violetred4` | `#8b2252` |
| `wheat` | `#f5deb3` | `wheat1` | `#ffe7ba` | `wheat2` | `#eed8ae` | `wheat3` | `#cdba96` |
| `wheat4` | `#8b7e66` | `white` | `#ffffff` | `whitesmoke` | `#f5f5f5` | `yellow` | `#ffff00` |
| `yellow1` | `#ffff00` | `yellow2` | `#eeee00` | `yellow3` | `#cdcd00` | `yellow4` | `#8b8b00` |
| `yellowgreen` | `#9acd32` |  |  |  |  |  |  |
