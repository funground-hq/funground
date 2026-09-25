# 13. Saving your work

`p.save("name.png")` writes the current frame to a file when the frame is finished — wherever in
`draw()` you call it.

```python
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("ivory")
    p.fill("tomato")
    p.circle(320, 200, 200)
    if p.frame_count == 0:
        p.save("my_picture.png")
        p.save("my_picture.pdf")


p.run(max_frames=1)
```

| Ending | What you get |
|---|---|
| `.png` | A picture, at your screen's full resolution |
| `.pdf` | A document made of shapes: sharp at any size, good for printing |
| `.svg` | Shapes for the web or for editing in a drawing program |

In PDF and SVG files, text is saved as letter *shapes*, so it looks right everywhere but cannot
yet be selected or searched.

## A transparent background

`p.clear()` makes every pixel transparent instead of painting a colour. A PNG saved afterwards
keeps the transparency — handy for stickers, icons and pictures to place on a web page. In the
window, transparent shows as black.

![Transparent PNG](../gallery/images/saving-02_transparent_png.png)

## Saving without a window

Set the environment variable `PLAYGROUND_HEADLESS=1` and Playground draws without opening a
window — useful for making many pictures at once. Combine it with `p.run(max_frames=...)`.

**Next:** [14. Coming from p5.js and Processing](14_coming_from_p5_processing.md)
