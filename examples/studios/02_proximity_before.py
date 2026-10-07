"""Proximity, without the studio words (studio 2, before)

The same picture as examples/gallery/studios/02_proximity.py: four panels of the same 36 dots,
where only the spaces between them change. This version uses only what funground had before the
studio words, so the page, the panels, the groups and the dots are all worked out with arithmetic.

How it works:
- The page is 8 inches square, and an inch is 72 units. The margin and the gutters are inches too.
- span(start, length, count, gap) finds where the cells of a row or column start and how big they
  are. The same sum is needed three times: for the panels, the groups and the dots.
- Four loops go down through the levels: panel, group, dot across, dot down.
- Each dot is an f.circle() at the centre of its cell.

Make it yours:
- Change DOT to 18 or 6. When do the groups stop reading as groups?
- Change GAP, the space between groups, to 0.1 * INCH.
- Compare the two versions: which lines are the same, and which are sums?
"""
import funground as f

INCH = 72
W = H = 8 * INCH
MARGIN = 0.5 * INCH
PANEL_GAP = 0.4 * INCH
CAPTION = 28

f.size(W, H)
f.background("white")

DOT = 12                              # every dot is the same size
GAP = 0.3 * INCH                      # the space between groups
# name, then groups across and down, then dots across and down in each group: always 36 dots
GROUPINGS = [("even", 1, 1, 6, 6), ("rows", 1, 3, 6, 2), ("columns", 3, 1, 2, 6), ("clusters", 3, 3, 2, 2)]


def span(start, length, count, gap):
    """Where each of count cells starts along a length, with gap between them, and the cell size."""
    size = (length - (count - 1) * gap) / count
    return [start + i * (size + gap) for i in range(count)], size


f.text_size(14)
f.text_align("center", "bottom")
panel_xs, panel_w = span(MARGIN, W - 2 * MARGIN, 2, PANEL_GAP)
panel_ys, panel_h = span(MARGIN, H - 2 * MARGIN, 2, PANEL_GAP)
for i, (name, groups_x, groups_y, dots_x, dots_y) in enumerate(GROUPINGS):
    px, py = panel_xs[i % 2], panel_ys[i // 2]
    field_h = panel_h - CAPTION
    f.no_stroke()
    f.fill("#1d3557")
    group_xs, group_w = span(px, panel_w, groups_x, GAP)
    group_ys, group_h = span(py, field_h, groups_y, GAP)
    for gy in group_ys:
        for gx in group_xs:
            dot_xs, dot_w = span(gx, group_w, dots_x, 0)
            dot_ys, dot_h = span(gy, group_h, dots_y, 0)
            for y in dot_ys:
                for x in dot_xs:
                    f.circle(x + dot_w / 2, y + dot_h / 2, DOT)
    f.fill("#6c757d")
    f.text(name, px + panel_w / 2, py + panel_h)

f.show()
