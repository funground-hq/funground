"""The models library: a body, a hand and the outline of a person in a camera or a picture, and the words and sounds in a microphone.

Bring it in with one line, then every call says ``ml.``::

    import funground as f
    from funground import camera, ml

    cam = camera.open()

    def draw():
        f.image(cam, 0, 0)
        body = ml.pose(cam)
        if body:
            f.circle(body.nose.x, body.nose.y, 20)

The models run on your own computer: what a camera sees never leaves it. The first call downloads the model it needs
(once) and keeps it in a ``models/`` folder beside your sketch. This is a separate install, ``funground-ml``; the core
keeps only a small ``funground.ml`` that imports it (ADR-007, D-125).

``ml.person(cam)`` gives a picture of the camera in which everything but the person is see-through, to draw over a background of
your own.

``ml.words(mic)`` listens to a microphone and gives the words it heard, a phrase at a time, in English. It works beside the sketch,
so ``draw()`` never waits for it.

``ml.sound(mic)`` listens to a microphone and gives the name of the sound it hears now, such as "Dog" or "Whistling", with a few
more guesses. It also works beside the sketch.

``ml.teach(name, picture)`` shows the computer a picture and what to call it, and ``ml.guess(picture)`` then names the taught
thing a new picture is most like. You teach it your own things, such as "thumbs up" and "thumbs down", with a few pictures of
each, and nothing leaves your computer.
"""
from __future__ import annotations

from funground.api import _sketch_folder

from . import _tasks, _teach
from ._results import Body, Guess, Hand, Heard, Words

__all__ = ["pose", "hand", "person", "words", "sound", "teach", "guess"]


def pose(source):
    """Find the body in a camera or a picture.

    The model finds one person. If there is no one it gives None, so ``if body:`` is enough. Calling it twice in one frame
    on the same camera gives the same body, and does the work once. The first call downloads the pose model (about 18 MB)
    and keeps it in a ``models/`` folder beside your sketch; it prints one line when it does. In Play the browser
    keeps the copy, and the answer can be one frame behind the picture.

    The body has 33 named points. Each is an f.Vector in pixels, on the source as drawn at (0, 0):
    nose, left_eye_inner, left_eye, left_eye_outer, right_eye_inner, right_eye, right_eye_outer, left_ear, right_ear,
    mouth_left, mouth_right, left_shoulder, right_shoulder, left_elbow, right_elbow, left_wrist, right_wrist,
    left_pinky, right_pinky, left_index, right_index, left_thumb, right_thumb, left_hip, right_hip, left_knee,
    right_knee, left_ankle, right_ankle, left_heel, right_heel, left_foot_index and right_foot_index. They are
    MediaPipe's names. ``body.points`` is a dict of every name and point, and ``body.score`` (0 to 1) says how sure the
    model is. A body with a score under 0.5 is not given: you get None.

    Left and right are the person's own sides. With a mirrored camera (the default of ``cam.start()``) the left wrist is
    the learner's own left wrist, wherever it shows on the screen.

    Arguments:
        source: a camera from camera.open(), or a picture from f.load_image() or f.create_graphics().

    Returns:
        a Body, or None if there is no one, or if the camera has no frame yet.

    Raises:
        TypeError: if source is not a camera or a picture.
        ConnectionError: if the model has to be downloaded and there is no connection.

    Example:
        body = ml.pose(cam)
        if body:
            f.line(body.left_wrist.x, body.left_wrist.y, body.right_wrist.x, body.right_wrist.y)

    See also: hand
    """
    return _tasks.find_body(source, _sketch_folder())


def hand(source):
    """Find a hand in a camera or a picture.

    The model finds one hand. If there is none it gives None, so ``if hand:`` is enough. Calling it twice in one frame on
    the same camera gives the same hand, and does the work once. The first call downloads the hand model (about 8 MB) and
    keeps it in a ``models/`` folder beside your sketch; it prints one line when it does. In Play the browser
    keeps the copy, and the answer can be one frame behind the picture.

    The hand has 21 named points. Each is an f.Vector in pixels, on the source as drawn at (0, 0):
    wrist, thumb_cmc, thumb_mcp, thumb_ip, thumb_tip, index_finger_mcp, index_finger_pip, index_finger_dip,
    index_finger_tip, middle_finger_mcp, middle_finger_pip, middle_finger_dip, middle_finger_tip, ring_finger_mcp,
    ring_finger_pip, ring_finger_dip, ring_finger_tip, pinky_mcp, pinky_pip, pinky_dip and pinky_tip. They are
    MediaPipe's names. ``hand.points`` is a dict of every name and point, and ``hand.score`` (0 to 1) says how sure the
    model is. A hand with a score under 0.8 is not given: you get None. A hand has no side (left or right) in this
    version.

    Arguments:
        source: a camera from camera.open(), or a picture from f.load_image() or f.create_graphics().

    Returns:
        a Hand, or None if there is no hand, or if the camera has no frame yet.

    Raises:
        TypeError: if source is not a camera or a picture.
        ConnectionError: if the model has to be downloaded and there is no connection.

    Example:
        palm = ml.hand(cam)
        if palm:
            f.circle(palm.index_finger_tip.x, palm.index_finger_tip.y, 12)

    See also: pose
    """
    return _tasks.find_hand(source, _sketch_folder())


