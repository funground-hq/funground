"""Ground, Area and Grid: the composition surface (story S-132 parts 1 and 4, contracts G1 and G2, D-073).

``Area`` is an immutable rectangle value: ``left``, ``top``, ``width`` and ``height``, with ``right``,
``bottom``, ``cx`` and ``cy`` worked out from them. ``Ground`` is an Area with margins (``f.ground``), and
``Cell`` is an Area that knows its place in a grid. ``Grid`` divides an area into equal cells; it iterates
and indexes like the list it used to be (before D-073 ``f.grid()`` returned a list).

Decisions made here (D-073, S-132 part 4):

- **Zero is allowed.** An area may be 0 wide or 0 high (a line, or a point): ``inset()`` may take an area
  exactly down to nothing. A negative width or height is a ``ValueError``.
- **A negative inset grows the area** (an outset, for a bleed). Only the result is checked.
- **Cells have no x, y, w, h.** The part 1 cell had them as duplicates of left, top, width, height; nothing
  outside the tests used them, so they were removed rather than kept as a second set of names.
- **Guides are not drawing.** ``Grid.show()`` puts its lines in the canvas sketch's guide list, which only
  the window shows (``Sketch._guides``), so saved files, ``get()`` and pixels never see them. With
  ``in_files=True`` they are ordinary drawing instead.

This module imports no backend (tests/test_boundaries.py).
"""
from __future__ import annotations

import math

POINTS_PER_INCH = 72.0
MM_PER_INCH = 25.4

GUIDE_COLOR = "#1e90ff"     # the default colour of grid guides: a clear blue that reads on light and dark grounds


def mm(n: float) -> float:
    """Millimetres as funground units (points, 72 to the inch)."""
    _number(n, "f.mm()")
    return n * POINTS_PER_INCH / MM_PER_INCH


def inch(n: float) -> float:
    """Inches as funground units (points, 72 to the inch)."""
    _number(n, "f.inch()")
    return n * POINTS_PER_INCH


