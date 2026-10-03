"""A poster file

This script draws a poster and saves it twice, as poster.pdf and poster.svg. The files carry more
than a picture.

The poster has four layers: "background", "artwork", "words" and "notes". The "notes" layer is
hidden with f.hide_layer(), so it is in the files but switched off.

The words are real text. There is an English headline, a Hindi line and an emoji. funground's
built-in fallback fonts draw the Hindi and the emoji.

What opens where:
- The PDF opens in Acrobat or Illustrator. The layers show in the layers panel, and you can switch
  each one on and off. The text can be selected and searched.
- The SVG opens in Inkscape or Illustrator. The layers are Inkscape layers. The text is live, so
  you can click it and change it.
- To edit the text, the font must be installed on your computer. Without it, the program swaps in
  another font. Guide chapter 13 ("Saving your work") has the section on fonts.
- For Hindi in Illustrator, switch on the World-Ready Composer in its Type settings. Without it
  the letters can come out joined up wrongly.

The gallery picture shows the poster. The hidden notes are not in it.
"""
import funground as f


def setup():
    f.size(480, 640)


def draw():
    if f.frame_count > 0:                # the poster is made once, in the first frame
        return
    # Each layer has its own pen, so each one turns the outline off.
    # Layer 1: the background, a soft gradient from top to bottom.
    with f.layer("background"):
        f.no_stroke()
        f.fill(f.linear_gradient(0, 0, 0, 640, ["midnightblue", "darkorchid", "tomato"]))
        f.rect(0, 0, 480, 640)

    # Layer 2: the artwork, a sun, hills and a rounded card for the words.
    with f.layer("artwork"):
        f.no_stroke()
        f.fill(f.linear_gradient(0, 120, 0, 340, ["gold", "orange"]))
        f.circle(240, 250, 190)
        f.fill(28, 20, 70)
        f.rect(-40, 400, 300, 300, 150, 150, 0, 0)
        f.fill(48, 30, 90)
        f.rect(180, 440, 360, 300, 180, 180, 0, 0)
        f.fill(255, 255, 255, 215)
        f.rect(40, 440, 400, 160, 28)

    # Layer 3: the words. All of it is real text in the saved files.
    with f.layer("words"):
        f.no_stroke()
        f.text_align("center", "center")
        f.fill("white")
        f.text_size(54)
        f.text("Open Day", 240, 70)
        f.text_size(26)
        f.fill("midnightblue")
        f.text("नमस्ते", 240, 490)
        f.text_size(18)
        f.text("Come and see what we made", 240, 540)
        f.text_size(36)
        f.text("🎉", 240, 575)

    # Layer 4: notes for the person who edits the file. Hidden, but still in it.
    with f.layer("notes"):
        f.fill("lime")
        f.text_align("left", "top")
        f.text_size(14)
        f.text("Check the date before printing", 12, 12)
    f.hide_layer("notes")

    f.save("poster.pdf")
    f.save("poster.svg")


f.run()
