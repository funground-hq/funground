"""The model files funground-ml uses: one table, each pinned to a commit and a checksum (D-124, D-125).

The pose and hand files are the OpenCV Zoo's ONNX conversions of MediaPipe's models (Apache-2.0), kept on the Hugging
Face Hub in the ``opencv`` organisation. The person file is Google's MediaPipe selfie segmentation model (the general one, 256 x 256,
Apache-2.0) as ONNX, from the ``onnx-community`` organisation. Each address names a commit, never ``main``, so the file cannot
change under a learner. ``_fetch`` checks the size and the SHA-256 before it keeps a download.

The words files (S-234) are OpenAI's Whisper tiny.en, converted to ONNX and quantized to 8 bits by the ``onnx-community``
organisation (Apache-2.0 on the original; the converted repository's card names no licence): the encoder, the decoder, and the
token table ``vocab.json`` that turns the model's numbers back into text. Reading the table is a few lines of our own
(``_speech.py``), so there is no ``tokenizers`` library to install.

The sound file (S-250) is Google's YAMNet as ONNX, funground's own copy of the community repository ``audiomagic/yamnet-onnx``, so it cannot vanish with someone else's account (Apache-2.0 on the
original; the converted repository's card names no licence). Its scores match Google's model to 6.7e-5 (spike 18). The 521 names
it scores are in ``_sound_names.py``, not downloaded. The sound names come from the AudioSet ontology by Google LLC, CC BY 4.0.

The picture file (S-235) is Meta AI's DINOv2-small (Apache-2.0), converted to ONNX and quantized to 8 bits by the ``onnx-community``
organisation. ``ml.teach`` and ``ml.guess`` turn a picture into a vector of 384 numbers with it (``_dinov2.py``).

The picture files (S-235) are two. MobileNetV4-small (Google; weights by timm; Apache-2.0) is the default (D-147): funground derived the
file from timm's weights and cut off the classifier, so it gives a vector of 1,280 numbers; the derivation script is in its Hub
repository, ``funground-hq/mobilenetv4-small-vector-onnx``. DINOv2-small is Meta AI's (Apache-2.0), converted to ONNX and quantized to
8 bits by the ``onnx-community`` organisation; it gives a vector of 384 numbers. ``ml.teach`` and ``ml.guess`` use them (``_pictures.py``).
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
    Model("words_encoder", "onnx-community/whisper-tiny.en", "2575352d61be1bf7225cf8f8b268a4678025fc58",
          "onnx/encoder_model_quantized.onnx", 10124993,
          "e93ec822f16a8fd264e7de972ad17d615ea7334b75a52d54c50c2e18dd503a25", "Apache-2.0",
          kept_as="whisper_tiny_en_encoder_q8.onnx"),
    Model("words_decoder", "onnx-community/whisper-tiny.en", "2575352d61be1bf7225cf8f8b268a4678025fc58",
          "onnx/decoder_model_merged_quantized.onnx", 30718858,
          "c0592d0749413c960569e1c7fb806b060d5d18f3ebad4a95cbf9a77dc6e9be52", "Apache-2.0",
          kept_as="whisper_tiny_en_decoder_q8.onnx"),
    Model("words_vocabulary", "onnx-community/whisper-tiny.en", "2575352d61be1bf7225cf8f8b268a4678025fc58",
          "vocab.json", 999186,
          "f6bd25a65e4e63ca31360e9fb11c7e4f9a391a78385d640acd814092dd6eee4f", "Apache-2.0",
          kept_as="whisper_tiny_en_vocab.json"),
    Model("sound_model", "funground-hq/yamnet-onnx", "9648eed1cf043f9163842e9cb6d5fd8291d0d1cf",
          "yamnet.onnx", 16093355,
          "d3835ffbbd4a1bb3e777f0ca217b5007907f5171dd5d17c4236b95b2af8f908e", "Apache-2.0"),
    Model("picture_mobilenet", "funground-hq/mobilenetv4-small-vector-onnx", "b234e0655ee20702f98785f82228dd6ad42412ba",
          "mobilenetv4_conv_small_vector.onnx", 9961955,
          "addc91348c45900b641eacd073fbaf1355ae395c2176f0a989a78be73205ae60", "Apache-2.0"),
    Model("picture_dinov2", "onnx-community/dinov2-small", "8b1f705a3a7f6f062f6bdd21986c1583d3ef105d",
          "onnx/model_quantized.onnx", 24446700,
          "c179f8f7f592449c4c1bca4cd124a7538021428c5ffb89afde9503935b197efb", "Apache-2.0",
          kept_as="dinov2_small_q8.onnx"),
)}

# What each task needs: a finder, then the landmark model (pose and hand); one model for the person's mask; the two halves of
# Whisper and its token table (words); one model each for the sound names (sound) and the picture's vector (teach and guess: one task for each picture model).
TASKS: dict[str, tuple[str, ...]] = {
    "pose": ("pose_detector", "pose_landmarks"),
    "hand": ("palm_detector", "hand_landmarks"),
    "person": ("person_mask",),
    "words": ("words_encoder", "words_decoder", "words_vocabulary"),
    "sound": ("sound_model",),
    "picture_mobilenet": ("picture_mobilenet",),
    "picture_dinov2": ("picture_dinov2",),
}

# The name each file of a task goes by in the paths ``_fetch.ensure`` gives back, in the order of TASKS.
ROLES: dict[str, tuple[str, ...]] = {
    "pose": ("detector", "landmarks"),
    "hand": ("detector", "landmarks"),
    "person": ("model",),
    "words": ("encoder", "decoder", "vocabulary"),
    "sound": ("model",),
    "picture_mobilenet": ("model",),
    "picture_dinov2": ("model",),
}

# What the download line calls a task, when its key says too little ("Downloading the picture model, ...").
SAYS: dict[str, str] = {"picture_mobilenet": "picture", "picture_dinov2": "picture"}
