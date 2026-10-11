"""Read the colours out of a PDF, for tests (story S-170, contract D4).

``scan(path)`` looks at every object in the file, not only the ones a walk from the page would reach, and
reports what it found:

- ``ops``: for each colour operator (``k``, ``K``, ``rg``, ``RG``, ``g``, ``G``, ``sc``, ``SC``), the list of
  operand tuples, in every page and form content stream;
- ``spaces``: the colour spaces named by shadings, images, groups and resources, as ``"DeviceRGB"``,
  ``"DeviceCMYK"``, ``"DeviceGray"`` or ``"ICCBased"``;
- ``shadings``: for each shading, its colour space and the colours in its functions (``C0`` and ``C1``);
- ``rgb``: every place that is still plain RGB: an ``rg`` or ``RG`` operator, or a ``DeviceRGB`` space.
  A drawing made of cmyk() colours has none, except its pictures: a picture is pixels, and its pixels
  stay RGB (tagged sRGB), so its image shows as ``ICCBased``, not ``DeviceRGB``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from pypdf import PdfReader
from pypdf.generic import ContentStream

COLOUR_OPERATORS = (b"k", b"K", b"rg", b"RG", b"g", b"G", b"sc", b"SC")


@dataclass
class ColourScan:
    ops: dict = field(default_factory=lambda: {op.decode(): [] for op in COLOUR_OPERATORS})
    spaces: set = field(default_factory=set)
    shadings: list = field(default_factory=list)
    rgb: list = field(default_factory=list)
    has_output_intent: bool = False


def _space_name(value) -> str | None:
    """'DeviceRGB' from /DeviceRGB, 'ICCBased' from [/ICCBased ...]; None for anything else."""
    value = value.get_object() if hasattr(value, "get_object") else value
    if isinstance(value, list):
        return str(value[0]).lstrip("/") if value else None
    if isinstance(value, str) and value.startswith("/Device"):
        return value.lstrip("/")
    return None


def _functions(function):
    function = function.get_object()
    if function.get("/FunctionType") == 3:
        for part in function["/Functions"]:
            yield from _functions(part)
    else:
        yield function


def scan(path) -> ColourScan:
    reader = PdfReader(str(path))
    result = ColourScan()
    result.has_output_intent = bool(reader.trailer["/Root"].get("/OutputIntents"))
    contents = [page.get_contents() for page in reader.pages]
    for number in sorted(n for generations in reader.xref.values() for n in generations):
        obj = reader.get_object(number)
        if obj is None:
            continue
        if hasattr(obj, "get"):
            _look_at_dictionary(obj, number, result)
        is_drawing = hasattr(obj, "get_data") and (obj.get("/Subtype") == "/Form" or obj.get("/PatternType") == 1)
        if is_drawing:
            contents.append(ContentStream(obj, reader))
    for content in contents:
        if content is not None:
            _look_at_content(content, result)
    return result


def _look_at_dictionary(obj, number: int, result: ColourScan) -> None:
    if obj.get("/ShadingType") is not None:
        space = _space_name(obj.get("/ColorSpace", "")) if "/ColorSpace" in obj else None
        colours = [tuple(float(v) for v in leaf[key]) for leaf in _functions(obj["/Function"]) for key in ("/C0", "/C1")]
        result.shadings.append((space, colours))
    for key in ("/ColorSpace", "/CS"):
        if key in obj:
            space = _space_name(obj[key])
            if space is not None:
                result.spaces.add(space)
                if space == "DeviceRGB":
                    result.rgb.append(f"object {number} {key} DeviceRGB")
            elif isinstance(obj[key].get_object(), dict):        # a resource table of named spaces
                for name, value in obj[key].get_object().items():
                    inner = _space_name(value)
                    if inner is not None:
                        result.spaces.add(inner)
                        if inner == "DeviceRGB":
                            result.rgb.append(f"object {number} {name} DeviceRGB")


def _look_at_content(content: ContentStream, result: ColourScan) -> None:
    for operands, operator in content.operations:
        if operator in COLOUR_OPERATORS:
            result.ops[operator.decode()].append(tuple(float(v) for v in operands))
            if operator in (b"rg", b"RG"):
                result.rgb.append(f"{operator.decode()} operator")
