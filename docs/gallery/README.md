# Playground Examples Gallery

Every picture below is made by running the example beside it — `python tools/make_gallery.py`
regenerates them. Each example is a complete sketch: copy it into a file and run it.

## Basics

### Your first sketch

![Your first sketch](images/basics-01_first_sketch.png)

A window, a background and one circle: the three lines every sketch starts from.

Source: [`examples/gallery/basics/01_first_sketch.py`](../../examples/gallery/basics/01_first_sketch.py)

### setup() once, draw() every frame

![setup() once, draw() every frame](images/basics-02_setup_and_draw.png)

setup() runs once; draw() runs again and again. p.frame_count counts the frames, p.width and p.height are the window size, and p.stop() ends the sketch.

Source: [`examples/gallery/basics/02_setup_and_draw.py`](../../examples/gallery/basics/02_setup_and_draw.py)

## Shapes

### The basic shapes

![The basic shapes](images/shapes-01_basic_shapes.png)

rect is placed by its top-left corner; circle and ellipse by their centre. line joins two points; point is a dot in the stroke colour.

Source: [`examples/gallery/shapes/01_basic_shapes.py`](../../examples/gallery/shapes/01_basic_shapes.py)

### More shapes

![More shapes](images/shapes-02_more_shapes.png)

square, triangle, quad and polygon for straight-sided shapes; arc for part of an ellipse, with angles in degrees turning clockwise from the right, in three modes: open, chord and pie.

Source: [`examples/gallery/shapes/02_more_shapes.py`](../../examples/gallery/shapes/02_more_shapes.py)

## Colour

### Four ways to say a colour

![Four ways to say a colour](images/colour-01_colour_forms.png)

A name, an (r, g, b) tuple from 0 to 255, a hex string, or an (r, g, b, a) tuple whose last number is the opacity. Overlapping translucent circles mix.

Source: [`examples/gallery/colour/01_colour_forms.py`](../../examples/gallery/colour/01_colour_forms.py)

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

### Shapes with holes

![Shapes with holes](images/curves-02_holes.png)

Between begin_contour() and end_contour(), list the corners of a hole. Playground makes the hole cut out of the shape whichever way round you draw it.

Source: [`examples/gallery/curves/02_holes.py`](../../examples/gallery/curves/02_holes.py)

## Text

### Text

![Text](images/text-01_text.png)

text_size sets the size in pixels; text is placed by its top-left corner. text_width measures a message, which is how you centre it.

Source: [`examples/gallery/text/01_text.py`](../../examples/gallery/text/01_text.py)

## Animation and time

### Bounce

![Bounce](images/animation-01_bounce.png)

Change a variable a little in every draw() and you have motion; flip the speed at the edges and it bounces.

Source: [`examples/gallery/animation/01_bounce.py`](../../examples/gallery/animation/01_bounce.py)

### Time-based motion

![Time-based motion](images/animation-02_time_based.png)

p.delta_time is the number of seconds the last frame took. Moving by speed * delta_time keeps the same speed on a fast or a slow computer. *(Uses real time, so the picture varies from run to run.)*

Source: [`examples/gallery/animation/02_time_based.py`](../../examples/gallery/animation/02_time_based.py)

### A clock

![A clock](images/animation-03_clock.png)

hour(), minute() and second() read the computer's clock; day(), month() and year() the date. millis() counts milliseconds since the sketch started and frame_rate() says how many frames per second it is really drawing. *(Uses real time, so the picture varies from run to run.)*

Source: [`examples/gallery/animation/03_clock.py`](../../examples/gallery/animation/03_clock.py)

## Transforms

### Rotating squares

![Rotating squares](images/transforms-01_rotating_squares.png)

translate moves the origin, rotate turns everything drawn afterwards (in degrees), scale grows it. push() saves the current transform and style, pop() brings them back.

Source: [`examples/gallery/transforms/01_rotating_squares.py`](../../examples/gallery/transforms/01_rotating_squares.py)

### saved_state and angles

![saved_state and angles](images/transforms-02_saved_state.png)

with p.saved_state(): is push() and pop() in one block: whatever the block changes is undone at the end. rotate() takes degrees; p.radians() converts for math.sin and math.cos.

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

p.path() builds a shape you can draw many times with draw_path(). clip(path) keeps later drawing inside the path until the end of the saved_state block.

Source: [`examples/gallery/paths/02_path_and_clip.py`](../../examples/gallery/paths/02_path_and_clip.py)

### Clipping on and off

![Clipping on and off](images/paths-03_no_clip.png)

no_clip() removes clipping until the end of the saved_state block; when the block ends, the clip that was there before comes back.

Source: [`examples/gallery/paths/03_no_clip.py`](../../examples/gallery/paths/03_no_clip.py)

## Randomness and noise

### Confetti

![Confetti](images/randomness-01_confetti.png)

p.random(high) or p.random(low, high) gives a random number; p.random_seed(n) makes the same "random" picture every time. constrain keeps a value in range; distance measures between points.

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

p.mouse_x and p.mouse_y are where the mouse is; p.mouse_pressed is True while a button is held; p.key_down("left") is True while that key is held.

Source: [`examples/gallery/interaction/01_follow_the_mouse.py`](../../examples/gallery/interaction/01_follow_the_mouse.py)

## Saving your work

### Saving your work

![Saving your work](images/saving-01_save_a_picture.png)

p.save("name.png") writes the frame when it is finished. Use .pdf or .svg for a picture made of shapes that stays sharp at any size.

Source: [`examples/gallery/saving/01_save_a_picture.py`](../../examples/gallery/saving/01_save_a_picture.py)

### A picture with a transparent background

![A picture with a transparent background](images/saving-02_transparent_png.png)

clear() makes every pixel transparent. A PNG saved afterwards keeps the transparency, so the shape can be placed on any background later. (The window shows transparent as black.)

Source: [`examples/gallery/saving/02_transparent_png.py`](../../examples/gallery/saving/02_transparent_png.py)
