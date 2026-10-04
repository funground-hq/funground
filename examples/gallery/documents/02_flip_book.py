"""A flip book saved as a GIF

Every page of a script is one frame of a GIF. Eight pages show a ball bouncing across, and
f.save("flip_book.gif") writes them in order. The gallery picture shows the last page.

How it works:
- f.size(320, 240) sets the size of every page. All the pages must be the same size.
- f.frame_duration(0.15) says how long each page is shown, in seconds.
- The loop draws one page for each step. f.new_page() starts each new page after the first.
- across goes from 0 to 1 over the pages. It sets the ball's x, and height sets how high the ball
  is. height is 0 at both ends and 1 in the middle, which makes the bounce.
- The shadow gets smaller as the ball rises, so f.ellipse() uses 40 - 20 * height.
- f.save("flip_book.gif") writes every page, and the GIF loops for ever. An MP4 works the same way
  with f.save("flip_book.mp4"), but it needs the free program ffmpeg.

Make it yours:
- Change STEPS = 8 to a bigger number for a smoother flip book. Try 16.
- Change 0.15 in f.frame_duration() to speed it up or slow it down.
- Change 140 in the ball's y value to make it bounce higher or lower.
- Change the colours in f.background() and f.fill().
- Make the ball grow as it rises: use 40 + 20 * height as its size.
"""
import funground as f

f.size(320, 240)
f.frame_duration(0.15)
f.no_stroke()

STEPS = 8
for step in range(STEPS):
    if step:
        f.new_page()
    across = step / (STEPS - 1)                  # 0 on the first page, 1 on the last
    height = 1 - (2 * across - 1) ** 2           # 0 at both ends, 1 in the middle: the bounce
    x = 40 + 240 * across
    f.background("midnightblue")
    f.fill("black")
    f.ellipse(x, 225, 40 - 20 * height, 8)       # the shadow shrinks as the ball rises
    f.fill("gold")
    f.circle(x, 200 - 140 * height, 40)

f.save("flip_book.gif")
f.show()
