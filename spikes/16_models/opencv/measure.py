"""S-231 step 3: OpenCV cv2.dnn running OpenCV Zoo models on the desktop. One task per process.

Usage: measure.py TASK ZOO_MODELS_DIR IMAGES_DIR OUT_JSON
  TASK = pose pose_landmarks_only hand hand_landmarks_only face face_2026 segment
ZOO_MODELS_DIR is the `models` folder of a checkout of github.com/opencv/opencv_zoo (with the .onnx files pulled from
git LFS). Zoo wrapper classes (mp_pose.py, mp_persondet.py, mp_handpose.py, mp_palmdet.py, yunet.py, pphumanseg.py) are
imported from there (Apache-2.0 / MIT, copyright OpenCV Zoo contributors); nothing of them is copied into funground.
Run with the scratch venv's Python. Model and image files are never committed.
"""
import json, os, statistics, sys, time

import numpy as np
import cv2 as cv

CALLS = []  # Python-level network audit events (native code is not seen here; see netwatch.ps1)
sys.addaudithook(lambda ev, a: CALLS.append(ev) if ev.startswith("socket.") else None)

N = 100
IMG = {"pose": "pose.jpg", "hand": "thumb_up.jpg", "face": "portrait.jpg", "segment": "pose.jpg"}
M = {  # task -> (zoo dir, file)
    "persondet": ("person_detection_mediapipe", "person_detection_mediapipe_2023mar.onnx"),
    "pose": ("pose_estimation_mediapipe", "pose_estimation_mediapipe_2023mar.onnx"),
    "palmdet": ("palm_detection_mediapipe", "palm_detection_mediapipe_2023feb.onnx"),
    "hand": ("handpose_estimation_mediapipe", "handpose_estimation_mediapipe_2023feb.onnx"),
    "face": ("face_detection_yunet", "face_detection_yunet_2023mar.onnx"),
    "face_2026": ("face_detection_yunet", "face_detection_yunet_2026may.onnx"),
    "segment": ("human_segmentation_pphumanseg", "human_segmentation_pphumanseg_2023mar.onnx"),
}


def path(models, key):
    d, f = M[key]
    sys.path.insert(0, os.path.join(models, d))
    return os.path.join(models, d, f)


def stats(ms):
    ms = sorted(ms)
    return {"median_ms": round(statistics.median(ms), 2), "p90_ms": round(ms[int(len(ms) * 0.9) - 1], 2),
            "per_second": round(1000 / statistics.mean(ms), 1)}


def load_frame(images, name):
    img = cv.imread(os.path.join(images, name))        # BGR
    return cv.resize(img, (640, 480), interpolation=cv.INTER_AREA)


def build(task, models):
    """Return (setup_seconds_free_callable, step(frame)->result, describe(result)->found)."""
    if task in ("pose", "pose_landmarks_only"):
        pd_path, po_path = path(models, "persondet"), path(models, "pose")
        from mp_persondet import MPPersonDet
        from mp_pose import MPPose
        det, pose = MPPersonDet(pd_path), MPPose(po_path)
        cache = {}

        def step(frame):
            if task == "pose_landmarks_only" and "p" in cache:   # detector ran once; reuse its box (like tracking)
                persons = cache["p"]
            else:
                persons = det.infer(frame)
                cache["p"] = persons
            return [r for r in (pose.infer(frame, p) for p in persons) if r is not None]

        def found(r):
            if not r:
                return {"people": 0}
            bbox, lm, world, mask, heat, conf = r[0]
            return {"people": len(r), "landmarks": 33, "extra_points": len(lm) - 33, "has_z": True,
                    "has_world_3d": True, "has_mask": True, "conf": round(float(conf), 2)}
        return step, found
    if task in ("hand", "hand_landmarks_only"):
        pd_path, hp_path = path(models, "palmdet"), path(models, "hand")
        from mp_palmdet import MPPalmDet
        from mp_handpose import MPHandPose
        det, hp = MPPalmDet(pd_path, nmsThreshold=0.3, scoreThreshold=0.6), MPHandPose(hp_path)
        cache = {}

        def step(frame):
            if task == "hand_landmarks_only" and "p" in cache:
                palms = cache["p"]
            else:
                palms = det.infer(frame)
                cache["p"] = palms
            return [r for r in (hp.infer(frame, p) for p in palms) if r is not None]

        def found(r):
            if not len(r):
                return {"hands": 0}
            row = r[0]  # 132 numbers: bbox 4, 21*3 screen, 21*3 world, handedness, conf
            return {"hands": len(r), "landmarks": 21, "row_len": len(row), "conf": round(float(row[-1]), 2)}
        return step, found
    if task in ("face", "face_2026"):
        p = path(models, task)
        from yunet import YuNet
        net = YuNet(p, inputSize=[640, 480])
        return (lambda frame: net.infer(frame)), (lambda r: {"faces": len(r), "values_per_face": int(r.shape[1]) if len(r) else 0,
                                                              "points_per_face": 5, "conf": round(float(r[0][-1]), 2) if len(r) else 0})
    if task == "segment":
        p = path(models, "segment")
        from pphumanseg import PPHumanSeg
        net = PPHumanSeg(p)
        return (lambda frame: net.infer(frame)), (lambda r: {"mask_shape": list(r.shape), "person_pixels": int((r == 1).sum()),
                                                              "mask_pixels": int(r.size)})
    raise SystemExit("unknown task " + task)


def main():
    task, models, images, out = sys.argv[1:5]
    print("pid", os.getpid(), flush=True)
    frame = load_frame(images, IMG[task.split("_landmarks")[0].replace("_2026", "")])
    t0 = time.perf_counter()
    step, found = build(task, models)
    r = step(frame)
    first = time.perf_counter() - t0
    ms = []
    for _ in range(N):
        t = time.perf_counter(); r = step(frame); ms.append((time.perf_counter() - t) * 1000)
    res = {"task": task, "frames": N, "first_result_s": round(first, 2), **stats(ms), "found": found(r),
           "opencv": cv.__version__, "threads": cv.getNumThreads(), "python_socket_events": len(CALLS)}
    print(json.dumps(res), flush=True)
    d = json.load(open(out)) if os.path.exists(out) else {}
    d[task] = res
    json.dump(d, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
