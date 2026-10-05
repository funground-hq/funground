# When something goes wrong

Everyone sees error messages. They are not a telling-off: they tell you what to change.

**How to read one.** Python prints a long message when a sketch stops. Read the **last line**
first. It names the kind of error (`ValueError`, `RuntimeError`, `TypeError`, `NameError`) and says
what went wrong. The lines above it show *where*: the file name and the line number in your sketch.

funground's own messages are written to be read. Most say what is wrong *and* what to try. The
messages below are the real ones. Where a message has your own words in it (a colour name, a file
name), they are shown here as `'tomatoe'` or `'photo.png'`.

Words you do not know? See the [glossary](glossary.md).

- [The sketch does not start](#the-sketch-does-not-start)
- [Python errors in sketches](#python-errors-in-sketches)
- [Drawing and style](#drawing-and-style)
- [Files](#files)
- [Saving and recording](#saving-and-recording)
- [Controls](#controls)
- [Sound and the microphone](#sound-and-the-microphone)
- [Warnings](#warnings)

## The sketch does not start

### Nothing happens, or "never started"

```
Your sketch has a draw() function but never started. Add f.run() as the last line.
```

An animated sketch needs `f.run()` as its **last line**. Without it, Python reads the file, defines
your functions and stops. funground prints the message above when you run the file from a terminal.
In IDLE or Thonny you may see nothing at all. A script (no `draw()`) needs `f.show()` instead if you
want to look at it.

```py
def draw():
    f.circle(100, 100, 50)

f.run()          # the last line
```

### The window opens and closes at once

Usually one of these:

- The file is a **script** (no `draw()`) and has no `f.show()` at the end. It draws, saves, and ends.
  Add `f.show()` as the last line to keep the window open.
- `draw()` stops itself with `f.stop()` or `f.exit()`, or the sketch has `f.run(max_frames=...)`.
- An error happened. Look in the terminal for a message: the window closes when the sketch stops.
- You ran it from an editor that shows only a short flash of output. Run it from a terminal with
  `python my_sketch.py` and read what is printed.

### This file mixes the two styles

```
This file mixes the two styles: it draws at the top level (a script) and also calls f.run() (an
animated sketch). Pick one. For an animation, move the drawing into draw(). For a script, remove
f.run() and end with f.show().
```

A file is **either** a script (lines run from top to bottom, ending with `f.show()`) **or** an
animated sketch (`setup()` and `draw()` and `f.run()`). Chapter [2](02_the_sketch.md) explains both.
Drawing at the top level *and* calling `f.run()` is mixing them. Move those lines into `draw()`.

### f.run() found a setup() but no draw()

```
f.run() found a setup() but no draw(). To animate, add a draw() function. To draw once, remove
setup() and f.run(), write the drawing at the top level and end with f.show() (a script).
```

An animated sketch needs a `draw()`, even if it is only `def draw(): pass`. If you only want one
still picture, write a script instead.

### No drawing window yet

```
No drawing window yet. Call f.size(...) first.
```

You tried to draw before there was a canvas. In a script, call `f.size(width, height)` before the
first drawing line. In an animated sketch, call `f.size()` in `setup()`. Do not draw at the top of
the file, outside any function, before `f.run()`: that is the "mixes the two styles" error above.

```py
f.size(400, 300)        # first
f.circle(200, 150, 80)  # then draw
```

### width and height must be positive

`f.size(0, 100)` and `f.size(-5, 50)` give `ValueError: width and height must be positive`.
A canvas needs a size above zero in both directions. Also check that you gave **numbers**: `f.size("400", 300)`
gives a `TypeError` that talks about `'<='` and `str`.

### Installing: the Cairo error on Linux

On Linux, `pip install funground` may stop with a long message about `pycairo`, such as
`Failed building wheel for pycairo` or `Dependency 'cairo' not found`. funground draws with the
Cairo library, and pip needs its development files to build the Python part. This is a pip message,
not a funground one. Install the system package first, then run pip again:

```
sudo apt install libcairo2-dev pkg-config python3-dev
python -m pip install funground
```

Other Linux distributions have an equivalent package (look for "cairo development files"). On
Windows and macOS, pip normally finds a ready-made version and needs nothing more. See chapter
[1](01_getting_started.md).

### No module named 'funground'

```
ModuleNotFoundError: No module named 'funground'
```

Python cannot find funground. Usually the virtual environment is not switched on, or you ran
`pip install` in a different one. Switch it on (`.venv\Scripts\activate` on Windows,
`source .venv/bin/activate` on macOS and Linux) and try again. Also check that your own file is not
called `funground.py`: Python would read that instead of the library.

## Python errors in sketches

These come from Python, not from funground, but you will meet them in your first sketches.

### NameError or AttributeError on an f. name

```
AttributeError: module 'funground' has no attribute 'cirle'
NameError: name 'f' is not defined
```

- `module 'funground' has no attribute 'cirle'` is a **typo** in a name after `f.`. It should be
  `f.circle`. Names are lower case with underscores: `f.stroke_width`, not `f.strokeWidth`. If you
  are not sure of a name, look in the [Quick Reference](../reference/Quick_Reference.md), or ask
  Python: `print(dir(f))`.
- `name 'f' is not defined` means the first line is missing. Start every sketch with
  `import funground as f`.
- `'TextIOWrapper' object has no attribute 'circle'` (or similar) means `f` has been used for
  something else, often `with open("x.txt") as f:`. Use another name for your own variables.
- `NameError: name 'circle' is not defined` means you left off the `f.`: write `f.circle(...)`.

### IndentationError and SyntaxError

```
IndentationError: expected an indented block after function definition on line 4
SyntaxError: '(' was never closed
SyntaxError: expected ':'
```

Python uses the **spaces at the start of a line** to know what belongs inside `def draw():`. Every line
inside needs the same indent (4 spaces is usual). Do not mix tabs and spaces. A `SyntaxError` usually
means a missing bracket, quote or colon *just before* the line Python points at. Check that every
`(` has its `)` and every `def`, `if`, `for` and `with` line ends with `:`.

### UnboundLocalError: a variable that draw() changes

```
UnboundLocalError: cannot access local variable 'x' where it is not associated with a value
```

You made `x` at the top of the file and then changed it inside `draw()`. Python needs to be told:
add `global x` as the first line of `draw()`. See chapter [2](02_the_sketch.md#variables-that-change).

### TypeError: missing arguments

```
TypeError: circle() missing 1 required positional argument: 'diameter'
```

You gave a function too few numbers. `f.circle(x, y, diameter)` needs three. The message names the
one that is missing. Chapter [3](03_shapes.md) lists what each shape needs. Too many numbers gives
`circle() takes 3 positional arguments but 5 were given`, which is the same kind of mistake.

## Drawing and style

### A colour is not accepted

```
ValueError: unknown colour 'tomatoe'. Use a name like 'tomato', a tuple like (255, 99, 71) or a hex string like '#FF6347'.
ValueError: a colour tuple needs 2, 3 or 4 numbers (grey, alpha or red, green, blue[, alpha]), got 5
ValueError: colour component r=300 must be an integer from 0 to 255
TypeError: True is not a colour: True and False are not numbers here
ValueError: f.fill() and friends take more than one argument only for numbers, not 'red': ...
```

Each one is a small mistake in a colour:

- A **name** is spelt wrongly. Check it against the [list of names](../reference/Quick_Reference.md#10-named-colours-and-other-fixed-names).
- A **tuple** has the wrong number of values. Use `(grey, alpha)`, `(red, green, blue)` or
  `(red, green, blue, alpha)`.
- A number is **outside 0 to 255** (unless you changed `f.color_mode()`).
- A name goes **with other numbers**: `f.fill("red", 100)` is not allowed. Give a name on its own, or
  use numbers, or use a tuple such as `(255, 0, 0, 100)`.

See chapter [4](04_colour.md).

### A word is not one of the choices

```
ValueError: f.stroke_cap() takes one of 'round', 'square', 'butt', not 'pointy'
ValueError: f.rect_mode() takes one of 'corner', 'corners', 'center', 'radius', not 'middle'
ValueError: f.text_align() takes one of 'left', 'center', 'right' first, not 'middle'
```

Some functions take a word, such as `"round"`. The message lists every word that works. Copy
one of them. Spelling matters, and so does the American `"center"`.

### unknown page size

```
ValueError: unknown page size 'A9': use one of A3, A4, A5, B5, Letter, Legal, Tabloid, Square
(add "Landscape" to turn it on its side, e.g. "A4Landscape")
```

Page names are listed in chapter [13](13_saving_your_work.md#documents-and-pages). Or give a width
and a height in pixels instead: `f.new_page(300, 200)`.

### Functions that need a shape, a layer or a picture

```
RuntimeError: f.end_shape() called outside a shape: call f.begin_shape() first.
RuntimeError: f.curve_vertex() called outside a shape: call f.begin_shape() first.
ValueError: f.hide_layer(): there is no layer called 'nope'. Layers so far: none yet
RuntimeError: f.layer() cannot be used inside another layer block: layers do not nest. ...
TypeError: f.image() needs a picture made with f.create_graphics(), not str (or an image file loaded with f.load_image())
```

- `f.vertex()`, `f.curve_vertex()` and `f.end_shape()` belong between `f.begin_shape()` and
  `f.end_shape()`. See chapter [9](09_paths_and_clipping.md).
- A layer is made the first time you use its name in `with f.layer("name"):`. Hide it only after that.
  A layer block cannot sit inside another layer block.
- `f.image("photo.png", 0, 0)` gives the TypeError above: a file name is only text. Load it first with
  `photo = f.load_image("photo.png")`, then draw `photo`.

### f.update_pixels() needs f.load_pixels() first

```
RuntimeError: f.update_pixels() needs f.load_pixels() first: it copies the canvas into pixels, which you then change
```

Call `f.load_pixels()`, change `f.pixels`, then call `f.update_pixels()`, in that order. Chapter
[9](09_paths_and_clipping.md#pixels).

## Files

### A file is not found

```
FileNotFoundError: f.load_image(): no image file found at 'C:\sketches\photo.png' or 'C:\Users\you\photo.png'
```

`f.load_image()`, `f.load_font()`, `f.load_sound()` and `f.load_svg()` all give a message like this one.
It names **both** places funground looked: first next to your sketch file, then in the folder you ran
Python from. To fix it:

- Check the spelling and the ending (`photo.jpg` is not `photo.jpeg`).
- Put the file in the same folder as your sketch.
- Or give the full path to the file.

A relative path such as `"images/photo.png"` is looked for from those same two places.

### An SVG is not an image

```
ValueError: f.load_image(): 'badge.svg' is an SVG file. SVG files cannot be loaded as images; use f.load_svg() to read them as drawings
```

Use `f.load_svg("badge.svg")` for SVG files, as in chapter [9](09_paths_and_clipping.md#loading-svg-drawings).

### A system font is not installed

```
FileNotFoundError: f.system_font(): no installed font with the family name 'Nopefont Zzz'
```

`f.system_font()` finds fonts that are installed on **your** computer, by their family name. The name
may be spelt differently on your system. Look in your Fonts folder. Or use a font file with
`f.load_font("MyFont.ttf")`, which works on every computer. See chapter [6](06_text.md).

## Saving and recording

### The file ending is not supported

```
ValueError: cannot save 'a.jpg': use one of .png, .pdf, .svg
```

`f.save()` writes `.png`, `.pdf` and `.svg` (and `.gif` or `.mp4` for several frames). It does not write
JPEG. Change the ending. See chapter [13](13_saving_your_work.md).

### save_frames needs a number marker

```
ValueError: f.save_frames() needs one run of # in the name for the number, e.g. "frames/####.png", not 'frames.png'
```

Put `####` in the name where the frame number should go.

### Animation functions in a script, and script functions in an animation

```
RuntimeError: f.no_loop() is for animated sketches, and this file is a script (it has no draw()). To animate, write a draw() function and end the file with f.run().
RuntimeError: f.show() is for scripts. An animated sketch already has its window: remove f.show() and end the file with f.run().
RuntimeError: f.new_page() is for scripts (a file with no draw()). An animated sketch has one canvas: ...
```

Some functions only make sense in one style:

| Only in an animated sketch | Only in a script |
|---|---|
| `f.no_loop()`, `f.loop()`, `f.redraw()`, `f.exit()` | `f.show()` |
| `f.save_frames()`, `f.save_gif()`, `f.save_movie()` | `f.new_page()`, `f.frame_duration()` |
| Controls such as `f.create_slider()` | |

Decide which style the file is, and remove the call that does not belong. See chapter
[2](02_the_sketch.md#scripts-drawing-without-draw).

### A GIF or MP4 cannot be made

```
RuntimeError: f.save_gif() and saving a .gif need Pillow or ffmpeg, and neither was found. The easy way is to install Pillow with:  pip install funground[extras]
RuntimeError: Saving an .mp4 needs ffmpeg, a free program, and funground cannot find it. Install it, then close and reopen your terminal. ...
```

A GIF needs a free Python package called Pillow: `pip install funground[extras]`. An MP4 needs ffmpeg:
`pip install funground[video]` brings its own copy. Close and reopen your terminal afterwards. See
chapter [13](13_saving_your_work.md#gif-and-mp4).

### Recording sizes and pages

`ValueError: f.save('x.gif'): every page of a GIF must be the same size. Page 1 is 200 x 120 but page 2 is ...`
means a flip book has pages of different sizes. A GIF or MP4 keeps one size, so use `f.new_page()` with
no size to keep the same one. `f.save_gif()` while another recording is still running gives a
`RuntimeError`: wait until the first has finished.

## Controls

### Controls in draw()

```
RuntimeError: Controls are made once, in setup() (or at the top of the file), not in draw(): draw() runs every frame, so it would make a new one each time. Make the control in setup(), keep it in a variable, and read it in draw().
```

`f.create_slider()`, `f.create_checkbox()` and `f.create_button()` go in `setup()`, and their results go
in a variable that `draw()` can reach (use `global`). Then **read** them in `draw()`:

```py
def setup():
    global size
    f.size(400, 300)
    size = f.create_slider(10, 120, 60)

def draw():
    f.circle(200, 150, size.value())
```

### Controls in a script

```
RuntimeError: Controls need an animated sketch, and this file is a script (it ends with f.show()). ...
```

A script has no loop to read a control. Rewrite the file as a sketch with `setup()`, `draw()` and
`f.run()`. A slider with `low` that is not below `high` gives
`ValueError: a slider needs low below high`. See chapter [10](10_interaction.md#3-controls-sliders-checkboxes-and-buttons).

## Sound and the microphone

### A tune is not understood

```
ValueError: f.note(): 'H4' is not a note name. Try a letter A-G, an optional # or b, and an octave, like 'A4', 'C#5' or 'Bb3'
ValueError: f.melody(): bad token 'H4': 'H4' is not a note name
ValueError: f.tone(): wave must be one of sine, square, saw, triangle, soft, noise, not 'wobble'
ValueError: f.tone(): volume must be at most 1, not 2
```

`f.melody()` names the exact word it could not read (a **token**). Note names go from A to G, so `H4`
is not one. After the letter comes an optional `#` or `b`, then the octave number. The error for a
wave lists the ones you can use. Volumes go from 0 to 1. See chapter [16](16_sound.md).

### A raga or a tala is not in the table

```
ValueError: f.raga(): 'Nope' is not in funground's raga table. It has: Yaman, Bhupali, Bilawal, Khamaj, ...
ValueError: f.tala(): 'Nope' is not in funground's tala table. It has: Teentaal, Ektaal, Jhaptaal, ...
```

The message lists every name that works. Capital letters do not matter, but spelling does: `f.ragas()` and
`f.talas()` print the lists. See chapter [17](17_ragas_and_talas.md).

### No microphone

```
RuntimeError: f.microphone(): no microphone was found on this computer. Check that one is plugged in. On a Mac, allow microphone access in System Settings, Privacy & Security, Microphone.
```

Check that a microphone is plugged in and that it is the default input. On a Mac, allow it in System
Settings. On Windows, check Settings, Privacy, Microphone. `f.microphones()` lists the ones funground
can see. If you pass part of a name, such as `f.microphone("USB")`, and no microphone has it, you get a
similar message that lists the ones that do exist.

If your microphone is not found by your computer, no sketch can use it. Test the microphone in another program first.
A sketch with a microphone still runs where there is none, if you set `FUNGROUND_HEADLESS=1`: the
microphone is then silent.

### The microphone needs a newer pygame

```
RuntimeError: microphone input needs pygame-ce 2.5 or newer ... Update it with: pip install --upgrade pygame-ce
```

Run the command in the message in your virtual environment.

### The sound is silent

No error, but you hear nothing. Check the computer's volume and the speakers. A sound loaded with
no sound device (or with `FUNGROUND_HEADLESS=1`) plays in silence on purpose, and keeps time. Also
check `sound.set_volume()` and that you called `play()` or `loop()`.

### A microphone method that needs the whole sound

```
ValueError: microphone.tempo() looks at a whole sound. Use microphone.capture(seconds).tempo() to look at what was heard
```

A microphone has no end, so it has no tempo or key. Capture a few seconds first, and ask the
capture. See chapter [16](16_sound.md#record-then-draw).

## Warnings

A **warning** is not an error. The sketch carries on, and funground prints a note.

```
FungroundWarning: draw() finished with 1 f.push() call(s) still open; funground popped them for you. Add a matching f.pop(), or use `with f.saved_state():`.
FungroundWarning: f.pop() called without a matching f.push(); ignored.
FungroundWarning: draw() finished inside a shape: f.begin_shape() had no f.end_shape(), so nothing was drawn for it.
```

Each `f.push()` needs one `f.pop()`, and each `f.begin_shape()` needs an `f.end_shape()`. The safest way
is `with f.saved_state():`, which closes itself. See chapter [8](08_transforms.md).

## Still stuck?

1. Read the **last line** of the message again. Then read the line number above it.
2. Make the sketch smaller. Delete lines until the error goes, then put the last one back.
3. Print what you have: `print(x)` shows a value in the terminal.
4. Compare with a working example in the [gallery](../gallery/README.md) that does something close.
5. Look up the name in the [Quick Reference](../reference/Quick_Reference.md).
