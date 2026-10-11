"""The PDF colour step: exact CMYK for cmyk() colours, and sRGB for every other colour (story S-170, D-087).

Cairo writes every colour as ``DeviceRGB``. This step rewrites the finished file, once, in two ways.

1. **CMYK.** A colour from ``f.cmyk()`` was drawn in a stand-in RGB value (see `cmyk.py`). Wherever the
   stand-in appears, the step puts the exact inks: ``k`` and ``K`` for fills and strokes, and four-number
   colours in a gradient's functions. A group of transparency that holds nothing but CMYK is made a
   CMYK group, so nothing in the file is RGB.
2. **sRGB.** Every other RGB colour is tagged as sRGB: ``/FunSRGB cs 1 0 0 sc`` for ``1 0 0 rg``, an
   ``ICCBased`` colour space for shadings, images and groups, and an sRGB output intent. The file says what
   its RGB means, instead of leaving it to the viewer. A file that is only CMYK has no sRGB and no
   output intent: there is nothing for them to describe.

Order (see `_write_pdf`): after the text and layer steps and before the page boxes, because those steps look
for their own markers and leave colours alone. The walk is the same one the text step makes: page,
forms, tiling patterns, soft-mask groups, shadings. If the file holds cmyk() colours and anything goes
wrong (a shading this code does not understand, a form it did not visit), the file is removed and
`ColourError` says so. A print file with a wrong colour is worse than none. If it holds none, a failure
leaves the file as Cairo wrote it. See `Colour_For_Print_Note.md`.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (ArrayObject, ContentStream, DecodedStreamObject, DictionaryObject, FloatObject,
                           IndirectObject, NameObject, NumberObject, TextStringObject)

from .cmyk import CmykStandins

PROFILE = Path(__file__).resolve().parent.parent / "data" / "sRGB.icc"
SRGB_NAME = NameObject("/FunSRGB")                  # the resource name of the sRGB colour space
INTENT_NAME = "sRGB IEC61966-2.1"
MIN_HEADER = "%PDF-1.4"                             # output intents and transparency groups need PDF 1.4
RGB_OPERATORS = (b"rg", b"RG")
LEFTOVER = re.compile(rb"(?<![\w.])[-+.\d]+\s+[-+.\d]+\s+[-+.\d]+\s+(?:rg|RG)(?![\w])")


class ColourError(RuntimeError):
    """A PDF with cmyk() colours could not be finished. The file is removed, not left wrong."""


def finish_colour(path: str, standins: CmykStandins | None) -> None:
    """Rewrite the PDF at *path*: the CMYK stand-ins to exact inks, every other RGB colour to sRGB."""
    inked = bool(standins)
    try:
        with open(path, "rb") as file:
            reader = PdfReader(io.BytesIO(file.read()))
        writer = PdfWriter(clone_from=reader)
        writer.pdf_header = max(reader.pdf_header, MIN_HEADER).encode()   # an earlier step may have written 1.3
        _Rewriter(writer, standins if inked else CmykStandins()).run()
        with open(path, "wb") as file:
            writer.write(file)
        if inked:
            _check_nothing_left(path)
    except Exception as error:
        if not inked:
            return                                  # no cmyk(): the file is still as Cairo wrote it, untagged RGB
        _remove(path)
        raise ColourError(f"the PDF could not be written with its cmyk() colours ({error}); no file was left") from error


def _remove(path: str) -> None:
    try:
        Path(path).unlink()
    except OSError:
        pass


def _number(value: float) -> FloatObject:
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return FloatObject(text or "0")


def _ink_fractions(inks) -> list[FloatObject]:
    return [_number(v / 100) for v in inks]


def _formula(red: float, green: float, blue: float) -> tuple[float, float, float, float]:
    """RGB (each 0 to 1) as inks (each 0 to 1): the exact opposite of the screen's formula (contract S17).
    Used only for the RGB stops of a gradient that also has cmyk() stops."""
    black = 1 - max(red, green, blue)
    if black >= 1:
        return (0.0, 0.0, 0.0, 1.0)
    return tuple((1 - ink - black) / (1 - black) for ink in (red, green, blue)) + (black,)


class _Rewriter:
    def __init__(self, writer: PdfWriter, standins: CmykStandins) -> None:
        self.writer = writer
        self.standins = standins
        self.rgb_used = False                       # any RGB (so sRGB) left in the file?
        self._srgb: IndirectObject | None = None
        self._profile: IndirectObject | None = None
        self._groups: list = []                     # every /Group dictionary whose /CS is DeviceRGB
        self._visited: set = set()

    # ---- the walk
    def run(self) -> None:
        for page in self.writer.pages:
            self._take_group(page)
            contents = page.get_contents()
            if contents is not None:
                rewritten = self._rewrite(contents, page)
                if rewritten is not None:
                    page.replace_contents(rewritten)
            self._resources(page.get("/Resources"))
        tagged = self.rgb_used or not self.standins          # a file with no cmyk() has an sRGB intent, even if empty
        if tagged:
            self._add_output_intent()
        for group in self._groups:
            group[NameObject("/CS")] = self._srgb_space() if tagged else NameObject("/DeviceCMYK")

    def _first_visit(self, ref) -> bool:
        key = (ref.idnum, ref.generation) if isinstance(ref, IndirectObject) else id(ref.get_object())
        if key in self._visited:
            return False
        self._visited.add(key)
        return True

    def _take_group(self, holder) -> None:
        group = holder.get("/Group")
        if group is not None and group.get_object().get("/CS") == "/DeviceRGB":
            self._groups.append(group.get_object())

    def _resources(self, resources) -> None:
        if resources is None:
            return
        res = resources.get_object()
        for ref in (res.get("/Shading") or {}).values():
            if self._first_visit(ref):
                self._shading(ref.get_object())
        for ref in (res.get("/Pattern") or {}).values():
            if not self._first_visit(ref):
                continue
            pattern = ref.get_object()
            if pattern.get("/PatternType") == 2:
                self._shading(pattern["/Shading"].get_object())
            elif pattern.get("/PatternType") == 1:
                self._form(pattern)
        for ref in (res.get("/XObject") or {}).values():
            if not self._first_visit(ref):
                continue
            xobject = ref.get_object()
            if xobject.get("/Subtype") == "/Image":
                self._image(xobject)
            else:
                self._form(xobject)
        for state in (res.get("/ExtGState") or {}).values():
            smask = state.get_object().get("/SMask")
            if smask is not None and not isinstance(smask.get_object(), NameObject):
                group = smask.get_object().get("/G")
                if group is not None and self._first_visit(group):
                    self._form(group.get_object())

    def _form(self, form) -> None:
        """A Form XObject, tiling pattern or soft-mask group: its colour operators, then what it uses."""
        self._take_group(form)
        rewritten = self._rewrite(form, form)
        if rewritten is not None:
            form.set_data(rewritten.get_data())
        self._resources(form.get("/Resources"))

    # ---- content streams
    def _rewrite(self, stream, holder):
        """The content of *stream* with its rg/RG operators changed, or None when it has none.

        A stand-in becomes k or K with its exact inks. Any other RGB colour becomes `/FunSRGB cs` and
        `sc` (or `CS` and `SC`), and *holder*'s resources then say what /FunSRGB is."""
        data = stream.get_data()
        if b"rg" not in data and b"RG" not in data:
            return None
        parsed = ContentStream(stream, self.writer)
        out, changed, tagged = [], False, False
        for operands, operator in parsed.operations:
            if operator not in RGB_OPERATORS:
                out.append((operands, operator))
                continue
            fill = operator == b"rg"
            inks = self.standins.inks_for(*(float(v) for v in operands))
            if inks is not None:
                out.append((_ink_fractions(inks), b"k" if fill else b"K"))
            else:
                out.append(([SRGB_NAME], b"cs" if fill else b"CS"))
                out.append((operands, b"sc" if fill else b"SC"))
                tagged = True
            changed = True
        if not changed:
            return None
        parsed.operations = out
        if tagged:
            self.rgb_used = True
            self._name_srgb(holder)
        return parsed

    def _name_srgb(self, holder) -> None:
        """Let the stream's own resources say what /FunSRGB is."""
        if "/Resources" not in holder:
            holder[NameObject("/Resources")] = DictionaryObject()
        res = holder["/Resources"].get_object()
        if "/ColorSpace" not in res:
            res[NameObject("/ColorSpace")] = DictionaryObject()
        res["/ColorSpace"].get_object()[SRGB_NAME] = self._srgb_space()

    # ---- images and shadings
    def _image(self, image) -> None:
        if image.get("/ColorSpace") == "/DeviceRGB":
            image[NameObject("/ColorSpace")] = self._srgb_space()
            self.rgb_used = True

    def _shading(self, shading) -> None:
        if shading.get("/ColorSpace") != "/DeviceRGB":
            return
        function = shading.get("/Function")
        if function is None or isinstance(function, ArrayObject):
            raise ColourError("a shading has no single colour function")
        leaves = list(self._leaves(function.get_object()))
        colours = [(leaf, key, [float(v) for v in leaf[key]]) for leaf in leaves for key in ("/C0", "/C1")]
        if any(self.standins.inks_for(*rgb) is not None for _, _, rgb in colours):
            for leaf, key, rgb in colours:             # a CMYK gradient: its RGB stops, if any, go by the formula
                inks = self.standins.inks_for(*rgb)
                leaf[NameObject(key)] = ArrayObject(_ink_fractions(inks) if inks is not None
                                                    else [_number(v) for v in _formula(*rgb)])
            shading[NameObject("/ColorSpace")] = NameObject("/DeviceCMYK")
        else:
            shading[NameObject("/ColorSpace")] = self._srgb_space()
            self.rgb_used = True

    def _leaves(self, function):
        """The exponential functions (Type 2) of a gradient, inside a stitching function (Type 3) or alone."""
        kind = function.get("/FunctionType")
        if kind == 2:
            if len(function["/C0"]) == 4 and len(function["/C1"]) == 4:
                return                                  # a function shared with a shading already done
            if len(function["/C0"]) != 3 or len(function["/C1"]) != 3:
                raise ColourError("a gradient colour function is not red, green, blue")
            yield function
        elif kind == 3:
            for part in function["/Functions"]:
                yield from self._leaves(part.get_object())
        else:
            raise ColourError(f"a gradient uses a function of type {kind}, which this code does not read")

    # ---- the sRGB profile
    def _srgb_space(self) -> IndirectObject:
        if self._srgb is None:
            self._profile = self.writer._add_object(self._profile_stream())
            self._srgb = self.writer._add_object(ArrayObject([NameObject("/ICCBased"), self._profile]))
        return self._srgb

    @staticmethod
    def _profile_stream():
        stream = DecodedStreamObject()
        stream.set_data(PROFILE.read_bytes())
        stream[NameObject("/N")] = NumberObject(3)
        stream[NameObject("/Alternate")] = NameObject("/DeviceRGB")
        return stream.flate_encode()

    def _add_output_intent(self) -> None:
        self._srgb_space()
        intent = DictionaryObject({
            NameObject("/Type"): NameObject("/OutputIntent"),
            NameObject("/S"): NameObject("/GTS_PDFX"),
            NameObject("/OutputConditionIdentifier"): TextStringObject(INTENT_NAME),
            NameObject("/Info"): TextStringObject(INTENT_NAME),
            NameObject("/RegistryName"): TextStringObject("http://www.color.org"),
            NameObject("/DestOutputProfile"): self._profile,
        })
        self.writer._root_object[NameObject("/OutputIntents")] = ArrayObject([self.writer._add_object(intent)])


