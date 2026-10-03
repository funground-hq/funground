# funground Examples Gallery

Every picture below is made by running the example beside it — `python tools/make_gallery.py`
regenerates them. Each example is a complete sketch: copy it into a file and run it.

Browse these examples interactively: `python -m funground.gallery`

Short on time? See the [showcase](SHOWCASE.md): a dozen of the best pictures on one page.

## Basics

### Your first sketch

![Your first sketch](images/basics-01_first_sketch.png)

A window, a background and one circle: the three lines every sketch starts from.

Source: [`examples/gallery/basics/01_first_sketch.py`](../../examples/gallery/basics/01_first_sketch.py)

### setup() once, draw() every frame

![setup() once, draw() every frame](images/basics-02_setup_and_draw.png)

setup() runs once; draw() runs again and again. f.frame_count counts the frames, f.width and f.height are the window size, and f.stop() ends the sketch.

Source: [`examples/gallery/basics/02_setup_and_draw.py`](../../examples/gallery/basics/02_setup_and_draw.py)

### A script: draw once, no draw() needed

![A script: draw once, no draw() needed](images/basics-03_a_script.png)

Not every picture moves. A script has no functions: f.size() makes the canvas, the lines after it draw on it, f.save() writes a file at once, and f.show() opens a window to look at it.

Source: [`examples/gallery/basics/03_a_script.py`](../../examples/gallery/basics/03_a_script.py)

## Shapes

### The basic shapes

![The basic shapes](images/shapes-01_basic_shapes.png)

rect is placed by its top-left corner; circle and ellipse by their centre. line joins two points; point is a dot in the stroke colour.

Source: [`examples/gallery/shapes/01_basic_shapes.py`](../../examples/gallery/shapes/01_basic_shapes.py)

### More shapes

![More shapes](images/shapes-02_more_shapes.png)

square, triangle, quad and polygon for straight-sided shapes; arc for part of an ellipse, with angles in degrees turning clockwise from the right, in three modes: open, chord and pie.

Source: [`examples/gallery/shapes/02_more_shapes.py`](../../examples/gallery/shapes/02_more_shapes.py)

### Placing shapes by their centre or corners

![Placing shapes by their centre or corners](images/shapes-03_modes.png)

The same four numbers, drawn under each drawing mode. The red dot marks (x, y) in every box. rect_mode and ellipse_mode have four modes each. image_mode has three.

Source: [`examples/gallery/shapes/03_modes.py`](../../examples/gallery/shapes/03_modes.py)

### Rounded corners

![Rounded corners](images/shapes-04_rounded.png)

Give rect() or square() one more number and every corner is rounded by that radius. Give it four numbers and each corner gets its own radius. They go clockwise, starting at the top left. A radius that is too big is cut down to fit.

Source: [`examples/gallery/shapes/04_rounded.py`](../../examples/gallery/shapes/04_rounded.py)

## Colour

### Four ways to say a colour

![Four ways to say a colour](images/colour-01_colour_forms.png)

A name, an (r, g, b) tuple from 0 to 255, a hex string, or an (r, g, b, a) tuple whose last number is the opacity. Overlapping translucent circles mix.

Source: [`examples/gallery/colour/01_colour_forms.py`](../../examples/gallery/colour/01_colour_forms.py)

### Hue-based colour: hsb, hsl and colour objects

![Hue-based colour: hsb, hsl and colour objects](images/colour-02_hsb_and_hsl.png)

f.hsb(hue, saturation, brightness) and f.hsl(hue, saturation, lightness) make colours by hue: 0 red, 120 green, 240 blue, and around again. By default a tuple means red, green, blue. f.color() makes a colour you can read (.hue, .brightness ...), and lerp_color mixes two colours.

Source: [`examples/gallery/colour/02_hsb_and_hsl.py`](../../examples/gallery/colour/02_hsb_and_hsl.py)

### Gradients

![Gradients](images/colour-03_gradients.png)

f.linear_gradient() blends colours along a line; f.radial_gradient() blends them outward from a centre. Either can be used wherever a colour goes - fill, stroke or background - and it follows f.translate() and f.rotate() like any shape. Saved as PDF or SVG, it stays smooth.

Source: [`examples/gallery/colour/03_gradients.py`](../../examples/gallery/colour/03_gradients.py)

