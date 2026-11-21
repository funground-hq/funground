"""Finger-jointed box

Six flat panels that fit together into a box, drawn at their real size for a laser cutter. Each edge has teeth
(fingers) that slot into the gaps of the panel it meets, so the box holds together with a dab of glue or none. Use the
sliders to set the box's width, depth and height and the thickness of your sheet, in millimetres. "save" writes
box.pdf and box.svg: open the PDF in the laser cutter's program. Red lines are cut; blue is engraved.

How it works:
- Everything is worked out in millimetres, and draw_sheet() turns millimetres into units with per_mm. On the screen
  per_mm is SCREEN, so an A3 sheet fits in the window. For the file it is f.mm(1), how many funground units one
  millimetre is, so the panels come out at their real size. A PDF keeps that size when it is printed or cut.
- A panel is its middle, a rectangle one thickness in from each edge, joined with | (union) to the pieces of the border
  it owns. Along each edge the border is cut into an odd number of pieces about FINGER wide. The panel that ranks
  higher (RANK) owns pieces 0, 2, 4 and so on; the panel it meets owns the others, so the two edges fit exactly.
- An odd number means both end pieces go to the same panel, so the pattern reads the same from either end.
- Where three panels meet in a corner, the corner square goes to the one that ranks highest. Without a lid, the walls'
  top edges have nothing to meet and stay straight.
- A laser burns away a thin line, about KERF wide, so a piece comes out a little smaller than its line. cut() makes each
  outline bigger by half of that: expand_stroke(KERF) is the shape a line KERF wide would paint around the outline, and
  | adds it on. join="miter" keeps the corners sharp. Holes get smaller by the same amount.
- "save" draws the sheet again on f.create_graphics(), an off-screen picture the size of A3, and saves that picture.
  It starts transparent and gets no plywood background, because a cutter would treat a filled rectangle as one more
  shape to engrave. The brown names are left out of it too.

Make it yours:
- Put your own name in NAME, or make it bigger with f.text_size().
- Measure your sheet with a ruler or callipers and set the thickness slider to it: the fingers must be as long as the
  sheet is thick, or they stick out or fall short.
- Ask what kerf your laser cutter burns, and change KERF. If the joints are loose, make it bigger; if they will not go
  together, make it smaller. Cut one corner first to test it.
- Cut a hole in the lid: take f.path().circle() away from it with - (difference) in make_panels().
- Untick "lid" for an open tray.
"""
import funground as f

NAME = "My box"         # engraved on the front
KERF = 0.2              # how wide a line the laser burns away, in mm
FINGER = 10             # about how wide a finger is, in mm
GAP = 4                 # the space between panels on the sheet, in mm
EDGE = 10               # the space round the edge of the sheet, in mm
RANK = {"bottom": 3, "top": 3, "front": 2, "back": 2, "left": 1, "right": 1}
CUT, ENGRAVE = "red", "blue"
SHEET = "#ecd9b4"         # plywood, on the screen only
SCREEN = 1.8             # pixels for each mm on the screen
A3 = (420, 297)          # the sheet, in mm

width = depth = height = thickness = lid = save_button = None


def setup():
    global width, depth, height, thickness, lid, save_button
    f.size(round(A3[0] * SCREEN), round(A3[1] * SCREEN))
    width = f.create_slider(40, 130, 100, step=1, label="width mm")
    depth = f.create_slider(40, 120, 80, step=1, label="depth mm")
    height = f.create_slider(30, 120, 60, step=1, label="height mm")
    thickness = f.create_slider(2, 6, 3, step=0.5, label="sheet mm")
    lid = f.create_checkbox("lid", True)
    save_button = f.create_button("save")


def rank(name):
    """How high a panel ranks; an edge with no panel to meet ranks lowest."""
    return RANK.get(name, 0)


