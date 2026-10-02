"""GIF and MP4 files (story S-100, contract M1, decision D-048).

Frames arrive as plain RGB bytes at the canvas's logical size. A GIF is written with Pillow
when it is installed (the optional ``funground[extras]``), else by ffmpeg. An MP4 is always
written by ffmpeg, which is fed raw frames through a pipe.

Pillow is imported only inside ``_pillow()``. ffmpeg is found in one place, ``find_ffmpeg()``:
that is the one function to extend if a bundled ffmpeg is ever offered (D-045).
"""
from __future__ import annotations

import array
import math
import shutil
import subprocess
import tempfile
from fractions import Fraction

MOTION_FORMATS = ("gif", "mp4")

_NO_ENCODER_GIF = (
    "f.save_gif() and saving a .gif need Pillow or ffmpeg, and neither was found. "
    "The easy way is to install Pillow with:  pip install funground[extras]"
)
_NO_FFMPEG = (
    "Saving an .mp4 needs ffmpeg, a free program, and funground cannot find it. "
    "Install it, then close and reopen your terminal. "
    "Windows: winget install ffmpeg. Mac: brew install ffmpeg. Linux: sudo apt install ffmpeg. "
    "To make a .gif instead, install Pillow with:  pip install funground[extras]"
)


def find_ffmpeg() -> str | None:
    """The ffmpeg program to use, or None. Today: the first one on the PATH (D-045 may add more)."""
    return shutil.which("ffmpeg")


def _pillow():
    """Pillow's Image module when the optional extra is installed, else None."""
    try:
        from PIL import Image
    except ImportError:
        return None
    return Image


def require_encoder(kind: str) -> None:
    """Raise the plain-English RuntimeError now, if a file of this kind could not be written."""
    if kind == "mp4":
        if find_ffmpeg() is None:
            raise RuntimeError(_NO_FFMPEG)
    elif _pillow() is None and find_ffmpeg() is None:
        raise RuntimeError(_NO_ENCODER_GIF)


# ------------------------------------------------------------------ frames
def bgra_to_rgb(bgra: bytes, width: int, height: int) -> bytes:
    """Premultiplied BGRA (Cairo layout) to RGB, laid over white where the canvas is see-through."""
    n = width * height
    data = bytes(bgra)
    if len(data) != n * 4:
        raise ValueError("pixel buffer size does not match its width and height")
    out = bytearray(n * 3)
    alpha = data[3::4]
    if alpha.count(255) == n:
        out[0::3], out[1::3], out[2::3] = data[2::4], data[1::4], data[0::4]
    else:
        for target, source in ((0, 2), (1, 1), (2, 0)):
            out[target::3] = bytes(c + 255 - a for c, a in zip(data[source::4], alpha))
    return bytes(out)


def resample_bgra(bgra: bytes, from_width: int, from_height: int, width: int, height: int) -> bytes:
    """The nearest-pixel copy of a BGRA picture at another size (a script page made at a finer scale)."""
    if (from_width, from_height) == (width, height):
        return bytes(bgra)
    src = memoryview(bytes(bgra)).cast("I")
    cols = [min(from_width - 1, int((x + 0.5) * from_width / width)) for x in range(width)]
    out = array.array("I")
    for y in range(height):
        start = min(from_height - 1, int((y + 0.5) * from_height / height)) * from_width
        row = src[start:start + from_width]
        out.extend(row[c] for c in cols)
    return out.tobytes()


# ------------------------------------------------------------------ timing
def gif_milliseconds(seconds: float) -> int:
    """A frame time as GIF can hold it: a multiple of 10 ms, at least 20 ms (contract M1)."""
    return max(20, int(round(seconds * 100)) * 10)


def _rate_text(rate: Fraction) -> str:
    return str(rate.numerator) if rate.denominator == 1 else f"{rate.numerator}/{rate.denominator}"


def plan_timing(durations: list[float]) -> tuple[str, list[int]]:
    """How to give ffmpeg the frame times: (input frame rate, how many times to send each frame).

    One shared time gives that rate and one copy of each frame. Different times are rounded to
    10 ms; the rate is then the biggest one that divides all of them, and a longer frame is sent
    several times. ffmpeg reads a plain pipe of frames, so this is simpler than a list of times.
    """
    first = durations[0]
    if all(d == first for d in durations):
        return _rate_text(1 / Fraction(first).limit_denominator(1000)), [1] * len(durations)
    ms = [max(10, int(round(d * 100)) * 10) for d in durations]
    step = math.gcd(*ms)
    return _rate_text(Fraction(1000, step)), [m // step for m in ms]


# ------------------------------------------------------------------ writing
def _check(frames: list[bytes], size: tuple[int, int], durations: list[float]) -> None:
    if not frames:
        raise ValueError("there are no frames to save")
    if len(durations) != len(frames):
        raise ValueError("there must be one time for each frame")
    w, h = size
    for number, frame in enumerate(frames, 1):
        if len(frame) != w * h * 3:
            raise ValueError(f"frame {number} is not {w} x {h} pixels")


def write_gif(path: str, frames: list[bytes], size: tuple[int, int], durations: list[float]) -> None:
    """Write an endlessly looping GIF: Pillow if it is installed, else ffmpeg."""
    _check(frames, size, durations)
    Image = _pillow()
    if Image is not None:
        images = [Image.frombytes("RGB", size, frame) for frame in frames]
        images[0].save(path, format="GIF", save_all=True, append_images=images[1:],
                       duration=[gif_milliseconds(d) for d in durations], loop=0, disposal=1)
        return
    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        raise RuntimeError(_NO_ENCODER_GIF)
    graph = "[0:v]split[a][b];[a]palettegen[p];[b][p]paletteuse"
    _run_ffmpeg(ffmpeg, path, frames, size, durations, ["-filter_complex", graph, "-loop", "0"])


def write_mp4(path: str, frames: list[bytes], size: tuple[int, int], durations: list[float]) -> None:
    """Write an H.264 MP4 with ffmpeg; an odd width or height is padded by one pixel."""
    _check(frames, size, durations)
    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        raise RuntimeError(_NO_FFMPEG)
    _run_ffmpeg(ffmpeg, path, frames, size, durations,
                ["-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                 "-movflags", "+faststart"])


def _run_ffmpeg(ffmpeg: str, path: str, frames: list[bytes], size: tuple[int, int],
                durations: list[float], output_options: list[str]) -> None:
    rate, repeats = plan_timing(durations)
    command = [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{size[0]}x{size[1]}", "-r", rate, "-i", "-", *output_options, path]
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=errors)
        try:
            for frame, count in zip(frames, repeats):
                for _ in range(count):
                    process.stdin.write(frame)
        except (BrokenPipeError, OSError):
            pass                                  # ffmpeg stopped early: its own message follows
        finally:
            try:
                process.stdin.close()
            except OSError:
                pass
            code = process.wait()
        if code != 0:
            errors.seek(0)
            message = errors.read().decode("utf-8", "replace").strip()[-400:]
            raise RuntimeError(f"ffmpeg could not write {path!r}" + (f": {message}" if message else ""))
