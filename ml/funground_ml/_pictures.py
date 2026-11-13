"""The picture models on a computer: MobileNetV4-small and DINOv2-small (8-bit) with onnxruntime, numpy for the sums (S-235; desktop only).

Both models share one recipe, spike 23's (MobileNetV4's own preprocessor config says the same): the colour only, the shorter side
scaled to 256 (bicubic), the middle 224 x 224 cut out, and ImageNet's mean and spread. What differs is which output is the vector:
MobileNetV4's one output, ``vector``, made length 1; DINOv2's first output at token 0 (the CLS token), made length 1. Two pictures
that look alike then have vectors whose dot product is near 1. numpy and Pillow are imported inside the functions, so importing this
module loads neither.
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


def load(paths: dict[str, str], pick: Callable) -> Callable:
    """The function from a Pillow RGB image to its vector (a float32 numpy array of length 1), for the model file in *paths*.

    *pick* takes the model's raw outputs (the list ``session.run`` gives) and returns the 1-D vector, before it is made length 1.

    The session is made here, so the caller decides which thread loads the model.
    """
    import numpy as np

    from . import _runtime      # here, not at the top: importing this module must not load onnxruntime's module

    session = _runtime.session(paths["model"])
    name = session.get_inputs()[0].name

    def vector(image):
        raw = np.asarray(pick(session.run(None, {name: prepare(image)})), dtype=np.float32)
        return (raw / np.linalg.norm(raw)).astype(np.float32)

    return vector


def mobilenet_vector(outputs):
    """MobileNetV4's vector: its one output, ``vector``, shape (1, 1280), for the one picture."""
    return outputs[0][0]


def dinov2_vector(outputs):
    """DINOv2's vector: output 0 at token 0 (the CLS token)."""
    return outputs[0][0, 0]
