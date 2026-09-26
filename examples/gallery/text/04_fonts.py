"""Fonts and styles

f.text_style() switches between the four built-in styles: normal, bold, italic and
bold_italic. f.load_font() reads a font file from disk and f.text_font() switches to it;
f.text_font(None) goes back to the built-in family, remembering whatever style was set.
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("black")
    f.text_size(32)

    f.text_style("normal")
    f.text("Normal - the default", 30, 20)

    f.text_style("bold")
    f.text("Bold", 30, 80)

    f.text_style("italic")
    f.text("Italic", 30, 140)

    f.text_style("bold_italic")
    f.text("Bold italic", 30, 200)

    mono = f.load_font("fonts/DejaVuSansMono.ttf")
    f.text_font(mono, size=28)
    f.text("A loaded font: DejaVu Sans Mono", 30, 270)

    f.text_font(None)                       # back to the built-in family
    f.text_style("normal")
    f.fill("gray")
    f.text_size(16)
    f.text("text_font(None) returns to the built-in family", 30, 340)


f.run()
