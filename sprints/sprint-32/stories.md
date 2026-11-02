# Sprint 32 — Libraries for sound, sangeet and the camera; models and sign-in spikes (E-39, E-37, E-38)

**Dates:** planned 28 October 2026. Scope chosen by the maintainer on 28 Oct ("complete Sprint S-31. Then work on
S-246, S-247 and spikes S-231, 238. Accommodate the smaller ones whenever they fit"). Work in funground,
`funground-web` and `funground-hq.github.io`. Each story ships when it is checked.

**Goal:** `f` keeps the core and sound, sangeet and the camera become libraries a sketch imports, on the desktop and in
Play; the models spike and the GitHub sign-in spike give the evidence for E-37's first API and for D-118.

**Decisions:** D-120 (ADR-007) accepted. Needed during the sprint, brought to the maintainer before building: the names
in each library (D-123, before S-246 and S-247 are built); D-118 from S-238's results; E-37's first API from S-231's.
S-238 needs the maintainer for anything created under their account (a GitHub App, a hosting account).

| Story | Value | Status |
|---|---|---|
| S-246 | Move sound and sangeet out of `f`: `from funground import sound`, `from funground import sangeet` | done 1 Nov (funground #48, funground-web #18): full suite 2765 and 1758 passed, 1 skipped; Play's runner 15 of 15 checks, 17 of 17 frames, sound check passed |
| S-247 | Move the camera out of `f`: `from funground import camera` (after S-246) | done 2 Nov (funground #49, funground-web #19): full suite 2777 and 1749 passed, 1 skipped; Play's camera check passed, runner 15 of 15, 17 of 17 |
| S-231 | Spike: which models, from which provider, on the web and on the desktop | done 2 Nov: vision, speech (Whisper tiny.en), sounds (YAMNet) and a taught kNN measured on both platforms, all on onnxruntime; recommendation at the end of `spikes/16_models/README.md` |
| S-238 | Spike: signing in to GitHub from Play, a static site (D-118) | carried over to sprint 33: waits for the GitHub App and the Worker |
| S-232 | Pose and hands: `ml.pose(source)` and `ml.hand(source)` with named points, in the `funground-ml` package (D-124 d, D-125 a) | done 2 Nov (funground #53 to #55; funground-web #20): desktop and Play agree within 0.41 px |
| S-233 | The person: `ml.person(source)`, the source with everything but the person see-through (D-125 a; after S-232) | done 2 Nov (funground #56; funground-web #21): desktop and Play masks differ by 0.08 of 255 on average |
| Smaller, when they fit | S-249's SVG background bug (no API change); S-244 (a loaded font never chosen); S-245 (tidy the cut-out, decided in D-115) | SVG background done 28 Oct (full suite 2814 and 1749 passed, 1 skipped); S-244 done 2 Nov (#57); S-245 done 2 Nov (#58; funground-web #22) |

Order: the names proposal (D-123) first, with the internal module renames that free the names (no public change);
the spikes' desk research alongside, in the background; S-246 after the maintainer's answer, then S-247; smaller
stories between heavy jobs. One heavy job at a time on this machine.

## S-246 tasks

- [x] Names proposal for `sound` and `sangeet` to the maintainer (D-123), with a pending row (`Library_Names_Note.md`)
- [x] Rename the internal modules so `sound` and `sangeet` are free (`sound.py`, `synth.py`, `sound_views.py`, `microphone_input.py`, `hindustani.py`); naming trap checked
- [x] The libraries as subpackages that import the core, never the reverse; `tests/test_boundaries.py` rows
- [x] A moved name on `f` gives one plain sentence naming the import line
- [x] Contract rows respelt; examples, guide 16 and 17, course lessons; the import line from the first sound lesson
- [x] Reference, completions and `llms.txt` per library (`tools/make_api_reference.py`)
- [x] Play's runner and its checks with the new spelling (funground-web #18)
- [x] Architecture's section on modules; the whole suite; the same sound sketch on the desktop and in Play

## S-247 tasks

- [x] Names for `camera` to the maintainer (in D-123)
- [x] `camera_input.py` into the library (`funground/camera/_device.py`); [x] Play's camera path (`host_services.camera`; funground-web #19)
- [x] Contract rows, examples, guide, reference, completions, `llms.txt`; the moved names' sentence on `f`
- [x] `f` has 183 names; camera goldens unchanged; the camera sketch on the desktop and in Play

## S-231 tasks

- [x] Desk research: every provider and task, with sizes, licences of code and weights, platforms, worker or page (`spikes/16_models/research.md`)
- [x] Measurements on this machine (desktop frames per second; headless Chrome), one heavy job at a time; macOS and Linux marked unverified or measured in CI. Web done 28 Oct (`spikes/16_models/web/results.md`): MediaPipe runs in a module worker; pose lite 11/s on CPU, about 40/s on GPU; no analytics hosts. Desktop done 28 Oct (`spikes/16_models/desktop/results.md`): 4 to 7 times faster than the web; the Python package logs usage to Google (play.googleapis.com) with no switch found Speech, sounds and a taught kNN 2 Nov (`spikes/16_models/speech_sounds/results.md`).
- [x] How a model's answer reaches a Python sketch in Pyodide without `async` (product code in S-232: `HostModels`, the latest answer read each frame)
- [x] The same 30-line pose sketch on the desktop and in Play (gallery `models-01_stick_figure`, S-232: within 0.03 px)
- [x] A recommendation per platform, and a first API (as the `ml` package, D-120) for the maintainer (D-124 d, D-125 a; closing table in `spikes/16_models/README.md`)

## S-238 tasks

- [x] Desk research: GitHub App user tokens from a browser, the exchange service, free hosts and their limits (`spikes/17_github_signin/research.md`)
- [ ] Option a (a pasted fine-grained token) prototyped against a sketchbook from `funground-hq/sketchbook`
- [ ] Option b: the exchange service's code (written, `exchange/worker.js`); the App and the host set up by or with the maintainer
- [ ] The maintainer's check on a phone and a laptop: sign in, list, open, save, new, sign out
- [ ] A recommendation for D-118, with who owns the App and the service

## S-232 tasks

- [x] The API to the maintainer (D-125, `docs/design/ML_First_API_Note.md`): accepted 2 Nov, option a
- [x] The `funground-ml` package in `ml/` (decided by Claude: a folder of this repository with its own `pyproject.toml`, not a new repository; the maintainer can ask for one): `onnxruntime` with `ORT_DISABLE_TELEMETRY=1` set before import, models fetched by funground's own HTTPS request and checked by SHA-256
- [x] The core's `funground/ml` stub with the install sentence; boundary rows
- [x] `ml.pose` and `ml.hand` on the desktop: named `f.Vector` points, `.points`, `.score`, `None` for nobody, the body's own sides with a mirrored camera, the same answer twice in a frame
- [x] Play: the same files in `onnxruntime-web` in the worker (funground-web), the latest result, points within 5 px of the desktop's
- [x] Contract rows, reference, completions, `llms.txt`; a gallery example and a guide section

## S-233 tasks

- [x] `ml.person(source)` on the desktop and in Play, the selfie model's mask applied as alpha; contract row; example and guide