### Colour mode

![Colour mode](images/colour-04_color_mode.png)

f.color_mode() changes how a tuple of numbers is read as a colour. In "hsb" mode the three numbers are hue, saturation and brightness. In "rgb" mode with a range of 1, red, green and blue run from 0 to 1 instead of 0 to 255. Names like "tomato" and hex strings like "#FF6347" are not changed. Each mode remembers its own ranges.

Source: [`examples/gallery/colour/04_color_mode.py`](../../examples/gallery/colour/04_color_mode.py)

## Blending, opacity and shadows

### Blend modes, opacity and shadows

![Blend modes, opacity and shadows](images/compositing-01_blend_opacity_shadow.png)

f.blend_mode() changes how new drawing mixes with what is already on the canvas: "multiply" darkens like overlapping inks, "screen" lightens like overlapping lights. f.opacity() makes everything after it see-through, and f.shadow() gives it a soft shadow.

Source: [`examples/gallery/compositing/01_blend_opacity_shadow.py`](../../examples/gallery/compositing/01_blend_opacity_shadow.py)

### Off-screen graphics: a trail

![Off-screen graphics: a trail](images/compositing-02_graphics.png)

f.create_graphics() makes a picture: an off-screen canvas with the same drawing commands as the window. Painting a translucent rectangle over it every frame, instead of clearing it, makes older drawing fade instead of vanish - a comet trail, the same trick Processing's PGraphics is used for. f.image() then places the picture wherever you like, at any size.

Source: [`examples/gallery/compositing/02_graphics.py`](../../examples/gallery/compositing/02_graphics.py)

### Scratch card: erasing

![Scratch card: erasing](images/compositing-03_scratch_card.png)

After f.erase(), everything you draw removes what is under it instead of painting. Here a grey "foil" picture covers a prize. Wavy scratch marks erase the foil, so the prize shows through the holes. Strength 255 removes the foil completely. A smaller number, like 90, only thins it. f.no_erase() goes back to normal painting.

Source: [`examples/gallery/compositing/03_scratch_card.py`](../../examples/gallery/compositing/03_scratch_card.py)

### Layers: a sky that stays and a trail that builds up

![Layers: a sky that stays and a trail that builds up](images/compositing-04_layers.png)

`with f.layer("name"):` sends everything drawn inside the block to a see-through layer that sits over the canvas. A layer keeps its drawing from one frame to the next. Here the canvas is wiped and redrawn every frame, yet the "trail" layer keeps every dot the ball leaves behind. The "sky" layer is drawn once, in the first frame, and never again. hide_layer() and show_layer() switch it off and on; it keeps its stars while it is hidden.

Source: [`examples/gallery/compositing/04_layers.py`](../../examples/gallery/compositing/04_layers.py)

## Fill, stroke and lines

### Fill and stroke

![Fill and stroke](images/lines-01_fill_and_stroke.png)

fill is the inside, stroke the outline. no_fill() and no_stroke() switch either off; the stroke is centred on the edge, half outside and half inside.

Source: [`examples/gallery/lines/01_fill_and_stroke.py`](../../examples/gallery/lines/01_fill_and_stroke.py)

### Line ends, corners and dashes

![Line ends, corners and dashes](images/lines-02_caps_joins_dashes.png)

stroke_cap sets how a line ends, stroke_join how corners look, and stroke_dash draws dashed outlines. They are style, like fill: saved_state puts them back.

Source: [`examples/gallery/lines/02_caps_joins_dashes.py`](../../examples/gallery/lines/02_caps_joins_dashes.py)

### Pixel art with no_smooth

![Pixel art with no_smooth](images/lines-03_pixel_art.png)

no_smooth() turns off the soft edges, so every pixel is either the shape's colour or not. Draw big and blocky with scale() and it looks like a retro game. smooth() switches back: compare the two white circles.

Source: [`examples/gallery/lines/03_pixel_art.py`](../../examples/gallery/lines/03_pixel_art.py)

## Curves

### Curves

![Curves](images/curves-01_curves.png)

bezier_vertex bends toward two control points; curve_vertex draws a smooth curve through the points (the first and last only steer it); curve_tightness straightens it. bezier and curve draw one curve in a single call; bezier_point and bezier_tangent find places and directions along it.

