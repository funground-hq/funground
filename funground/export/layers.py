"""Layers in PDF and SVG files (story S-096, contract F16, decision D-053).

A layer (S-095) reaches a PDF or SVG export as an ``ir.Image`` op tagged with the layer's name, put
over the canvas's own drawing. Cairo knows nothing about named layers, so the exporters do this:

1. **While drawing.** The Cairo renderer is given a `LayerMarkers`. For each layer op it asks for a
   *marker*: a large four-cornered shape around the layer, in user space. The renderer pushes a
   group, clips to the marker, draws the layer inside it (its history as vectors, or its pixels past
   P3's limit), and paints the group back. The marker holds everything the layer can draw, so the
   clip changes nothing. Cairo writes the group as one Form XObject (PDF) or one ``<g>`` in
   ``<defs>`` drawn by a ``<use>`` (SVG), with the marker's corners in its own coordinates.
   A hidden layer is drawn too: it is in the file, switched off.
2. **After ``surface.finish()``.** `LayerMarkers.finish_pdf` finds the marker in each Form XObject,
   gives the outermost XObject of each layer an ``/OC`` entry pointing at the layer's optional
   content group (OCG), removes the marker, and adds ``/OCProperties`` to the catalogue: every OCG,
   the order of first use, and the hidden ones in ``/D /OFF``. `LayerMarkers.finish_svg` finds the
   marker clip paths, moves each layer's drawing into a ``<g inkscape:groupmode="layer">`` at the
   place Cairo drew it, removes the markers, and hides hidden layers with ``display:none``.

How a marker is recognised. It is the quadrilateral P0, P1, Q, P2 of `pdf_text` (never a rectangle,
which Cairo would reduce to a box): P1 - P0 and P2 - P0 are two equal, square axes and
Q = P0 + a (P1 - P0) + b (P2 - P0). Here a and b lie in [1.1, 1.4), on a 0.001 grid that encodes
the layer's number. a + b > 1 keeps the shape convex, so it holds the whole square P0 .. P0 + 2 x
side / 4 where the layer is; real-text markers use [0.55, 0.95) and so never read as layer markers,
nor these as text. Affine maps keep a and b, so the number reads back under any transform; as a
safety check the axes must also match the transform recorded when the layer was drawn.

A layer name used on several pages of one document is one OCG. A name that is hidden on one page
and shown on another is two OCGs with the same name, so every page keeps its look.
"""
from __future__ import annotations

import contextlib
import io
import math
import re
import xml.etree.ElementTree as ET

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NameObject, TextStringObject

_GRID = 300                          # a and b each take 300 values: 90 000 layers per file
_STEP = 0.001
_LOW = 1.1
_TOLERANCE = 1e-4
MAX_LAYERS = _GRID * _GRID
_MIN_DEVICE = 2000.0                 # the marker's half side in device units, at least (precision)
_MAX_DEVICE = 1.0e6                  # its far corner in device units, at most (Cairo's fixed-point range)

_NUM = rb"(-?(?:\d+\.?\d*|\.\d+))"
_PDF_MARKER = re.compile(
    _NUM + rb"\s+" + _NUM + rb"\s+m\s+"
    + _NUM + rb"\s+" + _NUM + rb"\s+l\s+"
    + _NUM + rb"\s+" + _NUM + rb"\s+l\s+"
    + _NUM + rb"\s+" + _NUM + rb"\s+l\s+h\s+"
    + rb"(?:-?[\d.]+\s+-?[\d.]+\s+m\s+)?W\s+n\s*"
)
_SNUM = r"(-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)"
_SVG_MARKER = re.compile(
    r"^\s*M\s*" + _SNUM + r"[\s,]+" + _SNUM
    + r"\s*L\s*" + _SNUM + r"[\s,]+" + _SNUM
    + r"\s*L\s*" + _SNUM + r"[\s,]+" + _SNUM
    + r"\s*L\s*" + _SNUM + r"[\s,]+" + _SNUM
    + r"\s*Z(?:\s*M\s*-?[\d.eE+-]+[\s,]+-?[\d.eE+-]+)?\s*$"
)

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
_INLINE = {f"{{{SVG_NS}}}{tag}" for tag in ("g", "image", "path", "rect")}   # a <use> of one is the element
_URL = re.compile(r"url\(\s*#([^)\s]+)\s*\)")
_INVALID_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")


