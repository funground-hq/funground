# Original Funground course sketch. CC0; see ../LICENSE.
# Extend: the same experiment as 03_palettes.py, with funground laying out the versions.

import funground as f

# paper, ink, accent
PALETTES = {
    "Pale paper": ("#f4f1de", "#1d3557", "#e76f51"),
    "Dark paper": ("#16324f", "#f5f0dd", "#edc96b"),
    "Soft palette": ("#eef2e6", "#374939", "#9ab880"),
}

f.size(600, 400)
f.background("#ded8cc")


def card(palette):
    # One version: the same card in one palette. Only the colours change.
    paper, ink, accent = PALETTES[palette]
    f.no_stroke()
    f.fill(paper)
    f.rect(0, 0, 600, 400)
    f.fill(accent)
    f.circle(500, 95, 80)
    f.fill(ink)
    f.text_align("left", "top")
    f.text_style("bold")
    f.text_size(72)
    f.text("READ", 50, 170)
    f.text_style("normal")
    f.text_size(30)
    f.text("Saturday at 10 am", 50, 300)


f.variations(card, palette=list(PALETTES))

# When one version is the one you choose, keep it with a sentence:
# f.keep("I kept the dark paper because ...", palette="Dark paper")

f.save("03_palettes_variations.png")
f.show()
