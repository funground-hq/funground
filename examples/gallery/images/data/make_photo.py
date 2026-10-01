"""Makes photo.jpg, the picture that 01_load_image.py loads.

This is a funground script (no window, no draw()). Run it from this folder:

    python make_photo.py

It draws a small scene and saves photo.png. To get the JPEG, let pygame re-save it:

    python -c "import pygame; pygame.image.save(pygame.image.load('photo.png'), 'photo.jpg')"

Then delete photo.png. Everything here is original and free to use (CC0).
"""
import funground as f

f.size(400, 300)

# sky, fading from deep blue to peach at the horizon
sky = f.linear_gradient(0, 0, 0, 200, ["midnightblue", "orchid", "peachpuff"], [0, 0.6, 1])
f.no_stroke()
f.fill(sky)
f.rect(0, 0, 400, 300)

# a low sun
f.fill("gold")
f.circle(270, 170, 90)

# far hills, then near hills
f.fill("slateblue")
f.circle(80, 260, 260)
f.circle(330, 290, 240)
f.fill("seagreen")
f.circle(200, 400, 360)

# a few stars
f.fill("white")
for x, y in [(40, 30), (110, 70), (190, 25), (300, 45), (360, 90), (250, 100)]:
    f.circle(x, y, 4)

# a little house on the green hill
f.fill("firebrick")
f.rect(150, 205, 60, 40)
f.fill("sandybrown")
f.triangle(142, 205, 218, 205, 180, 170)
f.fill("khaki")
f.rect(172, 222, 16, 23)

f.save("photo.png")
