"""The model files funground-ml uses: one table, each pinned to a commit and a checksum (D-124, D-125).

The files are the OpenCV Zoo's ONNX conversions of MediaPipe's pose and hand models (Apache-2.0), kept on the Hugging
Face Hub in the ``opencv`` organisation. Each address names a commit, never ``main``, so the file cannot change under a
learner. ``_fetch`` checks the size and the SHA-256 before it keeps a download.
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

    @property
    def url(self) -> str:
        return f"{HUB}/{self.repo}/resolve/{self.commit}/{self.file}"


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
)}

# What each task needs: a finder, then the landmark model.
TASKS: dict[str, tuple[str, str]] = {
    "pose": ("pose_detector", "pose_landmarks"),
    "hand": ("palm_detector", "hand_landmarks"),
}
