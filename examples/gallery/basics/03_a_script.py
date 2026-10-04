"""A script: draw once, no draw() needed

Not every picture moves. A script has no functions: f.size() makes the canvas, the lines after
it draw on it, f.save() writes a file at once, and f.show() opens a window to look at it.

How it works:
- There is no setup() and no draw(). The lines run once, from top to bottom.
- f.size() makes the canvas. After that, each line draws on top of the ones before it.
- Order matters. The sea is drawn after the sun, so it covers the bottom of the sun.
- f.fill() and f.stroke() set the style for what follows. f.no_stroke() switches the outline off.
- f.circle(), f.rect(), f.quad(), f.triangle(), f.line() and f.text() draw the sun, sea, boat and
  words.
- f.save("a_script.pdf") writes the picture to a file. f.show() opens a window with it.

Make it yours:
- Change the sky: f.background("lightskyblue") takes any colour name.
- Move the sun with the two numbers after 470 in the f.circle() lines. Move both circles together.
- Save as a different kind of file: use "a_script.png" or "a_script.svg" in f.save().
- Add a second boat: copy the hull, mast and sail lines and change the numbers.
- Add stars with f.circle() before the sea is drawn, or change the words in f.text().
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
