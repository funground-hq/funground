# S-231 step 2: MediaPipe Tasks for Python on the desktop (measured)

28 Oct 2026. Windows 11, same slow machine as the web run. Python 3.14.7, `mediapipe` 1.2.0 in a throwaway venv.
Same model files (float16 / float32 `latest` from storage.googleapis.com/mediapipe-models) and same sample images as the web
run, resized to 640 x 480. VIDEO mode, CPU delegate, 100 frames of the same picture with rising timestamps, one task per
process, one run per cell. Numbers: `results.json`. Scripts: `measure.py`, `telemetry_probe.py`, `pose_sketch.py`.
The object detector was not asked for and was not measured.

## Install (Python 3.14: works)

`pip install mediapipe` installs and imports on 3.14.7 (`py3-none-win_amd64` wheel, 24.5 MB; import takes 1.5 s warm, about
9 s the first time). `site-packages` is 358 MB on disk (399 MB after also installing funground and its dependencies into the scratch venv).

| Package | Version | On disk | Download |
|---|---|---|---|
| mediapipe | 1.2.0 | 69 MB (`libmediapipe.dll` alone 66.7 MB) | 24.5 MB wheel |
| opencv-contrib-python (cv2) | 5.0.0.93 | 139 MB | 53.8 MB |
| numpy (+ numpy.libs) | 2.5.4 | 34 + 21 MB | n/a |
| matplotlib | 3.11.2 | 33 MB | n/a |
| fonttools | 4.68.0 | 19 MB | n/a |
| pillow | 13.0.0 | 17 MB | 7.3 MB |
| others (absl-py, flatbuffers, sounddevice, certifi, cffi, pycparser, contourpy, cycler, kiwisolver, packaging, pyparsing, python-dateutil, six, tzdata) | | a few MB each | |

pip itself is 13 MB of the total. Pulled in: 20 packages. `matplotlib`, `sounddevice` and a 139 MB OpenCV are pulled in
although none is used by a Tasks pose or hand call.

## Speed, desktop against web (CPU, VIDEO mode, 640 x 480, 100 frames)

Web numbers are from `../web/results.md`, main page, CPU. First result: desktop = model creation to the first result,
the library already imported (web = from loading the library, including the wasm download, so not like for like).

| Task | Desktop median ms | p90 ms | Results/s | First result | Found | Web median ms | Web results/s |
|---|---|---|---|---|---|---|---|
| Pose lite | 12.9 | 15.8 | 74.1 | 0.77 s (cold file cache) | 33 | 91.8 | 10.8 |
| Pose full | 18.0 | 25.1 | 52.9 | 0.20 s | 33 | 128.1 | 7.9 |
| Hand | 10.3 | 16.0 | 84.6 | 0.20 s | 21 | 58.9 | 16.1 |
| Face | 11.2 | 13.4 | 87.7 | 0.07 s | 478 | 46.6 | 21.3 |
| Selfie segmenter | 6.3 | 7.0 | 156.0 | 0.05 s | mask 307200 px | 20.6 | 39.8 |
| Image classifier (EfficientNet-Lite0) | 13.8 | 16.2 | 70.0 | 0.07 s | "sandbar" 0.17 | 72.2 | 13.3 |

The desktop is 4 to 7 times faster than the web CPU build here. Same point counts and same top label as the web run.
Caveat: the same still picture is fed 100 times, so pose, hand and face are tracking, not detecting, after frame 1
(same as the web run). A real camera costs more when the detector has to re-run.

## The camera route: pygame Surface to `mp.Image`

`pygame.image.tobytes(surface, "RGB")`, then `np.frombuffer(...).reshape(480, 640, 3)`, then
`mp.Image(image_format=ImageFormat.SRGB, data=arr)`. Median 2.4 ms, p90 4.4 ms per 640 x 480 frame (500 frames). That is
about a fifth of a pose lite call (12.9 ms). Not tried: `surfarray.pixels3d` (no copy, but transposed, so it needs a copy anyway).
funground's camera frame is BGRA bytes inside a Picture (`camera_input.py:325`); a Picture-based path would also need a
colour-order change, which is not measured here. numpy comes with mediapipe (it is a dependency).

## Telemetry: yes, Tasks logs to Google, and I found no switch

Evidence, in order of strength:

1. `mediapipe/tasks/c/libmediapipe.dll` (the native library every Python Task calls) contains the strings
   `https://play.googleapis.com/log`, `third_party/mediapipe/tasks/cc/core/logging/google_internal/clearcut_logging_client.cc`,
   `wireless/android/play/playlog/cplusplus/portable_clearcut_uploader.cc` and `mediapipe_log_extension.proto`: a Google
   "Clearcut" usage logger (file offset 52176584; there is no source file, so no line number inside the DLL).
2. The Python side hands the logger what it needs, on every task creation: `mediapipe/tasks/python/core/base_options.py`
   lines 90-107 (`BaseOptions.to_ctypes`) set `host_environment = HOST_ENVIRONMENT_PYTHON`, `host_system` (Windows, Linux or Mac),
   `host_version` (the Python version, e.g. 3.14.7), `ca_bundle_path = certifi.where()` (a CA bundle is needed only to make
   HTTPS calls) and `app_id`/`app_version = None`. The struct is declared in `core/base_options_c.py:25-48`, and
   `decision/decision_maker.py:192-196` has a comment saying these fields are "used for usage logging". `certifi` is a
   dependency of mediapipe 1.2.0 for this reason.
3. Observed: I flushed the Windows DNS cache, then (a) `import mediapipe` alone left it with no Google names; (b) creating
   and closing one task (selfie segmenter, model from a local file) made `play.googleapis.com` appear in the DNS cache
   (16 entries, v4 and v6). Another run with the pose task gave the same. Caveat: other programs (Chrome was open on the
   machine) share that cache; the repeat on demand and the import-only control point to mediapipe. I did not capture the
   TCP connection itself: `netstat` polled every 0.15 s for 28 s showed none, so what is sent, and when, is not observed.
4. No off switch found. In the Python package there is no `os.environ` or `getenv` use in `tasks/python`, and no option in
   `BaseOptions` (its fields are `model_asset_path`, `model_asset_buffer`, `delegate`). Scanning the DLL for names like
   `MEDIAPIPE_*`, `*_OPT_OUT`, `DISABLE_*` found none that relate to logging (only `DISABLE_SENTENCEPIECE_TOKENIZER` and
   `OPENCV_CPU_DISABLE`). I cannot rule out a switch compiled into the DLL under a name I did not search for.
5. The web build did not do this: every request in the web run was to jsdelivr, storage.googleapis.com or localhost.

For a library for children, treat the Python package as sending usage data to play.googleapis.com until the maintainer or
Google confirms otherwise. Options for the main session: block `play.googleapis.com` (hosts file, firewall) which is not
a library fix; ask upstream; or choose the OpenCV Zoo / ONNX route for the desktop (no Google logger).

## The pose sketch

`pose_sketch.py` (25 lines) runs PoseLandmarker lite on a still picture, draws the 33 points and their names with funground
and saves `pose_sketch.png` headless (not committed: its background is MediaPipe's sample photo). It works. Names overlap where points cluster (face, hands, feet); a real version would
choose which to label. funground was installed editable into the scratch venv (`pip install -e C:\Projects\playground`).
Run it: `<venv>\Scripts\python.exe -I pose_sketch.py MODEL.task IMAGE.jpg OUT.png`.
The sample picture is not committed; the PNG contains it as a background, so check its licence (MediaPipe sample asset)
before committing the PNG.