def person(source):
    """Cut the person out of a camera or a picture.

    You get a new picture, as big as the source, in which everything that is not the person is see-through. Draw it over
    anything you like: ``f.image(ml.person(cam), 0, 0)``. The edge is soft, not a hard line: a pixel can be a little
    see-through. The picture is in the source's own pixels, so a mirrored camera gives a mirrored picture, just as ``f.image(cam, 0, 0)``
    draws it. The source itself is not changed.

    The model always gives an outline, so a picture with no one in it does not give None: you get a picture that is see-through
    everywhere. Calling it twice in one frame on the same camera gives the same picture, and does the work once. The first call
    downloads the person model (under 1 MB) and keeps it in a ``models/`` folder beside your sketch; it prints one line when it
    does. In Play the browser keeps the copy, and the picture can be one frame behind the camera.

    Arguments:
        source: a camera from camera.open(), or a picture from f.load_image() or f.create_graphics().

    Returns:
        a Picture the size of the source with only the person showing, or None if the camera has no frame yet (in Play, also before the first answer).

    Raises:
        TypeError: if source is not a camera or a picture.
        ConnectionError: if the model has to be downloaded and there is no connection.

    Example:
        f.background("navy")
        f.image(ml.person(cam), 0, 0)

    See also: pose, hand, image
    """
    return _tasks.find_person(source, _sketch_folder())


def words(source):
    """Listen to a microphone or a sound, and give the words in it.

    It understands English. For a microphone (``sound.microphone()``, started) funground cuts what it hears into phrases: a phrase
    starts when the sound gets louder than a whisper and ends after a short pause. Each phrase is worked on beside your sketch, so
    ``draw()`` never waits. The words appear a moment after the speaker pauses (a second or two on a slow computer). Until then you
    get the last words, or None before the first. If you pass a sound (for example ``mic.capture(3)`` or ``sound.load("a.wav")``),
    the whole sound is one phrase, at most 30 seconds. On a computer the call waits for the answer, and asking again about the same
    sound is free. In Play it gives None until the answer arrives.

    You get a Words. ``words.text`` is what was said, with capitals and full stops. ``words.score`` (0 to 1) says how sure the
    model is. ``words.is_new`` is True in the frame the words first appear, and False after that, so you can do something once for
    each thing said. ``str(words)`` is the text. When the model is not sure (a score under 0.4) or hears nothing, the answer is
    dropped and you keep the last words. A microphone that is not listening, or one with no sound (``FUNGROUND_HEADLESS=1``), gives
    None or the last words. Calling it twice in one frame gives the same Words.

    The first call downloads the words model (42 MB) and keeps it in a ``models/`` folder beside your sketch; it prints one line
    when it does. The sound never leaves your computer.

    Arguments:
        source: a microphone from sound.microphone(), or a Sound.

    Returns:
        a Words, or None if nothing has been heard yet.

    Raises:
        TypeError: if source is not a microphone or a sound.
        ValueError: if the sound is longer than 30 seconds.
        ConnectionError: if the model has to be downloaded and there is no connection.

    Example:
        mic = sound.microphone()
        mic.start()
        heard = ml.words(mic)
        if heard:
            f.text(heard.text, 20, 100)

    See also: pose, microphone
    """
    return _tasks.find_words(source, _sketch_folder())


def sound(source):
    """Listen to a microphone or a sound, and give the name of what it hears.

    It names everyday sounds, such as a dog, a whistle, clapping, a car or speech. For a microphone (``sound.microphone()``,
    started) funground listens to the last second (0.96 s) and works out a new answer about twice a second (every 0.48 s). It
    works beside your sketch, so ``draw()`` never waits. You get None until a second has been heard, and whenever there is nothing
    to name: it is quiet, the likeliest sound is silence, or the model is not sure of any name (a score under 0.1). So a sound that
    stops does not stay on the screen. If you pass a sound (for example ``mic.capture(3)`` or ``sound.load("a.wav")``), you get one
    answer for the whole sound, at most 30 seconds. On a computer the call waits for the answer, and asking again about the same
    sound is free. In Play it gives None until the answer arrives. A microphone that is not listening, or one with no sound
    (``FUNGROUND_HEADLESS=1``), gives None.

    You get a Heard. ``heard.name`` is the name, in English. ``heard.score`` (0 to 1) says how sure the model is. ``heard.next`` is
    up to four more guesses, the likeliest first; each is a Heard with a name and a score. ``heard.is_new`` is True in the frame
    an answer first appears, and False after that. ``str(heard)`` is the name. The model often gives a broad name ("Music", not the
    instrument) and it can be wrong, so show the next guesses too. Calling it twice in one frame gives the same Heard.

    The first call downloads the sound model (16 MB) and keeps it in a ``models/`` folder beside your sketch; it prints one line
    when it does. The sound never leaves your computer. The sound names are from the AudioSet ontology by Google LLC (CC BY 4.0),
    and the model is YAMNet by Google LLC (Apache 2.0).

    Arguments:
        source: a microphone from sound.microphone(), or a Sound.

    Returns:
        a Heard, or None if there is nothing to name.

    Raises:
        TypeError: if source is not a microphone or a sound.
        ValueError: if the sound is longer than 30 seconds.
        ConnectionError: if the model has to be downloaded and there is no connection.

    Example:
        mic = sound.microphone()
        mic.start()
        heard = ml.sound(mic)
        if heard:
            f.text(heard.name, 20, 100)

    See also: words, microphone
    """
    return _tasks.find_sound(source, _sketch_folder())