# ---- the safety net
def _check_nothing_left(path: str) -> None:
    """Read the finished file back and look at every content stream, whether or not the walk reached it.

    A document that holds cmyk() colours must hold no rg/RG operator at all (the walk turned each into k/K
    or an sRGB colour) and no RGB shading that still holds stand-in colours."""
    reader = PdfReader(path)
    for number in sorted(n for generations in reader.xref.values() for n in generations):
        obj = reader.get_object(number)
        if hasattr(obj, "get") and obj.get("/ShadingType") is not None and obj.get("/ColorSpace") == "/DeviceRGB":
            raise ColourError(f"object {number} is an RGB shading the walk did not reach")
        if obj is None or not hasattr(obj, "get_data"):
            continue
        if obj.get("/Subtype") == "/Image" or obj.get("/Type") in ("/XRef", "/Metadata", "/EmbeddedFile"):
            continue
        if obj.get("/Length1") is not None or obj.get("/N") is not None or obj.get("/Subtype") in ("/CIDFontType0C", "/OpenType"):
            continue                                # a font or a colour profile, not a drawing
        if LEFTOVER.search(obj.get_data()):
            raise ColourError(f"object {number} still holds an RGB colour the walk did not reach")
    for page in reader.pages:
        if LEFTOVER.search(page.get_contents().get_data() if page.get_contents() else b""):
            raise ColourError("a page still holds an RGB colour the walk did not reach")
