"""A script: draw once, no draw() needed

Not every picture moves. A script has no functions: f.size() makes the canvas, the lines after
it draw on it, f.save() writes a file at once, and f.show() opens a window to look at it.
"""
import funground as f

f.size(640, 400, title="a script")

# sky
f.background("lightskyblue")
f.no_stroke()

# a low sun with a pale halo
f.fill((255, 255, 255, 90))
f.circle(470, 250, 170)
f.fill("orange")
f.circle(470, 250, 100)

# sea, over the bottom of the sun
f.fill("steelblue")
f.rect(0, 250, 640, 150)

# a sailing boat: hull, mast and sail
f.fill("saddlebrown")
f.quad(150, 290, 290, 290, 265, 325, 175, 325)
f.stroke("black")
f.stroke_width(3)
f.line(220, 290, 220, 170)
f.no_stroke()
f.fill("white")
f.triangle(226, 180, 226, 280, 290, 280)

f.fill("midnightblue")
f.text_size(28)
f.text("Off we go", 30, 350)

f.save("a_script.pdf")
f.show()
