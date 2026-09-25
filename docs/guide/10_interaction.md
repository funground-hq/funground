# 10. Interaction: mouse and keyboard

There are two ways to react to the mouse and keyboard.

## 1. Look, every frame

Inside `draw()`, check where things are:

| Value | Meaning |
|---|---|
| `p.mouse_x`, `p.mouse_y` | Where the mouse is |
| `p.pmouse_x`, `p.pmouse_y` | Where it was in the previous frame |
| `p.is_mouse_pressed` | `True` while a mouse button is held |
| `p.mouse_button` | The last button pressed: `"left"`, `"center"` or `"right"` |
| `p.key_down("left")` | `True` while that key is held: `"left"`, `"right"`, `"up"`, `"down"`, `"space"`, `"enter"`, `"escape"` or any single character |
| `p.is_key_pressed` | `True` while any key is held |
| `p.key`, `p.key_code` | The last key pressed: a character like `"a"`, or a name like `"left"` / its code |

```python
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("tomato" if p.is_mouse_pressed else "skyblue")
    p.circle(p.mouse_x, p.mouse_y, 60)


p.run()
```

![Follow the mouse](../gallery/images/interaction-01_follow_the_mouse.png)

Held keys work the same way: check `p.key_down("left")` inside `draw()` and move a little each
frame. The gallery's *Move with the keyboard* example does exactly that.

![Move with the keyboard](../gallery/images/interaction-03_keyboard_mover.png)

## 2. Be told, when it happens

Define a function with one of these names and Playground calls it when that thing happens —
once per click or key press, just before the next `draw()`:

| Define… | Called when |
|---|---|
| `mouse_pressed()` / `mouse_released()` | a mouse button goes down / up |
| `mouse_clicked()` | a button is pressed and released |
| `mouse_moved()` / `mouse_dragged()` | the mouse moves / moves with a button held |
| `mouse_wheel(delta)` | the wheel turns; `delta` is positive when scrolling down |
| `key_pressed()` / `key_released()` | a key goes down / up (`p.key` says which) |
| `key_typed()` | a character key is typed (not arrows or Shift) |

Callbacks are the right tool for "do this once per click": looking at `p.is_mouse_pressed` in
`draw()` would do it every frame the button is held.

```python
import playground as p

colour = "tomato"


def setup():
    p.size(640, 400)
    p.background("white")


def draw():
    pass


def mouse_dragged():
    p.stroke(colour)
    p.stroke_width(8)
    p.line(p.pmouse_x, p.pmouse_y, p.mouse_x, p.mouse_y)


def key_pressed():
    global colour
    if p.key == "c":
        p.background("white")
    if p.key == "b":
        colour = "navy"


p.run()
```

![A paint program](../gallery/images/interaction-02_paint.png)

Callbacks keep working while the sketch is paused with `p.no_loop()` — which is how a key can
call `p.redraw()` or `p.loop()`. See [7. Animation and time](07_animation_and_time.md).

![Pause and step](../gallery/images/animation-04_pause.png)

**Escape** always ends a sketch.

*Coming from Playground 0.5?* `p.mouse_pressed` is now `p.is_mouse_pressed`, because
`mouse_pressed()` is the name of the callback — as in p5.js.

**Next:** [11. Randomness and noise](11_randomness_and_noise.md)
