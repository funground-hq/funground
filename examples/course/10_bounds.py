# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

f.size(900, 355)
f.background("#f3efe6")
for panel, (low, high) in enumerate([(10, 16), (10, 36), (30, 36)]):
    left = 20 + panel*295
    f.random_seed(12)
    f.no_stroke()
    for row in range(5):
        for col in range(5):
            diameter = f.random(low, high)
            f.fill(f.random_choice(["#264653", "#2a9d8f", "#e76f51"]))
            f.circle(left + 25 + col*53, 45 + row*53, diameter)
    f.fill("#264653")
    f.text_size(16)
    f.text_align("left", "top")
    f.text("Diameters " + str(low) + "–" + str(high), left, 320)
f.save("10_bounds.png")
f.show()
