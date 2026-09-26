# 13. Saving your work

`f.save("name.png")` writes the current frame to a file when the frame is finished — wherever in
`draw()` you call it.

```python
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("ivory")
    f.fill("tomato")
    f.circle(320, 200, 200)
    if f.frame_count == 0:
        f.save("my_picture.png")
        f.save("my_picture.pdf")


f.run(max_frames=1)
```

| Ending | What you get |
|---|---|
| `.png` | A picture, at your screen's full resolution |
| `.pdf` | A document made of shapes: sharp at any size, good for printing |
| `.svg` | Shapes for the web or for editing in a drawing program |

A **PNG** holds exactly what is in the window — including everything earlier frames left there.
A **PDF or SVG** holds the shapes drawn in *that one frame*, so for those, draw the whole picture
in the frame you save (start `draw()` with `f.background(...)`).

In PDF and SVG files, text is saved as letter *shapes*, so it looks right everywhere but cannot
yet be selected or searched.

## A transparent background

`f.clear()` makes every pixel transparent instead of painting a colour. A PNG saved afterwards
keeps the transparency — handy for stickers, icons and pictures to place on a web page. In the
window, transparent shows as black.

![Transparent PNG](../gallery/images/saving-02_transparent_png.png)

## Saving an animation

`f.save_frames("frames/####.png", 60)` saves this frame and the next 59 as numbered pictures:
`frames/0001.png`, `frames/0002.png`, and so on. The `####` becomes the number.

```python
import funground as f


def setup():
    f.size(640, 200)


def draw():
    f.background("black")
    f.fill("gold")
    f.circle(f.frame_count * 10, 100, 40)
    if f.frame_count == 0:
        f.save_frames("frames/####.png", 60)


f.run()
```

![Saving an animation as frames](../gallery/images/saving-03_save_frames.png)

To turn the pictures into a video or a GIF, use a program such as [ffmpeg](https://ffmpeg.org):

```
ffmpeg -framerate 30 -i frames/%04d.png my_animation.mp4
ffmpeg -framerate 30 -i frames/%04d.png my_animation.gif
```

`%04d` is ffmpeg's way of writing `####`.

## Saving without a window

Set the environment variable `FUNGROUND_HEADLESS=1` and funground draws without opening a
window — useful for making many pictures at once. Combine it with `f.run(max_frames=...)`.

**Next:** [14. Coming from p5.js and Processing](14_coming_from_p5_processing.md)
