"""S-231 spike: our own minimal pre- and post-processing for ONNX models run by onnxruntime (numpy + Pillow only).
Written from the models' own cards and MediaPipe's documented graph settings; the OpenCV Zoo wrappers were READ for the tensor
layouts, nothing was copied. Frames are RGB uint8 arrays of 640 x 480. Every function returns points in frame pixels.
The line count in results.md counts the non-blank, non-comment lines of this file (per section marked  ## name).
"""
import json
import numpy as np
from PIL import Image


## shared
def warp(img, cx, cy, side, angle, out):
    """Cut a square `side` px wide, centred on (cx, cy) and turned by `angle` radians, and resample it to out x out.
    One affine call does crop, rotation, padding with black and resize. Returns the crop and the forward mapper."""
    c, s, k = np.cos(angle), np.sin(angle), side / out
    coeffs = (k * c, -k * s, cx - 0.5 * side * (c - s), k * s, k * c, cy - 0.5 * side * (s + c))
    crop = np.asarray(Image.fromarray(img).transform((out, out), Image.AFFINE, coeffs, Image.BILINEAR))

    def to_frame(p):  # crop pixel coordinates (n, 2) -> frame pixels
        p = np.asarray(p, np.float64)
        return np.stack([coeffs[0] * p[:, 0] + coeffs[1] * p[:, 1] + coeffs[2],
                         coeffs[3] * p[:, 0] + coeffs[4] * p[:, 1] + coeffs[5]], 1)
    return crop, to_frame


def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -50, 50)))


