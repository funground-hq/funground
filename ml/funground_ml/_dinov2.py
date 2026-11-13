"""The picture model on a computer: DINOv2-small (8-bit) with onnxruntime, numpy for the sums (S-235; desktop only).

The recipe is spike 23's: the colour only, the shorter side scaled to 256 (bicubic), the middle 224 x 224 cut out, ImageNet's mean
and spread, and the model's first output at token 0 (the CLS token) made length 1. Two pictures that look alike then have vectors
whose dot product is near 1. numpy and Pillow are imported inside the functions, so importing this module loads neither.
"""
from __future__ import annotations

from typing import Callable

SHORT_SIDE = 256
CROP = 224
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


def prepare(image):
    """The model's input for a Pillow RGB *image*: float32, shape (1, 3, 224, 224)."""
    import numpy as np
    from PIL import Image

    width, height = image.size
    scale = SHORT_SIDE / min(width, height)
    image = image.resize((round(width * scale), round(height * scale)), Image.BICUBIC)
    width, height = image.size
    left, top = (width - CROP) // 2, (height - CROP) // 2
    image = image.crop((left, top, left + CROP, top + CROP))
    pixels = np.asarray(image, dtype=np.float32) / 255.0
    pixels = (pixels - np.asarray(MEAN, dtype=np.float32)) / np.asarray(STD, dtype=np.float32)
    return np.ascontiguousarray(pixels.transpose(2, 0, 1)[None], dtype=np.float32)


def load(paths: dict[str, str]) -> Callable:
    """The function from a Pillow RGB image to its vector (a float32 numpy array of length 1), for the model file in *paths*.

    The session is made here, so the caller decides which thread loads the model.
    """
    import numpy as np

    from . import _runtime      # here, not at the top: importing this module must not load onnxruntime's module

    session = _runtime.session(paths["model"])
    name = session.get_inputs()[0].name

    def vector(image):
        token = session.run(None, {name: prepare(image)})[0][0, 0]          # output 0, the CLS token
        return (token / np.linalg.norm(token)).astype(np.float32)

    return vector
