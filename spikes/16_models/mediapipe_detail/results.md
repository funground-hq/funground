# S-231: MediaPipe telemetry and unbundling (measured 28 Oct 2026)

Windows 11, Python 3.14.7, `mediapipe` 1.2.0 (PyPI `py3-none-win_amd64`, 24.5 MB). Throwaway venv `mpvenv2` in the scratchpad.
Scripts are in this folder: `proxy.py`, `tcp_watch.py` (+ `tcp_watch_selftest.py`), `telemetry_run.py`, `exit_probe.py`,
`dll_strings.py`, `dll_proto_fields.py`, `tasks_check.py`, `stubs_check.py`, `nostubs.py`, `imp.py`.
Claims marked (unverified) have no direct evidence.

## a. Can we stop MediaPipe sending data, cleanly?

Short answer: **no clean switch exists, and Google has said it will not add one.** The clean routes are to build from source,
to block the host outside the library, or to avoid this library on the desktop.

### 1. Upstream source and Google's statement

- The open-source tree has **no** Google logger. `mediapipe/tasks/cc/core/logging/factory/logging_factory.cc:24-27`
  (`CreateTasksLogger`) returns `TasksDummyLogger::Create()`, and `tasks_dummy_logger.h` "drops all events". The logger interface
  is `logging/tasks_logger.h:30-80` (`LoggingOptions`: task name, running mode, host environment/system/version, app id/version,
  CA bundle path; events: session start, clone, invocation report, session end, init error).
  Wiring: `tasks/cc/core/task_runner.cc:102-113` builds the logger from the base options and calls it at lines 237, 281, 336, 357;
  `tasks/cc/core/BUILD:24-27` defines the swappable `tasks_logging_factory` target.
  Source: https://github.com/google-ai-edge/mediapipe (master, read with `gh api` / raw.githubusercontent.com).
- The published binary is **not** built from that tree. Strings in `libmediapipe.dll` (`dll_strings.py`): the build path
  `google3/.../odml.mediapipe_tasks_release_branch/...`, and
  `third_party/mediapipe/tasks/cc/core/logging/google_internal/clearcut_factory/logging_factory.cc` at offset 49905584. Google's
  internal build swaps in a Clearcut factory. So it is **compiled in only for Google's prebuilt wheels**, not for a source build.
- The Python side passes the fields: `tasks/python/core/base_options.py:90-107` (`to_ctypes`), struct in `base_options_c.py`.
  `tasks/c/BUILD` (target `mediapipe_source`, near line 158) builds `libmediapipe` from source, and has a `prebuilts/` glob
  (`mediapipe_windows`/`mediapipe_linux`) that picks a prebuilt library when one is present.
- No build flag, option field or environment variable: no `getenv` in `tasks/python`; `BaseOptions` has three fields; the DLL
  has no logging-related env names (I cannot rule out one I did not search for).
- **Google's answer, in writing:**
  - Issue #6291 "Mediapipe now includes undocumented telemetry" (closed): https://github.com/google-ai-edge/mediapipe/issues/6291.
    6 Jul 2026, schmidt-sebastian: "we will be rolling out telemetry for all of our platforms ... We are not adding an official
    API to disable this data collection ... You can build the SDK from source, which will not include telemetry, or you can block
    access to the host. We will not and will never send any input data to our servers." A fix for the error-log noise was promised.
    The reporter found 0.10.21 had no such connections and 0.10.35 did.
  - Issue #6306 (web): https://github.com/google-ai-edge/mediapipe/issues/6306. 10 Jun 2026: the web SDK "does not include
    telemetry" yet, it is planned, "no opt-out", "block outgoing requests". (Our web run on 1.2.0 saw none: `../web/results.md`.)
  - Privacy notice: https://developers.google.com/edge/mediapipe/solutions/tasks : "MediaPipe Tasks APIs send metrics about the
    performance and utilization of the APIs in your app to Google"; input data not sent; the developer is "responsible for
    obtaining informed consent from your app users". No opt-out described.

### 2. What is sent, and when (measured)

- **What (from the protobuf schema embedded in the DLL, `dll_proto_fields.py` bytes 66301000-66310000):** `SystemInfo`
  {platform, app_id, app_version, mediapipe_version, host_version, host_environment}; `SolutionEvent` {solution_name such as
  TASKS_POSELANDMARKER, event (start / invocations / end / error), session_start {mode, graph_name, init_latency_ms},
  invocation_report {mode, average and peak pipeline latency, elapsed time, dropped, counts per input type CPU/GPU},
  session_end, error_code}. No image or landmark fields. In practice: which task, how long it ran, frame counts, latency,
  Python and OS version, plus the learner's IP address (inherent in any HTTPS request).
