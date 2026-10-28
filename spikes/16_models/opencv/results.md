# S-231 step 3: OpenCV `cv2.dnn` + OpenCV Zoo on the desktop (measured)

28 Oct 2026. Windows 11, same slow machine (8 threads). Python 3.14.7, throwaway venvs in the scratchpad (never funground's).
OpenCV Zoo checked out at commit 48b10fa (main, 28 Oct 2026), `.onnx` files pulled with git LFS. Frames: the same sample pictures
as steps 1 and 2 (pose.jpg for pose and segmentation, thumb_up.jpg for the hand, portrait.jpg for the face), `cv2.imread` then
resized to 640 x 480, the same picture fed 100 times, CPU, one task per process, one run per cell.
Numbers: `results.json`. Scripts: `measure.py` (run it with `-I`), `netwatch.ps1` (polls TCP), `scan_urls.py`.
`onnxruntime` was not needed (the Zoo wrappers call `cv2.dnn` directly) and was not installed.

## Install (Python 3.14: works, both OpenCV 4.14 and 5.0)

| Package | Version | Download | On disk |
|---|---|---|---|
| opencv-python | 5.0.0.93 (abi3 wheel) | 44.0 MB | `cv2` 113 MB |
| opencv-python | 4.14.0.94 (abi3 wheel) | not logged | `cv2` 111 MB |
| numpy (+ numpy.libs) | 2.5.4 | 12.7 MB | 34 + 21 MB |

Whole venv: 182 MB (5.0) and 180 MB (4.14), of which pip is 13 MB. Nothing else is pulled in: 2 packages (MediaPipe: 20
packages, 358 MB). `opencv-python-headless` would be a little smaller (research.md: 43.8 MB wheel); not measured. Models on
disk: 12.0 MB person detector, 5.6 MB pose, 3.9 MB palm, 4.1 MB hand, 0.23 MB YuNet, 6.2 MB PP-HumanSeg (about 32 MB; the
MediaPipe `.task` files are 5.8 + 7.8 + 3.8 + 0.25 MB). int8 variants exist (`_int8bq`); not measured.

## Speed, against MediaPipe Tasks on the desktop (step 2)

Zoo pipelines have no tracking: the "every frame" rows run the detector on every frame. "Landmark model only" runs the detector
once and reuses its box for the 100 timed frames: the cost of a tracked frame, comparable to MediaPipe VIDEO mode on a still
picture. Both are given. OpenCV 4.14 runs every task; 5.0 is in the last column.

| Task | Found | MediaPipe median / p90 ms (results/s) | cv2.dnn 4.14 median / p90 ms (results/s) | cv2.dnn 5.0 median / p90 ms (results/s) |
|---|---|---|---|---|
| Pose, detector + landmarks every frame | 33 + 6 helper points, z, 3D world points, mask | 12.9 / 15.8 (74.1), lite | 104.4 / 118.1 (10.3) | does not run (below); 97.7 / 115.2 (10.4) with a fix |
| Pose, landmark model only (box reused) | same | same row | 44.8 / 54.8 (21.3) | does not run |
| Hand, palm detector + landmarks every frame | 21 (+ 21 world points, handedness) | 10.3 / 16.0 (84.6) | 74.9 / 90.9 (13.0) | 34.2 / 43.2 (28.2) |
| Hand, landmark model only | 21 | same row | 25.3 / 28.3 (39.4) | 17.9 / 22.2 (53.8) |
| Face points (YuNet 2023mar) | box + 5 points (eyes, nose, mouth corners) | 11.2 / 13.4 (87.7), 478 points | 41.3 / 73.0 (20.6) | 21.3 / 23.7 (46.6) |
| Face points (YuNet 2026may) | same | same | 38.1 / 53.8 (23.5) | 21.4 / 24.2 (46.9) |
| Person segmentation (PP-HumanSeg, 192 x 192 in) | mask 480 x 640 (class 0/1) | selfie segmenter 6.3 / 7.0 (156.0) | 29.2 / 33.2 (33.5) | 25.6 / 33.5 (36.3) |

- First result (model load + first frame, library already imported): 0.03 to 0.18 s for every task (pose 0.16 s).
- Points: the pose has MediaPipe's 33 points in the same order (plus 6 auxiliary ones: 39 rows of x, y, z, visibility,
  presence). The Zoo does not ship names; the BlazePose list (nose, eyes, ... ankles, foot index) is ours to supply. The hand
  has 21 points like MediaPipe. Face: the Zoo has **no landmark mesh**. YuNet gives a box and 5 points, not 478, and there are
  no blendshapes.
- Pose is 3.5 times (tracked) to 8 times (detector each frame) slower than MediaPipe here. Still 10 to 21 per second on this
  slow CPU.
- **OpenCV 5.0.0 breaks the Zoo person detector**: `getUnconnectedOutLayersNames()` returns the two tensors in the other
  order, so `mp_persondet._postprocess` fails with `ValueError: operands could not be broadcast together with shapes
  (2254,0) (2,)`. Palm, hand, YuNet and PP-HumanSeg run on 5.0. A wrapper that re-orders the outputs by last dimension made
  pose run on 5.0 (97.7 ms; ad hoc script, not kept). OpenCV 5.0 also prints `Targets are not supported by the new graph
  engine for now` for every net, and the Zoo README says `yunet_2023mar` has a fixed input shape that 5.x does not accept for
  other sizes (`2026may` is the 5.x file). Pinning `opencv-python<5` avoids all of it, but 4.x is the older line.
