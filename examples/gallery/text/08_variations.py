"""Variable font axes

f.font_variations(wght=700) sets the axes of a variable font, like its weight or width.
The built-in font is not variable, so here the three lines look the same: an axis the
font does not have is ignored, which makes the call safe to leave in. Load a variable
font with f.load_font() and the weight really changes. f.font_variations() with nothing
in the brackets goes back to the font's own defaults.
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background(246, 243, 236)
    f.no_stroke()
    f.text_size(36)

    f.fill(30, 40, 90)
    f.font_variations(wght=300)
    f.text("Light request: wght 300", 40, 50)

    f.font_variations(wght=700)
    f.text("Heavy request: wght 700", 40, 130)

    f.font_variations(wght=700, wdth=75)
    f.text("Two axes: wght and wdth", 40, 210)

    f.font_variations()                     # back to the font's defaults
    f.fill(110)
    f.text_size(18)
    f.text("This font has no axes, so nothing changes.", 40, 300)
    f.text("A variable font would follow each request.", 40, 330)


f.run()