- **When (`telemetry_run.py` with `tcp_watch.py`, own-process TCP table polled every 2 ms):** no connection at import, at create,
  during 100 frames, or during 90 s idle. **One TCP connection to a Google IPv6 address (2001:4860:...:443) starts about 0.1-0.2 s
  after `task.close()`** (4 runs, same result). Dropping the last reference (`del` + `gc.collect()`) also triggers it
  (`exit_probe.py del`). No connection when the task is left open and idle (8 s windows). Interpreter exit without close: none
  seen, but my watch window ended before native teardown, so that is inconclusive. Reading: the logger batches start +
  invocation report + end and uploads at session end.
- I saw only `SYN_SENT`: the connection is short-lived, so TLS and the body are **not observed**, nor whether Google answered.
  Reverse DNS did not resolve; the earlier `play.googleapis.com` finding rests on the DLL string and one DNS-cache observation
  (the DNS cache stayed empty in my runs, so the library probably resolves names itself; unverified). 2001:4860::/32 is
  Google's range (general knowledge, not checked in a registry here).
- **Environment proxy variables are ignored.** With `HTTPS_PROXY`/`HTTP_PROXY`/`ALL_PROXY` pointing at `proxy.py` (a CONNECT proxy
  that logs host names only), the proxy log stayed empty while the process still connected straight to Google. So a proxy cannot
  observe or block it; a firewall or hosts entry would (needs admin; not tried).
- `tcp_watch.py` had an IPv6 offset bug that I fixed during the work; `tcp_watch_selftest.py` now sees a real connection.
  Runs before the fix saw nothing for that reason, and are not used here.

### 3. Does a supported setting turn it off? No.

`telemetry_run.py --variant` patches `BaseOptions.to_ctypes` (a **hack, for measuring only**): `nocerts` (ca_bundle_path None),
`unknownhost` (host environment/system 0, version None), `all` (both). **All three still open the connection at close** and the
task works. So blank fields or no CA bundle do not stop the attempt (whether the upload then succeeds without a CA bundle is not
observed). Leaving the task unclosed postponed it in short tests, but that is an accident of object lifetime, not a setting, and
leaks the task. None of this is documented behaviour; relying on it would be relying on an accident.

### 4. Build from source without logging: feasible, high effort

Bazel build of `//mediapipe/tasks/c:libmediapipe` (`mediapipe_source`), which uses the dummy logger by construction.
A community member built manylinux wheels this way for 3.12 and adapted them to 3.14 (issue #6319, comments by marcreichman-pfi and
HarishPermal; `build_manylinux_wheel.sh` in the repo root). We would carry Windows, macOS and Linux wheels per release (Bazel,
MSVC, Xcode, a slow machine, CI minutes) and follow every upstream release. Estimate: days for a first Linux wheel, weeks to
carry three systems (unverified; no build tried). It is a fork to maintain.

### 5. Older `mediapipe.solutions` API

1.2.0 ships **no** `solutions` package (`find mediapipe -iname "*solution*"` is empty). Wheels that have it (0.10.21 and earlier,
cp39-cp312 only, 51 MB) did not connect according to the reporter of #6291 (not tested by me). No Python 3.13+ wheel, and the
line is unmaintained: a dead end for 3.14.

### Best clean route (for the maintainer to decide)

1. Do not make Google's prebuilt library the default for children. Prefer the OpenCV Zoo / ONNX route (D-124): no Google logger.
2. If MediaPipe is wanted on the desktop: make `funground-ml` opt-in, disclose it (Google's terms put informed consent on the
   developer), and say how to block it (firewall or hosts; the proxy variable does not work).
3. A self-built wheel is the only way to a library without the logger; costly.
Not recommended: the `to_ctypes` patch (does not stop it) or skipping `close()` (hack, leaks).

## b. Unbundling

### 1. Minimal set (throwaway venv, one package at a time; MB of Lib\site-packages, pip's own 13 MB included)

| Step | Total | `import mediapipe; from mediapipe.tasks.python import vision, audio` |
|---|---|---|
| `pip install mediapipe --no-deps` | 84 | fails: no numpy |
| + numpy | 139 | fails: no certifi (imported at top of `base_options.py`) |
| + certifi | 139 | fails: no cv2 |
| + absl-py, flatbuffers | 140 | fails: no cv2 |
| + opencv-python-headless (113 MB; not the 139 MB contrib) | 253 | fails: no matplotlib |
| + matplotlib (+10 dependencies) | 328 | **OK**; all 6 tasks work (`tasks_check.py`: pose 33, hand 21, face 478, selfie mask, image classifier, audio classifier) |
| remove cv2, matplotlib and its 10 dependencies, run with empty stand-in modules (`stubs_check.py`) | 140 | all 6 tasks work |
| also remove absl-py and flatbuffers | about 138 | still works (they serve the metadata writers only) |

