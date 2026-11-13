# 20. Models: bodies, hands, words and sounds

A model is a program that has learnt to find something in a picture, or in a sound. funground has six. One finds a **body**. One
finds a **hand**. One cuts out the **person**. One writes down the **words** you say. One names the **sound** you hear. And one
learns from **you**: teach it a few pictures of each thing, and it names new ones. Point your camera at yourself, and your sketch knows where your nose, your wrists and your fingertips
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
model is about 18 MB, the hand model about 8 MB, the words model 42 MB, the sound model 16 MB and the picture model (for teaching) 10 MB. The files are kept in a `models/` folder beside your sketch. The next
time you run it, nothing is downloaded, and it works without the internet.

## What a model is

Most programs follow rules that a person wrote. "If the score is over 10, show a star." You can read every rule.

A model is different. Nobody wrote its rules. It **learnt** them from a great many examples.

Think of how you learnt to tell a cat from a dog. Nobody gave you a list of rules. You saw many cats and many dogs, and
somebody said which was which. After a while you could tell, even for a cat you had never seen.

A model learns in a like way. To find a body, it was shown many pictures of people, with their points marked. To write down
words, it was shown many hours of speech, with what was said. To name a sound, it was shown many sound clips, with their
names. Then the learning stopped, and the result is the file you download. Your sketch only asks it questions.

Two things follow.

- **What a model learnt from decides what it is good at.** It is good at things like its examples. It is worse at things
  that were rare in them, or that were not in them at all.
- **Its answer is a best guess, not a fact.** That is why every answer has a `score`. A high score means "I am quite
  sure". It does not mean "I am right".

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

## Name a sound

> **Since 0.2.** In Play now; on your computer with funground 0.2.

`ml.sound(source)` listens and says what the sound is. The source is a microphone from `sound.microphone()`, or a sound. It
gives you a **heard** with the name of the sound, such as `"Dog"`, `"Whistling"` or `"Speech"`. It knows about 500 everyday
sounds.

```py
import funground as f
from funground import ml, sound

mic = sound.microphone()

def setup():
    f.size(640, 480)
    mic.start()

def draw():
    f.background("navy")
    heard = ml.sound(mic)
    if heard:
        f.text_size(48)
        f.text(heard.name, 20, 20)
        for i, guess in enumerate(heard.next):
            f.text_size(24)
            f.text(guess.name, 20, 100 + 40 * i)

f.run()
```

A heard has four parts. `heard.name` is the best guess. `heard.score` says how sure the model is, from 0 to 1.
`heard.next` is up to four more guesses, the likeliest first. Each one is a heard too, with its own `name` and `score`.
`heard.is_new` is `True` in the frame a new answer first appears, and `False` after that. `str(heard)` is the name.

**It does not wait.** The model listens to the last second of your microphone. A new answer comes about twice a second.
It is worked out beside your sketch, so `draw()` never stops. You get `None` for the first second after you start the
microphone.

**You also get `None` when there is nothing to name.** That is when the room is quiet, when the likeliest sound is
silence, or when the model is not sure of any name (a score under 0.1). So a sound that stops does not stay on the screen.
Check `if heard:` before you use it.

**A sound works too.** `ml.sound(mic.capture(3))` names the last three seconds. `ml.sound(sound.load("dog.wav"))` names a
file. A sound can be up to 30 seconds long. You get one answer for all of it. On your computer the call waits for the
answer, and asking again about the same sound is free. In Play you get `None` until the answer arrives.

**It often gives a broad name, and it can be wrong.** The model is small. For a piano it may say `"Music"`. For clapping it
may say `"Hands"` or `"Explosion"`. For a dog it may say `"Bark"` first and `"Dog"` next. That is why `heard.next` is there:
show the other guesses too. A few very broad names, such as `"Animal"` or `"Vehicle"`, are never given. Sounds that are
close together, like rain and a shower, can be mixed up.

The first call downloads the model. It is 16 MB, and it is kept like the others. The sound never leaves your computer.
The names of the sounds are from the AudioSet ontology by Google, and the model is YAMNet by Google.

