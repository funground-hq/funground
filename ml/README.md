# funground-ml

The models library for [funground](https://github.com/funground-hq/funground). It finds a body or a hand, or cuts the person out, in a camera or a
picture, and hears the words you say, on your own computer. Nothing you show it or say to it leaves the computer.

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

- `ml.person(source)` gives a new picture in which everything that is not the person is see-through, to draw over a background of your own: `f.image(ml.person(cam), 0, 0)`. A picture with no one in it gives a picture that is see-through everywhere, not `None`.

- `ml.words(source)` gives the words said, as `words.text` with `words.score` and `words.is_new`, or `None` before anything is heard. The source is a microphone from `sound.microphone()` (listened to beside your sketch: the words of a phrase arrive a moment after you pause) or a Sound, such as `mic.capture(3)`. English only.

- `ml.sound(source)` gives the name of the sound heard, as `heard.name` with `heard.score`, `heard.next` (up to four more guesses) and `heard.is_new`, or `None` when it is quiet or the model is not sure. The source is a microphone from `sound.microphone()` (the last second, a new answer about twice a second, beside your sketch) or a Sound, such as `mic.capture(3)`. The name is often broad and can be wrong.

- `ml.teach(name, source)` keeps a picture as one example of a name you choose, and `ml.guess(source)` gives the name you taught that a new picture is most like, as `guess.name` with `guess.score` (and `guess.next` with `k=2` or more), or `None` before the first answer for a camera. Teach at least two names, 5 or more pictures of each, and a name such as "nothing" for an empty scene. What you taught lasts while the sketch runs; nothing is saved.

For pose, hand, person, teach and guess the source is a camera from `camera.open()` or a picture from `f.load_image()`.

## The model files

The first call downloads the model it needs from the Hugging Face Hub (about 18 MB for the body, 8 MB for the hand, under 1 MB for the person, 42 MB for the words, 16 MB for the sound, 10 MB for the picture model that teach and guess use, or 24 MB with `model="dinov2"`) and
prints one line. The files are kept in a `models/` folder beside your sketch, so the next run works offline. They are
the OpenCV Zoo's conversions of MediaPipe's models, MediaPipe's selfie segmentation, OpenAI's Whisper tiny.en and Google's YAMNet (as ONNX, from the community repository `audiomagic/yamnet-onnx`), Google's MobileNetV4-small (weights by timm, cut before its classifier by funground: `funground-hq/mobilenetv4-small-vector-onnx`) and Meta AI's DINOv2-small (from `onnx-community`), all under the Apache-2.0 licence.

The 521 sound names that YAMNet scores are in the package (`funground_ml/_sound_names.py`), not downloaded. They are from the AudioSet ontology by Google LLC, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). YAMNet is by Google LLC (Apache-2.0). Each file is checked against a
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