def anchors(size, strides):
    """SSD anchor centres (x, y in 0..1) as MediaPipe's detectors define them: 2 per cell, layers of equal stride merged."""
    out, i = [], 0
    while i < len(strides):
        j = i
        while j < len(strides) and strides[j] == strides[i]:
            j += 1
        g = -(-size // strides[i])
        ys, xs = np.mgrid[:g, :g]
        out.append(np.repeat(np.stack([(xs + .5) / g, (ys + .5) / g], -1).reshape(-1, 1, 2), 2 * (j - i), 1).reshape(-1, 2))
        i = j
    return np.concatenate(out)


def roi(img, box, k0, k1, scale, shift_y, out):
    """MediaPipe's region of interest from a detection: turn so that key point k0 -> k1 points up, grow the box by `scale`
    (square, long side) and move the centre along the box's own up axis by shift_y * its height."""
    (cx, cy, w, h), (x0, y0), (x1, y1) = box, k0, k1
    ang = np.pi / 2 - np.arctan2(-(y1 - y0), x1 - x0)
    ang -= 2 * np.pi * np.floor((ang + np.pi) / (2 * np.pi))
    cx, cy = cx - shift_y * h * np.sin(ang), cy + shift_y * h * np.cos(ang)
    return warp(img, cx, cy, max(w, h) * scale, ang, out)


def letterbox(img, out):
    return warp(img, img.shape[1] / 2, img.shape[0] / 2, max(img.shape[:2]), 0.0, out)


## detector (pose person detector and palm detector share this)
def detect(sess, crop, to_frame, anc, size, n_kp, centre_norm):
    """Run the SSD detector on the letterboxed crop; return the best (box cx, cy, w, h; key points) in frame pixels or None."""
    x = crop.astype(np.float32)[None] / 255
    x = (x - 0.5) * 2 if centre_norm else x
    out = sess.run(None, {sess.get_inputs()[0].name: x.transpose(0, 3, 1, 2) if sess.get_inputs()[0].shape[1] == 3 else x})
    reg, sc = (out[0][0], out[1][0, :, 0]) if out[0].shape[-1] > 1 else (out[1][0], out[0][0, :, 0])
    i = int(np.argmax(sc))
    if sigmoid(sc[i]) < 0.5:
        return None
    d = reg[i].reshape(-1, 2)                         # rows: box centre, box size, then the key points (all in crop pixels)
    centre = to_frame(((d[:1] / size + anc[i]) * size))[0]
    k = to_frame(np.array([[1.0, 0]]))[0, 0] - to_frame(np.array([[0.0, 0]]))[0, 0]      # crop pixel -> frame pixel
    kps = to_frame((d[2:2 + n_kp] / size + anc[i]) * size)
    return (*centre, *(np.abs(d[1]) * k)), kps


## pose: person detector + 33-point landmark model (OpenCV Zoo files, MediaPipe weights)
class Pose:
    def __init__(self, det, lm, ort):
        self.det, self.lm, self.anc = ort.InferenceSession(det), ort.InferenceSession(lm), anchors(224, [8, 16, 32, 32, 32])
        self.region = None

    def find(self, img):
        crop, f = letterbox(img, 224)
        r = detect(self.det, crop, f, self.anc, 224, 4, True)
        self.region = None if r is None else r[1][:2]     # mid-hip point and a point on the circle round the body
        return self.region

    def points(self, img):
        """The 33 body points (x, y, z, visibility) in frame pixels, or None. Uses the box of the last find()."""
        if self.region is None:
            return None
        (x0, y0), (x1, y1) = self.region
        dist = np.hypot(x1 - x0, y1 - y0)
        crop, f = roi(img, (x0, y0, 2 * dist, 2 * dist), (x0, y0), (x1, y1), 1.25, 0, 256)
        out = self.lm.run(None, {self.lm.get_inputs()[0].name: crop.astype(np.float32)[None] / 255})
        if out[1][0, 0] < 0.5:
            return None
        raw = out[0][0].reshape(-1, 5)[:33]
        xy = f(raw[:, :2])
        return np.c_[xy, raw[:, 2] * 2 * dist * 1.25 / 256, sigmoid(raw[:, 3])]


## hand: palm detector + 21-point landmark model
class Hand:
    def __init__(self, det, lm, ort):
        self.det, self.lm, self.anc = ort.InferenceSession(det), ort.InferenceSession(lm), anchors(192, [8, 16, 16, 16])
        self.box = None

    def find(self, img):
        crop, f = letterbox(img, 192)
        r = detect(self.det, crop, f, self.anc, 192, 7, False)
        self.box = None if r is None else (r[0], r[1][0], r[1][2])
        return self.box

    def points(self, img):
        """The 21 hand points (x, y, z) in frame pixels, or None. Uses the palm of the last find()."""
        if self.box is None:
            return None
        crop, f = roi(img, *self.box, 2.6, -0.5, 224)
        out = self.lm.run(None, {self.lm.get_inputs()[0].name: crop.astype(np.float32)[None] / 255})
        if out[1][0, 0] < 0.8:
            return None
        raw = out[0][0].reshape(-1, 3)
        return np.c_[f(raw[:, :2]), raw[:, 2]]


## single-stage models
def movenet(sess, img):
    """17 COCO points (x, y, score) in frame pixels; MoveNet wants a square, so the frame is letterboxed (int32, 0..255)."""
    crop, f = letterbox(img, 192)
    o = sess.run(None, {sess.get_inputs()[0].name: crop.astype(np.int32)[None]})[0][0, 0]
    return np.c_[f(o[:, [1, 0]] * 192), o[:, 2]]


def selfie(sess, img):
    """Person mask (480 x 640 floats, 0..1) from MediaPipe's selfie model as ONNX: 256 x 256 in, 0..1 scale, no mean."""
    x = np.asarray(Image.fromarray(img).resize((256, 256), Image.BILINEAR), np.float32).transpose(2, 0, 1)[None] / 255
    a = sess.run(None, {sess.get_inputs()[0].name: x})[0][0, 0]
    return np.asarray(Image.fromarray(a).resize((img.shape[1], img.shape[0]), Image.BILINEAR))


def humanseg(sess, img):
    """PP-HumanSeg (OpenCV Zoo): 192 x 192, mean 0.5, std 0.5; two class maps -> person mask (bool, 480 x 640)."""
    x = (np.asarray(Image.fromarray(img).resize((192, 192), Image.BILINEAR), np.float32) / 255 - 0.5) / 0.5
    o = sess.run(None, {sess.get_inputs()[0].name: x.transpose(2, 0, 1)[None]})[0][0]
    big = [np.asarray(Image.fromarray(c).resize((img.shape[1], img.shape[0]), Image.BILINEAR)) for c in o]
    return big[1] > big[0]


def yunet(sess, img):
    """YuNet face detector (OpenCV Zoo, 640 x 640 in, BGR 0..255): best face as (box x, y, w, h, score, 5 points)."""
    canvas = np.zeros((640, 640, 3), np.float32)
    canvas[:img.shape[0], :img.shape[1]] = img[:, :, ::-1]
    o = sess.run(None, {"input": canvas.transpose(2, 0, 1)[None]})
    best = (-1, None)
    for n, s in enumerate((8, 16, 32)):
        cls, obj, bb, kp = (o[n][0, :, 0], o[3 + n][0, :, 0], o[6 + n][0], o[9 + n][0])
        score = np.sqrt(np.clip(cls, 0, 1) * np.clip(obj, 0, 1))
        i = int(np.argmax(score))
        if score[i] > best[0]:
            g = 640 // s
            r, c = divmod(i, g)
            cx, cy, w, h = (c + bb[i, 0]) * s, (r + bb[i, 1]) * s, np.exp(bb[i, 2]) * s, np.exp(bb[i, 3]) * s
            pts = (kp[i].reshape(5, 2) + [c, r]) * s
            best = (score[i], (cx - w / 2, cy - h / 2, w, h, float(score[i]), pts))
    return best[1] if best[0] > 0.6 else None


def classify(sess, img, labels):
    """MobileNetV4 (ImageNet): shortest edge 256 (bicubic), centre crop 224, mean/std; returns the best 5 (label, probability)."""
    h, w = img.shape[:2]
    k = 256 / min(h, w)
    im = Image.fromarray(img).resize((round(w * k), round(h * k)), Image.BICUBIC)
    l, t = (im.width - 224) // 2, (im.height - 224) // 2
    x = (np.asarray(im.crop((l, t, l + 224, t + 224)), np.float32) / 255 - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    lg = sess.run(None, {sess.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0]
    p = np.exp(lg - lg.max())
    p /= p.sum()
    return [(labels[str(i)], float(p[i])) for i in np.argsort(-p)[:5]]


def objects(sess, img, labels, threshold=0.4):
    """D-FINE nano (COCO): 640 x 640 stretched, 0..1 scale; returns (label, score, x, y, w, h) in frame pixels."""
    x = np.asarray(Image.fromarray(img).resize((640, 640), Image.BILINEAR), np.float32).transpose(2, 0, 1)[None] / 255
    logits, boxes = sess.run(None, {sess.get_inputs()[0].name: x})
    p = sigmoid(logits[0])
    cls, score = p.argmax(1), p.max(1)
    keep = score > threshold
    b = boxes[0][keep] * [img.shape[1], img.shape[0], img.shape[1], img.shape[0]]
    return [(labels[str(c)], float(s), *(bb[:2] - bb[2:] / 2), *bb[2:]) for c, s, bb in zip(cls[keep], score[keep], b)]


def embed(sess, img):
    """Picture -> vector: the same resize, crop and normalisation as classify(); the output (or the CLS token) as a unit vector."""
    h, w = img.shape[:2]
    k = 256 / min(h, w)
    im = Image.fromarray(img).resize((round(w * k), round(h * k)), Image.BICUBIC)
    l, t = (im.width - 224) // 2, (im.height - 224) // 2
    x = (np.asarray(im.crop((l, t, l + 224, t + 224)), np.float32) / 255 - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    o = sess.run(None, {sess.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0]
    v = o[0, 0] if o.ndim == 3 else o.reshape(-1)      # DINOv2: the first token (CLS) of the last hidden state
    return v / np.linalg.norm(v)
