# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

f.size(720, 300)
f.background("#f3efe6")
for row in range(2):
    y = 95 + row*125
    f.fill("#264653")
    f.text_size(17)
    f.text_align("left", "top")
    f.text(["Equal speed", "Ease in and out"][row], 20, y-9)
    f.no_stroke()
    for step in range(7):
        u = step / 6
        p = u if row == 0 else 3*u*u - 2*u*u*u
        f.circle(240 + p*425, y, 16)
f.save("09_timing.png")
f.show()