def teach(name, source=None, model=None):
    """Teach the computer what to call a picture.

    Give a name and a camera or a picture. The computer keeps a copy of the picture as one example of that name. Then
    ``ml.guess()`` can say which name a new picture is most like. Teach at least two names, and 5 or more pictures of each. The
    pictures should look different from each other: different light, different places, different angles.

    Teaching a camera keeps the picture it shows now. Hold a key down and it teaches as fast as the computer can, one picture at a
    time, so ``draw()`` never waits. The picture is turned into numbers beside your sketch; a picture counts in a guess once that is done.
    Teaching the same picture again under the same name adds nothing, and neither does a camera with no picture yet.

    There are three ways to call it. ``ml.teach("cat", cam)`` teaches one picture. ``ml.teach("cat", [a, b, c])`` teaches each
    picture in the list, in order. ``ml.teach({"cat": [a, b], "dog": [c, d]})`` teaches each name in order. What you taught lasts
    while the sketch runs. Nothing is saved.

    There are two picture models. ``"mobilenet"`` (MobileNetV4-small) is the default. It is quick and small (10 MB). ``"dinov2"``
    (DINOv2-small) is slower and larger (24 MB). On some pictures it can tell look-alike things apart better. The first call picks
    the model, and the sketch keeps it: a later call cannot use the other one. The first call downloads the model (once) and keeps it
    in a ``models/`` folder beside your sketch; it prints one line when it does. The pictures never leave your computer.
    MobileNetV4 is by Google, and its weights are by timm (Apache 2.0). DINOv2 is by Meta AI (Apache 2.0).

    Arguments:
        name: what to call the picture, as text, such as "thumbs up". It cannot be empty. Or a dict of names and lists of pictures.
        source: a camera from camera.open(), or a picture from f.load_image() or f.create_graphics(), or a list of them. Leave it out when name is a dict.
        model: "mobilenet" or "dinov2". None keeps the model already in use, and starts with "mobilenet".

    Returns:
        how many examples that name has now, as an int, counting the ones still being turned into numbers. For a dict, a dict of
        each name and its count.

    Raises:
        TypeError: if name is not text, or something to teach is not a camera or a picture (the message says which item).
        ValueError: if name is empty, or model is not "dinov2" or "mobilenet", or the sketch already uses the other model.
        ConnectionError: if the model has to be downloaded and there is no connection.

    Example:
        if f.key_down("u"):
            ml.teach("thumbs up", cam)

    See also: guess
    """
    return _teach.teach(name, source, model, _sketch_folder())


def guess(source, k=1):
    """Guess what a camera or a picture shows, from the things you taught.

    You get a Guess. ``guess.name`` is the name you taught that the picture is most like. ``guess.score`` (0 to 1) says how sure
    it is: 1 is fairly sure, and 0.5 means it is guessing between two. It is not how often the guess is right. With ``k`` of 2 or
    more, ``guess.next`` is the next names, the nearest first, each a Guess with its own name and score. A name appears once, and
    you get fewer than ``k`` if fewer names were taught. ``str(guess)`` is the name. Calling it twice in one frame on the same camera gives the same Guess.

    Each name is judged by the example of it that is nearest. With one name taught, the Guess is that name with a score of 0.5,
    and one line is printed to say to teach a second. With fewer than 5 examples of a name, one line is printed to say that more
    make better guesses. Each line is printed once.

    The computer always names the nearest thing you taught. It does not know what it was never shown. A picture of something else
    still gets a name. So teach a name for it, such as "nothing", with pictures of an empty room, the wall or whatever else the
    camera sees when nothing you care about is there.

    For a camera the answer is worked out beside your sketch, so ``draw()`` never waits. The Guess is the newest one, and can be a
    frame or more behind. You get None until the first one arrives, and if the camera has no picture yet. For a picture on a
    computer the call waits for the answer. You get None if nothing is taught yet, or no taught picture is ready.

    Arguments:
        source: a camera from camera.open(), or a picture from f.load_image() or f.create_graphics().
        k: how many names to give, as a whole number of 1 or more. The default is 1.

    Returns:
        a Guess, or None if nothing can be guessed yet.

    Raises:
        TypeError: if source is not a camera or a picture, or k is not a whole number.
        ValueError: if k is less than 1.
        ConnectionError: if the model has to be downloaded and there is no connection.

    Example:
        answer = ml.guess(cam)
        if answer:
            f.text(answer.name, 20, 100)

    See also: teach
    """
    return _teach.guess(source, k)
