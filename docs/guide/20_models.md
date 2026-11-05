# 20. Models: your body and your hands

A model is a program that has learnt to find something in a picture, or in a sound. funground has four. One finds a **body**. One
finds a **hand**. One cuts out the **person**. One writes down the **words** you say. Point your camera at yourself, and your sketch knows where your nose, your wrists and your fingertips
are. Speak to your microphone, and it knows what you said. Then you can draw with them.

Everything runs on your own computer. What the camera sees never leaves it.

## Install it first

Models are a library, and it is a **separate install**. Run this once, in a terminal:

```sh
python -m pip install funground-ml
```

Then one line brings it in, and every call says `ml.`

```py
import funground as f
from funground import camera, ml
```

Without the install, that line stops with one sentence: "The models library is a separate install: run
`python -m pip install funground-ml`".

Why is it separate? A model is a big file, and a program to run it. Most sketches need neither. So the core of
funground stays small, and you add the models when you want them.

**The first call downloads the model.** It prints one line, such as `Downloading the pose model, 18 MB, once.` The body
model is about 18 MB, the hand model about 8 MB and the words model 42 MB. The files are kept in a `models/` folder beside your sketch. The next
time you run it, nothing is downloaded, and it works without the internet.

**What stays on your computer:** the camera's pictures, what the microphone hears, the points and words the model finds and the model files. The only thing
that goes over the internet is the download of the model files.

**In Play** (the website), you install nothing. The browser keeps the model files and runs the models for you. The
answer can be **one frame behind** the picture. Your sketch does not change.

## Find a body

`ml.pose(source)` looks for a body. The source is a camera from `camera.open()`, or a picture from `f.load_image()`.

```py
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
        f.circle(body.nose.x, body.nose.y, 30)


f.run()
```

`ml.pose()` gives you a **body**, or `None` if no one is there. So `if body:` is all the check you need.

The body has 33 **named points**. Each one is an `f.Vector`, in pixels, on the source as you draw it at `(0, 0)`. So
you can put a point straight into a drawing call:

```py
f.line(body.left_wrist.x, body.left_wrist.y, body.right_wrist.x, body.right_wrist.y)
f.circle(body.nose.x, body.nose.y, 30)
```

Two more things are on a body:

- `body.points` is a dict of every name and its point. Use it to go through all of them, or to look one up by a name you
  have in a variable: `body.points["left_elbow"]`.
- `body.score` says how sure the model is, from 0 to 1. A body below 0.5 is not given, so you never see a weak guess:
  you get `None`.

```py
for name, point in body.points.items():
    f.circle(point.x, point.y, 6)           # a dot on every point of the body
```

A wrong name is helped. `body.left_sholder` says "A body has no point called 'left_sholder'. Did you mean
'left_shoulder'?"

**Left and right are the person's own sides.** A camera is mirrored by default, as in a mirror. Even so,
`body.left_wrist` is **your own left wrist**, wherever it shows on the screen. Raise your left hand, and the left wrist
goes up. On a mirrored screen, that hand is on the left of the picture, as it would be in a mirror.