def _number(value, where: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{where} needs a number, not {value!r}")


def _finite(value, where: str, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{where}: {name} needs a number, not {value!r}")
    if not math.isfinite(value):
        raise ValueError(f"{where}: {name} needs a finite number, not {value!r}")
    return value


def _shown(value: float) -> str:
    """A number for a repr or a message: whole numbers without '.0', others to 4 decimal places."""
    if float(value).is_integer():
        return str(int(value))
    return repr(round(value, 4))


def check_margin(margin, width: float, height: float) -> tuple[float, float, float, float]:
    """Return margin as (top, right, bottom, left). Raise if it is wrong or leaves no content area."""
    if isinstance(margin, (tuple, list)):
        if len(margin) != 4:
            raise ValueError(f"margin needs one number or four, (top, right, bottom, left), not {len(margin)} values")
        top, right, bottom, left = margin
    else:
        top = right = bottom = left = margin
    for value in (top, right, bottom, left):
        _number(value, "margin")
        if value < 0:
            raise ValueError(f"margin cannot be negative, but got {margin!r}")
    if left + right >= width:
        raise ValueError(f"the left and right margins ({left} + {right}) leave no room in a width of {width}")
    if top + bottom >= height:
        raise ValueError(f"the top and bottom margins ({top} + {bottom}) leave no room in a height of {height}")
    return (top, right, bottom, left)


_CHANGE = "an area cannot be changed. Make a new one, for example with inset() or f.area()."


class Area:
    """A rectangle on the canvas, kept as a value.

    An area has a left edge, a top edge, a width and a height, in canvas units. It also gives its right and bottom edges and its centre. Make one with f.area(x, y, w, h). f.ground, f.ground.content and every cell of a grid are areas too, so anything that takes an area takes them.

    An area never changes. inset() and grid() give new values. An area may be 0 wide or 0 high, but never less.

    Example:
        panel = f.area(40, 40, 300, 200)
        f.rect(panel.left, panel.top, panel.width, panel.height)
        f.circle(panel.cx, panel.cy, 20)

    See also: inset, grid
    """

    __slots__ = ("_left", "_top", "_width", "_height")

    def __init__(self, left: float, top: float, width: float, height: float) -> None:
        where = "f.area()"
        for name, value in (("left", left), ("top", top), ("width", width), ("height", height)):
            _finite(value, where, name)
        if width < 0 or height < 0:
            raise ValueError(f"{where}: the width and height cannot be negative, but got width {_shown(width)} "
                             f"and height {_shown(height)}")
        object.__setattr__(self, "_left", left)
        object.__setattr__(self, "_top", top)
        object.__setattr__(self, "_width", width)
        object.__setattr__(self, "_height", height)

    # ---- a value
    def __setattr__(self, name, value) -> None:
        raise AttributeError(_CHANGE)

    def __delattr__(self, name) -> None:
        raise AttributeError(_CHANGE)

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def _key(self) -> tuple:
        return (self._left, self._top, self._width, self._height)

    def __reduce__(self):
        return (type(self), self._key())

    def __eq__(self, other) -> bool:
        if type(other) is not type(self):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        return hash((type(self), self._key()))

    def __repr__(self) -> str:
        return f"Area({self._edges()})"

    def _edges(self) -> str:
        return (f"left={_shown(self._left)}, top={_shown(self._top)}, right={_shown(self.right)}, "
                f"bottom={_shown(self.bottom)}, width={_shown(self._width)}, height={_shown(self._height)}")

    # ---- edges and centre
    @property
    def left(self) -> float:
        """The x of the area's left edge."""
        return self._left

    @property
    def top(self) -> float:
        """The y of the area's top edge."""
        return self._top

    @property
    def width(self) -> float:
        """How wide the area is: 0 or more."""
        return self._width

    @property
    def height(self) -> float:
        """How high the area is: 0 or more."""
        return self._height

    @property
    def right(self) -> float:
        """The x of the area's right edge: left + width."""
        return self._left + self._width

    @property
    def bottom(self) -> float:
        """The y of the area's bottom edge: top + height."""
        return self._top + self._height

    @property
    def cx(self) -> float:
        """The x of the area's centre."""
        return self._left + self._width / 2

    @property
    def cy(self) -> float:
        """The y of the area's centre."""
        return self._top + self._height / 2

    # ---- new areas from this one
    def inset(self, all: float | None = None, *, top: float | None = None, right: float | None = None,  # noqa: A002
              bottom: float | None = None, left: float | None = None) -> "Area":
        """Return a smaller area inside this one.

        One number moves every edge in by that much. top=, right=, bottom= and left= move one edge each, and a side you name wins over the one number. A side you leave out does not move. A negative number moves that edge out instead, which makes the area bigger, as for a bleed around a page. The area itself does not change.

        Arguments:
            all: how far to move every edge in. The default None moves none of them.
            top: how far to move the top edge down. The default None uses all.
            right: how far to move the right edge left. The default None uses all.
            bottom: how far to move the bottom edge up. The default None uses all.
            left: how far to move the left edge right. The default None uses all.

        Returns:
            A new Area. It may be 0 wide or 0 high.

        Raises:
            TypeError: a side is not a number.
            ValueError: the insets are more than the width or the height, which would leave a negative size.

        Example:
            page = f.ground.inset(20)
            header = page.inset(bottom=page.height - 60)

        See also: grid, area
        """
        sides = {}
        for name, value in (("top", top), ("right", right), ("bottom", bottom), ("left", left)):
            chosen = all if value is None else value
            sides[name] = 0 if chosen is None else _finite(chosen, "inset()", name)
        width = self._width - sides["left"] - sides["right"]
        height = self._height - sides["top"] - sides["bottom"]
        if width < 0:
            raise ValueError(f"inset(): the left and right insets ({_shown(sides['left'])} + {_shown(sides['right'])}) "
                             f"are more than the width, {_shown(self._width)}. Use smaller insets.")
        if height < 0:
            raise ValueError(f"inset(): the top and bottom insets ({_shown(sides['top'])} + {_shown(sides['bottom'])}) "
                             f"are more than the height, {_shown(self._height)}. Use smaller insets.")
        return Area(self._left + sides["left"], self._top + sides["top"], width, height)

    def grid(self, cols: int, rows: int, *, gutter: float | tuple = 0) -> "Grid":
        """Return a grid of equal cells over this area.

        It is the same as f.grid(cols, rows, gutter=gutter, area=this_area). A cell is an area too, so a cell can hold a grid of its own.

        Arguments:
            cols: how many columns. A whole number above 0.
            rows: how many rows. A whole number above 0.
            gutter: the gap between cells. One number is used both across and down. A tuple (column_gutter, row_gutter) sets them apart. The default is 0.

        Returns:
            A Grid. It goes row by row, left to right, like a list of cells.

        Raises:
            TypeError: cols or rows is not a whole number, or a gutter is not a number.
            ValueError: cols or rows is 0 or less, a gutter is negative, or the gutters leave no room for the cells.

        Example:
            for cell in f.ground.content.grid(4, 3, gutter=8):
                f.circle(cell.cx, cell.cy, cell.width * 0.5)

        See also: inset, area
        """
        return make_grid(cols, rows, gutter, self, "area.grid()")


class Ground(Area):
    """The canvas as an area, with its margins.

    f.ground is the whole canvas and f.ground.content is the part inside the margins. Both are areas, so they have left, top, right, bottom, width, height, cx and cy, and inset() and grid(). f.ground is made fresh each time you read it, so it always matches the canvas. You do not make a Ground yourself: set the margins with f.size(..., margin=...).

    Example:
        f.size("A5", margin=f.mm(12))
        f.background("linen")
        c = f.ground.content
        f.rect(c.left, c.top, c.width, c.height)

    See also: area, grid, size
    """

    __slots__ = ("_margin",)

    def __init__(self, left: float, top: float, width: float, height: float, margin: tuple = (0, 0, 0, 0)) -> None:
        super().__init__(left, top, width, height)
        object.__setattr__(self, "_margin", tuple(margin))

    def _key(self) -> tuple:
        return (*super()._key(), self._margin)

    def __reduce__(self):
        return (type(self), self._key())

    @property
    def margin(self) -> tuple:
        """The margins as (top, right, bottom, left). (0, 0, 0, 0) when there are none."""
        return self._margin

    @property
    def content(self) -> "Ground":
        """The area inside the margins. With no margin it is this same object, and its own margin is (0, 0, 0, 0)."""
        top, right, bottom, left = self._margin
        if not (top or right or bottom or left):
            return self
        return Ground(self._left + left, self._top + top, self._width - left - right, self._height - top - bottom)

    def __repr__(self) -> str:
        return f"Ground({self._edges()}, margin={self._margin})"


class Cell(Area):
    """One cell of a grid: an area that knows its column, row and place in the grid.

    A cell has everything an area has (left, top, width, height, cx, cy and so on), plus col, row and index, all counted from 0. A cell can be the area of another grid, so grids nest.

    Example:
        for cell in f.grid(3, 2, gutter=10):
            if cell.row == 0:
                f.circle(cell.cx, cell.cy, cell.width * 0.5)

    See also: grid, area
    """

    __slots__ = ("_col", "_row", "_index")

    def __init__(self, left: float, top: float, width: float, height: float, col: int, row: int, index: int) -> None:
        super().__init__(left, top, width, height)
        object.__setattr__(self, "_col", col)
        object.__setattr__(self, "_row", row)
        object.__setattr__(self, "_index", index)

    def _key(self) -> tuple:
        return (*super()._key(), self._col, self._row, self._index)

    def __reduce__(self):
        return (type(self), self._key())

    @property
    def col(self) -> int:
        """The cell's column, counted from 0 at the left."""
        return self._col

    @property
    def row(self) -> int:
        """The cell's row, counted from 0 at the top."""
        return self._row

    @property
    def index(self) -> int:
        """The cell's place in the grid, counted from 0, row by row: row * column_count + col."""
        return self._index

    def __repr__(self) -> str:
        return f"Cell(col={self._col}, row={self._row}, index={self._index}, {self._edges()})"


def as_area(area, where: str = "f.grid()") -> Area:
    """*area* as an Area: itself when it is one, else an Area from its left, top, width and height."""
    if isinstance(area, Area):
        return area
    try:
        left, top, width, height = area.left, area.top, area.width, area.height
    except AttributeError:
        raise TypeError(f"{where}: area needs left, top, width and height, like f.ground.content, a grid cell "
                        f"or f.area(x, y, w, h), not {area!r}") from None
    return Area(left, top, width, height)


def make_grid(cols, rows, gutter, area, where: str = "f.grid()") -> "Grid":
    """A Grid over *area*, with errors that name *where* (f.grid() or area.grid())."""
    grid = Grid.__new__(Grid)
    grid._setup(area, cols, rows, gutter, where)
    return grid


def _whole(value, where: str, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{where} needs a whole number for {name}, not {value!r}")
    return value


class Grid:
    """An area divided into equal cells, with gutters between them.

    f.grid() and area.grid() make one. A grid works like a list of its cells, row by row, left to right: a for loop goes through them, len() counts them, g[0] is the top-left cell and g[-1] the last one, and g[2:5] gives a list. It also finds cells by column and row, joins cells into larger areas, and draws guide lines to help you see the layout.

    A grid never changes. Columns, rows and cells are all counted from 0.

    Example:
        g = f.grid(4, 3, gutter=10)
        for cell in g:
            f.circle(cell.cx, cell.cy, cell.width * 0.6)
        banner = g.span(0, 0, cols=4)
        g.show()

    See also: grid, area
    """

    __slots__ = ("_area", "_cols", "_rows", "_gutter", "_cells")

    def __init__(self, area, cols: int, rows: int, gutter: float | tuple = 0) -> None:
        self._setup(area, cols, rows, gutter, "f.grid()")

    def _setup(self, area, cols, rows, gutter, where: str) -> None:
        cols = _whole(cols, where, "cols")
        rows = _whole(rows, where, "rows")
        for name, value in (("cols", cols), ("rows", rows)):
            if value <= 0:
                raise ValueError(f"{where} needs {name} above 0, but got {value}")
        if isinstance(gutter, (tuple, list)):
            if len(gutter) != 2:
                raise ValueError(f"{where}: gutter needs one number or two, (column_gutter, row_gutter)")
            gx, gy = gutter
        else:
            gx = gy = gutter
        for g in (gx, gy):
            _finite(g, where, "gutter")
            if g < 0:
                raise ValueError(f"{where}: gutter cannot be negative, but got {gutter!r}")
        area = as_area(area, where)
        w = (area.width - gx * (cols - 1)) / cols
        h = (area.height - gy * (rows - 1)) / rows
        if w <= 0 or h <= 0:
            raise ValueError(f"{where}: the gutter {gutter!r} leaves no room for {cols} columns and {rows} rows "
                             f"in an area {_shown(area.width)} wide and {_shown(area.height)} high")
        left, top = area.left, area.top
        cells = tuple(Cell(left + col * (w + gx), top + row * (h + gy), w, h, col, row, row * cols + col)
                      for row in range(rows) for col in range(cols))
        for name, value in (("_area", area), ("_cols", cols), ("_rows", rows), ("_gutter", (gx, gy)),
                            ("_cells", cells)):
            object.__setattr__(self, name, value)

    # ---- a value
    def __setattr__(self, name, value) -> None:
        raise AttributeError("a grid cannot be changed. Make a new one with f.grid() or area.grid().")

    def __delattr__(self, name) -> None:
        raise AttributeError("a grid cannot be changed. Make a new one with f.grid() or area.grid().")

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def __reduce__(self):
        return (type(self), (self._area, self._cols, self._rows, self._gutter))

    def __eq__(self, other) -> bool:
        if type(other) is not Grid:
            return NotImplemented
        return (self._area, self._cols, self._rows, self._gutter) == (other._area, other._cols, other._rows,
                                                                      other._gutter)

    def __hash__(self) -> int:
        return hash((self._area, self._cols, self._rows, self._gutter))

    def __repr__(self) -> str:
        gx, gy = self._gutter
        return (f"Grid({self._cols} columns x {self._rows} rows, gutter=({_shown(gx)}, {_shown(gy)}), "
                f"area={self._area!r})")

    # ---- like a list of cells
    def __len__(self) -> int:
        return len(self._cells)

    def __iter__(self):
        return iter(self._cells)

    def __reversed__(self):
        return reversed(self._cells)

    def __contains__(self, item) -> bool:
        return item in self._cells

    def __getitem__(self, index):
        if isinstance(index, slice):
            return list(self._cells[index])
        if isinstance(index, bool) or not isinstance(index, int):
            raise TypeError(f"a grid's cells are found by a whole number, as in g[0], not {index!r}. "
                            "For a column and a row, use g.cell(col, row).")
        n = len(self._cells)
        if not -n <= index < n:
            raise IndexError(f"cell {index} is not in this grid: it has {n} cells, 0 to {n - 1} "
                             f"(or -{n} to -1 from the end)")
        return self._cells[index]

    # ---- what it is made of
    @property
    def area(self) -> Area:
        """The area the grid divides."""
        return self._area

    @property
    def gutter(self) -> tuple:
        """The gaps between cells, as (column_gutter, row_gutter)."""
        return self._gutter

    @property
    def column_count(self) -> int:
        """How many columns the grid has."""
        return self._cols

    @property
    def row_count(self) -> int:
        """How many rows the grid has."""
        return self._rows

    @property
    def columns(self) -> list:
        """The columns as a list of areas, left to right, each as high as the whole grid."""
        top, height = self._area.top, self._area.height
        return [Area(c.left, top, c.width, height) for c in self._cells[:self._cols]]

    @property
    def rows(self) -> list:
        """The rows as a list of areas, top to bottom, each as wide as the whole grid."""
        left, width = self._area.left, self._area.width
        return [Area(left, c.top, width, c.height) for c in self._cells[::self._cols]]

    # ---- finding cells
    def _check(self, where: str, col, row) -> None:
        _whole(col, where, "col")
        _whole(row, where, "row")
        if not 0 <= col < self._cols:
            raise IndexError(f"{where}: column {col} is not in this grid. Its columns are 0 to {self._cols - 1}.")
        if not 0 <= row < self._rows:
            raise IndexError(f"{where}: row {row} is not in this grid. Its rows are 0 to {self._rows - 1}.")

    def cell(self, col: int, row: int) -> Cell:
        """Return the cell at a column and a row.

        Both count from 0, so g.cell(0, 0) is the top-left cell. It is the same cell as g[row * g.column_count + col].

        Arguments:
            col: the column, from 0 at the left.
            row: the row, from 0 at the top.

        Returns:
            The Cell.

        Raises:
            TypeError: col or row is not a whole number.
            IndexError: there is no such column or row. The message says which ones there are.

        Example:
            corner = f.grid(3, 3).cell(2, 0)
            f.rect(corner.left, corner.top, corner.width, corner.height)

        See also: span, columns, rows
        """
        self._check("grid.cell()", col, row)
        return self._cells[row * self._cols + col]

    def span(self, col: int, row: int, cols: int = 1, rows: int = 1) -> Area:
        """Return one area that covers several cells, with the gutters between them.

        The area starts at the cell (col, row) and is cols cells wide and rows cells high. The gutters inside it are part of it, so its edges line up with the cells around it.

        Arguments:
            col: the column of the top-left cell, from 0.
            row: the row of the top-left cell, from 0.
            cols: how many columns it covers. The default is 1.
            rows: how many rows it covers. The default is 1.

        Returns:
            A new Area.

        Raises:
            TypeError: a value is not a whole number.
            ValueError: cols or rows is less than 1.
            IndexError: the cells it would cover are not all in the grid. The message says which ones there are.

        Example:
            g = f.grid(4, 3, gutter=10)
            title = g.span(0, 0, cols=4)
            f.rect(title.left, title.top, title.width, title.height)

        See also: cell, columns, rows
        """
        where = "grid.span()"
        self._check(where, col, row)
        for name, value in (("cols", cols), ("rows", rows)):
            _whole(value, where, name)
            if value < 1:
                raise ValueError(f"{where}: {name} must be 1 or more, but got {value}")
        if col + cols > self._cols:
            raise IndexError(f"{where}: {cols} columns from column {col} would reach column {col + cols - 1}, "
                             f"but this grid's columns are 0 to {self._cols - 1}.")
        if row + rows > self._rows:
            raise IndexError(f"{where}: {rows} rows from row {row} would reach row {row + rows - 1}, "
                             f"but this grid's rows are 0 to {self._rows - 1}.")
        first = self._cells[row * self._cols + col]
        last = self._cells[(row + rows - 1) * self._cols + col + cols - 1]
        return Area(first.left, first.top, last.right - first.left, last.bottom - first.top)

    # ---- guides (contract G2)
    def _guide_path(self):
        """The guide lines as one path: the area's outline and every cell's outline (drawn as one stroke, so
        lines shared by two cells are not drawn twice)."""
        from .paths import PathBuilder

        a = self._area
        path = PathBuilder().rect(a.left, a.top, a.width, a.height)
        for c in self._cells:
            path.rect(c.left, c.top, c.width, c.height)
        return path

    def show(self, *, color=GUIDE_COLOR, in_files: bool = False) -> None:
        """Draw thin guide lines that show the grid: the outline of its area and of every cell.

        Guides help you see a layout while you work. They are drawn over everything else in the window, and they are not part of the picture: they are left out of every saved file (PNG, PDF, SVG, f.keep(), save_frames(), GIFs and movies), and get() and pixels do not see them. Give in_files=True to make them ordinary drawing instead, so they are saved too; then later drawing can cover them.

        The lines are 1 unit wide and follow the current transform. show() does not change the fill, stroke, transform, clip or anything else. In an animated sketch the guides last one frame, so call show() in draw().

        Arguments:
            color: the colour of the lines. The default is a clear blue.
            in_files: True draws the guides as ordinary drawing, so saved files have them. The default False shows them only in the window.

        Raises:
            RuntimeError: it is used inside a ``with f.mark()`` block without in_files=True, or before f.size().

        Example:
            g = f.grid(4, 3, gutter=10)
            g.show()
            g.show(color="red", in_files=True)

        See also: cell, span
        """
        from .api import active_sketch, canvas_sketch
        from .marks import refuse_in_mark

        if not isinstance(in_files, bool):
            raise TypeError(f"grid.show(): in_files is True or False, not {in_files!r}")
        canvas = canvas_sketch()
        sketch = active_sketch()
        if in_files:
            sketch.draw_guides(self._guide_path(), color)
            return
        refuse_in_mark("grid.show()")
        canvas.show_guides(sketch, self._guide_path(), color)
