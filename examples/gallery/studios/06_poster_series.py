"""A poster series: four events, one design (studio 6)

One function draws a poster for any event, so the posters look like a family. f.variations() draws
all four side by side on one sheet, to compare them. Press K to keep the sheet: a numbered picture,
a copy of this file and a record of the seed go into a folder called studio. The same picture is
written without the studio words in examples/studios/06_poster_series_before.py.

How it works:
- poster(event) draws one poster on the whole A4 page, as if it were alone: a grid of spots, the
  title, and the date on a band. f.grid(4, 6) and grid.span() give its cells and its text areas.
- The band runs to the edges of the page, past the margin: f.area() makes it from f.ground, the
  whole page.
- spot(colour) is a function that returns a mark, so every event gets its own colour of spot.
  place(..., anchor="center", width=...) sizes each spot to its cell.
- f.variations(poster, columns=2, event=[...]) calls poster() once for each event and shrinks each
  poster into a labelled cell. Every cell starts from the same random seed, so the spots fall in
  the same cells on every poster.
- f.random_seed(2026) fixes that seed, so the sheet is the same every time.
- f.keep() saves the sheet with a note and the settings given, in the studio folder.

Make it yours:
- Add a fifth event to EVENTS. The sheet makes room for it.
- Change 0.55 in poster() to make the spots thicker or thinner on the ground.
- Change the seed in f.random_seed() to scatter the spots differently.
- Change the second argument of f.grid() in poster() and see the whole series change.
"""
import funground as f

# event: (paper, ink, accent, date)
EVENTS = {
    "Book fair": ("#264653", "#f4f1de", "#e9c46a", "12 - 14 March"),
    "Science week": ("#1d3557", "#f1faee", "#e63946", "3 - 7 June"),
    "Music night": ("#3c1642", "#fdf0d5", "#f4a261", "21 June"),
    "Sports day": ("#0b3d2e", "#f0efeb", "#90be6d", "9 September"),
}


def spot(colour, ink):
    """A ring with a dot in it, as a mark centred on its own (0, 0)."""
    with f.mark() as m:
        f.no_fill()
        f.stroke(colour)
        f.stroke_width(6)
        f.circle(0, 0, 40)
        f.no_stroke()
        f.fill(ink)
        f.circle(0, 0, 12)
    return m


def poster(event):
    paper, ink, accent, date = EVENTS[event]
    f.background(paper)
    grid = f.grid(4, 6, gutter=f.mm(4))
    mark = spot(accent, ink)
    for cell in grid[:16]:                              # the top four rows
        if f.random() < 0.55:
            mark.place(cell.cx, cell.cy, anchor="center", width=cell.width * f.random(0.35, 1))
    title = grid.span(0, 4, cols=4)
    f.fill(ink)
    f.text_style("bold")
    f.text_size(54)
    f.text_align("left", "bottom")
    f.text(event, title.left, title.bottom)
    footer = grid.span(0, 5, cols=4)
    band = f.area(f.ground.left, footer.top - f.mm(3), f.ground.width, f.ground.bottom - footer.top + f.mm(3))
    f.no_stroke()
    f.fill(accent)
    f.rect(band.left, band.top, band.width, band.height)    # full bleed: from edge to edge of the page
    f.fill(paper)
    f.text_style("normal")
    f.text_size(24)
    f.text_align("left", "top")
    f.text(date + "  ·  Town hall  ·  all welcome", footer.left, footer.top)


def setup():
    f.size("A4", margin=f.mm(12))
    f.random_seed(2026)


def draw():
    f.background("#e9e5dc")
    f.variations(poster, columns=2, event=list(EVENTS))


def key_pressed():
    if f.key == "k":
        f.keep("the series so far", events=len(EVENTS))


f.run()