- 5.0 was faster than 4.14 on hand and face; the machine is noisy (YuNet 4.14 p90 73 ms against median 41 ms), so differences
  under about 25 percent are not meaningful.
- Same-picture caveat as before: one clear subject, best case. Segmentation found 17 370 (5.0) and 22 206 (4.14) person pixels
  on pose.jpg: the two builds do not agree exactly; I did not look at the masks. BGR/RGB handling is inside the Zoo wrappers.

## Telemetry: nothing found in this route

1. **Polling** (`netwatch.ps1`): `Get-NetTCPConnection -OwningProcess <pid>` repeatedly (7 to 27 polls per run, each call is
   slow) for every task and both builds, models already on disk: **0 TCP connections**. Runs are only 2 to 6 s long, so this is
   weak evidence alone; the cmdlet does not show UDP (DNS). Python's audit hook saw 0 `socket.*` events (it cannot see native code).
2. **Package grep** (`scan_urls.py`, 40 files in `cv2/`): 69 distinct URLs, all in comments and docs (Wikipedia, arXiv, onnx.ai,
   netron.app, tensorflow.org, licence texts, XML names inside ffmpeg). The only `googleapis` is `type.googleapis.com/`, the
   protobuf `Any` type-URL prefix (the TF/ONNX importer). No `clearcut`, `telemetry`, `analytics`, `sentry` or `usage_log`.
   `cv2.pyd` has no WinHTTP, WinInet, libcurl, WSAStartup or getaddrinfo reference.
3. `opencv_videoio_ffmpeg500_64.dll` does import sockets (WS2_32, `getaddrinfo`): it is what `cv2.VideoCapture("rtsp://...")`
   uses for network streams, and only runs if code opens such a URL. A local camera does not.
4. The six Zoo wrappers import only `numpy` and `cv2` and take file paths; `cv2.dnn.readNet` takes a path, not a URL. Model
   downloads are a separate step (git LFS or a file fetch by us), not something the library does.

Not done: a packet capture and a DNS-cache check. I cannot rule out something I did not look for.

## Licences

Zoo repository: Apache-2.0 (root `LICENSE`). The wrapper code used (`mp_pose.py`, `mp_persondet.py`, `mp_palmdet.py`,
`mp_handpose.py`, `yunet.py`, `pphumanseg.py`) is under its folder's `LICENSE`, as below. I imported it unmodified from the
checkout in the scratchpad; none is copied into this repository. funground would write its own glue.

| Model (Zoo folder) | Weights licence | Source |
|---|---|---|
| `person_detection_mediapipe` (12.0 MB) | Apache-2.0; origin MediaPipe's BlazePose detector, converted via PINTO0309 `tflite2tensorflow` | `models/person_detection_mediapipe/README.md`, `LICENSE` |
| `pose_estimation_mediapipe` (5.6 MB) | Apache-2.0; converted from MediaPipe's pose landmark TFLite | `models/pose_estimation_mediapipe/README.md`, `LICENSE` |
| `palm_detection_mediapipe` (3.9 MB) | Apache-2.0; converted from MediaPipe TFLite | `models/palm_detection_mediapipe/README.md`, `LICENSE` |
| `handpose_estimation_mediapipe` (4.1 MB) | Apache-2.0; converted from MediaPipe TFLite | `models/handpose_estimation_mediapipe/README.md`, `LICENSE` |
| `face_detection_yunet` (0.23 MB) | MIT (Shiqi Yu, 2020); source libfacedetection.train | `models/face_detection_yunet/README.md`, `LICENSE` |
| `human_segmentation_pphumanseg` (6.2 MB) | Apache-2.0 (PaddlePaddle Authors); ported from PaddleHub | `models/human_segmentation_pphumanseg/README.md`, `LICENSE` |

Caveat: these are the Zoo's own statements for the converted files. I did not read the original MediaPipe model cards for
the person, palm and hand models (step 1 left the hand card "unverified"), so that the Apache folder licence covers the
upstream weights rests on the Zoo's word. OpenCV itself is Apache-2.0; the wheel carries `LICENSE-3RD-PARTY.txt` and an FFmpeg
(LGPL) DLL.

## Glue code (detector, crop, landmark model, back to image coordinates)

Lines of code without blanks and comments in the Zoo wrappers. Each detector also carries a 2000-line SSD anchor table
(`_load_anchors`, a literal numpy array); it could be generated, but the Zoo does not.

| Pipeline | Detector wrapper | Landmark wrapper | Driver | Total (without the anchor table) |
|---|---|---|---|---|
| Pose | `mp_persondet.py` 76 | `mp_pose.py` 129 | 3 | about 210 (plus about 2250 anchor lines) |
| Hand | `mp_palmdet.py` 73 | `mp_handpose.py` 154 | 4 | about 230 (plus about 2010 anchor lines) |
| Face (YuNet) | `cv2.FaceDetectorYN` | `yunet.py` 41 | 1 | about 40 |
| Segmentation | none | `pphumanseg.py` 43 | 1 | about 45 |

What the pose and hand glue does: letterbox the frame to 224 or 256 px; decode anchors and run non-maximum suppression;
compute a rotated, enlarged region of interest from 2 keypoints; warp the crop upright; run the landmark net; undo the warp,
the padding and the scale for every point; sigmoid the scores; paste the mask back. Driver: `for p in detector.infer(img):
pose.infer(img, p)`. funground would have to own or vendor this (and keep it working across OpenCV 4 and 5), against
MediaPipe where one `landmarker.detect(image)` call does it. Point names, the skeleton and the camera's BGRA to BGR
conversion would also be ours.
