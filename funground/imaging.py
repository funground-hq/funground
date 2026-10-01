"""Reading image files (story S-077, contract P4, ADR-004).

pygame-ce decodes every file; this is the only module outside ``platform/`` that imports it
(the provider boundary, tests/test_boundaries.py). Nothing here needs a window: images are
loaded without a display, so it works headless.

``decode(path)`` returns ``(width, height, bgra)``. The bytes are already in Cairo's ARGB32
layout - premultiplied alpha, little-endian, so the byte order is B, G, R, A - which lets
``Picture.from_pixels`` copy them straight onto a Cairo surface with no further conversion.
This module may not import Cairo (the boundary test), so it does not ask Cairo for the row
stride. It does not need to: for ARGB32 Cairo's stride is always ``width * 4``, because four
bytes per pixel is already a multiple of Cairo's 4-byte row alignment. ``Picture.from_pixels``
checks that against the real surface and refuses to guess if it ever differs.
"""
from __future__ import annotations

import re
import struct

import pygame

_SVG_MESSAGE = "SVG files cannot be loaded as images; use f.load_svg() to read them as drawings"


def decode(path: str) -> tuple[int, int, bytes]:
    """Read the image file at *path* (an existing file): ``(width, height, premultiplied BGRA)``.

    Raises ``ValueError`` for an SVG file or a file pygame cannot read as an image. A JPEG is
    turned the right way up from its EXIF orientation tag first.
    """
    with open(path, "rb") as handle:
        head = handle.read(1024)
    if path.lower().endswith((".svg", ".svgz")) or (head.lstrip()[:1] == b"<" and b"<svg" in head.lower()):
        raise ValueError(f"f.load_image(): {path!r} is an SVG file. {_SVG_MESSAGE}")
    try:
        loaded = pygame.image.load(path)
    except Exception as exc:                      # pygame.error, or anything the decoder raises
        raise ValueError(f"f.load_image(): {path!r} is not an image funground can read ({exc})") from exc
    if head[:2] == b"\xff\xd8":
        loaded = _orient(loaded, exif_orientation(path))
    width, height = loaded.get_size()
    if width <= 0 or height <= 0:
        raise ValueError(f"f.load_image(): {path!r} has no pixels")
    # A transparent 32-bit surface needs no display (convert_alpha() would), and blitting onto
    # it also gives palette (GIF) and colour-keyed images a proper alpha channel.
    rgba = pygame.Surface((width, height), pygame.SRCALPHA, 32)
    rgba.blit(loaded, (0, 0))
    return width, height, pygame.image.tobytes(rgba.premul_alpha(), "BGRA")


# ------------------------------------------------------------------ orientation (EXIF)
def exif_orientation(path: str) -> int:
    """The EXIF orientation (1-8) of a JPEG file; 1 when there is none or it is damaged."""
    try:
        with open(path, "rb") as handle:
            data = handle.read(1 << 20)           # the Exif block sits at the very start
        return _orientation_from_jpeg(data)
    except Exception:                              # never an error: a bad tag just means "upright"
        return 1


def _orientation_from_jpeg(data: bytes) -> int:
    if data[:2] != b"\xff\xd8":
        return 1
    pos = 2
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            return 1
        marker = data[pos + 1]
        if marker == 0xFF:                         # padding byte
            pos += 1
            continue
        if marker in (0xD9, 0xDA):                 # end of image / start of scan: no Exif after this
            return 1
        (length,) = struct.unpack(">H", data[pos + 2:pos + 4])
        if length < 2:
            return 1
        segment = data[pos + 4:pos + 2 + length]
        if marker == 0xE1 and segment[:6] == b"Exif\x00\x00":
            return _orientation_from_tiff(segment[6:])
        pos += 2 + length
    return 1


