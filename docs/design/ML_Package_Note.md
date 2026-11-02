# The models package: `funground-ml` on the desktop (S-232, D-124, D-125)

**Status:** built on 2 November 2026 for the desktop and for Play; the contract rows ML1 to ML4 are drafts.

## Problem

D-125 decided what a learner writes: `ml.pose(cam)` and `ml.hand(cam)` give named points. This note records how the desktop
half is built and how Play's half (the same files in `onnxruntime-web`) matches it, so that a later change knows what must
stay true.

## Layout

```
ml/                          its own distribution, funground-ml 0.1.0.dev0 (LGPL-2.1-only)
  pyproject.toml             funground, onnxruntime>=1.31,<2, numpy>=2,<3, pillow>=11,<13
  funground_ml/
    __init__.py              pose(), hand(): the only public names, with their docstrings
    _tasks.py                from a source to a Body or a Hand: the desktop path, and the host path (Play)
    _source.py               what a source is, and the answer kept for each source and frame
    _glue.py                 numpy and Pillow: cut, detect, landmarks, tracker (no onnxruntime)
    _results.py              Body, Hand, the point names, the mirrored swap
    _models.py               the table of four files: Hub address (pinned commit), size, SHA-256, licence
    _fetch.py                the download and the kept copy
    _runtime.py              the only module that imports onnxruntime
  tests/                     unit tests, model tests, the two test photographs (data/SOURCES.md)
funground/ml/__init__.py     the core's stub: imports funground_ml, or one sentence about the separate install
funground/platform/browser_models.py   HostModels: the bridge to a page that runs the models (Play)
```

The core never imports onnxruntime (`tests/test_boundaries.py` lists it as a backend with no allowed module in the core;
`ml/tests/test_unit.py` checks that only `funground_ml/_runtime.py` imports it). The stub raises
`ImportError("The models library is a separate install: run `python -m pip install funground-ml`")` from `None`, and only when
`funground_ml` itself is missing: a missing module inside the package is not hidden. `funground.ml` is in the root
`pyproject.toml`'s package list, and `ml` is not in `_PUBLIC_NAMES`, so the naming trap does not apply.

## The models

Four ONNX files, the OpenCV Zoo's conversions of MediaPipe's models (Apache-2.0), taken from the `opencv` organisation on the
Hugging Face Hub at the commit named in `_models.py`, never `main`. They are byte for byte the files the S-231 spike measured.

| File | Task | Bytes |
|---|---|---|
| `person_detection_mediapipe_2023mar.onnx` | pose detector | 11,990,159 |
| `pose_estimation_mediapipe_2023mar.onnx` | 33 body points | 5,557,238 |
| `palm_detection_mediapipe_2023feb.onnx` | palm detector | 3,905,734 |
| `handpose_estimation_mediapipe_2023feb.onnx` | 21 hand points | 4,099,621 |

## The download and the copy

`_fetch.ensure(task, base_dir, who)` runs before the first inference of a task. It looks in `models/` beside the sketch file (found
by the core's own `_sketch_folder()`, called from the public function, as the sound library does; the current folder when there
is no sketch file). `FUNGROUND_ML_MODELS` names another folder, for tests and CI. A file that is there, has the right size and
the right SHA-256 is used (the checksum is read once for each file in a process). Anything else is downloaded:

- one `urllib.request` call, with funground's own User-Agent, not the Hub's library and not `requests`;
- written to `<name>.part`, then renamed once its size and SHA-256 match; on a mismatch the temporary file is deleted and
  a `ValueError` says the file is not the expected one; a download longer than the table says is stopped at once;
- one line is printed first: `Downloading the pose model, 18 MB, once. After that funground uses the copy in models/.`;
- no connection or a site error is a `ConnectionError` in one sentence ("Run the sketch once while online; ...").

Unit tests put a fake opener in `_fetch._open` and use small fake files; no unit test uses the network.

## Telemetry

