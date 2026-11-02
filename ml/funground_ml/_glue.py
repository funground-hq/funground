"""The pictures-in, points-out part of the pose and hand models (numpy and Pillow only; no onnxruntime).

Both tasks have two steps, as MediaPipe's own do:

1. A **detector** looks at the whole picture, squeezed into a square, and says roughly where the body (or the palm) is.
2. A **landmark model** looks at a square cut from the picture around that place, turned so the body (or hand) stands
   upright, and says where each point is.

The detectors give boxes and key points as offsets from a fixed grid of anchors, and the landmark models give points in
the cut square's own pixels. This file turns those back into pixels of the picture. It follows MediaPipe's documented
graph settings and the model files' own input and output shapes. Pictures are Pillow RGB images; points come out in the
picture's pixels as numpy arrays.

Every function takes the model's session (anything with ``run`` and ``get_inputs``) so that it needs no onnxruntime.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, NamedTuple

import numpy as np
from PIL import Image

# ---- the numbers that decide what is "a body" or "a hand", and how long a found box is trusted
DETECTOR_MIN_SCORE = 0.5     # the detector's best score, after the sigmoid, must reach this
POSE_MIN_SCORE = 0.5         # the pose landmark model's "there is a body" score
HAND_MIN_SCORE = 0.8         # the hand landmark model's "there is a hand" score
REUSE_MIN_SCORE = 0.9        # a box is reused for the next picture only if the landmarks found in it scored this well
REUSE_LIMIT = 10             # ... and for at most this many pictures in a row, then the detector looks again


# ---- cutting a square out of the picture
class Crop(NamedTuple):
    """A square cut from a picture and the way back from its pixels to the picture's pixels."""
    pixels: np.ndarray       # (size, size, 3) uint8
    scale: float             # picture pixels for one crop pixel (the crop is square and not stretched)
    coefficients: tuple      # the 2 x 3 affine matrix from crop pixels to picture pixels, row by row

    def to_picture(self, points) -> np.ndarray:
        """Crop pixel coordinates, shape (n, 2), as picture pixel coordinates."""
        p = np.asarray(points, np.float64)
        a, b, c, d, e, f = self.coefficients
        return np.stack([a * p[:, 0] + b * p[:, 1] + c, d * p[:, 0] + e * p[:, 1] + f], axis=1)


def cut(image: Image.Image, cx: float, cy: float, side: float, angle: float, size: int) -> Crop:
    """Cut a square *side* pixels wide, centred on (cx, cy) and turned by *angle* radians, and resample it to size x size.

    One affine transform does the cut, the turn, the padding with black where the square leaves the picture, and the
    resize. Pillow's transform maps each output pixel to a source pixel, which is the matrix kept in the Crop.
    """
    cos, sin, k = np.cos(angle), np.sin(angle), side / size
    coefficients = (k * cos, -k * sin, cx - 0.5 * side * (cos - sin),
                    k * sin, k * cos, cy - 0.5 * side * (sin + cos))
    pixels = np.asarray(image.transform((size, size), Image.Transform.AFFINE, coefficients, Image.Resampling.BILINEAR))
    return Crop(pixels, float(k), coefficients)


def letterbox(image: Image.Image, size: int) -> Crop:
    """The whole picture inside a size x size square, not stretched, with black bars where it does not reach."""
    return cut(image, image.width / 2, image.height / 2, max(image.size), 0.0, size)


def region_of_interest(image: Image.Image, box: tuple, key_from: tuple, key_to: tuple,
                       scale: float, shift_y: float, size: int) -> Crop:
    """MediaPipe's region of interest for a landmark model, from a detection.

    The square is turned so that the line from *key_from* to *key_to* points up, made *scale* times the box's longer
    side, and moved along the box's own up direction by *shift_y* times its height. *box* is (centre x, centre y, width,
    height) in picture pixels.
    """
    (cx, cy, width, height), (x0, y0), (x1, y1) = box, key_from, key_to
    angle = np.pi / 2 - np.arctan2(-(y1 - y0), x1 - x0)
    angle -= 2 * np.pi * np.floor((angle + np.pi) / (2 * np.pi))       # into -pi .. pi
    cx, cy = cx - shift_y * height * np.sin(angle), cy + shift_y * height * np.cos(angle)
    return cut(image, cx, cy, max(width, height) * scale, angle, size)


