"""S-231 step 2: MediaPipe Tasks (Python) on the desktop. One task per process.

Usage: measure.py TASK MODELS_DIR IMAGES_DIR OUT_JSON   (TASK = pose_lite pose_full hand face segment classify convert)
Run with the scratch venv's Python. Model and image files are never committed.
"""
import json, os, statistics, sys, time

os.environ.setdefault("FUNGROUND_HEADLESS", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import numpy as np
import pygame
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

TASKS = {
    "pose_lite": ("PoseLandmarker", "pose_landmarker_lite.task", "pose.jpg"),
    "pose_full": ("PoseLandmarker", "pose_landmarker_full.task", "pose.jpg"),
    "hand": ("HandLandmarker", "hand_landmarker.task", "thumb_up.jpg"),
    "face": ("FaceLandmarker", "face_landmarker.task", "portrait.jpg"),
    "segment": ("ImageSegmenter", "selfie_segmenter.tflite", "pose.jpg"),
    "classify": ("ImageClassifier", "efficientnet_lite0.tflite", "pose.jpg"),
}
N = 100


def frame_640(images, name):
    pygame.init()
    s = pygame.image.load(os.path.join(images, name))
    return pygame.transform.smoothscale(s.convert(24), (640, 480))


def to_mp_image(surface):
    """Surface (640 x 480) to mp.Image: tobytes -> numpy view -> SRGB image."""
    w, h = surface.get_size()
    raw = pygame.image.tobytes(surface, "RGB")
    arr = np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 3)
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=arr)


def stats(ms):
    ms = sorted(ms)
    return {"median_ms": round(statistics.median(ms), 2), "p90_ms": round(ms[int(len(ms) * 0.9) - 1], 2),
            "per_second": round(1000 / statistics.mean(ms), 1)}


def found(task, r):
    if task.startswith("pose"):
        return len(r.pose_landmarks[0]) if r.pose_landmarks else 0
    if task == "hand":
        return len(r.hand_landmarks[0]) if r.hand_landmarks else 0
    if task == "face":
        return len(r.face_landmarks[0]) if r.face_landmarks else 0
    if task == "segment":
        return int(r.confidence_masks[0].numpy_view().size) if r.confidence_masks else 0
    if task == "classify":
        c = r.classifications[0].categories[0]
        return f"{c.category_name} {c.score:.2f}"


def call(det, task):
    name = {"segment": "segment_for_video", "classify": "classify_for_video"}.get(task, "detect_for_video")
    return getattr(det, name)


def make(task, path):
    kind = TASKS[task][0]
    base = BaseOptions(model_asset_path=path, delegate=BaseOptions.Delegate.CPU)
    M = vision.RunningMode.VIDEO
    cls = getattr(vision, kind)
    opt = getattr(vision, kind + "Options")
    return cls.create_from_options(opt(base_options=base, running_mode=M))


def main():
    task, models, images, out = sys.argv[1:5]
    surf = frame_640(images, TASKS[task][2] if task in TASKS else "pose.jpg")
    if task == "convert":
        for _ in range(20):
            to_mp_image(surf)
        ms = []
        for _ in range(500):
            t = time.perf_counter(); to_mp_image(surf); ms.append((time.perf_counter() - t) * 1000)
        res = {"task": task, "frames": 500, **stats(ms)}
    else:
        t0 = time.perf_counter()
        det = make(task, os.path.join(models, TASKS[task][1]))
        img = to_mp_image(surf)
        r = call(det, task)(img, 0)
        first = time.perf_counter() - t0
        ms = []
        for i in range(1, N + 1):
            t = time.perf_counter()
            r = call(det, task)(img, i * 33)
            ms.append((time.perf_counter() - t) * 1000)
        res = {"task": task, "frames": N, "first_result_s": round(first, 2), **stats(ms), "found": found(task, r)}
        det.close()
    res["mediapipe"] = mp.__version__
    print(json.dumps(res))
    d = json.load(open(out)) if os.path.exists(out) else {}
    d[task] = res
    json.dump(d, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