The gallery has a whole sketch: [name that sound](../gallery/README.md#name-that-sound).

**Do something once, when a sound starts.** `heard.is_new` is `True` for every new answer, about twice a second, so a long
whistle is new many times. That suits a list of what was heard. To do something once, keep the last name, and act when it
changes:

```py
import funground as f
from funground import ml, sound

mic = sound.microphone()
woof = sound.note("C5", 0.3)
last = None

def setup():
    f.size(640, 480)
    mic.start()

def draw():
    global last
    f.background("navy")
    heard = ml.sound(mic)
    name = heard.name if heard else None
    if name == "Dog" and last != "Dog":
        woof.play()                  # once, when the dog starts
    last = name

f.run()
```

The same dog can be `"Dog"` in one answer and `"Bark"` in the next. To catch both, look at `heard.next` as well.

## Teach a model

> **Since 0.2.** In Play now; on your computer with funground 0.2.

The other models learnt from someone else's examples. This one learns from **yours**. You show it a few pictures of each
thing, and say what each thing is called. Then it can name a new picture.

`ml.teach(name, source)` keeps a copy of a picture as one example of `name`. The source is a camera or a picture. It gives
back how many examples that name has now. `ml.guess(source)` then names the taught thing that a picture is most like.

```py
import funground as f
from funground import camera, ml

cam = camera.open()

def setup():
    f.size(640, 480)
    cam.start(320, 240)

def draw():
    f.background("navy")
    f.image(cam, 0, 0)
    if f.key_down("1"):
        ml.teach("thumbs up", cam)
    if f.key_down("2"):
        ml.teach("thumbs down", cam)
    if f.key_down("0"):
        ml.teach("nothing", cam)
    guess = ml.guess(cam)
    if guess:
        f.text_size(40)
        f.text(guess.name, 340, 40)

f.run()
```

Hold up a thumb and hold down 1 for a few seconds. Turn your thumb down and hold down 2. Take your hand away and hold down
0. Now show a thumb, and the guess follows it.

**Holding a key teaches as fast as the computer can.** Each picture is turned into numbers beside your sketch, so `draw()`
never waits. While one picture is being worked on, a held key adds nothing, and the count stays true. How many pictures
a second that makes depends on your computer. A taught picture counts in a guess once it is ready.

A guess has three parts. `guess.name` is the name it chose. `guess.score` says how sure it is: 0.5 means it is guessing
between two names, and 0.95 is as sure as it gets. `guess.next` is empty, unless you ask for more names:
`ml.guess(cam, k=3)` gives the next two names in `guess.next`, the nearest first. `str(guess)` is the name.

**Teach a name for "nothing".** The computer always picks the nearest thing you taught. It never says "I don't know". Show
it your empty desk, and it will still say "thumbs up" or "thumbs down", whichever is nearer. So teach a third name, such as
`"nothing"`, with pictures of what the camera sees when nothing you care about is there.

**Teach 5 or more of each.** One or two examples are not enough. With look-alike things, such as two hand signs, five
examples of each were right about 84 times in 100 in our tests, and ten examples about 92 times in 100. Things that look
very different, such as a cup and a book, need only about three. Move a little while you teach: nearer, further, a bit to
the side, in brighter and dimmer light. Different pictures teach it more than the same picture many times. If you teach
fewer than 5 of a name, or only one name, the first guess prints one line to remind you.

**Three ways to teach.** `ml.teach("cup", cam)` teaches one picture. `ml.teach("cup", [a, b, c])` teaches each picture in a
list. `ml.teach({"cup": [a, b], "book": [c, d]})` teaches each name in turn, and gives back a dict of counts. The same
picture taught twice under one name counts once.

**How it decides.** Each picture becomes a list of numbers that describes how it looks. Pictures that look alike get
lists that are close together. A guess finds, for each name, the example nearest to the new picture, and picks the
nearest name. The score says how far ahead that name is of the next one: a clear lead gives a high score, and a near tie
gives about 0.5.

**On your computer, a picture waits.** `ml.guess(picture)` waits for the answer. In Play it gives `None` until the answer
arrives. A camera never waits, anywhere: the guess is the newest one, and can be a frame or more behind.

**Two picture models.** The first teach downloads the picture model, 10 MB, once. It is **MobileNetV4**, small and quick.
`ml.teach(name, cam, model="dinov2")` on the first teach chooses **DINOv2** instead: 24 MB, and much slower (in Play, about
2 guesses a second on a slow computer), but it sometimes tells look-alike things apart better. The first teach picks the
model for the whole sketch. What you taught lasts while the sketch runs. Nothing is saved, and the pictures never leave
your computer.

The gallery has a whole sketch: [teach by example](../gallery/README.md#teach-by-example).

### Make it look at the thing

The model looks at the **whole** picture you give it. Sit a few feet from the camera, and most of the picture is you, your
chair and the room. Your thumb is a small part of it. So the model learns "this room, with something here", and when you
hold your thumb somewhere else, the picture changes more than the sign does. The guesses get worse.

The cure is to give the model a picture where the thing fills most of the space. The easiest way is a **focus box**: cut a
square out of the middle of the camera, and teach and guess only that.

```py
import funground as f
from funground import camera, ml

BOX = 160
cam = camera.open()
focus = None

def setup():
    global focus
    f.size(640, 480)
    cam.start(320, 240)
    focus = f.create_graphics(BOX, BOX)

def draw():
    left, top = (320 - BOX) // 2, (240 - BOX) // 2
    focus.image(cam, -left, -top)        # the middle of the camera, copied into the box
    f.background("navy")
    f.image(cam, 0, 0)
    f.no_fill()
    f.stroke("gold")
    f.rect(left, top, BOX, BOX)          # show where the box is
    if f.key_down("1"):
        ml.teach("thumbs up", focus)
    if f.key_down("2"):
        ml.teach("thumbs down", focus)
    if f.key_down("0"):
        ml.teach("nothing", focus)
    guess = ml.guess(focus)
    if guess:
        f.no_stroke()
        f.fill("white")
        f.text_size(40)
        f.text(guess.name, 340, 40)

f.run()
```

`focus` is one picture that the sketch draws again every frame, so it works like a camera: holding a key teaches one
picture at a time, and in Play the guess is the newest one. Hold the thing inside the gold box, both when you teach and
when you test. "nothing" is now the box with nothing in it.

Two more ways, when you are ready for them:

- **Follow the hand.** `ml.hand(cam)` finds the hand anywhere in the picture. Cut the box around its points instead of
  from the middle, and the hand can move about. Two models work together: one finds where to look, the other names
  what it sees.
- **Take away the background.** With the camera still, keep a copy of the empty box (`empty = focus.copy()` when a key is
  pressed). Then, each frame, `focus.remove_background(empty)` makes every pixel that has not changed see-through, and the
  model sees it as black. Only the thing you hold up is left. It needs steady light: a shadow counts as a change.

### Test what you taught

Do not trust a few lucky guesses. Count. Add a **test mode** to your sketch: press T, and now holding a key does not teach.
It means "the camera shows this now", and every new guess is marked right or wrong.

```py
testing = False
tested = 0
right = 0
last = None

def key_pressed():
    global testing
    if f.key == "t":
        testing = not testing

def check(guess):                        # call it in draw() with the guess
    global tested, right, last
    if testing and guess is not None and guess is not last:
        for key, name in KEYS.items():   # KEYS = {"1": "thumbs up", "2": "thumbs down", "0": "nothing"}
            if f.key_down(key):
                tested += 1
                if guess.name == name:
                    right += 1
    last = guess
```

In test mode, skip the teaching: `if not testing:` before the `ml.teach` lines. Show `right` and `tested` on the screen.
Then try it fairly:

- **Test with new pictures.** Move the thing a little while you test, as you did while teaching. The same picture the model
  was taught tells you nothing.
- **Test every name,** "nothing" too, for about the same time each.
- **Teach 5, test; teach up to 10, test again.** Does it get better?
- **Change one thing at a time:** the place in the box, the light, the distance, another person's hand. Which one makes it
  worse? Teach a few more examples of that, and test again.
- **Compare the score with how often it is right.** If it says 0.9 and is right 9 times in 10, the score is honest.

## One call a frame

If you call `ml.pose(cam)` twice in one frame, you get the same body, and the work is done once. So you can ask for the
body in two places in your code without slowing it down. `ml.hand(cam)`, `ml.person(cam)`, `ml.words(mic)`, `ml.sound(mic)` and `ml.guess(cam)` do the same.

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

## What each model learnt from

Each model was made by someone else, from their own examples. funground uses their files and says who made them.

| Model | Name and who made it | What it learnt from |
|---|---|---|
| Body (`ml.pose`) | MediaPipe pose, by Google. The files are the OpenCV Zoo's copies, in the ONNX format. | Pictures of people in many kinds of pose, from many parts of the world, with their points marked. Google does not say how many. |
| Hand (`ml.hand`) | MediaPipe hand and palm, by Google. The files are the OpenCV Zoo's copies. | About 30,000 photos of real hands, and drawn computer hands placed over many backgrounds. |
| Person (`ml.person`) | MediaPipe selfie segmentation, by Google. | Phone photos of people, taken with their consent, in real rooms and streets, in all kinds of light. Google tested it on people from 17 parts of the world: it did about as well for every skin tone (within about 1 in 100). |
| Words (`ml.words`) | Whisper tiny.en, by OpenAI. It hears English only. | 680,000 hours of speech from the internet, with what was said. About two thirds of it was English. |
| Pictures you teach (`ml.teach`, `ml.guess`) | MobileNetV4, by Google; the weights were trained with timm, a library by Ross Wightman, now kept by Hugging Face. funground cut off its last layer, which names 1,000 kinds of thing, and uses the numbers just before it. The other choice, `model="dinov2"`, is DINOv2 by Meta AI. | MobileNetV4: ImageNet, about 1.3 million photos of 1,000 kinds of thing (animals, objects, foods), each labelled by people. DINOv2: 142 million pictures with no labels at all; it learnt which pictures look alike by itself. Neither learnt your names: those come from your examples. |
| Sound (`ml.sound`) | YAMNet, by Google. The 521 sound names are from the AudioSet ontology, also by Google. | AudioSet: about 2 million ten-second sound clips from YouTube videos, each one named by people who listened to it. Google left out 6 of AudioSet's 527 names, so that the model could not give an offensive name by mistake. |

All the model files are free to use (the Apache-2.0 licence). The sound names are free to use with a credit (CC BY 4.0).

Where these facts come from: Google's notes on the [body](https://research.google/blog/on-device-real-time-body-pose-tracking-with-mediapipe-blazepose/),
[hand](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker) and
[person](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20MediaPipe%20Selfie%20Segmentation.pdf) models,
OpenAI's [notes on Whisper](https://huggingface.co/openai/whisper-tiny.en), and Google's pages on
[YAMNet](https://github.com/tensorflow/models/blob/master/research/audioset/yamnet/README.md) and
[AudioSet](https://research.google.com/audioset/), the [MobileNetV4 paper](https://arxiv.org/abs/2404.10518) and
[timm's MobileNetV4 card](https://huggingface.co/timm/mobilenetv4_conv_small.e2400_r224_in1k), and Meta AI's
[DINOv2 paper](https://arxiv.org/abs/2304.07193).

## Why a model is sometimes wrong

A model is only as good as the examples it learnt from. Voices, faces and sounds that were rare in those examples get
worse answers. That is nobody's fault, and it is not about you. It is a gap in the examples, and you can see it in numbers.

**Words.** The words model was tested on clips of English where the right words were known. For each clip we counted the words it got
wrong. Here is what the test found for Whisper tiny.en:

- A person reading aloud in US English: about 1 word in 18 was wrong.
- A person reading aloud in Indian English: about 1 word in 8 was wrong. That is twice as many. It was one speaker, so it
  is an example, not a rule about all Indian English.
- Two people talking freely in Indian English: about 1 word in 3 was wrong. Some of that is the way people talk when they
  chat (fast, overlapping, informal), not the accent. The test could not tell how much.
- Add the noise of a fan or a busy room, and it got worse. For the two chatting speakers, about 6 words in 10 were wrong. In a few
  clips it got stuck and said one word again and again.

The mistakes are small and human. It writes a word that sounds alike ("price" for "prize"). It swaps little words ("he" for
"we"). It prefers a common word to a rare name ("Yukon" became "can"). It tidies up how people really talk, and leaves out
"you know" and "like". Whisper's makers say the same: it does better for some accents than for others. They do not say
how much Indian English it heard while it learnt, so how much of the gap comes from that, we do not know.

**Sounds.** The sound model often names the big family before the sound. For a dog it may say "Animal" first. In a test
of 1,840 five-second clips of everyday sounds, the right name came first in about 1 clip in 4 (24.5 in 100). It was in the
first three names in about 2 clips in 3 (64.6 in 100). funground hides the very broadest names, and gives you the next
guesses in `heard.next`, so you can use them. Short sounds were often called "Silence", because they were over so fast.

**Bodies and hands.** Low light, part of your body out of the picture, and more than one person are the usual causes. See
"What can go wrong", just below.

What to do about it: use the `score`, show the other guesses, and let a person correct the sketch. Test it with the
people who will use it, not only with yourself.

## What stays on your computer

These stay on your computer: the camera's pictures, what the microphone hears, the pictures you teach, the points and words the model finds and the model files. The only thing
that goes over the internet is the download of the model files. The program that runs the models is also told not to send anything about itself.

**In Play** (the website), you install nothing. The browser keeps the model files and runs the models for you. The
answer can be **one frame behind** the picture. Your sketch does not change.

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
- **The guess is wrong, or stuck on one name.** Teach more examples of the names it mixes up, from different places and
  angles, and teach a `"nothing"`. Check the counts: a name with many more examples than the others wins more often.
- **A model is not exact.** The points move a little even when you stand still. To make them calmer, draw the average of
  the last few places instead of the newest one.

## Try it

1. Draw a circle on each of your two wrists. Raise your left hand. Which circle moves?
2. Draw a line from each shoulder to its elbow, and from each elbow to its wrist. You have two arms.
3. Make a circle at your index finger tip that gets bigger when `hand.thumb_tip` and `hand.index_finger_tip` are far
   apart. Hint: `f.distance()`.
4. Add one circle to the canvas each time you say something new. Hint: `words.is_new`, and a list that grows.
5. Clap, whistle and hum. Which names does `ml.sound(mic)` give? Which one is wrong? Is the right name in `heard.next`?
6. Say the same sentence in two voices or accents, or in a quiet room and a noisy one. Does `ml.words` give the same
   words? Does the `score` change?
7. Teach three things on your desk with 3 examples each, then with 10 each. Which guesses get better? Then teach it
   only from one side of the desk, and guess from the other side.

**Previous:** [19. Studios: the same picture, twice](19_studios.md)
