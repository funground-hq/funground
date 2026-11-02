"""The models library: a body and a hand in a camera or a picture.

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
"""
from __future__ import annotations

from funground.api import _sketch_folder

from . import _tasks
from ._results import Body, Hand

__all__ = ["pose", "hand"]


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