def _orientation_from_tiff(tiff: bytes) -> int:
    if tiff[:2] == b"II":
        end = "<"
    elif tiff[:2] == b"MM":
        end = ">"
    else:
        return 1
    if struct.unpack(end + "H", tiff[2:4])[0] != 42:
        return 1
    (ifd,) = struct.unpack(end + "I", tiff[4:8])
    (count,) = struct.unpack(end + "H", tiff[ifd:ifd + 2])
    for i in range(count):
        entry = tiff[ifd + 2 + 12 * i:ifd + 14 + 12 * i]
        if len(entry) < 12:
            return 1
        tag, kind, n = struct.unpack(end + "HHI", entry[:8])
        if tag == 0x0112:
            if kind != 3 or n < 1:
                return 1
            (value,) = struct.unpack(end + "H", entry[8:10])
            return value if 1 <= value <= 8 else 1
    return 1


def _orient(surface: "pygame.Surface", orientation: int) -> "pygame.Surface":
    """Turn *surface* upright. pygame rotates counter-clockwise; EXIF 6 means "turn 90 clockwise"."""
    flip, rotate = pygame.transform.flip, pygame.transform.rotate
    if orientation == 2:
        return flip(surface, True, False)
    if orientation == 3:
        return rotate(surface, 180)
    if orientation == 4:
        return flip(surface, False, True)
    if orientation == 5:                           # transpose: clockwise, then mirror
        return flip(rotate(surface, -90), True, False)
    if orientation == 6:
        return rotate(surface, -90)
    if orientation == 7:                           # transverse: counter-clockwise, then mirror
        return flip(rotate(surface, 90), True, False)
    if orientation == 8:
        return rotate(surface, 90)
    return surface


def tint_pixels(bgra: bytes, width: int, height: int, red: int, green: int, blue: int) -> bytes:
    """Multiply the red, green and blue of premultiplied BGRA pixels by a tint colour (contract P5).

    Alpha is left alone, so a transparent area stays transparent. Premultiplied colour times the
    tint is exactly the multiplied colour at the same alpha. White (255, 255, 255) changes nothing.
    """
    if (red, green, blue) == (255, 255, 255):
        return bgra
    surface = pygame.image.frombuffer(bytearray(bgra), (width, height), "BGRA")   # a copy: never change the snapshot
    surface.fill((red, green, blue), special_flags=pygame.BLEND_RGB_MULT)
    return pygame.image.tobytes(surface, "BGRA")


# ------------------------------------------------------------------ pixel access (S-079, P7/P8)
# Cairo keeps premultiplied BGRA; learners see plain RGBA. pygame-ce reorders the channels (fast, in C).
# Only the pixels that are partly transparent need arithmetic, so a Python loop runs over those
# alone: it is the soft edges of a drawing, not every pixel. Rounding is to the nearest whole number
# in both directions, which makes premultiply(unpremultiply(p)) == p for every Cairo value, so
# load_pixels() followed by update_pixels() changes nothing.
_PARTIAL_ALPHA = re.compile(rb"[\x01-\xfe]")