Source: [`examples/gallery/curves/01_curves.py`](../../examples/gallery/curves/01_curves.py)

## Text

### Text

![Text](images/text-01_text.png)

text_size sets the size in pixels; text is placed by its top-left corner. text_width measures a message, which is how you centre it.

Source: [`examples/gallery/text/01_text.py`](../../examples/gallery/text/01_text.py)

### Aligning text

![Aligning text](images/text-02_align.png)

f.text_align() says which point of the text the (x, y) you give is: left, center or right, then top, center, baseline or bottom. Each red cross below is the (x, y) passed to f.text(). text_ascent() and text_descent() measure how far letters reach above and below the baseline.

Source: [`examples/gallery/text/02_align.py`](../../examples/gallery/text/02_align.py)

### Text in boxes and columns

![Text in boxes and columns](images/text-03_text_box.png)

f.text_box() wraps text inside a box and gives back whatever did not fit, so the rest can flow on into the next box - the way DrawBot's textBox() works. A "\n" inside f.text() starts a new line, and f.text_leading() sets the distance from one line to the next.

Source: [`examples/gallery/text/03_text_box.py`](../../examples/gallery/text/03_text_box.py)

### Fonts and styles

![Fonts and styles](images/text-04_fonts.png)

f.text_style() switches between the four built-in styles: normal, bold, italic and bold_italic. f.load_font() reads a font file from disk and f.text_font() switches to it; f.text_font(None) goes back to the built-in family, remembering whatever style was set.

Source: [`examples/gallery/text/04_fonts.py`](../../examples/gallery/text/04_fonts.py)

### Letters as shapes

![Letters as shapes](images/text-05_text_path.png)

f.text_path() gives the outlines of a word as a path, set exactly as f.text() would set it. Cut the letters out of a panel with difference(), draw only their edge with expand_stroke(), or fill them with a gradient. The path has no colour, so you choose one when you draw it.

Source: [`examples/gallery/text/05_text_path.py`](../../examples/gallery/text/05_text_path.py)

### Spacing and ligatures

![Spacing and ligatures](images/text-06_tracking_and_features.png)

f.text_tracking() adds space after every letter, or takes it away. f.text_features() turns OpenType features on or off by name: "liga" joins letters like f, f and i into one shape, and "salt" picks alternate letters. f.text_features() with nothing in the brackets goes back to the font's own choices. A variable font has axes, like weight. f.font_variations(wght=700) sets them. This gallery has no variable font, so see the guide for that one.

Source: [`examples/gallery/text/06_tracking_and_features.py`](../../examples/gallery/text/06_tracking_and_features.py)

### Mixed styles in one text

![Mixed styles in one text](images/text-07_formatted.png)

A FormattedString holds runs of text. Each run can have its own size, style and colour. Settings you leave out follow the drawing state, so they can change between frames. f.text() draws it, and f.text_box() wraps it. Whatever does not fit comes back as a FormattedString too, still styled, ready for the next box. f.text_path() gives its outlines.

Source: [`examples/gallery/text/07_formatted.py`](../../examples/gallery/text/07_formatted.py)

### Variable font axes

![Variable font axes](images/text-08_variations.png)

f.font_variations(wght=700) sets the axes of a variable font, like its weight or width. The built-in font is not variable, so here the three lines look the same: an axis the font does not have is ignored, which makes the call safe to leave in. Load a variable font with f.load_font() and the weight really changes. f.font_variations() with nothing in the brackets goes back to the font's own defaults.

Source: [`examples/gallery/text/08_variations.py`](../../examples/gallery/text/08_variations.py)

### Words made of dots

![Words made of dots](images/text-09_text_dots.png)

f.text_to_points() walks along the outline of a word and gives back a point every few pixels. Draw a small circle at each point and the word is made of beads. A smaller spacing gives more dots. The same call works with any font, size and alignment, because it follows f.text_path(). f.current_font() tells you which font is in use: its family, its style, and whether it has the characters you want.

Source: [`examples/gallery/text/09_text_dots.py`](../../examples/gallery/text/09_text_dots.py)

### Letters from other fonts

![Letters from other fonts](images/text-10_fallback.png)

