"""Make the synthetic test photos for spike S-227 (original, CC0).

Three scenes at 640 x 480. Each has an "empty room" shot, a "person in the room" shot and the true mask of the
person (known, because we draw it). The shots are made hard on purpose, like a real camera:

- sensor noise, different in the two shots;
- a slight lighting change (a little brighter, more on the right);
- a JPEG round trip (the files are JPEG);
- a soft shadow of the person (attached to the feet in scene 1, detached on the wall in scene 2, faint in 3);
- clothes and skin close to the wall's colour (they become holes);
- scene 3 also has a moved object in the background (a speck far from the person) and a thin raised arm.

A short moving take (the person walks across scene 1) stands in for a camera. It is made in memory.

Run:  FUNGROUND_HEADLESS=1 .venv/Scripts/python spikes/14_cutout/make_photos.py
"""
from __future__ import annotations

import io
import random
from dataclasses import dataclass, field
from pathlib import Path

import pygame

W, H = 640, 480
HERE = Path(__file__).parent
SCENES_DIR = HERE / "scenes"
NOISE_AMP = 8          # each channel gets two uniform 0..8 draws added, minus 8: roughly +-8, sd 3.7


# ------------------------------------------------------------------------------------------ small helpers
def _shift_table(amp: int) -> bytes:
    return bytes(b % (amp + 1) for b in range(256))


