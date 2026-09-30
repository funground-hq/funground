"""Tests for tools/check_originality.py.

All corpora here are synthetic sketches written for this test file; nothing is pasted
from a real project. No network use.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import check_originality as co  # noqa: E402

TOOL = Path(__file__).resolve().parent.parent / "tools" / "check_originality.py"

# A small p5.js sketch: a ball that bounces off the floor, with a comment and magic numbers.
JS_BOUNCE = """\
let ballY = 50;
let ballSpeed = 0;
let ballGravity = 0.6;

function setup() {
  createCanvas(400, 300);
}

function draw() {
  // the ball falls under gravity and bounces off the floor
  background(220);
  ballSpeed = ballSpeed + ballGravity;
  ballY = ballY + ballSpeed;
  if (ballY > 250) {
    ballY = 250;
    ballSpeed = ballSpeed * -0.8;
  }
  noStroke();
  fill(255, 0, 0);
  ellipse(200, ballY, 40, 40);
  rect(0, 280, 400, 20);
}
"""

# A faithful Python translation: same calls, same numbers, same comment, renamed to snake_case.
PY_BOUNCE_FAITHFUL = """\
import funground as f

ball_y = 50
ball_speed = 0
ball_gravity = 0.6


def setup():
    f.size(400, 300)


def draw():
    # the ball falls under gravity and bounces off the floor
    global ball_y, ball_speed
    f.background(220)
    ball_speed = ball_speed + ball_gravity
    ball_y = ball_y + ball_speed
    if ball_y > 250:
        ball_y = 250
        ball_speed = ball_speed * -0.8
    f.no_stroke()
    f.fill(255, 0, 0)
    f.ellipse(200, ball_y, 40, 40)
    f.rect(0, 280, 400, 20)
"""

# Same calls and numbers, but every name and the comment have been changed.
PY_BOUNCE_RENAMED = """\
import funground as f

drop_height = 50
fall_rate = 0
pull = 0.6


def setup():
    f.size(400, 300)


def draw():
    # a dropped shape settles after a few bounces near the bottom edge
    global drop_height, fall_rate
    f.background(220)
    fall_rate = fall_rate + pull
    drop_height = drop_height + fall_rate
    if drop_height > 250:
        drop_height = 250
        fall_rate = fall_rate * -0.8
    f.no_stroke()
    f.fill(255, 0, 0)
    f.ellipse(200, drop_height, 40, 40)
    f.rect(0, 280, 400, 20)
"""

# Two independent sketches that only share the common vocabulary of the craft.
PY_UNRELATED_A = """\
import funground as f

phase = 0.0


def setup():
    f.size(640, 400)


def draw():
    global phase
    # a slow colour wash across the whole canvas
    f.background("white")
    for column in range(0, f.width, 20):
        shade = 128 + 100 * f.sin(phase + column * 0.01)
        f.fill((shade, 60, 200 - shade / 2))
        f.rect(column, 0, 20, f.height)
    phase += 0.02
    f.circle(60, 60, 10)
"""

PY_UNRELATED_B = """\
import funground as f

particles = []


def setup():
    f.size(640, 400)
    f.random_seed(7)
    for _ in range(30):
        particles.append([f.random(0, f.width), f.random(0, f.height)])


def draw():
    # scattered dots that drift sideways and wrap around the window
    f.background("black")
    f.no_stroke()
    for spot in particles:
        spot[0] += 1.5
        if spot[0] > f.width:
            spot[0] = 0
        f.fill("gold")
        f.circle(spot[0], spot[1], 6)
"""


def write(root: Path, name: str, content: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_faithful_translation_is_flagged(tmp_path):
    corpus_dir = tmp_path / "corpus"
    write(corpus_dir, "sketches/bounce.js", JS_BOUNCE)

    ours = co.CodeUnit("bounce.py", PY_BOUNCE_FAITHFUL)
    corpus_units = co.iter_corpus_units(corpus_dir)
    results = co.compare_all([ours], corpus_units)

    assert len(results) == 1
    assert results[0].flagged, results[0].comparison


def test_renamed_translation_is_still_flagged(tmp_path):
    corpus_dir = tmp_path / "corpus"
    write(corpus_dir, "sketches/bounce.js", JS_BOUNCE)

    ours = co.CodeUnit("bounce.py", PY_BOUNCE_RENAMED)
    corpus_units = co.iter_corpus_units(corpus_dir)
    results = co.compare_all([ours], corpus_units)

    assert results[0].flagged, results[0].comparison
    # Renaming should have driven the identifier overlap down even though it's still flagged.
    assert results[0].comparison.identifiers_jaccard < 0.5


def test_unrelated_sketches_sharing_common_vocabulary_are_not_flagged(tmp_path):
    corpus_dir = tmp_path / "corpus"
    write(corpus_dir, "sketches/a.py", PY_UNRELATED_A)

    ours = co.CodeUnit("b.py", PY_UNRELATED_B)
    corpus_units = co.iter_corpus_units(corpus_dir)
    results = co.compare_all([ours], corpus_units)

    assert not results[0].flagged, results[0].comparison


def test_code_inside_markdown_fence_is_found(tmp_path):
    corpus_dir = tmp_path / "corpus"
    markdown = f"""# A sketch

Here is a bouncing ball example:

```js
{JS_BOUNCE}
```

Some more prose.
"""
    write(corpus_dir, "guide/bounce.md", markdown)

    corpus_units = co.iter_corpus_units(corpus_dir)
    labels = [u.label for u in corpus_units]
    assert any("bounce.md#fence1" in label for label in labels)
    # The extracted block should contain the call it came from.
    fenced = next(u for u in corpus_units if "fence1" in u.label)
    assert "createCanvas" in fenced.text


def test_guide_code_blocks_are_included_by_default():
    units = co.default_our_units()
    labels = [u.label for u in units]
    assert any(label.startswith("examples/") for label in labels)
    assert any(label.startswith("docs/guide/") and "#fence" in label for label in labels)
    # Every example .py file under examples/ should be present.
    example_files = sorted((co.ROOT / "examples").rglob("*.py"))
    assert len(example_files) == len([label for label in labels if label.startswith("examples/")])


def test_exit_code_zero_when_nothing_flagged(tmp_path):
    corpus_dir = tmp_path / "corpus"
    write(corpus_dir, "sketches/a.py", PY_UNRELATED_A)
    ours_path = write(tmp_path / "ours", "b.py", PY_UNRELATED_B)

    result = subprocess.run(
        [sys.executable, str(TOOL), "--corpus", str(corpus_dir), str(ours_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_exit_code_one_and_markdown_report_when_flagged(tmp_path):
    corpus_dir = tmp_path / "corpus"
    write(corpus_dir, "sketches/bounce.js", JS_BOUNCE)
    ours_path = write(tmp_path / "ours", "bounce.py", PY_BOUNCE_FAITHFUL)
    report_path = tmp_path / "report.md"

    result = subprocess.run(
        [sys.executable, str(TOOL), "--corpus", str(corpus_dir), "--report", str(report_path), str(ours_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert report_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    assert "bounce.py" in report_text
    assert "YES" in report_text


def test_no_corpus_given_is_a_usage_error(tmp_path):
    ours_path = write(tmp_path / "ours", "b.py", PY_UNRELATED_B)
    result = subprocess.run(
        [sys.executable, str(TOOL), str(ours_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