No font has every letter. When the font you are using lacks one, funground draws it from another font and keeps the line together: same size, same baseline. Here one greeting mixes English, Hindi and emoji, with no extra code. The emoji have one colour, the colour of the fill. The grey line turns the help off with f.text_fallback(None), so the missing letters show as empty boxes.

Source: [`examples/gallery/text/10_fallback.py`](../../examples/gallery/text/10_fallback.py)

## Animation and time

### Bounce

![Bounce](images/animation-01_bounce.png)

Change a variable a little in every draw() and you have motion; flip the speed at the edges and it bounces.

Source: [`examples/gallery/animation/01_bounce.py`](../../examples/gallery/animation/01_bounce.py)

### Time-based motion

![Time-based motion](images/animation-02_time_based.png)

f.delta_time is the number of seconds the last frame took. Moving by speed * delta_time keeps the same speed on a fast or a slow computer. *(Uses real time, so the picture varies from run to run.)*

Source: [`examples/gallery/animation/02_time_based.py`](../../examples/gallery/animation/02_time_based.py)

### A clock

![A clock](images/animation-03_clock.png)

hour(), minute() and second() read the computer's clock; day(), month() and year() the date. millis() counts milliseconds since the sketch started and frame_rate() says how many frames per second it is really drawing. *(Uses real time, so the picture varies from run to run.)*

Source: [`examples/gallery/animation/03_clock.py`](../../examples/gallery/animation/03_clock.py)

### Pause, step and quit

![Pause, step and quit](images/animation-04_pause.png)

no_loop() stops draw() being called every frame (it still runs once); a key callback can call redraw() to draw one more frame or loop() to carry on. is_looping() says which it is doing, and exit() ends the sketch.

Source: [`examples/gallery/animation/04_pause.py`](../../examples/gallery/animation/04_pause.py)

### Record an animation as a GIF

![Record an animation as a GIF](images/animation-05_record_a_gif.png)

f.save_gif("spinner.gif", 2) records the next 2 seconds of the sketch and writes them as a GIF that loops for ever. Each frame is shown for 1 divided by the frame rate. f.save_movie("spinner.mp4", 2) does the same for an MP4, which needs the free program ffmpeg. Call either one once; here it is on the first frame. The animation turns once in 60 frames, so the GIF loops without a jump.

Source: [`examples/gallery/animation/05_record_a_gif.py`](../../examples/gallery/animation/05_record_a_gif.py)

## Motion

### Movers with vectors

![Movers with vectors](images/motion-01_movers.png)

A Vector holds an x and a y together: a position, a velocity, a force. Each frame the forces add to the velocity and the velocity adds to the position, just as in p5.js - methods like add() and limit() change the vector itself. heading() gives the direction, for the arrows.

Source: [`examples/gallery/motion/01_movers.py`](../../examples/gallery/motion/01_movers.py)

## Transforms

### Rotating squares

![Rotating squares](images/transforms-01_rotating_squares.png)

translate moves the origin, rotate turns everything drawn afterwards (in degrees), scale grows it. push() saves the current transform and style, pop() brings them back.

Source: [`examples/gallery/transforms/01_rotating_squares.py`](../../examples/gallery/transforms/01_rotating_squares.py)

### saved_state and angles

![saved_state and angles](images/transforms-02_saved_state.png)

with f.saved_state(): is push() and pop() in one block: whatever the block changes is undone at the end. rotate() takes degrees; f.radians() converts for math.sin and math.cos.

Source: [`examples/gallery/transforms/02_saved_state.py`](../../examples/gallery/transforms/02_saved_state.py)

### Shear and matrices

![Shear and matrices](images/transforms-03_shear_and_matrices.png)

shear_x and shear_y slant everything drawn afterwards; apply_matrix multiplies in any transform at once; reset_matrix forgets all transforms until the end of the saved_state block.

Source: [`examples/gallery/transforms/03_shear_and_matrices.py`](../../examples/gallery/transforms/03_shear_and_matrices.py)

## Paths and clipping

### A star from vertices

![A star from vertices](images/paths-01_star.png)

begin_shape(), a vertex() for each corner, end_shape(close=True). Closed shapes are filled; open ones are only stroked.

Source: [`examples/gallery/paths/01_star.py`](../../examples/gallery/paths/01_star.py)

### Reusable paths and clipping

![Reusable paths and clipping](images/paths-02_path_and_clip.png)