def add_noise(surface: pygame.Surface, rng: random.Random, amp: int = NOISE_AMP) -> None:
    """Add per-pixel, per-channel noise (a sum of two uniform draws, so roughly bell shaped)."""
    table = _shift_table(amp)
    n = W * H * 3
    for _ in range(2):
        layer = pygame.image.frombytes(rng.randbytes(n).translate(table), (W, H), "RGB")
        surface.blit(layer, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    surface.fill((amp, amp, amp), special_flags=pygame.BLEND_RGB_SUB)


def lighting_change(surface: pygame.Surface, base: int, right: int) -> None:
    """Brighten the picture by *base*, and by up to *base + right* on its right edge (a lamp, or the sun moving)."""
    ramp = pygame.Surface((2, 1))
    ramp.set_at((0, 0), (base, base, base))
    ramp.set_at((1, 0), (base + right, base + right, base + right))
    surface.blit(pygame.transform.smoothscale(ramp, (W, H)), (0, 0), special_flags=pygame.BLEND_RGB_ADD)


def jpeg_round_trip(surface: pygame.Surface) -> tuple[pygame.Surface, bytes]:
    """Save to JPEG in memory and read it back: what a camera's file does to the pixels."""
    buffer = io.BytesIO()
    pygame.image.save(surface, buffer, "shot.jpg")
    data = buffer.getvalue()
    return pygame.image.load(io.BytesIO(data), "shot.jpg"), data


# ------------------------------------------------------------------------------------------ the person
Shape = tuple  # ("poly", colour, points) or ("circle", colour, centre, radius)


def person_shapes(x: int, palette: dict, arm_up: bool = True, step: int = 0) -> list[Shape]:
    """A standing figure about 390 pixels tall, centred on x. *step* swings the legs (for the walking take)."""
    skin, shirt, trousers = palette["skin"], palette["shirt"], palette["trousers"]
    s = step
    shapes: list[Shape] = [
        ("poly", trousers, [(x - 48, 300), (x - 6, 300), (x - 12 - s, 452), (x - 46 - s, 452)]),
        ("poly", trousers, [(x + 6, 300), (x + 48, 300), (x + 46 + s, 452), (x + 12 + s, 452)]),
        ("poly", skin, [(x - 44 - s, 452), (x - 12 - s, 452), (x - 12 - s, 464), (x - 58 - s, 464)]),
        ("poly", skin, [(x + 12 + s, 452), (x + 44 + s, 452), (x + 58 + s, 464), (x + 12 + s, 464)]),
        ("poly", shirt, [(x - 62, 168), (x + 62, 168), (x + 52, 306), (x - 52, 306)]),
        ("poly", shirt, [(x - 64, 172), (x - 40, 172), (x - 66, 300), (x - 88, 296)]),       # hanging arm
        ("circle", skin, (x - 77, 308), 13),
        ("poly", skin, [(x - 12, 140), (x + 12, 140), (x + 14, 172), (x - 14, 172)]),         # neck
        ("circle", skin, (x, 105), 40),                                                       # head
    ]
    if arm_up:      # the thin part: an arm 16 pixels wide, raised, with a hand
        shapes += [("poly", shirt, [(x + 52, 176), (x + 66, 190), (x + 128, 70), (x + 112, 62)]),
                   ("circle", skin, (x + 122, 54), 14)]
    else:
        shapes += [("poly", shirt, [(x + 40, 172), (x + 64, 172), (x + 88, 296), (x + 66, 300)]),
                   ("circle", skin, (x + 77, 308), 13)]
    return shapes


def draw_shapes(surface: pygame.Surface, shapes: list[Shape], scale: int = 1, override=None, offset=(0, 0)) -> None:
    for kind, colour, *geometry in shapes:
        colour = override or colour
        if kind == "poly":
            points = [((px + offset[0]) * scale, (py + offset[1]) * scale) for px, py in geometry[0]]
            pygame.draw.polygon(surface, colour, points)
        else:
            (cx, cy), r = geometry
            pygame.draw.circle(surface, colour, ((cx + offset[0]) * scale, (cy + offset[1]) * scale), r * scale)


def coverage(shapes: list[Shape]) -> bytes:
    """How much of each pixel the person covers (0..255), from a 2 x 2 supersample: soft edges."""
    big = pygame.Surface((W * 2, H * 2))
    draw_shapes(big, shapes, scale=2, override=(255, 255, 255))
    return pygame.image.tobytes(pygame.transform.smoothscale(big, (W, H)), "RGB")[0::3]


def truth_mask(shapes: list[Shape]) -> pygame.mask.Mask:
    """The person: every pixel at least half covered."""
    grey = bytes(v for v in coverage(shapes) for _ in range(3))         # small enough to do once per scene
    surface = pygame.image.frombytes(grey, (W, H), "RGB")
    return pygame.mask.from_threshold(surface, (255, 255, 255), (127, 127, 127, 255))


def paint_person(room: pygame.Surface, shapes: list[Shape], details) -> None:
    """Put the person on the room with soft edges. *details* draws extra pattern on the clothes."""
    layer = pygame.Surface((W, H))
    layer.fill((52, 48, 58))                                           # what an edge pixel shows through to
    draw_shapes(layer, shapes)
    details(layer)
    colours = pygame.image.tobytes(layer, "RGB")
    rgba = bytearray(W * H * 4)
    for channel in range(3):
        rgba[channel::4] = colours[channel::3]
    rgba[3::4] = coverage(shapes)
    room.blit(pygame.image.frombytes(bytes(rgba), (W, H), "RGBA"), (0, 0))


def shadow(room: pygame.Surface, shapes: list[Shape], offset, strength: int, blur: int) -> None:
    """Darken the room where the person's shadow falls: the person's outline moved by *offset* and blurred."""
    grey = pygame.Surface((W, H))
    draw_shapes(grey, shapes, override=(strength,) * 3, offset=offset)
    room.blit(pygame.transform.gaussian_blur(grey, blur), (0, 0), special_flags=pygame.BLEND_RGB_SUB)


# ------------------------------------------------------------------------------------------ the scenes
@dataclass
class Scene:
    name: str
    palette: dict
    paint_room: object                     # (surface, rng) -> None: the empty room
    person_x: int = 320
    arm_up: bool = False
    shadows: list = field(default_factory=list)     # (offset, strength, blur)
    details: object = lambda layer: None            # extra pattern drawn on the person
    moved: object = lambda surface: None            # things that differ in the person's shot (a moved object)
    lighting: tuple = (4, 10)


def room_plain(surface: pygame.Surface, rng: random.Random) -> None:
    surface.fill((186, 176, 160))
    top, bottom = (190, 180, 164), (180, 170, 154)
    ramp = pygame.Surface((1, 2))
    ramp.set_at((0, 0), top)
    ramp.set_at((0, 1), bottom)
    surface.blit(pygame.transform.smoothscale(ramp, (W, 400)), (0, 0))
    pygame.draw.rect(surface, (150, 124, 104), (0, 400, W, H - 400))            # the floor
    pygame.draw.rect(surface, (170, 160, 146), (0, 396, W, 6))                  # skirting board
    pygame.draw.rect(surface, (222, 224, 226), (470, 80, 110, 150))             # a picture frame
    pygame.draw.rect(surface, (150, 170, 190), (478, 88, 94, 134))


def room_stripes(surface: pygame.Surface, rng: random.Random) -> None:
    surface.fill((170, 150, 120))
    for x in range(0, W, 48):
        pygame.draw.rect(surface, (188, 168, 134), (x, 0, 24, 400))
    pygame.draw.rect(surface, (96, 84, 76), (0, 400, W, H - 400))
    for x in range(0, W, 64):
        pygame.draw.line(surface, (84, 72, 64), (x, 400), (x - 40, H), 3)         # floorboards


def room_busy(surface: pygame.Surface, rng: random.Random) -> None:
    surface.fill((205, 198, 182))
    for y in range(0, 400, 20):                                                  # wallpaper dots
        for x in range((y // 20 % 2) * 14, W, 28):
            pygame.draw.circle(surface, (192, 184, 168), (x, y), 4)
    for row in range(4):                                                         # bookshelves on the left and right
        for left in (0, 470):
            x = left
            while x < left + 170:
                book_w, book_h = rng.randint(12, 26), rng.randint(46, 72)
                colour = (rng.randint(60, 220), rng.randint(40, 200), rng.randint(40, 200))
                pygame.draw.rect(surface, colour, (x, 40 + row * 90 + (72 - book_h), book_w, book_h))
                x += book_w + 1
            pygame.draw.rect(surface, (110, 80, 52), (left, 40 + row * 90 + 72, 170, 8))
    pygame.draw.rect(surface, (120, 160, 200), (220, 60, 200, 120))              # a window
    pygame.draw.line(surface, (240, 240, 240), (320, 60), (320, 180), 5)
    pygame.draw.rect(surface, (130, 100, 70), (0, 400, W, H - 400))
    for i in range(8):                                                           # clutter on the floor
        pygame.draw.circle(surface, (rng.randint(80, 230), rng.randint(60, 200), rng.randint(60, 200)),
                           (rng.randint(30, 610), rng.randint(420, 470)), rng.randint(8, 18))


def details_plain(layer: pygame.Surface) -> None:
    pygame.draw.rect(layer, (180, 170, 154), (282, 196, 40, 32))               # a pocket the colour of the wall
    pygame.draw.rect(layer, (188, 178, 162), (250, 168, 100, 14))              # a pale collar band
    pygame.draw.line(layer, (120, 128, 150), (300, 182), (300, 306), 2)        # a seam


def details_stripes(layer: pygame.Surface) -> None:
    for x in range(0, W, 48):                                                  # striped trousers, same stripes as the wall
        pygame.draw.rect(layer, (188, 168, 134), (x - 8, 304, 24, 148))
    pygame.draw.rect(layer, (170, 150, 120), (290, 120, 60, 12))


def moved_books(surface: pygame.Surface) -> None:
    pygame.draw.rect(surface, (230, 120, 60), (500, 60, 40, 60))               # a different book
    pygame.draw.circle(surface, (60, 140, 90), (120, 440), 24)                 # a ball rolled into view


SCENES = [
    Scene("plain_wall", {"skin": (214, 152, 122), "shirt": (140, 150, 172), "trousers": (84, 90, 112)},
          room_plain, person_x=300, shadows=[((40, 4), 26, 12), ((12, 48), 44, 8)], details=details_plain,
          lighting=(3, 6)),
    Scene("striped_wall", {"skin": (206, 160, 128), "shirt": (60, 96, 160), "trousers": (172, 152, 124)},
          room_stripes, person_x=250, shadows=[((230, 4), 44, 14)], details=details_stripes, lighting=(3, 6)),
    Scene("busy_background", {"skin": (208, 164, 134), "shirt": (196, 120, 70), "trousers": (60, 70, 96)},
          room_busy, person_x=320, arm_up=True, shadows=[((26, 4), 20, 8)], moved=moved_books, lighting=(3, 6)),
]


def render_shot(scene: Scene, seed: int, person: bool, x: int | None = None, step: int = 0,
                lighting: tuple | None = None) -> tuple[pygame.Surface, bytes, list[Shape]]:
    """One shot: the room, plus the person and shadow if asked, then lighting, noise and a JPEG round trip.

    The room itself is the same every time (it uses a fixed seed); only the noise (from *seed*) differs."""
    surface = pygame.Surface((W, H))
    scene.paint_room(surface, random.Random(1000 + len(scene.name)))
    shapes: list[Shape] = []
    if person:
        scene.moved(surface)
        shapes = person_shapes(x if x is not None else scene.person_x, scene.palette, scene.arm_up, step)
        for offset, strength, blur in scene.shadows:
            shadow(surface, shapes, offset, strength, blur)
        paint_person(surface, shapes, scene.details)
        base, right = lighting or scene.lighting
        lighting_change(surface, base, right)
    add_noise(surface, random.Random(seed))
    out, data = jpeg_round_trip(surface)
    return out, data, shapes


def make_take(frames: int = 30) -> list[tuple[pygame.Surface, pygame.mask.Mask]]:
    """The moving take: the person walks across scene 1, noise and a light flicker differ in every frame."""
    scene = SCENES[0]
    take = []
    for i in range(frames):
        x = 110 + round(i * 420 / (frames - 1))
        flicker = (2 + i % 3, 6)
        surface, _data, shapes = render_shot(scene, seed=5000 + i, person=True, x=x, step=(i % 6) * 3 - 6,
                                             lighting=flicker)
        take.append((surface, truth_mask(shapes)))
    return take


def main() -> None:
    SCENES_DIR.mkdir(exist_ok=True)
    for index, scene in enumerate(SCENES):
        empty, empty_bytes, _ = render_shot(scene, seed=10 * index + 1, person=False)
        shot, shot_bytes, shapes = render_shot(scene, seed=10 * index + 2, person=True)
        (SCENES_DIR / f"{scene.name}_empty.jpg").write_bytes(empty_bytes)
        (SCENES_DIR / f"{scene.name}_person.jpg").write_bytes(shot_bytes)
        truth = truth_mask(shapes)
        pygame.image.save(truth.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 255)),
                          str(SCENES_DIR / f"{scene.name}_truth.png"))
        print(f"{scene.name}: person {truth.count()} pixels, "
              f"files {len(empty_bytes) // 1024} KB + {len(shot_bytes) // 1024} KB")


if __name__ == "__main__":
    main()