# ---- the detectors
def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -50, 50)))


def anchors(size: int, strides: list[int]) -> np.ndarray:
    """The detector's anchor centres, (n, 2), as fractions of the square (0 to 1), as MediaPipe defines them.

    Each stride gives a grid with a cell every *stride* pixels and two anchors in each cell; consecutive layers with the
    same stride are merged into one grid with more anchors per cell.
    """
    layers, i = [], 0
    while i < len(strides):
        j = i
        while j < len(strides) and strides[j] == strides[i]:
            j += 1
        cells = -(-size // strides[i])
        ys, xs = np.mgrid[:cells, :cells]
        centres = np.stack([(xs + 0.5) / cells, (ys + 0.5) / cells], axis=-1).reshape(-1, 1, 2)
        layers.append(np.repeat(centres, 2 * (j - i), axis=1).reshape(-1, 2))
        i = j
    return np.concatenate(layers)


@dataclass(frozen=True)
class Detector:
    """What differs between the two detectors; the rest of the work is shared."""
    size: int                # the square the picture is squeezed into
    strides: list            # for the anchors
    key_points: int          # how many key points follow the box in each detection
    channels_first: bool     # the input is (1, 3, size, size) instead of (1, size, size, 3)
    centred: bool            # the input is -1 to 1 instead of 0 to 1


POSE_DETECTOR = Detector(224, [8, 16, 32, 32, 32], 4, channels_first=True, centred=True)
PALM_DETECTOR = Detector(192, [8, 16, 16, 16], 7, channels_first=False, centred=False)
_anchor_cache: dict[tuple, np.ndarray] = {}


def _anchors_of(spec: Detector) -> np.ndarray:
    key = (spec.size, tuple(spec.strides))
    if key not in _anchor_cache:
        _anchor_cache[key] = anchors(spec.size, spec.strides)
    return _anchor_cache[key]


class Detection(NamedTuple):
    box: tuple               # (centre x, centre y, width, height) in picture pixels
    key_points: np.ndarray   # (key_points, 2) in picture pixels


def detect(session, image: Image.Image, spec: Detector) -> Detection | None:
    """The detector's best detection in the picture, or None when its best score is under DETECTOR_MIN_SCORE.

    Only the best detection is used (one body, one hand), so there is no non-maximum suppression.
    """
    crop = letterbox(image, spec.size)
    x = crop.pixels.astype(np.float32)[None] / 255
    if spec.centred:
        x = (x - 0.5) * 2
    if spec.channels_first:
        x = x.transpose(0, 3, 1, 2)
    outputs = session.run(None, {session.get_inputs()[0].name: x})
    # One output has a single number for each anchor (the score), the other has the box and key points. Their order
    # is not the same in every file, so they are told apart by their shape.
    scores, regressions = sorted(outputs, key=lambda o: o.shape[-1])
    scores, regressions = scores[0, :, 0], regressions[0]
    best = int(np.argmax(scores))
    if sigmoid(scores[best]) < DETECTOR_MIN_SCORE:
        return None
    rows = regressions[best].reshape(-1, 2)          # box centre, box size, then the key points, in crop pixels
    anchor = _anchors_of(spec)[best]
    centre = crop.to_picture((rows[:1] / spec.size + anchor) * spec.size)[0]
    key_points = crop.to_picture((rows[2:2 + spec.key_points] / spec.size + anchor) * spec.size)
    width, height = np.abs(rows[1]) * crop.scale
    return Detection((float(centre[0]), float(centre[1]), float(width), float(height)), key_points)


# ---- the landmark models
class Landmarks(NamedTuple):
    points: np.ndarray       # (n, 2) in picture pixels
    score: float             # 0 to 1


def _run_landmarks(session, crop: Crop):
    return session.run(None, {session.get_inputs()[0].name: crop.pixels.astype(np.float32)[None] / 255})


def body_region(detection: Detection) -> tuple:
    """What the pose landmark model needs from a body detection: the middle of the hips and a point on the circle that
    holds the whole body (their distance is the body's size, their direction is which way up it is)."""
    return (tuple(detection.key_points[0]), tuple(detection.key_points[1]))


def body_landmarks(session, image: Image.Image, region: tuple, count: int = 33) -> Landmarks | None:
    """The body's 33 points in the square around *region*, or None when the score is under POSE_MIN_SCORE.

    The model gives 39 rows of (x, y, depth, visible, present); the first 33 are the body, the last 6 are helpers for
    tracking that are not used here.
    """
    (x0, y0), (x1, y1) = region
    radius = float(np.hypot(x1 - x0, y1 - y0))
    crop = region_of_interest(image, (x0, y0, 2 * radius, 2 * radius), (x0, y0), (x1, y1), 1.25, 0.0, 256)
    outputs = _run_landmarks(session, crop)
    score = float(outputs[1][0, 0])
    if score < POSE_MIN_SCORE:
        return None
    rows = outputs[0][0].reshape(-1, 5)[:count]
    return Landmarks(crop.to_picture(rows[:, :2]), min(score, 1.0))


def hand_region(detection: Detection) -> tuple:
    """What the hand landmark model needs from a palm detection: the box, and the key points at the wrist and at the
    base of the middle finger (which way is up for the hand)."""
    return (detection.box, tuple(detection.key_points[0]), tuple(detection.key_points[2]))


def hand_landmarks(session, image: Image.Image, region: tuple, count: int = 21) -> Landmarks | None:
    """The hand's 21 points in the square around *region*, or None when the score is under HAND_MIN_SCORE."""
    box, key_from, key_to = region
    crop = region_of_interest(image, box, key_from, key_to, 2.6, -0.5, 224)
    outputs = _run_landmarks(session, crop)
    score = float(outputs[1][0, 0])
    if score < HAND_MIN_SCORE:
        return None
    rows = outputs[0][0].reshape(-1, 3)[:count]
    return Landmarks(crop.to_picture(rows[:, :2]), min(score, 1.0))


# ---- tracking: the box of the last picture, reused
class Tracker:
    """The region found for the last picture of one source, so the detector need not run for every picture.

    The region is reused for the next picture only while the landmarks found in it scored at least REUSE_MIN_SCORE,
    and for at most REUSE_LIMIT pictures in a row; then, or when a reused region does not do, the detector looks again.
    (This is the "box reused" mode of the S-231 spike: it is faster, and a body or hand that moves a long way between
    two pictures is found again by the detector.)
    """

    def __init__(self) -> None:
        self.region = None
        self.reused = 0
        self.size: tuple | None = None      # the size of the pictures it has seen: a new size starts again

    def forget(self) -> None:
        self.region, self.reused = None, 0

    def can_reuse(self) -> bool:
        return self.region is not None and self.reused < REUSE_LIMIT

    def find(self, image: Image.Image, detect_region: Callable[[], tuple | None],
             landmarks: Callable[[tuple], Landmarks | None]) -> Landmarks | None:
        """The landmarks in *image*. *detect_region()* gives a new region (or None for nobody); *landmarks(region)* gives
        the points in a region (or None when the score is too low)."""
        if self.size != image.size:
            self.forget()
            self.size = image.size
        if self.can_reuse():
            found = landmarks(self.region)
            if found is not None and found.score >= REUSE_MIN_SCORE:
                self.reused += 1
                return found
        region = detect_region()
        if region is None:
            self.forget()
            return None
        found = landmarks(region)
        if found is not None and found.score >= REUSE_MIN_SCORE:
            self.region, self.reused = region, 0
        else:
            self.forget()
        return found


# ---- the person's mask: one model, no boxes
MASK_SIZE = 256              # the selfie model reads a 256 x 256 picture and gives a 256 x 256 mask


def person_mask(session, image: Image.Image) -> bytes:
    """The model's mask for the whole picture: MASK_SIZE x MASK_SIZE bytes, 0 (not the person) to 255 (the person).

    The picture is stretched to the model's square (not letterboxed: the mask must cover the whole picture, and the model
    was made for stretched pictures), scaled to 0..1 with no mean, and the model gives a 0..1 value for each pixel. The
    values stay soft: nothing is cut at a threshold. (The browser's twin is ``personMask`` in models-glue.js.)
    """
    x = np.asarray(image.resize((MASK_SIZE, MASK_SIZE), Image.Resampling.BILINEAR), np.float32).transpose(2, 0, 1)[None] / 255
    alphas = session.run(None, {session.get_inputs()[0].name: x})[0][0, 0]
    return np.clip(np.floor(alphas * 255 + 0.5), 0, 255).astype(np.uint8).tobytes()
