# The first models library: pose, hands and the person (D-125)

**Status:** proposed 2 November 2026 (D-125, pending). It comes from spike S-231 (`spikes/16_models/README.md`) and
D-124 (ONNX files from the Hugging Face Hub, run by `onnxruntime` on the desktop and `onnxruntime-web` in Play). Stories
S-232 (pose and hands) and S-233 (the person's outline) are built after the answer.

## Context

D-120 and ADR-007 make models a library in a package of its own, `funground-ml`, imported as `from funground import ml`.
The spike measured what the first stories can offer on both platforms, with the same files:
- **A body:** 33 named points (MediaPipe's pose model, converted by the OpenCV Zoo, Apache-2.0).
- **A hand:** 21 named points.
- **The person's outline:** Google's selfie model, 0.25 MB.

The face mesh waits for an open model. What a learner writes has to be decided before building.

## Proposed API

```python
import funground as f
from funground import camera, ml

cam = camera.open()

def setup():
    f.size(640, 480)
    cam.start()

def draw():
    f.image(cam, 0, 0)
    body = ml.pose(cam)
    if body:
        f.circle(body.nose.x, body.nose.y, 20)
        f.line(body.left_wrist.x, body.left_wrist.y, body.right_wrist.x, body.right_wrist.y)

f.run()
```

| Name | What it gives |
|---|---|
| `ml.pose(source)` | The body in a camera or picture, or `None` if there is no one. Its 33 points are named, as `body.nose`, `body.left_wrist`, `body.right_ankle`, and so on. Each point is an `f.Vector` in canvas pixels, on the source as drawn at `(0, 0)`. `body.points` is a dict of every name and point; `body.score` (0 to 1) says how sure the model is |
| `ml.hand(source)` | One hand, or `None`, with 21 named points: `hand.wrist`, `hand.thumb_tip`, `hand.index_tip`, and so on, plus `hand.points` and `hand.score` |
| `ml.person(source)` | A picture of the source with everything that is not the person made see-through: `f.image(ml.person(cam), 0, 0)` |

**The source** is a camera (`camera.open()`) or a picture (`f.load_image()`). The camera's frame is the one taken before
`draw()` (contract I4), so calling `ml.pose(cam)` twice in a frame gives the same body.

**Models arrive on first use.** The first call downloads its model file from the Hugging Face Hub with funground's own
request, without the Hub's library. It prints one line ("Downloading the pose model, 6 MB, once"), and the file is
kept for offline runs, as fonts from the web are (D-119).

**In Play** the model runs in JavaScript beside the sketch, and `ml.pose(cam)` returns its latest result for that
camera. The result can be one frame behind the picture: the guide says so, and nothing in a sketch changes. No
`async` is needed.

**Without the package:** `from funground import ml` gives one sentence: "The models library is a separate install: run
`python -m pip install funground-ml`". In Play it is always there. The core keeps only that small `funground/ml`
stub, which imports the package.

**Privacy:** everything runs on the learner's computer or in their browser. Pictures and points never leave it.
`ORT_DISABLE_TELEMETRY=1` is set before `onnxruntime` is imported.

## Options

- **Keep current behaviour:** no models.
- **a. The three functions above** (recommended): one function per thing a learner wants, with named points.
- **b. A model object first:** `detector = ml.load("pose")`, then `detector.find(cam)`. It is closer to MediaPipe and
  ml5, and makes the loading visible, but it adds a step and a name for every model.
- **c. Results as lists:** `ml.pose(cam)` returns a list of 33 `(x, y)` tuples, and the guide gives the index of each
  point. It is the least code, but `body[15]` says nothing to a learner.

## Trade-offs

| | a | b | c |
|---|---|---|---|
| Lines before the first point | 1 | 2 | 1 |
| Says which point it is | yes (`body.left_wrist`) | yes | no (`body[15]`) |
| Shows that a model loads | the first-use line | in the code | the first-use line |
| More people or hands later | `ml.poses(cam)` returns a list (a later story) | `find_all` | a list of lists |

## Recommendation: a

**Why:** a learner asks "where is my wrist?", and `body.left_wrist` answers it in the words they use. The model and its
download are details the first-use line explains. `f.Vector` points work with `f.line`, `f.distance` and the rest of
the core.

**What would change it:** if the course wants learners to see that a model is something you load, b makes that a line
of code.

## Open questions

1. Point names: MediaPipe's own (`left_wrist`, `left_index` for the hand's tip in the body), or plainer words where they
   are obscure (`left_hand` for `left_index`)? Proposed: MediaPipe's, so that their documentation still helps.
2. Mirroring: with `cam.start(mirror=True)`, `left_wrist` is the learner's own left wrist, wherever it shows on the screen.
   Proposed: yes, the body's own sides.
