# The models package: `funground-ml` on the desktop (S-232, D-124, D-125)

**Status:** built on 2 November 2026 for the desktop and for Play; the contract rows ML1 to ML5 are drafts. `ml.person` (S-233) was added on 2 November 2026: see "The person's mask". `ml.words` (S-234, row ML6, a draft) was added on 3 November 2026 for the desktop: see "The words". `ml.sound` (S-250, row ML7, a draft) was added on 5 November 2026 for the desktop and for Play: see "The sound names".

## Problem

D-125 decided what a learner writes: `ml.pose(cam)` and `ml.hand(cam)` give named points. This note records how the desktop
half is built and how Play's half (the same files in `onnxruntime-web`) matches it, so that a later change knows what must
stay true.

## Layout

```
ml/                          its own distribution, funground-ml 0.1.0.dev0 (LGPL-2.1-only)
  pyproject.toml             funground, onnxruntime>=1.31,<2, numpy>=2,<3, pillow>=11,<13
  funground_ml/
    __init__.py              pose(), hand(), person(), words(), sound(): the only public names, with their docstrings
    _tasks.py                from a source to a Body, a Hand, a Picture or some Words: the desktop path, and the host path (Play)
    _speech.py               no numpy: the phrase cutter, the byte-level token decoder, the numbers of the speech model
    _listen.py               no numpy: Heard (the answer a frame sees), Worker (the thread), HostSink, Ear (a microphone), Clip (a Sound)
    _sound.py                no numpy: the rules for choosing the names (choose, HIDDEN) and the level rule (is_quiet)
    _sound_names.py          the 521 sound names, generated once from YAMNet's class map (CC BY 4.0 credit in its header)
    _hearing.py              no numpy: Latest (the answer a frame sees), SoundEar (a microphone), SoundClip (a Sound), SoundHostSink
    _yamnet.py               numpy: the sound model (resampling by _whisper.to_model_rate, the mean of the rows)
    _whisper.py              numpy: resampling, log-mel, the greedy decode loop (the only other user of _runtime)
    _source.py               what a source is, and the answer kept for each source and frame
    _glue.py                 numpy and Pillow: cut, detect, landmarks, tracker (no onnxruntime)
    _results.py              Body, Hand, Words, Heard, the point names, the mirrored swap
    _models.py               the table of nine files: Hub address (pinned commit), size, SHA-256, licence
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

## The person's mask (S-233, built 2 November 2026)

`ml.person(source)` (contract ML5) gives a new picture of the source in which everything but the person is see-through.

- **The model.** One file, `mediapipe_selfie_segmentation.onnx` (kept name; `onnx/model.onnx` in the repository
  `onnx-community/mediapipe_selfie_segmentation`, commit `be49485c8e027524be38591817fc5cd31bd9d00e`, 462,352 bytes, Apache-2.0): Google's
  MediaPipe selfie segmentation, the **general** variant (256 x 256 in, 256 x 256 out; the landscape variant reads 144 x 256 and is not
  used). It is the file the S-231 spike measured. `Model.kept_as` names the copy in `models/` when the repository's own name ("model.onnx")
  says too little; `TASKS["person"]` has one name, and `_fetch.ensure` gives its path as `{"model": path}`.
- **In and out.** `_glue.person_mask`: the picture is stretched (not letterboxed) to 256 x 256 with Pillow's bilinear resize, scaled to 0..1 with no
  mean, channels first; the model's 0..1 output becomes bytes (0..255), not thresholded. `models-glue.js` has the twin (`stretchToTensor`,
  `personMask`), with Pillow's resize (a triangle filter that averages when shrinking) written out so the two inputs agree to the grey level.
- **From mask to picture.** Both platforms end in `Picture._masked_copy(mask, width, height)`, a private core helper (no public API) that calls
  `renderers.cairo2d.mask_pixels`: Cairo paints the picture through the mask as an A8 pattern scaled over the picture (bilinear, edge pixels carried on),
  so each premultiplied pixel is multiplied by the mask. It is one paint in C. A plain Python loop for the same work took 204 ms in CPython for 640 x 480
  (more in Pyodide, which has no numpy), against 3.7 ms for the Cairo call in Pyodide, so the mask goes to Python at its own 256 x 256 size and
  there is no full-size alpha plane to send. The desktop uses the same helper, so the last step cannot differ between platforms.
- **Play.** `HostModels` has two result types: `PointsResult` (pose and hand) and `MaskResult` (person); the page calls `push` or `push_mask`
  (`Session.push_models_mask`). `_tasks._from_host` takes a builder that is given the frame and the result, one builder for points and one for the mask.
- **Measured** (Windows, this machine): the same sketch on both platforms on `standing_woman_640.jpg` (640 x 960): the alpha planes differ by 0.08 of 255 on average,
  0.0 percent of the pixels by more than 32, largest difference 37 (the bound, set before measuring: mean 3, at most 1 percent over 32). The desktop gives 85
  pictures a second at 640 x 480 (11.8 ms a call, new frame each time: Pillow image 1.0 ms, resize and model 4.9 ms, cut-out 3.0 ms); Play about 16 answers a second
  with the sketch drawing at about 32 frames a second.
- **Tests.** `ml/tests/test_unit.py` (a stand-in model: size, alpha, soft edge, no threshold, nobody, cache, high density, the download of a one-file task),
  `test_host.py` (the mask result and the page path), `test_models.py` (the photograph: her dress solid, the corners clear, within half a grey level of the spike's own mask),
  `tests/test_pictures.py` (`_masked_copy`), and `funground-web/tools/test_models.py` (Play against the desktop, the mask time, the speed).

## The words (S-234, built 3 November 2026)

`ml.words(source)` (contract ML6) gives the words in a microphone or a Sound. The speech model is Whisper tiny.en, 8-bit, the files the S-231 spike measured
(`onnx-community/whisper-tiny.en` at commit `2575352d61be1bf7225cf8f8b268a4678025fc58`): the encoder, the merged decoder, and `vocab.json`.

- **Why no `tokenizers`.** Decoding needs only number to text. `vocab.json` is a table of byte-level pieces (GPT-2's scheme: each byte is one printable
  character, so a space is U+0120), and `_speech.decode` joins the pieces, maps the characters back to bytes and reads them as UTF-8. That is about 20 lines of ours,
  the same as the web page's. The `tokenizers` library (a compiled package, a new dependency in every install, and nothing on Pyodide) would give the same text.
  The 90 numbers the model must never choose come from `generation_config.json`; they are a constant in `_speech.py`, so that file is not downloaded.
  The download is therefore 41.8 MB (10.1 + 30.7 + 1.0), printed as "42 MB" (contract ML6 said 43 for the 2.4 MB `tokenizer.json`, which is not used).
- **The phrase cutter** (`_speech.PhraseCutter`, pure Python so that Pyodide can run it). It reads the microphone's ring buffer since it last looked, by `mic._total`
  (the position it has reached; `mic._version` says when `start()` cleared the buffer), in 30 ms blocks; a block with an RMS level over 0.02 is speech; a phrase ends after
  0.6 s of quiet, is dropped if it holds under 0.3 s of speech, and is cut at 10 s. Three blocks of quiet before the start are kept so the first sound is not clipped.
  A sketch that looks rarely catches up with up to what the ring holds (10 s); what has gone is skipped and the open phrase ends there. Stopping the microphone ends the open phrase.
  The numbers are named constants at the top of `_speech.py`. The cutter is run by the sketch's thread, inside `ml.words()`: measured at 0.06 ms for the 735 samples of one 60 fps frame at 44.1 kHz, so it needs no thread.
- **The thread** (`_listen.Worker`). One daemon thread for each microphone, started with its first phrase, holding at most one phrase waiting (a newer phrase replaces it, under one
  `threading.Condition`). It loads the two sessions on its first phrase (so `draw()` does not stall; the first answer is about a second later), resamples, and runs the model.
  An exception in it is kept and raised by the sketch's next `ml.words()` call. The download (ML4) happens in the sketch's thread on the first call, as for pose.
  `weakref.finalize` ends the thread when the microphone's memory is dropped. The memory is kept for each microphone in a weak dictionary and does not refer back to it.
- **A Sound** is one phrase: `sound.samples()` (mono) at `sound._sample_rate()`, answered in the sketch's thread, kept for each Sound (`_listen.Clip`).
- **What a frame sees** (`_listen.Heard`). The first call in a frame settles the answer for that frame (the sketch's `frame_count`), so the same object is given for the whole
  frame and `is_new` is True in the frame the answer first shows. A Words given earlier is never changed. An answer under 0.4 or with no text never reaches it.
- **The model.** `_whisper`: resample to 16 kHz by linear interpolation (the formula is in `to_model_rate`'s docstring and in `browser_models.py`; the web page does the same),
  log-mel as Whisper's feature extractor does it, the encoder, then the decoder with its key and value cache, greedy, at most 224 pieces, the score the mean probability of the
  pieces chosen (a softmax over the logits with the banned numbers removed). For `tts.wav` the words are the spike's exactly.
- **In Play.** `HostModels.request_sound("words", key, float32 bytes, rate)` and `push_words(task, key, text, score)` (`Session.push_models_words`); the protocol is in the module
  docstring of `browser_models.py`. `_listen.HostSink` keeps the newest phrase waiting while one is in flight. The page's worker (`models-worker.js`) is a later task:
  it must do the same resampling, log-mel, loop and decoding as `_whisper.py`, and `ml/tests/test_host.py` only checks the Python side with a stand-in page.
- **Tests.** `ml/tests/test_words.py` (the cutter on synthetic sound, the decoder, the resampling against the formula, Heard, the thread with a stand-in model, the errors),
  `test_host.py` (the host path), `test_words_model.py` (the real files on `data/tts.wav`, from a Sound and from a microphone that is fed it).

## The sound names (S-250, built 5 November 2026)

`ml.sound(source)` (contract ML7, D-126, D-129) gives the name of a sound heard by a microphone or in a Sound. The model is Google's YAMNet as ONNX, from the community
repository `funground-hq/yamnet-onnx` at commit `9648eed1cf043f9163842e9cb6d5fd8291d0d1cf` (funground's copy of `audiomagic/yamnet-onnx`, commit `f25b741c2f0bdc6d7e6db24b5fddda23347dbafd`): `yamnet.onnx`, 16,093,355 bytes, SHA-256
`d3835ffbbd4a1bb3e777f0ca217b5007907f5171dd5d17c4236b95b2af8f908e` (the table of `_models.py`, task "sound", one file). It takes the raw waveform (float32, 16 kHz, input `waveform`) and
gives one row of 521 scores for each 0.96 s window. Spike 18 measured its scores against Google's model at 6.7e-5 on 2,000 clips. The community file has no licence on its card; the original is Apache-2.0.
The repository is not the project's, so a mirror in a funground Hugging Face organisation is still open (D-129).

- **The 521 names are in the package** (`_sound_names.py`, generated once, not downloaded): the `display_name` column of `yamnet_class_map.csv` in the same repository and commit (14,096 bytes, SHA-256
  `cdf24d193e196d9e95912a2667051ae203e92a2ba09449218ccb40ef787c6df2`), in the order of the `index` column. The header of the file says this and carries the credit: the sound names come from the AudioSet ontology by
  Google LLC, CC BY 4.0 (also in `ml/README.md` and `THIRD_PARTY_LICENSES.md`). A test checks that there are 521 different names, and that every hidden name is one of them.
- **One function chooses** (`_sound.choose`, pure Python, no numpy): given the 521 scores, `None` when the likeliest name of all is `Silence`; the fifteen umbrella names of D-129 (`_sound.HIDDEN`) are
  left out; `None` when the best name left scores under 0.1; otherwise the best and up to four next, likeliest first (a tie keeps the model's order). The desktop and Play both use it: the page sends only the 521 scores
  and no names. The level rule (`_sound.is_quiet`: the loudest 30 ms block of the 0.96 s, RMS, under 0.02) is applied in Python before a window is sent, on both. It applies to a microphone's windows only; a Sound is
  given to the model whole, and only the two rules about the answer apply to it.
- **The windows** (`_hearing.SoundEar`, no numpy). Like the words' Ear it reads the microphone since it last looked (`mic._since`), but it keeps the newest 0.96 s and cuts a window when 0.96 s has been heard and then
  every 0.48 s of sound (counted in samples at the microphone's rate, so it does not drift with the frame rate; a sketch that looks rarely gets the newest window, not a queue). Nothing is answered for the first 0.96 s.
  A window travels as a `Window(tag, samples)`; a quiet window has `samples=None` and is never sent to the model, but it goes through the sink in its place, so that "nothing to name" arrives in order after the
  answers before it. The tag changes when the microphone stops or starts again, and an answer with an old tag is dropped: a sound that stopped does not come back from a window still being worked on.
  `is_new` is True in the frame each new answer first shows (a whistle that goes on is a new answer every 0.48 s). The names are chosen in the sketch's thread, after the sink.
- **The thread** (`_listen.Worker`, now with a thread name): one daemon thread for each microphone, one window in work, the newest waiting. The model runs in it, never in the sketch's thread; a daemon thread, ended by
  `weakref.finalize` when the microphone's memory goes, so it holds up neither the end of a sketch nor the microphone's own close at the sketch's end (S-251). Verified: the thread is a daemon, and drops with the microphone (`test_hearing.py`).
  An exception in it is raised by a later `ml.sound()` call, once. The download happens in the sketch's thread on the first call: `Downloading the sound model, 16 MB, once.`
- **A Sound** is one window: `sound.samples()` at `sound._sample_rate()`, up to 30 s (a longer one is a `ValueError`), answered at once in the sketch's thread on the desktop and kept for each Sound (`_hearing.SoundClip`); in Play it is sent
  whole and the answer is `None` until it comes. The Sound's rows are averaged (Google's demo does the same). Words and sound keep separate memory for one Sound.
- **The model** (`_yamnet.Yamnet`): `to_model_rate` of `_whisper.py` (linear interpolation, the formula in its docstring and in `browser_models.py`), `session.run`, the mean of the rows in double precision. A window of 0.96 s is one row (ONNX
  pads it into one window: 15,360 samples give 1 row, 16,000 give 2).
- **In Play.** `HostModels.request_sound("sound", key, float32 bytes, rate)` and `push_sound_scores(task, key, scores)` with the 521 scores as float32 bytes (`Session.push_models_sound`); the protocol is in `browser_models.py`.
  `_hearing.SoundHostSink` keeps the newest window waiting while one is in flight, and answers a quiet window in order. The page (`runner/models-glue.js` `createSound`, `models-worker.js`, `worker.js` in funground-web)
  resamples with the same formula, runs the session, averages the rows and sends a `Float32Array`; it has no names. The one file is in `models.json`, made from `_models.py` by `tools/build_runtime.py`.
- **Same answers, desktop and Play** (`funground-web/tools/test_models.py`, case "sound"): `tts.wav`, `whistle.wav` and `clapping.wav` give the same name and the same four next names, and scores that agree to
  four decimals (largest difference 0.0). The test makes each Sound itself in plain Python instead of calling `sound.load()`: measured while writing it, `sound.load()` of the same 16 kHz file gives a different 44.1 kHz waveform
  on the desktop than in a page (clapping.wav: the sum of absolute values is 25,447 on the desktop, 22,125 in the page and 22,125 by exact linear interpolation, and the 5th name differed, "Cap gun" on the desktop and
  "Firecracker" in Play, with scores up to 0.027 apart). That is in the core's decoder, not in the model, and is not fixed here.
- **What it gives for the three recordings** (desktop and Play the same, with the Sounds made as above):

  | Recording | Name | Score | Next |
  |---|---|---|---|
  | `tts.wav` (a computer voice) | Speech | 0.998 | Speech synthesizer, Narration, monologue, Conversation, Radio |
  | `whistle.wav` | Whistling | 0.712 | Alarm, Whistle, Police car (siren), Siren |
  | `clapping.wav` | Hands | 0.415 | Explosion, Slap, smack, Gunshot, gunfire, Firecracker |

  The clapping is "Hands", not "Applause": the names are often broad or sideways, and the contract and the guide say so. (With `sound.load()` on the desktop the same file gives "Hands" 0.40 and "Cap gun" in fifth place.)
- **Speed.** On this machine the desktop works out one 0.96 s window in 2.2 ms. In Play (headless Chrome, onnxruntime-web, wasm) the 7.2 s recording (14 windows) is answered in 0.47 s once the model is loaded,
  a real-time factor of 0.065; the first answer in a page needs 3.5 s for the first Sound (model load) and 0.3 to 0.4 s for the next ones. A single window is therefore well under the 0.48 s hop. Chrome's fake microphone
  (a beep every second) gave answers in Play within 2.5 s of starting; the time of each window in the page was not measured on its own.
- **Tests.** `ml/tests/test_hearing.py` (the names, the choosing and every rule that gives `None`, the level rule, Heard and `is_new`, the windows, the thread with a stand-in model, a stopped microphone, the host path with a stand-in
  page, errors), `test_hearing_model.py` (the real file on the three recordings in `data/`, from a Sound and from a microphone that is fed one), and the case "sound" and "sound microphone" in funground-web's `tools/test_models.py`.

## What is left

- Tracking from the last frame's points (not the box of the last detection) if the speed needs it; WebGPU and threads in Play (S-231: about twice as fast for pose, if the page can be cross-origin isolated).
- A gallery example, a guide section and the Quick Reference rows; `tools/make_api_reference.py` does not yet read the library's docstrings.
- CI on Linux and macOS for `ml/`, and the check of `ORT_DISABLE_TELEMETRY` when the pinned `onnxruntime` changes.
