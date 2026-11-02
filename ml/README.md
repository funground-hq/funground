# funground-ml

The models library for [funground](https://github.com/funground-hq/funground). It finds a body or a hand in a camera or a
picture, on your own computer. Nothing you show it leaves the computer.

```sh
python -m pip install funground-ml
```

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

f.run()
```

- `ml.pose(source)` gives the body: 33 named points (`body.nose`, `body.left_wrist`, ...), or `None` if there is no one.
- `ml.hand(source)` gives one hand: 21 named points (`hand.wrist`, `hand.index_finger_tip`, ...), or `None`.

The source is a camera from `camera.open()` or a picture from `f.load_image()`.

## The model files

The first call downloads the model it needs from the Hugging Face Hub (about 18 MB for the body, 8 MB for the hand) and
prints one line. The files are kept in a `models/` folder beside your sketch, so the next run works offline. They are
the OpenCV Zoo's conversions of MediaPipe's models, under the Apache-2.0 licence. Each file is checked against a
fixed SHA-256 before it is kept.

To keep the files in another folder, set `FUNGROUND_ML_MODELS` to its path. (The tests use this.)

## Privacy

The models run with `onnxruntime` on your computer. funground-ml sets `ORT_DISABLE_TELEMETRY=1` before it loads
`onnxruntime`. The only network use is the download of the model files.

## Tests

```sh
python -m pytest ml/tests
```

The tests that run the real models download them into `ml/tests/.models/` the first time, and are skipped when you are offline.

Licence: LGPL-2.1-only, like funground.