f.path() builds a shape you can draw many times with draw_path(). clip(path) keeps later drawing inside the path until the end of the saved_state block.

Source: [`examples/gallery/paths/02_path_and_clip.py`](../../examples/gallery/paths/02_path_and_clip.py)

### Clipping on and off

![Clipping on and off](images/paths-03_no_clip.png)

no_clip() removes clipping until the end of the saved_state block; when the block ends, the clip that was there before comes back.

Source: [`examples/gallery/paths/03_no_clip.py`](../../examples/gallery/paths/03_no_clip.py)

### Shapes with holes

![Shapes with holes](images/paths-04_holes.png)

Between begin_contour() and end_contour(), list the corners of a hole. funground makes the hole cut out of the shape whichever way round you draw it.

Source: [`examples/gallery/paths/04_holes.py`](../../examples/gallery/paths/04_holes.py)

### Combining shapes

![Combining shapes](images/paths-05_booleans.png)

Two shapes can be joined, overlapped, cut and mixed with union, intersection, difference and xor. Each one gives back a new path. The bottom panel shows remove_overlap, which turns a crossing outline into one clean edge.

Source: [`examples/gallery/paths/05_booleans.py`](../../examples/gallery/paths/05_booleans.py)

### Outlines, tests and moving paths

![Outlines, tests and moving paths](images/paths-06_outlines.png)

expand_stroke turns a thick line into a shape you can fill with a gradient. contains tells you whether a point is inside a shape. bounds gives the box around it. rotate and scale make copies.

Source: [`examples/gallery/paths/06_outlines.py`](../../examples/gallery/paths/06_outlines.py)

## Randomness and noise

### Confetti

![Confetti](images/randomness-01_confetti.png)

f.random(high) or f.random(low, high) gives a random number; f.random_seed(n) makes the same "random" picture every time. constrain keeps a value in range; distance measures between points.

Source: [`examples/gallery/randomness/01_confetti.py`](../../examples/gallery/randomness/01_confetti.py)

### Bell-curve randomness and random choices

![Bell-curve randomness and random choices](images/randomness-02_gaussian_and_choice.png)

random_gaussian gives numbers that cluster around a middle value, like heights in a class; random_choice picks one item from a list. random_seed makes both repeat exactly.

Source: [`examples/gallery/randomness/02_gaussian_and_choice.py`](../../examples/gallery/randomness/02_gaussian_and_choice.py)

### Noise: smooth randomness

![Noise: smooth randomness](images/randomness-03_noise.png)

noise(x) gives a value from 0 to 1 that changes smoothly as x changes: hills instead of static. noise(x, y) makes a smooth 2-D pattern. noise_seed(n) picks the pattern; noise_detail sets how rough it is. The same seed gives the same values as p5.js.

Source: [`examples/gallery/randomness/03_noise.py`](../../examples/gallery/randomness/03_noise.py)

## Useful maths

### Mapping and blending numbers

![Mapping and blending numbers](images/maths-01_map_and_lerp.png)

map_range re-scales a number from one range to another; lerp finds a point part of the way between two numbers; norm says how far along a range a number is; mag measures an arrow.

Source: [`examples/gallery/maths/01_map_and_lerp.py`](../../examples/gallery/maths/01_map_and_lerp.py)

## Interaction

### Follow the mouse

![Follow the mouse](images/interaction-01_follow_the_mouse.png)

f.mouse_x and f.mouse_y are where the mouse is; f.is_mouse_pressed is True while a button is held; f.key_down("left") is True while that key is held.

Source: [`examples/gallery/interaction/01_follow_the_mouse.py`](../../examples/gallery/interaction/01_follow_the_mouse.py)

### A paint program

![A paint program](images/interaction-02_paint.png)