def pieces(length, thick, mine, other):
    """The pieces of the border along an edge that this panel owns, as (start, size) pairs in mm."""
    inside = length - 2 * thick
    if other is None:
        return [(thick, inside)]          # nothing to meet: the whole edge is ours
    count = max(1, round(inside / FINGER))
    if count % 2 == 0:
        count += 1                        # odd, so both ends go to the same panel
    size = inside / count
    first = 0 if rank(mine) > rank(other) else 1
    return [(thick + k * size, size) for k in range(first, count, 2)]


def panel(name, w, h, thick, top, right, bottom, left):
    """One panel, w by h mm, with fingers on each edge for the panel it meets there (None for nothing)."""
    shape = f.path().rect(thick, thick, w - 2 * thick, h - 2 * thick)
    for other, y in ((top, 0), (bottom, h - thick)):
        for x, size in pieces(w, thick, name, other):
            shape = shape | f.path().rect(x, y, size, thick)
    for other, x in ((left, 0), (right, w - thick)):
        for y, size in pieces(h, thick, name, other):
            shape = shape | f.path().rect(x, y, thick, size)
    for x, y, across, down in ((0, 0, left, top), (w - thick, 0, right, top),
                               (0, h - thick, left, bottom), (w - thick, h - thick, right, bottom)):
        if rank(name) > rank(across) and rank(name) > rank(down):
            shape = shape | f.path().rect(x, y, thick, thick)
    return shape


def make_panels(w, d, h, thick, with_lid):
    """The panels of a w by d by h box, as (name, shape, place on the sheet) in mm."""
    top = "top" if with_lid else None
    row = EDGE + max(d, h) + GAP           # where the second row starts
    panels = [
        ("bottom", panel("bottom", w, d, thick, "back", "right", "front", "left"), (EDGE, EDGE)),
        ("front", panel("front", w, h, thick, top, "right", "bottom", "left"), (EDGE + w + GAP, EDGE)),
        ("left", panel("left", d, h, thick, top, "back", "bottom", "front"), (EDGE + 2 * (w + GAP), EDGE)),
        ("back", panel("back", w, h, thick, top, "left", "bottom", "right"), (EDGE + w + GAP, row)),
        ("right", panel("right", d, h, thick, top, "front", "bottom", "back"), (EDGE + 2 * (w + GAP), row)),
    ]
    if with_lid:
        panels.append(("top", panel("top", w, d, thick, "front", "right", "back", "left"), (EDGE, row)))
    return panels


def cut(shape):
    """The outline to cut, bigger by half the kerf all round, so the piece comes out the size it was drawn."""
    return shape | shape.expand_stroke(KERF, join="miter")


def draw_sheet(canvas, per_mm, labels):
    """Draw every panel on canvas (f, or a picture), per_mm units for each millimetre, with names if labels is True."""
    w, d, h = width.value(), depth.value(), height.value()
    for name, shape, (x, y) in make_panels(w, d, h, thickness.value(), lid.checked()):
        canvas.no_fill()
        canvas.stroke(CUT)
        canvas.stroke_width(1)
        canvas.draw_path(cut(shape).translate(x, y).scale(per_mm))
        _, _, across, down = shape.bounds()
        middle_x, middle_y = (x + across / 2) * per_mm, (y + down / 2) * per_mm
        canvas.no_stroke()
        canvas.text_align("center", "center")
        if name == "front":
            canvas.fill(ENGRAVE)
            canvas.text_size(10 * per_mm)        # letters 10 mm tall
            canvas.draw_path(canvas.text_path(NAME, middle_x, middle_y))
        elif labels:
            canvas.fill("saddlebrown")
            canvas.text_size(14)
            canvas.text(name, middle_x, middle_y)


def draw():
    f.background(SHEET)
    draw_sheet(f, SCREEN, labels=True)
    if save_button.clicked():
        sheet = f.create_graphics(round(f.mm(A3[0])), round(f.mm(A3[1])))
        draw_sheet(sheet, f.mm(1), labels=False)
        sheet.save("box.pdf")
        sheet.save("box.svg")


f.run()