A picture works as well as a camera. The points are in the picture's own pixels, so draw the picture at `(0, 0)` and
the points land in the right place. The gallery has a
[stick figure on a photograph](../gallery/README.md#a-stick-figure-on-a-photograph).

## Find a hand

`ml.hand(source)` does the same for a hand. It gives a **hand**, or `None`.

```py
hand = ml.hand(cam)
if hand:
    tip = hand.index_finger_tip
    f.circle(tip.x, tip.y, 20)
```

A hand has 21 named points, and `hand.points` and `hand.score`, in the same way. A hand below 0.8 is not given. A hand
has no side, left or right, in this version: you get one hand, whichever it is.

A trail that follows a fingertip is a list of its places. Add the newest, and drop the oldest:

```py
trail = []


def draw():
    f.image(cam, 0, 0)
    hand = ml.hand(cam)
    if hand:
        trail.append(hand.index_finger_tip)
        del trail[:-30]                     # keep the last 30 places
    for a, b in zip(trail, trail[1:]):
        f.line(a.x, a.y, b.x, b.y)
```

The gallery has a whole sketch: [follow your finger](../gallery/README.md#follow-your-finger).

## Cut out the person

> **Since 0.2.** In Play now; on your computer with funground 0.2.

`ml.person(source)` does not give points. It gives a new **picture**. The picture is as big as the camera's, and
everything that is not the person is see-through. Draw something behind it, then draw the picture on top:

```py
import funground as f
from funground import camera, ml

cam = camera.open()

def setup():
    f.size(640, 480)
    cam.start(640, 480)

def draw():
    f.background("navy")                  # anything you like: a gradient, shapes, a photo
    if cam.is_ready():
        f.image(ml.person(cam), 0, 0)     # only you, in front of it

f.run()
```

The edge of the cut-out is soft. A pixel on the edge is a little see-through, so you do not see a hard line.

If nobody is there, you do not get `None`. You get a picture that is see-through everywhere, so `f.image()` draws nothing.
Only a camera with no picture yet gives `None`. The first call downloads the person model. It is under 1 MB, and it is
kept like the others.

The picture is in the camera's own pixels, so it is mirrored when the camera is. It lines up with `f.image(cam, 0, 0)`
exactly. The gallery has a whole sketch: [in front of the sea](../gallery/README.md#in-front-of-the-sea).

## Listen for words

> **Since 0.2.** In Play now; on your computer with funground 0.2.

`ml.words(source)` listens. The source is a microphone from `sound.microphone()`, or a sound. It gives you the **words**
that were said, in English, or `None` if nothing has been said yet.

```py
import textwrap

import funground as f
from funground import ml, sound

mic = sound.microphone()

def setup():
    f.size(640, 480)
    mic.start()

def draw():
    f.background("navy")
    words = ml.words(mic)
    if words:
        f.text_size(32)
        f.text(textwrap.fill(words.text, 30), 20, 20)

f.run()
```

A words has three parts. `words.text` is what was said, with capitals and full stops. `words.score` says how sure the model is,
from 0 to 1. `words.is_new` is `True` in the frame the words first appear, and `False` after that. So you can do something once
for each thing said: `if words and words.is_new:`. `str(words)` is the text.

**It does not wait.** funground cuts what the microphone hears into **phrases**. A phrase starts when you speak, and ends
when you have been quiet for about half a second. Each phrase is worked on beside your sketch, so `draw()` never stops. The
words appear a moment after you pause (a second or two on a slow computer). Until then you get the last words you said.
If you speak again while it is still working, only your newest phrase waits.

**A sound works too.** `ml.words(mic.capture(3))` listens to the last three seconds. `ml.words(sound.load("hello.wav"))`
listens to a file. A sound can be up to 30 seconds long. On your computer the call waits for the answer, and asking again
about the same sound is free.

The model is Whisper tiny, a small one for English. It is good with a clear voice and a quiet room. It can be wrong about
names and unusual words. When it is not sure (a score under 0.4), or hears nothing, the answer is dropped and you keep the
last words, so you never get an empty answer. The first call downloads the model. It is 42 MB, and it is kept like the others.

The gallery has a whole sketch: [say a colour](../gallery/README.md#say-a-colour).

## One call a frame

If you call `ml.pose(cam)` twice in one frame, you get the same body, and the work is done once. So you can ask for the
body in two places in your code without slowing it down. `ml.hand(cam)`, `ml.person(cam)` and `ml.words(mic)` do the same.

Until the camera has sent its first picture, `ml.pose(cam)` gives `None`. You never need to wait on purpose.

## The 33 points of a body

| Part | Names |
|---|---|
| Face | `nose`, `left_eye_inner`, `left_eye`, `left_eye_outer`, `right_eye_inner`, `right_eye`, `right_eye_outer`, `left_ear`, `right_ear`, `mouth_left`, `mouth_right` |
| Shoulders and arms | `left_shoulder`, `right_shoulder`, `left_elbow`, `right_elbow`, `left_wrist`, `right_wrist` |
| Hands | `left_pinky`, `right_pinky`, `left_index`, `right_index`, `left_thumb`, `right_thumb` |
| Hips and legs | `left_hip`, `right_hip`, `left_knee`, `right_knee`, `left_ankle`, `right_ankle` |
| Feet | `left_heel`, `right_heel`, `left_foot_index`, `right_foot_index` |

## The 21 points of a hand

| Part | Names |
|---|---|
| Wrist | `wrist` |
| Thumb | `thumb_cmc`, `thumb_mcp`, `thumb_ip`, `thumb_tip` |
| Index finger | `index_finger_mcp`, `index_finger_pip`, `index_finger_dip`, `index_finger_tip` |
| Middle finger | `middle_finger_mcp`, `middle_finger_pip`, `middle_finger_dip`, `middle_finger_tip` |
| Ring finger | `ring_finger_mcp`, `ring_finger_pip`, `ring_finger_dip`, `ring_finger_tip` |
| Little finger | `pinky_mcp`, `pinky_pip`, `pinky_dip`, `pinky_tip` |

The names are MediaPipe's own, so its pictures and notes help you find the point you want. In a finger, `mcp` is the
knuckle where it joins the hand, `pip` and `dip` are the next two joints, and `tip` is the end.

## What can go wrong

- **It gives `None`.** Nobody was found. Always write `if body:` or `if hand:` before you use a point. Without the
  check, `body.nose` on `None` stops the sketch.
- **The light is low.** A dim room, or a bright window behind you, makes the model unsure. It may give `None`, or points
  that jump about. Turn on a light, and face it.
- **Part of the body is out of the picture.** The model has to guess the points it cannot see, so they may be wrong, or
  off the canvas. Step back until your arms are in the picture, and check `body.score` if you want to be careful.
- **There is one person and one hand.** If two people stand in the picture, you get one of them. If you hold up two
  hands, you get one.
- **The first run is slow.** It is downloading the model. The next run starts at once.
- **"Could not download".** There was no internet on the first run. Connect once, run the sketch, and the files are kept.
- **A model is not exact.** The points move a little even when you stand still. To make them calmer, draw the average of
  the last few places instead of the newest one.

## Try it

1. Draw a circle on each of your two wrists. Raise your left hand. Which circle moves?
2. Draw a line from each shoulder to its elbow, and from each elbow to its wrist. You have two arms.
3. Make a circle at your index finger tip that gets bigger when `hand.thumb_tip` and `hand.index_finger_tip` are far
   apart. Hint: `f.distance()`.
4. Add one circle to the canvas each time you say something new. Hint: `words.is_new`, and a list that grows.

**Previous:** [19. Studios: the same picture, twice](19_studios.md)