Callbacks are functions you define with special names; funground calls them when something happens. mouse_dragged draws, mouse_wheel changes the brush, key_pressed clears or picks a colour, and pmouse_x/pmouse_y (last frame's mouse) join the strokes up smoothly.

Source: [`examples/gallery/interaction/02_paint.py`](../../examples/gallery/interaction/02_paint.py)

### Move with the keyboard

![Move with the keyboard](images/interaction-03_keyboard_mover.png)

Two ways to read the keyboard. For smooth movement, ask every frame whether a key is held: f.key_down("left"). For one-off actions, define key_pressed(), which runs once per press; f.key says which key it was. key_released() runs when the key comes back up.

Source: [`examples/gallery/interaction/03_keyboard_mover.py`](../../examples/gallery/interaction/03_keyboard_mover.py)

### The window: cursor, size and full screen

![The window: cursor, size and full screen](images/interaction-04_window.png)

f.cursor() picks the mouse pointer - here a hand over the button, crosshairs elsewhere - and f.no_cursor() hides it. Press f for f.full_screen(), where f.width and f.height become the screen's size, and 1, 2 or 3 for f.resize_canvas(). Everything is placed using f.width and f.height, so the drawing fits whatever the size.

Source: [`examples/gallery/interaction/04_window.py`](../../examples/gallery/interaction/04_window.py)

### Sliders, a checkbox and a button

![Sliders, a checkbox and a button](images/interaction-05_controls.png)

A slider, a checkbox and a button sit in a panel below the canvas. Make each one once in setup(), keep it in a variable, and ask it for its value in draw(). Here the sliders set the number and the length of the petals, the checkbox makes the flower spin, and the button picks the next colour.

Source: [`examples/gallery/interaction/05_controls.py`](../../examples/gallery/interaction/05_controls.py)

## Saving your work

### Saving your work

![Saving your work](images/saving-01_save_a_picture.png)

f.save("name.png") writes the frame when it is finished. Use .pdf or .svg for a picture made of shapes that stays sharp at any size.

Source: [`examples/gallery/saving/01_save_a_picture.py`](../../examples/gallery/saving/01_save_a_picture.py)

### A picture with a transparent background

![A picture with a transparent background](images/saving-02_transparent_png.png)

clear() makes every pixel transparent. A PNG saved afterwards keeps the transparency, so the shape can be placed on any background later. (The window shows transparent as black.)

Source: [`examples/gallery/saving/02_transparent_png.py`](../../examples/gallery/saving/02_transparent_png.py)

### Saving an animation as frames

![Saving an animation as frames](images/saving-03_save_frames.png)

f.save_frames("frames/####.png", 30) saves this frame and the next 29 as numbered pictures: frames/0001.png, frames/0002.png and so on. A program such as ffmpeg can join them into a video or a GIF - see chapter 13 of the guide.

Source: [`examples/gallery/saving/03_save_frames.py`](../../examples/gallery/saving/03_save_frames.py)

## Documents and pages

### A booklet with three pages

![A booklet with three pages](images/documents-01_booklet.png)

A script can make a document. f.new_page() ends one page and starts the next. A size name such as "A5" sets the page size, and f.page_size() gives the numbers for a name. f.save("booklet.pdf") writes every page into one PDF. The gallery picture shows the last page, which is on its side.

Source: [`examples/gallery/documents/01_booklet.py`](../../examples/gallery/documents/01_booklet.py)

### A flip book saved as a GIF

![A flip book saved as a GIF](images/documents-02_flip_book.png)

Every page of a script is one frame of a GIF. f.frame_duration(0.15) says how long each page is shown, in seconds. f.save("flip_book.gif") writes all the pages, in order, and the GIF loops for ever. All the pages must be the same size. An MP4 works the same way, f.save("flip_book.mp4"), but it needs the free program ffmpeg. The gallery picture shows the last page.

Source: [`examples/gallery/documents/02_flip_book.py`](../../examples/gallery/documents/02_flip_book.py)

## Pictures and images

### Loading and drawing an image

![Loading and drawing an image](images/images-01_load_image.png)

f.load_image() reads a picture file (PNG, JPEG, GIF, BMP, TGA) and gives you a picture. f.image() draws it, at its own size or stretched. It follows f.translate(), f.rotate() and f.opacity() like any other drawing.

Source: [`examples/gallery/images/01_load_image.py`](../../examples/gallery/images/01_load_image.py)

### Tinting a picture and drawing part of it

![Tinting a picture and drawing part of it](images/images-02_tint_and_parts.png)

f.tint() colours every picture drawn after it: the red, green and blue of each pixel are multiplied by the tint, and its alpha too. f.no_tint() stops it. To draw only part of a picture, give image() four more numbers: the left, top, width and height of the part.

Source: [`examples/gallery/images/02_tint_and_parts.py`](../../examples/gallery/images/02_tint_and_parts.py)

### Reading and writing single pixels

![Reading and writing single pixels](images/images-03_pixels.png)

f.set() makes one pixel a colour, and f.get() reads one back as a colour. f.load_pixels() copies the whole canvas into the list f.pixels: four numbers for each pixel (red, green, blue, alpha), row by row. Change the list, then f.update_pixels() writes it back. A Python loop over every pixel is slow, so keep the area small.

Source: [`examples/gallery/images/03_pixels.py`](../../examples/gallery/images/03_pixels.py)

### Changing pictures: copy, resize, mask and filters

![Changing pictures: copy, resize, mask and filters](images/images-04_filters.png)

picture.copy() makes a new picture that you can change without touching the first. picture.resize(w, h) changes the size of a picture. picture.mask(other) lets the other picture decide what shows through. picture.filter(kind) changes every pixel: "threshold", "gray", "invert", "blur", "posterize", "erode", "dilate" or "opaque". Some take a value, like picture.filter("blur", 3). f.filter() does the same to the whole canvas: change what you have drawn so far.

Source: [`examples/gallery/images/04_filters.py`](../../examples/gallery/images/04_filters.py)

### Loading an SVG drawing

![Loading an SVG drawing](images/images-05_svg.png)

f.load_svg() reads an SVG file and gives you a picture, like f.load_image(). The picture is made of the SVG's shapes, not of pixels, so you can draw it small or large and it stays sharp. f.svg_paths() gives the same shapes as paths, for booleans and clips.

Source: [`examples/gallery/images/05_svg.py`](../../examples/gallery/images/05_svg.py)

## Sound

### Sound: play a tune and watch it

![Sound: play a tune and watch it](images/sound-01_visualiser.png)

f.load_sound() reads a sound file. sound.loop() plays it over and over. While it plays, sound.level() tells you how loud it is now, and sound.spectrum() tells you how strong each range of pitch is: low notes on the left, high notes on the right. Both are numbers from 0 to 1. With no sound device, the sketch still runs, in silence. *(Uses real time, so the picture varies from run to run.)*

Source: [`examples/gallery/sound/01_visualiser.py`](../../examples/gallery/sound/01_visualiser.py)

### Making sound: write a tune, then watch it play

![Making sound: write a tune, then watch it play](images/sound-02_write_a_tune.png)

f.melody() turns text into a sound. A note is a name like "E4", a dash is a rest, and :2 after a note makes it last two beats. Here the tune is a short list, so the same list builds the sound and draws the bars. The top shows the wave itself. A soft chord from f.mix() plays underneath. sound.pitch() reads the note that is sounding now. With no sound device the sketch still runs, in silence. *(Uses real time, so the picture varies from run to run.)*

Source: [`examples/gallery/sound/02_write_a_tune.py`](../../examples/gallery/sound/02_write_a_tune.py)

### Making sound: a sargam phrase over a drone

![Making sound: a sargam phrase over a drone](images/sound-03_sargam_over_a_drone.png)

With sa="D4", f.melody() reads swaras instead of note names: S r R g G m M P d D n N. A ' after a swara is the octave above and a comma is the octave below. Here the notes use just tuning, the pure ratios from Sa. Under the phrase, a drone of plucked strings plays Pa, Sa, Sa, Sa over and over. The ladder shows the swara that sound.pitch() hears. *(Uses real time, so the picture varies from run to run.)*

Source: [`examples/gallery/sound/03_sargam_over_a_drone.py`](../../examples/gallery/sound/03_sargam_over_a_drone.py)

### Sound: a tuner that listens

![Sound: a tuner that listens](images/sound-04_tuner.png)

f.microphone() listens to your computer's microphone. mic.start() begins, and then mic.pitch() gives the pitch of the one note you sing or play, or None when it is quiet. f.frequency_to_note() turns that pitch into a name like "A4". The needle shows whether you are a little flat (left) or sharp (right). The bar at the bottom is mic.level(). Nothing is recorded or played back. With no microphone to hear, the sketch still runs, and just waits. *(Uses real time, so the picture varies from run to run.)*

Source: [`examples/gallery/sound/04_tuner.py`](../../examples/gallery/sound/04_tuner.py)
