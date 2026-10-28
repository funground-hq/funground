"""Pose on a still picture: MediaPipe finds 33 points, funground draws them and their names.
Usage: pose_sketch.py MODEL.task IMAGE.jpg [OUT.png]   (run with the scratch venv's Python)"""
import os, sys
os.environ.setdefault("FUNGROUND_HEADLESS", "1")
import funground as f
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

NAMES = ["nose", "left eye inner", "left eye", "left eye outer", "right eye inner", "right eye", "right eye outer",
         "left ear", "right ear", "mouth left", "mouth right", "left shoulder", "right shoulder", "left elbow",
         "right elbow", "left wrist", "right wrist", "left pinky", "right pinky", "left index", "right index",
         "left thumb", "right thumb", "left hip", "right hip", "left knee", "right knee", "left ankle",
         "right ankle", "left heel", "right heel", "left foot index", "right foot index"]
model, path, out = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else "pose_sketch.png")
pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=model)))
points = pose.detect(mp.Image.create_from_file(path)).pose_landmarks[0]
picture = f.load_image(path)
f.size(picture.width, picture.height)
f.image(picture, 0, 0)
f.text_size(11)
for i, p in enumerate(points):
    x, y = p.x * f.width, p.y * f.height
    f.no_stroke(); f.fill("red"); f.circle(x, y, 6)
    f.fill("yellow" if i % 2 else "white"); f.text(NAMES[i], x + 6, y - 4)
f.save(out)