- cv2 and matplotlib are needed only because `mediapipe/tasks/python/vision/__init__.py:19` imports `drawing_utils.py:20-21`
  (`import cv2`, `import matplotlib.pyplot`), which draws landmarks. No Task calls them. `sounddevice` is optional
  (`audio/core/audio_record.py:18-25` catches ImportError): only live microphone capture needs it; audio from arrays works without.
- **Minimal on disk: mediapipe 69 MB + numpy 55 MB (34 + 21 libs) + certifi 0.3 MB = about 124 MB (125.5 MB with absl and
  flatbuffers), plus pip.** Against 358 MB for `pip install mediapipe`: about 230 MB less. The stand-in modules are a **hack**
  (nothing in MediaPipe supports it; `vision.drawing_utils` becomes unusable). With real packages the floor is 253 MB (headless
  cv2) or 328 MB (with matplotlib): no real saving.
- Of note: certifi is imported unconditionally but is used only for the telemetry CA bundle.

### 2. What is large in the wheel, and how to depend on the minimal set

Biggest files: `tasks/c/libmediapipe.dll` 66.7 MB (the whole native Tasks runtime, the only thing the Tasks need),
`tasks/metadata/schema_py_generated.py` 0.68 MB, `metadata_schema_py_generated.py` 0.12 MB, `vision/face_landmarker.py` 0.10 MB.
The rest is small Python (3 MB in `tasks/python`). One DLL serves all tasks. No models in the wheel.

pip always installs declared dependencies unless `--no-deps`. Options:
- **Extras / our own dependency list: does not work.** `mediapipe` declares `opencv-contrib-python`, `matplotlib`,
  `sounddevice` as hard requirements (METADATA); `funground-ml` cannot remove them. Depending on `mediapipe` gives 358 MB.
- **`pip install --no-deps mediapipe numpy certifi`** (a documented command, or a funground-ml helper that runs it): 124 MB. But
  `import mediapipe.tasks.python.vision` then fails on cv2/matplotlib, and importing a submodule directly does not help (the
  package `__init__` runs first). So funground-ml would need a shim that puts empty `cv2`/`matplotlib` modules in `sys.modules`
  before the import: a hack, fragile on every MediaPipe release (checked on 1.2.0 only).
- **A smaller official package: none.** PyPI returns 404 for `mediapipe-tasks`, `mediapipe-tasks-vision`, `mediapipe-lite`,
  `mediapipe-c`; `mediapipe-silicon` exists but is an old third-party Apple-silicon repack. Only Google could split the package
  (a request upstream is possible).
- **Load `libmediapipe.dll` via ctypes** (our own thin wrapper over the C API headers in `mediapipe/tasks/c/`, Apache-2.0, keep the
  NOTICE): drops the cv2/matplotlib problem and certifi; leaves about 67 MB plus numpy. Real work (structs per task, ABI changes
  per release, results parsing) and the DLL **still contains the Clearcut logger**. We would take the DLL from the PyPI wheel.
- **Our own wheel built from source:** see a4.

### 3. Models

Confirmed: the wheel contains no `.task` or `.tflite` files (searched). A task takes `model_asset_path`, so a sketch fetches only
the model it names. Measured sizes: selfie segmenter 0.25 MB, face 3.76, pose lite 5.78, hand 7.82, pose full 9.40,
EfficientNet-Lite0 18.6, YAMNet (audio) 4.13 MB, from storage.googleapis.com/mediapipe-models/... The audio classifier ran with
`yamnet.tflite`.

### 4. Web, for comparison

From `../web/results.md`: `@mediapipe/tasks-vision` 1.2.0 wasm on the wire 3.25 MB (main build, `vision_wasm_internal.wasm` plus
loader, brotli) and 3.7 MB (module build for workers); 14.5 MB unpacked. One `FilesetResolver.forVisionTasks()` fileset served all
7 vision tasks measured there, so the wasm is shared (that is how the API is built; audio tasks are another package, not
measured). Web: about 3.3-3.7 MB runtime once plus 0.25-9.4 MB per model, against 124-358 MB on the desktop.

## Summary

- a: no supported off switch (Google: "not adding an official API", block the host or build from source). The prebuilt library
  uploads one batch (task name, run time, counts, latency, OS and Python version) when a task is closed, straight to Google
  (proxy variables ignored). Best clean route: do not make the prebuilt library the default for children; use the OpenCV Zoo
  route, or build from source if MediaPipe is required.
- b: minimal install is 124 MB (mediapipe + numpy + certifi) against 358 MB, through `pip install --no-deps` plus an import shim;
  there is no official smaller package and no extras route.
