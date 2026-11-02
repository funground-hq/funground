# Sprint 32 review — Libraries for sound, sangeet and the camera; the models library (E-39, E-37, E-38)

**Dates:** 28 October to 2 November 2026. Work in funground (PRs #41 to #61), `funground-web` (PRs #18 to #22) and
`funground-hq.github.io`. Every story shipped when it was checked. **Awaiting sign-off.**

## Outcome

Goal met for everything except the sign-in spike, which waits for accounts. `f` keeps the core; `sound`, `sangeet`
and `camera` are libraries a sketch imports, on the desktop and in Play. The models spike ended in two decisions
(D-124, D-125), and its first API shipped in the same sprint as the separate `funground-ml` package: a body, a hand and
the person, with the desktop and Play agreeing by test. The three smaller stories fitted in.

| Story | Result |
|---|---|
| S-246 Sound and sangeet as libraries | `from funground import sound`, `from funground import sangeet` (D-123 names); a moved name on `f` says which import line to add (#48, web #18) |
| S-247 The camera as a library | `from funground import camera`; `f` has 183 names; camera goldens unchanged (#49, web #19) |
| S-231 Spike: models | ONNX everywhere (D-124 d): the same files in `onnxruntime` and `onnxruntime-web`. Vision, speech (Whisper tiny.en), sounds (YAMNet) and a taught kNN measured on both platforms, all passing their criteria. Closing recommendation in `spikes/16_models/README.md` (#47, #50, #59) |
| S-232 Pose and hands | `ml.pose(source)`, `ml.hand(source)`: 33 and 21 named `f.Vector` points, `.score`, the learner's own sides with a mirrored camera; Play through a models worker; reference, two gallery examples, guide chapter 20 (#53 to #55, web #20) |
| S-233 The person | `ml.person(source)`: everything but the person see-through, soft edge (#56, web #21) |
| S-244 A font never chosen | one line at the end of the run naming the font and the call to add; quiet after an error (#57) |
| S-245 Tidy the cut-out | `tidy=`, `at=` on `remove_background` and `remove_color`; `g.outline(points=80)` (#58, web #22) |
| S-249's SVG background bug | an SVG keeps its `background()` (28 Oct) |
| S-238 Spike: GitHub sign-in from Play | **not done**: desk research and the exchange service's code are written; the GitHub App and the Worker need the maintainer. Carried over to sprint 33 |

**Tests:** the whole core suite in parts, without `FUNGROUND_HEADLESS`, before each product merge:

| PR | Core suite | Other |
|---|---|---|
| #48 S-246 | 2765 and 1758 passed, 1 skipped | Play: runner 15 of 15 checks, 17 of 17 frames, sound check |
| #49 S-247 | 2777 and 1749 passed, 1 skipped | Play's camera check |
| #53 S-232 desktop | 2768 + 1119 + 638 passed, 1 skipped | `ml/tests` 43 passed with the real models |
| #54 S-232 Play | 2768 + 1120 + 638 passed, 1 skipped | `ml/tests` 65; funground-web `test_models.py` 8 of 8 |
| #55 S-232 docs | 2429 + 343 + 1120 + 638 passed | models examples 4 passed in the funground-ml venv |
| #56 S-233 | 2431 + 343 + 1126 + 638 passed | `ml/tests` 90; models examples 7 passed |
| #57 S-244 | 2440 + 343 + 1131 + 647 passed | `test_unused_font.py` 23 |
| #58 S-245 | 2474 + 346 + 1126 + 638 passed | `test_cutout_tidy.py` 40; one failure in the third part did not repeat on the rerun (not identified) |

## Measurements

| What | Result | How |
|---|---|---|
| Pose, desktop against Play | within 0.03 px (gallery stick figure); hands within 0.41 px | the same photo through both, S-232 |
| Person mask, desktop against Play | mean 0.08 of 255 | S-233 |
| Mask stretch in Play | 3.7 ms with Cairo, against 204 ms in pure Python | S-233 |
| Tidy cut-out | busy scene overlap 0.874 to 0.967, striped 0.478 to 0.564 with `at=`; 5 to 8 ms at 640 x 480 | `tests/data/cutout/`, S-245 |
| Whisper tiny.en q8 | real-time factor 0.11 to 0.17 desktop, 0.37 to 0.54 web; same words on both | `spikes/16_models/speech_sounds/` |
| YAMNet | 1.4 ms desktop, 13 to 28 ms web per window; scores within 1e-5 | same |
| Taught kNN, 3 examples a class | DINOv2 91 %, MobileNetV4 90 % at k=1 | same, 200 splits |

## Decisions

- Maintainer: D-123 (library names), D-124 d (ONNX everywhere, models from the Hugging Face Hub), D-125 a (the first
  models API), D-126 (`ml.words`, `ml.sound`, `ml.teach`, `ml.guess`), D-127 (0.2 waits for the next models and Play
  stories; `funground-ml` is published beside it).
- Decided by Claude, for review: `funground-ml` lives in `ml/` of this repository with its own `pyproject.toml`
  rather than its own repository; test photos for pose (Gandhi, public domain) and hands (a US government photo,
  public domain), chosen with the maintainer; the models examples' snapshots compare with a 0.01 px tolerance, because
  onnxruntime's answers differ in the last digits between CPUs (#57); the Whisper and YAMNet glue is funground's own
  decode loop, not Transformers.js.
- Pending: D-118 (Play's sketchbook on GitHub, after S-238).

## Findings that change later work

1. **Exact snapshots do not survive model inference across machines.** GitHub's runner gave a point 0.00004 px away
   from this machine's. Model examples compare with a stated tolerance; every other example stays exact.
2. **A CI run hung for 25 minutes in a guide sound example** (`16_sound`, near #7) and was cancelled; the same commit
   passed on the other run and on a rerun. The 5-minute per-test timeout did not fire. Not yet explained.
3. **The site rebuilds once a day**, so work merged after about 11:00 UTC appears the next day; the maintainer looked
   for the models guide on the day it merged.
4. **Builders typed a bare `python3` four times** across the sprint, despite the rule at the top of every brief. No
   installer opened, but two stray processes were left. The rule stays at the top; a hook that refuses it would be
   stronger.
5. **YAMNet's only ONNX copy has an unknown uploader.** Before S-250 ships, the file is checked against Google's
   model and hosted by us.

## Built by subagents

Parts of S-232 (the package and the Play worker), S-233 and S-245, and the S-231 measurements (ONNX on both platforms;
speech, sounds and the kNN), were built by Sonnet subagents. The main session reviewed each diff, reran the tests and
the Whisper measurement, fixed what CI found (the reference tool leaving `ml/` on the import path; the snapshot
tolerance) and made every commit.

## Retrospective

Running a spike and shipping its result in the same sprint worked because the API went to the maintainer as soon as
the evidence was in, and was answered the same day. The machine's memory was the bottleneck again: running suite parts
side by side once turned a 10-minute part into 36 minutes. One heavy job at a time is slower to plan and faster to
finish.
