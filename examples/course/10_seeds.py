# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

f.size(900, 355)
f.background("#f3efe6")
for panel, seed in enumerate([12, 29, 61]):
    left = 20 + panel*295
    f.random_seed(seed)
    f.no_stroke()
    for row in range(5):
        for col in range(5):
            diameter = f.random(10, 36)
            f.fill(f.random_choice(["#264653", "#2a9d8f", "#e76f51"]))
            f.circle(left + 25 + col*53, 45 + row*53, diameter)
    f.fill("#264653")
    f.text_size(16)
    f.text_align("left", "top")
    f.text("Seed " + str(seed), left, 320)
f.save("10_seeds.png")
f.show()
