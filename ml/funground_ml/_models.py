"""The model files funground-ml uses: one table, each pinned to a commit and a checksum (D-124, D-125).

The pose and hand files are the OpenCV Zoo's ONNX conversions of MediaPipe's models (Apache-2.0), kept on the Hugging
Face Hub in the ``opencv`` organisation. The person file is Google's MediaPipe selfie segmentation model (the general one, 256 x 256,
Apache-2.0) as ONNX, from the ``onnx-community`` organisation. Each address names a commit, never ``main``, so the file cannot
change under a learner. ``_fetch`` checks the size and the SHA-256 before it keeps a download.
"""
from __future__ import annotations

from dataclasses import dataclass

HUB = "https://huggingface.co"


@dataclass(frozen=True)
class Model:
    """One model file."""
    name: str          # what funground calls it
    repo: str          # the Hub repository, "organisation/name"
    commit: str        # the commit of that repository the file is taken from
    file: str          # the file's name in the repository (and the name it is kept under)
    size: int          # bytes
    sha256: str
    licence: str
    kept_as: str = ""  # the name the copy in ``models/`` has, when the file's own name says too little ("onnx/model.onnx")

    @property
    def url(self) -> str:
        return f"{HUB}/{self.repo}/resolve/{self.commit}/{self.file}"

    @property
    def local_name(self) -> str:
        """The file name of the copy kept beside the sketch."""
        return self.kept_as or self.file


MODELS: dict[str, Model] = {m.name: m for m in (
    Model("pose_detector", "opencv/person_detection_mediapipe", "531b6da87204aa40aa5cc680b4d032dd09b5055e",
          "person_detection_mediapipe_2023mar.onnx", 11990159,
          "47fd5599d6fa17608f03e0eb0ae230baa6e597d7e8a2c8199fe00abea55a701f", "Apache-2.0"),
    Model("pose_landmarks", "opencv/pose_estimation_mediapipe", "8cd55743af63a8578effaf144a68cb58f6450fe9",
          "pose_estimation_mediapipe_2023mar.onnx", 5557238,
          "9d89c599319a18fb7d2e28451a883476164543182bafca5f09eb2cf767ed2f3f", "Apache-2.0"),
    Model("palm_detector", "opencv/palm_detection_mediapipe", "233e619dcea1759bf6de707b9b904fe30881ea55",
          "palm_detection_mediapipe_2023feb.onnx", 3905734,
          "78ff51c38496b7fc8b8ebdb6cc8c1abb02fa6c38427c6848254cdaba57fcce7c", "Apache-2.0"),
    Model("hand_landmarks", "opencv/handpose_estimation_mediapipe", "4b2a0b446e5cf2f11fb6b2c7251091c035d2c1f7",
          "handpose_estimation_mediapipe_2023feb.onnx", 4099621,
          "db0898ae717b76b075d9bf563af315b29562e11f8df5027a1ef07b02bef6d81c", "Apache-2.0"),
    Model("person_mask", "onnx-community/mediapipe_selfie_segmentation", "be49485c8e027524be38591817fc5cd31bd9d00e",
          "onnx/model.onnx", 462352,
          "3241ac4ad8aa35bdaf33946776db29f7c283a413aa0b0dacb9483594b4531aad", "Apache-2.0",
          kept_as="mediapipe_selfie_segmentation.onnx"),
)}

# What each task needs: a finder, then the landmark model (pose and hand); one model for the person's mask.
TASKS: dict[str, tuple[str, ...]] = {
    "pose": ("pose_detector", "pose_landmarks"),
    "hand": ("palm_detector", "hand_landmarks"),
    "person": ("person_mask",),
}