def bgra_to_rgba(bgra: bytes, width: int, height: int) -> bytearray:
    """Premultiplied BGRA (Cairo) to RGBA that is not premultiplied (what ``pixels`` holds)."""
    out = bytearray(pygame.image.tobytes(pygame.image.frombuffer(bytearray(bgra), (width, height), "BGRA"), "RGBA"))
    alpha = bytes(out[3::4])
    for m in _PARTIAL_ALPHA.finditer(alpha):
        i = m.start()
        a = alpha[i]
        j = i * 4
        out[j] = min(255, (out[j] * 255 + a // 2) // a)
        out[j + 1] = min(255, (out[j + 1] * 255 + a // 2) // a)
        out[j + 2] = min(255, (out[j + 2] * 255 + a // 2) // a)
    return out


def rgba_to_bgra(rgba: bytes, width: int, height: int) -> bytes:
    """RGBA that is not premultiplied to premultiplied BGRA (Cairo's layout)."""
    surface = pygame.image.frombuffer(bytearray(rgba), (width, height), "RGBA")
    out = bytearray(pygame.image.tobytes(surface.premul_alpha(), "BGRA"))   # exact for alpha 0 and 255
    alpha = bytes(rgba[3::4])
    for m in _PARTIAL_ALPHA.finditer(alpha):
        i = m.start()
        a = alpha[i]
        j = i * 4
        out[j] = (rgba[j + 2] * a + 127) // 255        # blue
        out[j + 1] = (rgba[j + 1] * a + 127) // 255
        out[j + 2] = (rgba[j] * a + 127) // 255        # red
    return bytes(out)


# ------------------------------------------------------------------ copy, resize, mask (S-080, P9)
def resize_bgra(bgra: bytes, width: int, height: int, new_width: int, new_height: int) -> bytes:
    """Premultiplied BGRA scaled smoothly to a new size (pygame-ce ``smoothscale``)."""
    if (width, height) == (new_width, new_height):
        return bytes(bgra)
    surface = pygame.image.frombuffer(bytearray(bgra), (width, height), "BGRA")
    return pygame.image.tobytes(pygame.transform.smoothscale(surface, (new_width, new_height)), "BGRA")


_NOT_OPAQUE = re.compile(rb"[\x00-\xfe]")


def mask_bgra(bgra: bytes, mask_alpha: bytes) -> bytes:
    """Multiply the alpha of premultiplied BGRA by *mask_alpha* (one byte per pixel).

    Premultiplied colour is multiplied too, which is the same as multiplying the alpha alone.
    Only pixels where the mask is not fully opaque need any arithmetic.
    """
    out = bytearray(bgra)
    for m in _NOT_OPAQUE.finditer(mask_alpha):
        i = m.start()
        a = mask_alpha[i]
        j = i * 4
        out[j] = (out[j] * a + 127) // 255
        out[j + 1] = (out[j + 1] * a + 127) // 255
        out[j + 2] = (out[j + 2] * a + 127) // 255
        out[j + 3] = (out[j + 3] * a + 127) // 255
    return bytes(out)


# ------------------------------------------------------------------ filters (S-080, P10)
FILTER_KINDS = ("threshold", "gray", "opaque", "invert", "blur", "posterize", "erode", "dilate")


def check_filter(kind, value):
    """Check a ``filter(kind, value)`` call (contract P10) and return the value to use.

    Raises ``ValueError`` for an unknown kind or a value out of range, ``TypeError`` for a value
    that is not a number. Kinds that take no value ignore it, as p5 does.
    """
    if kind not in FILTER_KINDS:
        raise ValueError(f"f.filter(): unknown filter {kind!r}. Choose one of: " + ", ".join(FILTER_KINDS))

    def number() -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"f.filter({kind!r}): the value must be a number, not {value!r}")
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError(f"f.filter({kind!r}): the value must be a finite number, not {value!r}")
        return value

    if kind == "threshold":
        v = 0.5 if value is None else number()
        if not 0 <= v <= 1:
            raise ValueError("f.filter('threshold'): the value must be from 0 to 1 (default 0.5)")
        return float(v)
    if kind == "blur":
        v = 1 if value is None else number()
        if v < 0:
            raise ValueError("f.filter('blur'): the radius must be 0 or more (default 1)")
        return float(v)
    if kind == "posterize":
        if value is None:
            raise ValueError("f.filter('posterize') needs a value: how many levels each colour gets, "
                             "from 2 to 255, e.g. f.filter('posterize', 4)")
        v = number()
        if v != int(v) or not 2 <= v <= 255:
            raise ValueError("f.filter('posterize'): the value must be a whole number from 2 to 255")
        return int(v)
    return None


def luminance_plane(rgba: bytes) -> bytes:
    """The luminance 0.299 R + 0.587 G + 0.114 B of each pixel, rounded to the nearest whole number."""
    tr = [299 * v for v in range(256)]
    tg = [587 * v for v in range(256)]
    tb = [114 * v for v in range(256)]
    return bytes((tr[r] + tg[g] + tb[b] + 500) // 1000
                 for r, g, b in zip(rgba[0::4], rgba[1::4], rgba[2::4]))


def _gray_like(rgba: bytes, plane: bytes) -> bytearray:
    """*rgba* with red, green and blue all set from *plane*; alpha kept."""
    out = bytearray(rgba)
    out[0::4] = plane
    out[1::4] = plane
    out[2::4] = plane
    return out


def _map_channels(rgba: bytes, table: bytes) -> bytearray:
    """Apply a 256-byte lookup table to red, green and blue; alpha kept."""
    out = bytearray(rgba)
    for c in (0, 1, 2):
        out[c::4] = bytes(rgba[c::4]).translate(table)
    return out


def posterize_table(levels: int) -> bytes:
    """Each value v becomes round(v (L-1) / 255) * 255 / (L-1), rounded half up, as whole numbers."""
    n = levels - 1
    return bytes(((2 * ((2 * v * n + 255) // 510) * 255 + n) // (2 * n)) for v in range(256))


def _extreme_plane(plane: bytes, width: int, height: int, pick) -> bytes:
    """The minimum or maximum (*pick* = min or max) over each 3 x 3 neighbourhood, edges repeating."""
    rows = []
    for y in range(height):
        row = plane[y * width:(y + 1) * width]
        rows.append(bytes(map(pick, row[:1] + row[:-1], row, row[1:] + row[-1:])))
    out = bytearray()
    for y in range(height):
        out += bytes(map(pick, rows[max(y - 1, 0)], rows[y], rows[min(y + 1, height - 1)]))
    return bytes(out)


def _extreme_plain(rgba: bytes, width: int, height: int, pick) -> bytearray:
    out = bytearray(rgba)
    for c in (0, 1, 2):
        out[c::4] = _extreme_plane(bytes(rgba[c::4]), width, height, pick)
    return out


def _pillow():
    """The Pillow modules when the optional extra is installed, else None."""
    try:
        from PIL import Image, ImageFilter
    except ImportError:
        return None
    return Image, ImageFilter


def _posterize(rgba: bytes, width: int, height: int, levels: int) -> bytearray:
    table = posterize_table(levels)
    pil = _pillow()
    if pil is None:
        return _map_channels(rgba, table)
    Image, _ = pil
    image = Image.frombytes("RGBA", (width, height), bytes(rgba))
    out = image.point(list(table) * 3 + list(range(256)))     # red, green, blue by table; alpha unchanged
    return bytearray(out.tobytes())


def _extreme(rgba: bytes, width: int, height: int, kind: str) -> bytearray:
    pil = _pillow()
    if pil is None:
        return _extreme_plain(rgba, width, height, min if kind == "erode" else max)
    Image, ImageFilter = pil
    image = Image.frombytes("RGBA", (width, height), bytes(rgba))
    red, green, blue, alpha = image.split()
    rank = ImageFilter.MinFilter(3) if kind == "erode" else ImageFilter.MaxFilter(3)
    merged = Image.merge("RGBA", (red.filter(rank), green.filter(rank), blue.filter(rank), alpha))
    return bytearray(merged.tobytes())


def filter_bgra(bgra: bytes, width: int, height: int, kind: str, value=None) -> bytes:
    """Premultiplied BGRA with a filter applied (contract P10); *kind* and *value* as ``check_filter``.

    Everything except blur works on plain RGBA (not premultiplied), as P10's formulas assume. Blur
    works on the premultiplied pixels, so see-through edges blur without a coloured fringe.
    """
    value = check_filter(kind, value)
    if kind == "blur":
        radius = int(value + 0.5)
        if radius == 0:
            return bytes(bgra)
        surface = pygame.image.frombuffer(bytearray(bgra), (width, height), "BGRA")
        blurred = pygame.transform.gaussian_blur(surface, radius, True)
        return pygame.image.tobytes(blurred, "BGRA")
    rgba = bytes(bgra_to_rgba(bgra, width, height))
    if kind == "gray":
        out = _gray_like(rgba, luminance_plane(rgba))
    elif kind == "threshold":
        cut = bytes(255 if v / 255 > value else 0 for v in range(256))
        out = _gray_like(rgba, luminance_plane(rgba).translate(cut))
    elif kind == "opaque":
        out = bytearray(rgba)
        out[3::4] = b"\xff" * (width * height)
    elif kind == "invert":
        out = _map_channels(rgba, bytes(255 - v for v in range(256)))
    elif kind == "posterize":
        out = _posterize(rgba, width, height, value)
    else:                                                  # erode or dilate
        out = _extreme(rgba, width, height, kind)
    return rgba_to_bgra(bytes(out), width, height)
