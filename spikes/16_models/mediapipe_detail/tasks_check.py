"""Run every task once: python -I tasks_check.py MODELS_DIR IMAGES_DIR
Prints one line per task. Exit code 0 if all worked."""
import sys, os, numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision, audio
from mediapipe.tasks.python.components.containers.audio_data import AudioData
M, I = sys.argv[1], sys.argv[2]
def img(n): return mp.Image.create_from_file(os.path.join(I, n))
def base(n): return BaseOptions(model_asset_path=os.path.join(M, n))
ok = True
def run(name, fn):
    global ok
    try: print(f"{name}: {fn()}", flush=True)
    except Exception as e:
        ok = False; print(f"{name}: FAIL {type(e).__name__}: {e}", flush=True)
def pose():
    with vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(base_options=base("pose_landmarker_lite.task"))) as t:
        return len(t.detect(img("pose.jpg")).pose_landmarks[0]), "landmarks"
def hand():
    with vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(base_options=base("hand_landmarker.task"))) as t:
        return len(t.detect(img("thumb_up.jpg")).hand_landmarks[0]), "landmarks"
def face():
    with vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(base_options=base("face_landmarker.task"))) as t:
        return len(t.detect(img("portrait.jpg")).face_landmarks[0]), "landmarks"
def seg():
    with vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(base_options=base("selfie_segmenter.tflite"), output_confidence_masks=True)) as t:
        return t.segment(img("pose.jpg")).confidence_masks[0].numpy_view().shape, "mask"
def cls():
    with vision.ImageClassifier.create_from_options(vision.ImageClassifierOptions(base_options=base("efficientnet_lite0.tflite"), max_results=1)) as t:
        return t.classify(img("pose.jpg")).classifications[0].categories[0].category_name
def aud():
    with audio.AudioClassifier.create_from_options(audio.AudioClassifierOptions(base_options=base("yamnet.tflite"), max_results=1)) as t:
        data = AudioData.create_from_array(np.zeros(15600, dtype=np.float32), 16000)
        return t.classify(data)[0].classifications[0].categories[0].category_name
for n, f in [("pose", pose), ("hand", hand), ("face", face), ("selfie", seg), ("image classifier", cls), ("audio classifier", aud)]: run(n, f)
print("ALL OK" if ok else "SOME FAILED")
