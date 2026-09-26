# 10. Interaction: mouse and keyboard

There are two ways to react to the mouse and keyboard.

## 1. Look, every frame

Inside `draw()`, check where things are:

| Value | Meaning |
|---|---|
| `f.mouse_x`, `f.mouse_y` | Where the mouse is |
| `f.pmouse_x`, `f.pmouse_y` | Where it was in the previous frame |
| `f.is_mouse_pressed` | `True` while a mouse button is held |
| `f.mouse_button` | The last button pressed: `"left"`, `"center"` or `"right"` |
| `f.key_down("left")` | `True` while that key is held: `"left"`, `"right"`, `"up"`, `"down"`, `"space"`, `"enter"`, `"escape"` or any single character |
| `f.is_key_pressed` | `True` while any key is held |
| `f.key`, `f.key_code` | The last key pressed: a character like `"a"`, or a name like `"left"` / its code |

```python
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("tomato" if f.is_mouse_pressed else "skyblue")
    f.circle(f.mouse_x, f.mouse_y, 60)


f.run()
```

![Follow the mouse](../gallery/images/interaction-01_follow_the_mouse.png)

Held keys work the same way: check `f.key_down("left")` inside `draw()` and move a little each
frame. The gallery's *Move with the keyboard* example does exactly that.

![Move with the keyboard](../gallery/images/interaction-03_keyboard_mover.png)

## 2. Be told, when it happens

Define a function with one of these names and funground calls it when that thing happens —
once per click or key press, just before the next `draw()`:

| Define… | Called when |
|---|---|
| `mouse_pressed()` / `mouse_released()` | a mouse button goes down / up |
| `mouse_clicked()` | a button is pressed and released |
| `mouse_moved()` / `mouse_dragged()` | the mouse moves / moves with a button held |
| `mouse_wheel(delta)` | the wheel turns; `delta` is positive when scrolling down |
| `key_pressed()` / `key_released()` | a key goes down / up (`f.key` says which) |
| `key_typed()` | a character key is typed (not arrows or Shift) |

Callbacks are the right tool for "do this once per click": looking at `f.is_mouse_pressed` in
`draw()` would do it every frame the button is held.

```python
import funground as f

colour = "tomato"


def setup():
    f.size(640, 400)
    f.background("white")


def draw():
    pass


def mouse_dragged():
    f.stroke(colour)
    f.stroke_width(8)
    f.line(f.pmouse_x, f.pmouse_y, f.mouse_x, f.mouse_y)


def key_pressed():
    global colour
    if f.key == "c":
        f.background("white")
    if f.key == "b":
        colour = "navy"


f.run()
```

![A paint program](../gallery/images/interaction-02_paint.png)

Callbacks keep working while the sketch is paused with `f.no_loop()` — which is how a key can
call `f.redraw()` or `f.loop()`. See [7. Animation and time](07_animation_and_time.md).

![Pause and step](../gallery/images/animation-04_pause.png)

**Escape** always ends a sketch.

*Coming from Playground 0.5?* `f.mouse_pressed` is now `f.is_mouse_pressed`, because
`mouse_pressed()` is the name of the callback — as in p5.js.

**Next:** [11. Randomness and noise](11_randomness_and_noise.md)
