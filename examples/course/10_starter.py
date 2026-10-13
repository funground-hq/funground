# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

SEED = 12
PALETTE = ["#264653", "#2a9d8f", "#e76f51"]

f.size(420, 420)
f.background("#f3efe6")
f.random_seed(SEED)
f.no_stroke()
for row in range(6):
    for col in range(6):
        diameter = f.random(12, 42)
        f.fill(f.random_choice(PALETTE))
        f.circle(35 + col*70, 35 + row*70, diameter)
f.save("10_starter.png")
f.show()