`_runtime._onnxruntime()` sets `os.environ["ORT_DISABLE_TELEMETRY"] = "1"` (an assignment, so a learner's `0` is not kept) and
only then imports `onnxruntime`. The import happens on the first call, not when the package is imported. A test in a fresh
interpreter spies on the import and checks the variable's value at that moment. The session cache is one
`InferenceSession` for each model file, on the CPU provider.

## Mirroring

For a camera with `_mirror` set (`cam.start(mirror=True)`, the default), `Body.from_points` swaps every `left_` and `right_` name. The model
decides sides from where a limb is in the picture: a person facing a normal camera has their left side on the picture's
right. A mirrored picture shows the learner as in a mirror, so their own left wrist is on the picture's left, and the model
calls it `right_wrist`. The learner's own left wrist is the model's `right_wrist`, and the same for each pair. Points keep the
positions they have in the picture. A `Picture` is never swapped, and a hand has no side in this story.

## One answer for each frame, and the box that is reused

`_source.answer()` keeps the last result for each source and task, keyed on the Picture and its version. The camera's picture is
the same Picture object for every frame (the camera writes into it and the version changes: `Picture._write_pixels`), so
the object's identity alone would give a stale answer for ever; identity and version together say "the same frame" (I4). The
cache holds the Picture only through a weak reference. "Nobody" is kept as well. The picture's pixels come from
`Picture._snapshot()`, which also draws anything the picture has waiting: this is the one private part of the core that the
package uses.

The detector is the slow part. For one source, `_glue.Tracker` reuses the region the detector found while the landmarks found in
it scored at least `REUSE_MIN_SCORE` (0.9), for at most `REUSE_LIMIT` (10) pictures in a row, then the detector looks again.
A reused region that does poorly makes the detector look again in the same call, so a body that moves a long way is found
again at the cost of one slow frame. A new picture size starts again. This is the spike's "box reused" mode: the region is
not moved to follow the body between detections (MediaPipe's own tracking does that; it is a later improvement).

Thresholds: a detector score under 0.5, a pose score under 0.5 or a hand score under 0.8 gives `None`.

Measured on this machine (Windows, 8 threads, onnxruntime 1.31.1, the 640 x 960 hand photograph `standing_woman_640.jpg`, median of 50 calls, each a new frame): pose
34 a second with the detector on every frame and 44 with the box reused; hand 53 and 89.

## Invariants

- Nothing leaves the computer except the model download; the models run on `onnxruntime` on the CPU.
- A model file is never used unless its SHA-256 matches the table.
- Points are `f.Vector`s in the source's pixels as drawn at (0, 0); a picture drawn at a higher density is scaled back to logical pixels.
- The same source in the same frame gives the same object.
- A result with a score under the threshold is `None`, never a Body with a low score.
- `_glue.py` imports no onnxruntime; it takes anything with `run()` and `get_inputs()`.

## Tests

`ml/tests/test_unit.py` needs no model and no network (names, the mirrored swap, repr, the misspelt-name message, the `TypeError`,
the cache key and the weak reference, the box reuse and its bound, the download, the checksum and the offline sentences,
the telemetry switch, the provider boundary, the stub's sentence). `ml/tests/test_models.py` runs the real models on two photographs (`ml/tests/data/SOURCES.md`). The pose tests use
`gandhi_london_rain.jpg` (a 1931 photograph of Mahatma Gandhi walking in the rain, 330 x 454, `PD-UK-unknown` and `PD-1996`): a body is
found, its score is above 0.5, the nose is above the hips, the hips are above the knees and the knees above the ankles, a mirrored
camera swaps the sides, and the second frame does not run the detector. The hand tests use `standing_woman_640.jpg` (a US federal
work): a hand is found with a score of 0.8 or more. Each result agrees within 5 px with the spike's numpy glue
(`spikes/16_models/onnx/ort_glue.py`, imported by path and run on the same picture). An empty picture gives `None`. (Old photographs
are low contrast and the hand model does not find a hand in any Gandhi photograph tried, which is why the hand tests use another picture.) `ml/tests/test_host.py` tests the host path with a fake page and no browser (see "In Play").
The model
files go in `ml/tests/.models/` (ignored by git), downloaded on the first run; a run with no connection skips these tests with a reason.

## In Play (S-232, built 2 November 2026)

The same two tasks, from the same four files, run by `onnxruntime-web` in a worker of their own. The sketch is the same file and
has no `async`. How it is wired is in `Web_Runner_Note.md` ("Models"); this section is what the package has to keep true.

- **`host_services.models`.** The web `Session` sets it (a `platform/browser_models.HostModels`); the desktop leaves it `None`. `_tasks.find_body`
  and `find_hand` read it at the call: when it is set they take the host path. The host path imports none of onnxruntime, numpy, Pillow,
  `_runtime`, `_glue` or `_fetch`, and neither does `import funground_ml` (those imports are inside the desktop path, and `_source` makes
  its Tracker and Pillow image on first use). `ml/tests/test_host.py` checks `sys.modules` in a fresh interpreter, so the wheel that Play installs
  needs no numpy and no Pillow.
- **Sending.** The answer is looked up as on the desktop, by source, task, picture and version. When the picture's version is new and no
  picture of this task and source is being worked on, `Frame.rgba()` (the snapshot's pixels as opaque RGBA, in the physical size) goes to
  `HostModels.request`. A picture that comes while another is in flight is dropped, not queued. `key` is `id()` of the camera or picture.
- **Reading.** The result is built from `HostModels.latest(task, key)`: the model's raw points on the pixels it was sent. Python scales them to logical
  pixels from the size the page worked on, and swaps the sides for a mirrored camera (`Body.from_points(..., mirrored)`), exactly as on the desktop. The kept answer is keyed on
  the picture, its version and `HostModels.generation` (the count of results), so a still picture is answered when its result arrives and a result never
  changes an answer inside a frame (the host delivers results between steps).
- **The answer is the newest the browser has.** `None` until the first result arrives, and it can be one frame behind the picture (contract ML3; D-125).
  Nobody found is a result too. A task the page cannot run (no connection for the first download, a file that fails its check) prints one sentence and stays `None` for the run.
- **The page** (`funground-web`, `runner/models-worker.js`, `models-glue.js`): `onnxruntime-web` 1.30.0 from jsDelivr (`ort.wasm.mjs`, wasm only; one thread without cross-origin isolation), the
  model files from the table `runtime/models.json` that `tools/build_runtime.py` writes from `_models.py`, each checked with `crypto.subtle` and kept in Cache Storage.
  `models-glue.js` is the twin of `_glue.py` with the same numbers, and its crop is Pillow's bilinear lookup written out, not the canvas's smoothing.
- **Measured** on this machine (Windows, headless Chrome 156 with a temporary profile, one wasm thread; `funground-web/tools/test_models.py`), the same sketch on both platforms on the two test photographs:
  the largest difference from the desktop's points is 0.03 px for the body (33 points, mean 0.01 px) and 0.41 px for the hand (21 points, mean 0.20 px), against the 5 px bound
  (S-231's canvas crop gave 4.65 px and 2.17 px). Speed with a new picture sent every frame, the box reused as above: between 5.2 and 8.5 pose answers a second and between 6.7 and 9.2 hand answers a second in two runs (the machine is noisy), with the sketch drawing at the same time.
  The first answer waits for the library (3 MB) and the models (18 MB or 8 MB) to download once; after that they come from the browser's cache.

## What is left

- Tracking from the last frame's points (not the box of the last detection) if the speed needs it; WebGPU and threads in Play (S-231: about twice as fast for pose, if the page can be cross-origin isolated).
- A gallery example, a guide section and the Quick Reference rows; `tools/make_api_reference.py` does not yet read the library's docstrings.
- CI on Linux and macOS for `ml/`, and the check of `ORT_DISABLE_TELEMETRY` when the pinned `onnxruntime` changes.
