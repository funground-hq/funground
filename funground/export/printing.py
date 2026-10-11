"""Print-ready PDF: bleed, crop marks, TrimBox and BleedBox (story S-164, contract D2).

A printer cuts a poster from a larger sheet, so the colour has to run past the cut ("bleed") and the
cutter needs marks to aim at. `f.save("poster.pdf", bleed=f.mm(3), marks=True)` therefore writes pages
bigger than the learner's canvas. The canvas is the *trim*: the size of the finished piece. See
`Scripts_and_Pages_Note.md`, "Bleed and crop marks".

The mechanism is small. For each page the exporter

1. makes the PDF page `margin` bigger on every side (`PrintSetup.page_size`),
2. moves the drawing by `margin`, so the trim sits at (margin, margin) and the learner's coordinates
   are unchanged: drawing at -5 or at width + 5 lands in the bleed (`PrintSetup.begin_page`),
3. keeps the drawing inside the bleed box, so a `background()` fills the bleed and nothing leaks into
   the slug, the strip outside the bleed that holds the marks (`CairoRenderer.clip_box`),
4. draws the crop marks in the slug (`PrintSetup.draw_marks`), and
5. once the file is written, sets each page's TrimBox and BleedBox (`write_print_boxes`).
"""
from __future__ import annotations

import io
import math

import cairo
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

from ..surface import mm

MARK_WIDTH = 0.25                    # points: a hairline, as printers use
MARK_LENGTH = mm(5)                  # each crop mark is 5 mm long
MARK_GAP = mm(1)                     # and starts 1 mm beyond the bleed, so it never touches the bleed


class PrintSetup:
    """The bleed and the crop marks asked for by `save(..., bleed=..., marks=...)`, and the sums that follow."""

    __slots__ = ("bleed", "marks")

    def __init__(self, bleed: float = 0.0, marks: bool = False) -> None:
        self.bleed = float(bleed)
        self.marks = marks

    @property
    def active(self) -> bool:
        """True when the page needs to be made bigger: there is a bleed or there are marks."""
        return self.bleed > 0 or self.marks

    @property
    def margin(self) -> float:
        """How far the page grows on each side: the bleed, plus the slug for the marks."""
        return self.bleed + (MARK_GAP + MARK_LENGTH if self.marks else 0.0)

    def page_size(self, width: float, height: float) -> tuple[float, float]:
        """The PDF page (its MediaBox) for a trim of *width* x *height*."""
        return width + 2 * self.margin, height + 2 * self.margin

    def begin_page(self, renderer, ctx: cairo.Context, width: float, height: float) -> None:
        """Place the learner's page on the bigger one. Call before `renderer.draw(ctx, frame)`."""
        if not self.active:
            return
        ctx.translate(self.margin, self.margin)
        bleed = self.bleed
        renderer.clip_box = (-bleed, -bleed, width + 2 * bleed, height + 2 * bleed)
        ctx.rectangle(*renderer.clip_box)
        ctx.clip()

    def draw_marks(self, ctx: cairo.Context, width: float, height: float) -> None:
        """Draw a crop mark along each edge at each trim corner, in the slug. Call after the page is drawn."""
        if not self.marks:
            return
        near = self.bleed + MARK_GAP                      # from the trim edge to where a mark starts
        far = near + MARK_LENGTH
        ctx.save()
        ctx.reset_clip()
        ctx.set_source_rgb(0, 0, 0)                       # black: PDF here is RGB, so this is not yet true registration colour
        ctx.set_line_width(MARK_WIDTH)
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        for x, step_x in ((0, -1), (width, 1)):
            for y, step_y in ((0, -1), (height, 1)):
                ctx.move_to(x + step_x * near, y)         # along the horizontal edge's line
                ctx.line_to(x + step_x * far, y)
                ctx.move_to(x, y + step_y * near)         # along the vertical edge's line
                ctx.line_to(x, y + step_y * far)
        ctx.stroke()
        ctx.restore()


def check_print_options(bleed: object, marks: object, name: str = "f.save()") -> PrintSetup:
    """Validate `bleed=` and `marks=` (contract D2) and return them as a PrintSetup."""
    if isinstance(bleed, bool) or not isinstance(bleed, (int, float)):
        raise TypeError(f"{name}: bleed must be a number of points (use f.mm(3) for 3 mm), not {bleed!r}")
    if not (math.isfinite(bleed) and bleed >= 0):
        raise ValueError(f"{name}: bleed must be 0 or more points (use f.mm(3) for 3 mm), not {bleed!r}")
    if not isinstance(marks, bool):
        raise TypeError(f"{name}: marks must be True or False, not {marks!r}")
    return PrintSetup(bleed, marks)


def write_print_boxes(path: str, setup: PrintSetup) -> None:
    """Set every page's TrimBox (the page as the learner drew it) and BleedBox (the trim grown by the bleed).

    The MediaBox is the whole sheet, and the margin is the same on all sides, so the boxes follow from it.
    Run this last: the text and layer steps rewrite the file but leave the page boxes alone."""
    if not setup.active:
        return
    with open(path, "rb") as file:
        writer = PdfWriter(clone_from=PdfReader(io.BytesIO(file.read())))
    margin, bleed = setup.margin, setup.bleed
    for page in writer.pages:
        media = page.mediabox
        left, bottom = float(media.left), float(media.bottom)
        right, top = float(media.right), float(media.top)
        page.trimbox = RectangleObject([left + margin, bottom + margin, right - margin, top - margin])
        page.bleedbox = RectangleObject([left + margin - bleed, bottom + margin - bleed,
                                         right - margin + bleed, top - margin + bleed])
    with open(path, "wb") as file:
        writer.write(file)
