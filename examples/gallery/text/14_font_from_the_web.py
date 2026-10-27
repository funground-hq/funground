"""A font from the web

A small poster set in Lora, a font that is not on your computer. The sketch gives f.load_font() the
address of the font file. The first run downloads it. After that the sketch uses the copy that was kept in
the fonts folder beside it, so it works without the internet.

How it works:
- f.load_font() takes a web address where it would take a path. An address starts with https://.
- The first run downloads the file into fonts/ beside the sketch. A small file there, sources.json, says where
  the font came from. The second run finds the copy and does not use the internet.
- Lora is a variable font, so one file gives every weight. f.font_variations(wght=700) makes the headline bold
  and f.font_variations(wght=400) makes the next line light again.
- f.text_font() then chooses the font, and f.text_size() and f.text_align() place the words as with any font.
- Keep the font file and its licence (OFL.txt, in the same folder) with the sketch when you share it.

Make it yours:
- Change HEADLINE and SUBTITLE to your own words.
- Try wght=500 or wght=600 for a weight in between.
- Use another font file: on GitHub, open the file, copy the address from the browser, and give it to f.load_font().
  A github.com address is read from the right place for you.
- Ask for a family by name instead, with f.load_font("Lora", provider=f.CONSTANTS.PROVIDERS.GOOGLE_FONTS, weight=700).
"""
import funground as f

ADDRESS = "https://raw.githubusercontent.com/google/fonts/main/ofl/lora/Lora%5Bwght%5D.ttf"
HEADLINE = "Letters from far away"
SUBTITLE = "set in Lora, downloaded once, kept beside this sketch"

f.size(640, 360)
f.background("ivory")

lora = f.load_font(ADDRESS)
f.text_font(lora)

f.stroke("tomato")
f.stroke_width(3)
f.line(60, 70, 160, 70)
f.no_stroke()

f.fill(35, 30, 45)
f.text_align("left", "baseline")
f.font_variations(wght=700)
f.text_size(f.fit_text_size(HEADLINE, f.width - 120, 90))
f.text(HEADLINE, 60, 190)

f.font_variations(wght=400)
f.fill("tomato")
f.text_size(22)
f.text(SUBTITLE, 60, 240)

f.fill(35, 30, 45)
f.text_size(15)
f.text(lora.family() + ", Open Font License (see OFL.txt)", 60, 320)

f.show()
