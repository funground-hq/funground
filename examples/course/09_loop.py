# Original Funground course sketch. CC0; see ../LICENSE.

# Optional GIF export: install funground[extras] if Pillow is not available.
import math
import funground as f

f.size(420, 260)
f.frame_duration(1 / 12)
for step in range(24):
    if step:
        f.new_page()
    f.background("#f3efe6")
    progress = (1 - math.cos(2*math.pi*step/24)) / 2
    f.no_stroke()
    f.fill("#e76f51")
    f.circle(50 + progress*320, 120, 36)
    if step == 0:
        f.save("09_loop.png")
f.save("09_loop.gif")
f.show()
