"""A flip book saved as a GIF

Every page of a script is one frame of a GIF. f.frame_duration(0.15) says how long each page is
shown, in seconds. f.save("flip_book.gif") writes all the pages, in order, and the GIF loops for
ever. All the pages must be the same size. An MP4 works the same way, f.save("flip_book.mp4"),
but it needs the free program ffmpeg. The gallery picture shows the last page.
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
