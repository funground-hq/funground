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

_SVG_MESSAGE = ("SVG files cannot be loaded as images; SVG import comes with a later release "
                "(f.load_svg). Save the drawing as a PNG for now")


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