class LayerMarkers:
    """Collects the layers drawn into one PDF or SVG file, then turns them into real layers."""

    def __init__(self) -> None:
        self.layers: list[tuple[str, bool]] = []      # (name, hidden), by number, in first-use order
        self._numbers: dict[tuple[str, bool], int] = {}
        self._drawn: dict[int, list[tuple[float, tuple]]] = {}    # number -> [(half, linear)]

    # ---- while drawing (called by the Cairo renderer)
    def add(self, name: str, hidden: bool, box: tuple, matrix: tuple) -> list[tuple[float, float]] | None:
        """Record layer *name* drawn in user-space *box* (x, y, w, h) under the device *matrix*
        (Cairo's xx, yx, xy, yy, x0, y0). Return the marker's corners in user space, or None to
        draw the layer without one (it then is not a file layer)."""
        key = (name, bool(hidden))
        number = self._numbers.get(key)
        if number is None and len(self.layers) >= MAX_LAYERS:
            return None
        if not all(math.isfinite(v) for v in (*matrix, *box)):
            return None
        xx, yx, xy, yy = matrix[:4]
        det = xx * yy - xy * yx
        norm2 = xx * xx + xy * xy + yx * yx + yy * yy
        if abs(det) < 1e-12 or norm2 <= 0:
            return None
        s_max = math.sqrt((norm2 + math.sqrt(max(norm2 * norm2 - 4 * det * det, 0.0))) / 2)
        s_min = abs(det) / s_max
        x, y, w, h = box
        half = max(abs(w), abs(h), _MIN_DEVICE / s_min)
        cx, cy = x + w / 2, y + h / 2
        reach = (math.hypot(cx, cy) + 6 * half) * s_max + math.hypot(matrix[4], matrix[5])
        if reach > _MAX_DEVICE:
            return None
        if number is None:
            number = len(self.layers)
            self.layers.append(key)
            self._numbers[key] = number
        self._drawn.setdefault(number, []).append((half, (xx, yx, xy, yy)))
        a = _LOW + (number % _GRID) * _STEP
        b = _LOW + (number // _GRID) * _STEP
        side = 4 * half
        p0 = (cx - half, cy - half)
        p1 = (p0[0] + side, p0[1])
        p2 = (p0[0], p0[1] + side)
        q = (p0[0] + side * a, p0[1] + side * b)
        return [p0, p1, q, p2]

    def _decode(self, e0, e1, eq, e2) -> int | None:
        """The layer number of a marker whose corners came out as e0, e1, eq, e2, or None."""
        v1 = (e1[0] - e0[0], e1[1] - e0[1])
        v2 = (e2[0] - e0[0], e2[1] - e0[1])
        dq = (eq[0] - e0[0], eq[1] - e0[1])
        det = v1[0] * v2[1] - v1[1] * v2[0]
        if abs(det) < 1e-9:
            return None
        a = (dq[0] * v2[1] - dq[1] * v2[0]) / det
        b = (v1[0] * dq[1] - v1[1] * dq[0]) / det
        ia, ib = round((a - _LOW) / _STEP), round((b - _LOW) / _STEP)
        if not (0 <= ia < _GRID and 0 <= ib < _GRID):
            return None
        if abs(a - (_LOW + ia * _STEP)) > _TOLERANCE or abs(b - (_LOW + ib * _STEP)) > _TOLERANCE:
            return None
        number = ia + ib * _GRID
        if number not in self._drawn:
            return None
        for half, linear in self._drawn[number]:
            side = 4 * half
            found = (v1[0] / side, v1[1] / side, v2[0] / side, v2[1] / side)
            scale = max(math.hypot(*linear[:2]), math.hypot(*linear[2:]))
            if all(abs(u - w) <= 1e-3 * scale for u, w in zip(found, linear)):
                return number
        # On the grid but under a transform the layer was never drawn with: refuse rather than guess.
        raise RuntimeError("layer marker found under an unexpected transform")

    # ---- PDF: optional content groups
    def finish_pdf(self, path: str) -> None:
        """Make each layer in the PDF at *path* an optional content group (OCG)."""
        if not self.layers:
            return
        with open(path, "rb") as fh:
            data = fh.read()
        reader = PdfReader(io.BytesIO(data))
        writer = PdfWriter(clone_from=reader)
        header = reader.pdf_header if isinstance(reader.pdf_header, str) else reader.pdf_header.decode("ascii")
        match = re.match(r"%PDF-(\d+)\.(\d+)", header)
        if match is None or (int(match.group(1)), int(match.group(2))) < (1, 5):
            writer.pdf_header = "%PDF-1.5"           # optional content needs PDF 1.5
        else:
            writer.pdf_header = header
        ocgs =[writer._add_object(DictionaryObject({
            NameObject("/Type"): NameObject("/OCG"),
            NameObject("/Name"): TextStringObject(name),
        })) for name, _ in self.layers]
        self._ocgs = ocgs
        visited: set = set()
        for page in writer.pages:
            contents = page.get("/Contents")
            if contents is not None:
                streams = contents.get_object()
                streams = list(streams) if isinstance(streams, ArrayObject) else [contents]
                for s in streams:
                    if self._strip_pdf(s.get_object().get_data())[1]:
                        raise RuntimeError("a layer marker was drawn straight onto the page, not in a group")
            self._visit_pdf(page.get("/Resources"), frozenset(), visited)
        off = [ocgs[n] for n, (_, hidden) in enumerate(self.layers) if hidden]
        writer.root_object[NameObject("/OCProperties")] = DictionaryObject({
            NameObject("/OCGs"): ArrayObject(ocgs),
            NameObject("/D"): DictionaryObject({
                NameObject("/Order"): ArrayObject(ocgs),
                NameObject("/OFF"): ArrayObject(off),
            }),
        })
        out = io.BytesIO()
        writer.write(out)
        with open(path, "wb") as fh:
            fh.write(out.getvalue())

    def _strip_pdf(self, data: bytes) -> tuple[bytes, set[int]]:
        """*data* without its layer markers, and the layer numbers they carried."""
        if b"W" not in data:
            return data, set()
        found: set[int] = set()

        def swap(m: re.Match) -> bytes:
            corners = [(float(m.group(i)), float(m.group(i + 1))) for i in (1, 3, 5, 7)]
            number = self._decode(*corners)
            if number is None:
                return m.group(0)
            found.add(number)
            return b""

        return _PDF_MARKER.sub(swap, data), found

    def _visit_pdf(self, resources, inherited: frozenset, visited: set) -> None:
        """Mark and clean every Form XObject (and pattern, and soft mask group) under *resources*."""
        if resources is None:
            return
        res = resources.get_object()
        children = []
        for kind in ("/XObject", "/Pattern"):
            entries = res.get(kind)
            if entries is not None:
                children.extend(entries.get_object().values())
        states = res.get("/ExtGState")
        if states is not None:
            for gs in states.get_object().values():
                smask = gs.get_object().get("/SMask")
                if smask is not None and not isinstance(smask.get_object(), NameObject):
                    group = smask.get_object().get("/G")
                    if group is not None:
                        children.append(group)
        for ref in children:
            key = (ref.idnum, ref.generation) if isinstance(ref, IndirectObject) else id(ref.get_object())
            if key in visited:
                continue
            visited.add(key)
            obj = ref.get_object()
            if not hasattr(obj, "get_data"):
                continue
            if obj.get("/Subtype") != "/Form" and obj.get("/PatternType") != 1:
                continue
            data = obj.get_data()
            new, found = self._strip_pdf(data)
            fresh = found - inherited
            if fresh:
                # The outermost group of a layer: one layer, one Form XObject, made optional content.
                if len(fresh) > 1 or obj.get("/Subtype") != "/Form":
                    raise RuntimeError("a layer group came out in a form this code does not understand")
                number = next(iter(fresh))
                obj[NameObject("/OC")] = self._ocgs[number]
            if new != data:
                obj.set_data(new)
            self._visit_pdf(obj.get("/Resources"), inherited | found, visited)

    # ---- SVG: Inkscape layer groups
    def finish_svg(self, path: str) -> None:
        """Make each layer in the SVG at *path* an Inkscape layer group."""
        if not self.layers:
            return
        tree = ET.parse(path)
        root = tree.getroot()
        parent = {child: el for el in root.iter() for child in el}
        defs_children = {child for el in root.iter(f"{{{SVG_NS}}}defs") for child in el}
        by_id = {el.get("id"): el for el in root.iter() if el.get("id") is not None}

        # 1. The marker clip paths and the layer each one stands for.
        layer_of: dict[ET.Element, int] = {}
        markers: list[ET.Element] = []
        for clip in root.iter(f"{{{SVG_NS}}}clipPath"):
            kids = list(clip)
            if len(kids) != 1 or kids[0].tag != f"{{{SVG_NS}}}path" or clip not in defs_children:
                continue
            if kids[0].get("transform") or clip.get("transform"):
                continue
            m = _SVG_MARKER.match(kids[0].get("d", ""))
            if m is None:
                continue
            corners = [(float(m.group(i)), float(m.group(i + 1))) for i in (1, 3, 5, 7)]
            number = self._decode(*corners)
            if number is not None:
                layer_of[clip] = number
                markers.append(clip)
        marker_ids = {clip.get("id") for clip in markers}

        def refs(el: ET.Element) -> list[str]:
            out = []
            for name, value in el.attrib.items():
                if name in (f"{{{XLINK_NS}}}href", "href") and value.startswith("#"):
                    out.append(value[1:])
                else:
                    out.extend(_URL.findall(value))
            return out

        def defs_child_of(el: ET.Element) -> ET.Element | None:
            while el is not None and el not in defs_children:
                el = parent.get(el)
            return el

        # 2. Spread each layer from its marker to every definition that uses it, until nothing changes.
        changed = True
        while changed:
            changed = False
            for el in root.iter():
                for ref in refs(el):
                    target = by_id.get(ref)
                    if target is None or target not in layer_of:
                        continue
                    holder = defs_child_of(el)
                    if holder is None or holder in layer_of:
                        if holder is not None and layer_of[holder] != layer_of[target]:
                            raise RuntimeError("a layer's drawing is shared with another layer")
                        continue
                    layer_of[holder] = layer_of[target]
                    changed = True

        # 3. In the document body, the outermost element using each layer: that is where it is drawn.
        roots: dict[int, ET.Element] = {}
        for el in root.iter():
            if defs_child_of(el) is not None or el is root:
                continue
            numbers = {layer_of[by_id[r]] for r in refs(el) if r in by_id and by_id[r] in layer_of}
            if not numbers:
                continue
            if len(numbers) > 1:
                raise RuntimeError("one element draws two layers")
            number = numbers.pop()
            up, outer = parent.get(el), False
            while up is not None and up is not root:
                if any(r in by_id and layer_of.get(by_id[r]) == number for r in refs(up)):
                    outer = True
                    break
                up = parent.get(up)
            if outer:
                continue
            if number in roots:
                raise RuntimeError("a layer was drawn in two places on one page")
            roots[number] = el

        # 4. Each layer's group, where its drawing was; the drawing itself moves out of <defs>.
        used = set(by_id)
        href_count: dict[str, int] = {}           # id -> how many references (href or url()) it has
        for el in root.iter():
            for ref in refs(el):
                href_count[ref] = href_count.get(ref, 0) + 1
        groups: dict[int, ET.Element] = {}
        for number in sorted(roots):
            el = roots[number]
            host = parent[el]
            group = self._layer_group(number, used)
            index = list(host).index(el)
            host.remove(el)
            host.insert(index, group)
            group.tail, el.tail = el.tail, None
            group.text = "\n"
            group.append(el)
            self._inline_uses(group, by_id, parent, href_count)
            group[-1].tail = "\n"
            groups[number] = group

        # 5. The markers go: their clips held everything, so dropping them changes nothing.
        parent = {child: el for el in root.iter() for child in el}
        for el in list(root.iter()):
            value = el.get("clip-path")
            if value is None:
                continue
            m = _URL.fullmatch(value.strip())
            if m is None or m.group(1) not in marker_ids:
                continue
            del el.attrib["clip-path"]
            if el.tag == f"{{{SVG_NS}}}g" and not el.attrib and el in parent:
                host = parent[el]
                index = list(host).index(el)
                kids = list(el)
                host.remove(el)
                for offset, kid in enumerate(kids):
                    host.insert(index + offset, kid)
                    parent[kid] = host
                if kids:
                    kids[-1].tail = el.tail
        for clip in markers:
            parent[clip].remove(clip)

        # 6. A layer that drew nothing still gets its (empty) group, in its place in the order.
        for number in range(len(self.layers)):
            if number in groups:
                continue
            group = self._layer_group(number, used)
            group.tail = "\n"
            before = [n for n in groups if n < number]
            after = [n for n in groups if n > number]
            parent = {child: el for el in root.iter() for child in el}
            if before:
                anchor = groups[max(before)]
                host = parent[anchor]
                host.insert(list(host).index(anchor) + 1, group)
            elif after:
                anchor = groups[min(after)]
                host = parent[anchor]
                host.insert(list(host).index(anchor), group)
            else:
                root.append(group)
            groups[number] = group
        with _svg_prefixes():
            tree.write(path, encoding="UTF-8", xml_declaration=True)

    def _layer_group(self, number: int, used: set) -> ET.Element:
        name, hidden = self.layers[number]
        group = ET.Element(f"{{{SVG_NS}}}g")
        group.set("id", svg_id(name, used))
        group.set(f"{{{INKSCAPE_NS}}}groupmode", "layer")
        group.set(f"{{{INKSCAPE_NS}}}label", _INVALID_XML.sub("�", name))
        if hidden:
            group.set("style", "display:none")
        return group

    @staticmethod
    def _inline_uses(group: ET.Element, by_id: dict, parent: dict, href_count: dict) -> None:
        """Inside *group*, swap each ``<use>`` of a group or image in ``<defs>`` that nothing else
        uses for the element itself (with the use's transform), nested ones too, so the layer holds its
        drawing rather than links to it. Cairo writes every group and image it draws as such a pair."""
        use_tag, g_tag, defs_tag = f"{{{SVG_NS}}}use", f"{{{SVG_NS}}}g", f"{{{SVG_NS}}}defs"
        hrefs = (f"{{{XLINK_NS}}}href", "href")
        pending = [group]
        while pending:
            container = pending.pop()
            for host in list(container.iter()):
                for index, el in enumerate(list(host)):
                    if el.tag != use_tag:
                        continue
                    href = el.get(hrefs[0]) or el.get(hrefs[1]) or ""
                    target = by_id.get(href[1:]) if href.startswith("#") else None
                    if (target is None or target.tag not in _INLINE or href_count.get(href[1:]) != 1
                            or target not in parent or parent[target].tag != defs_tag):
                        continue
                    rest = {k: v for k, v in el.attrib.items() if k not in (*hrefs, "x", "y")}
                    x, y = el.get("x", "0"), el.get("y", "0")
                    if (x, y) != ("0", "0"):
                        rest["transform"] = (rest.get("transform", "") + f" translate({x}, {y})").strip()
                    parent[target].remove(target)
                    del parent[target]
                    target.tail = None
                    content = target
                    if rest:
                        content = ET.Element(g_tag, rest)
                        content.text = "\n"
                        content.append(target)
                        target.tail = "\n"
                    content.tail = el.tail
                    host.remove(el)
                    host.insert(index, content)
                    pending.append(target)          # its own uses, once it is in place


@contextlib.contextmanager
def _svg_prefixes():
    """SVG as the default namespace, and the usual xlink and inkscape prefixes, while one file is
    written; ElementTree's prefix table is global, so it is put back afterwards."""
    table = getattr(ET, "_namespace_map", None)
    saved = dict(table) if table is not None else None
    for prefix, uri in (("", SVG_NS), ("xlink", XLINK_NS), ("inkscape", INKSCAPE_NS)):
        ET.register_namespace(prefix, uri)
    try:
        yield
    finally:
        if saved is not None:
            table.clear()
            table.update(saved)


def svg_id(name: str, used: set) -> str:
    """A valid, unused XML id for layer *name*: ASCII letters, digits, ``_ - .`` (others become ``_``),
    starting with a letter or ``_``; a number is added when the id is taken."""
    base = re.sub(r"[^A-Za-z0-9_.-]", "_", name) or "layer"
    if not (base[0].isalpha() or base[0] == "_"):
        base = "layer-" + base
    candidate, n = base, 2
    while candidate in used:
        candidate = f"{base}-{n}"
        n += 1
    used.add(candidate)
    return candidate
