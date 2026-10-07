"""Play: f.variations, f.keep and the recorded seed (S-132 part 3, a prototype for D-071; no contract row yet)."""
from __future__ import annotations

import importlib
import json
import pkgutil
from pathlib import Path

import pygame
import pytest

import funground as f
from funground import api, exploring, ir, typography
from funground.marks import Mark
from funground.platform.base import InputEvent
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

from conftest import LiveCanvas

PACKAGE = Path(f.__file__).resolve().parent


def labels(sketch) -> list[ir.Text]:
    return [op for op in sketch.frame.ops if type(op) is ir.Text]


def circles(mark: Mark) -> list[tuple[float, float]]:
    return [(op.x, op.y) for op in mark._ops if type(op) is ir.Circle]


def run_file(tmp_path: Path, source: str, name: str = "sketch.py") -> dict:
    """Run *source* as a sketch file in *tmp_path*, so keep() finds it there."""
    path = tmp_path / name
    path.write_text(source, encoding="utf-8")
    namespace = {"__name__": "__main__", "__file__": str(path)}
    exec(compile(source, str(path), "exec"), namespace)
    return namespace


@pytest.fixture(autouse=True)
def _headless(monkeypatch, tmp_path):
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    monkeypatch.chdir(tmp_path)
    typography.files_read.clear()
    yield
    typography.files_read.clear()


# ---------------------------------------------------------------- variations: layout and labels
def test_one_parameter_in_a_wide_content_area_is_one_row(sketch):
    # The layout makes the cells largest. Cells have the canvas's shape, so a row wins only when the
    # area (here, inside wide top and bottom margins) is much wider than the canvas.
    f.size(800, 400, margin=(150, 0, 150, 0))
    result = f.variations(lambda gap: f.circle(gap, 100, 20), gap=[10, 20, 30, 40])
    assert len(result) == 4
    found = labels(sketch)
    assert [t.text for t in found] == ["gap = 10", "gap = 20", "gap = 30", "gap = 40"]
    assert len({round(t.y) for t in found}) == 1           # one row
    assert len({round(t.x) for t in found}) == 4


def test_one_parameter_on_a_square_canvas_wraps_into_a_near_square_grid(sketch):
    f.size(600, 600)
    f.variations(lambda n: f.circle(300, 300, n), n=[10, 20, 30, 40])
    found = labels(sketch)
    assert len({round(t.y) for t in found}) == 2 and len({round(t.x) for t in found}) == 2


def test_two_parameters_give_rows_for_the_first_and_columns_for_the_second(sketch):
    f.size(600, 400)
    result = f.variations(lambda a, b: f.circle(a, b, 10), a=[1, 2], b=[10, 20, 30])
    assert [values for values, _ in result] == [{"a": 1, "b": 10}, {"a": 1, "b": 20}, {"a": 1, "b": 30},
                                                {"a": 2, "b": 10}, {"a": 2, "b": 20}, {"a": 2, "b": 30}]
    found = labels(sketch)
    assert found[0].text == "a = 1, b = 10" and found[-1].text == "a = 2, b = 30"
    assert len({round(t.y) for t in found}) == 2           # rows: a
    assert len({round(t.x) for t in found}) == 3           # columns: b
    assert found[0].y == found[2].y and found[0].x == found[3].x


def test_cells_cover_the_content_area_inside_the_margins(sketch):
    f.size(400, 200, margin=30)
    f.variations(lambda k: None, k=[1, 2])
    for t in labels(sketch):
        assert 30 <= t.x <= 370 and 30 <= t.y <= 170


def test_labels_show_floats_and_text_plainly():
    assert exploring.label_of({"gap": 35}) == "gap = 35"
    assert exploring.label_of({"scale": 0.5, "colour": "tomato"}) == "scale = 0.5, colour = tomato"


# ---------------------------------------------------------------- variations: seed, isolation, clipping
def dots(size):
    for _ in range(6):
        f.circle(f.random(f.width), f.random(f.height), size)


def test_every_cell_starts_from_the_same_seed(sketch):
    f.size(400, 200)
    f.random_seed(21)
    result = f.variations(dots, size=[4, 8, 16])
    first = circles(result[0][1])
    assert len(first) == 6
    assert all(circles(m) == first for _, m in result)
    f.random_seed(21)
    assert first == [(f.random(400), f.random(200)) for _ in range(6)]     # the learner's seed itself


def test_variations_leaves_the_random_sequence_where_it_was(sketch):
    f.size(400, 200)
    f.random_seed(5)
    f.random()
    expected = Sketch.random(sketch, 0, 1)                # what comes next without variations
    f.random_seed(5)
    f.random()
    f.variations(dots, size=[4, 8])
    assert f.random(0, 1) == expected


def test_one_cells_style_and_transform_cannot_reach_the_next(sketch):
    f.size(400, 200)
    f.fill("navy")

    def leaky(k):
        if k == 1:
            f.fill("red")
            f.stroke_width(9)
            f.translate(100, 50)
        f.circle(0, 0, 10)

    result = f.variations(leaky, k=[1, 2])
    second = result[1][1]._ops
    assert not any(type(op) is ir.Concat for op in second)
    circle = next(op for op in second if type(op) is ir.Circle)
    assert circle.style.fill.rgba[:3] == (0, 0, 128) and circle.style.stroke_width == 1
    assert sketch.style.fill.rgba[:3] == (0, 0, 128)        # and nothing leaked out to the canvas


def test_each_cell_is_clipped_to_its_picture():
    pygame.init()
    f.size(400, 200)
    canvas = LiveCanvas(api.active_sketch())
    f.background("white")

    def flood(k):
        f.fill("red")
        f.no_stroke()
        f.rect(-1000, -1000, 3000, 3000)

    f.variations(flood, k=[1, 2])
    # Two cells side by side: pictures 195 x 97.5 at x = 0 and x = 205, y = 43.25 (see exploring's layout).
    assert canvas.get_at((100, 90))[:3] == (255, 0, 0)
    assert canvas.get_at((300, 90))[:3] == (255, 0, 0)
    assert canvas.get_at((201, 90))[:3] == (255, 255, 255)      # the gutter between the cells
    assert canvas.get_at((100, 20))[:3] == (255, 255, 255)      # above the pictures
    assert canvas.get_at((100, 170))[:3] == (255, 255, 255)     # the label strip, below


def test_background_in_the_study_paints_only_its_cell():
    pygame.init()
    f.size(400, 200)
    canvas = LiveCanvas(api.active_sketch())
    f.background("white")
    f.variations(lambda k: f.background("black"), k=[1, 2])
    assert canvas.get_at((100, 90))[:3] == (0, 0, 0)
    assert canvas.get_at((201, 90))[:3] == (255, 255, 255)


def test_every_cell_is_scaled_by_the_same_amount(sketch):
    f.size(400, 200)
    f.variations(lambda w: f.rect(0, 0, w, 10), w=[50, 300])
    places = [op.transform for op in sketch.frame.ops if type(op) is ir.Concat]
    assert len(places) == 2 and places[0].a == pytest.approx(places[1].a) == pytest.approx(0.4875)


# ---------------------------------------------------------------- variations: return value and errors
def test_the_result_is_values_and_marks_you_can_place(sketch):
    f.size(400, 200)
    result = f.variations(lambda r: f.circle(200, 100, r), r=[10, 40])
    assert [type(m) for _, m in result] == [Mark, Mark]
    values, chosen = result[1]
    assert values == {"r": 40}
    before = len(sketch.frame.ops)
    chosen.place(0, 0)
    assert len(sketch.frame.ops) > before


def test_three_parameters_are_refused_with_advice(sketch):
    f.size(400, 200)
    with pytest.raises(ValueError, match="one or two parameters.*Fix the others"):
        f.variations(lambda a, b, c: None, a=[1], b=[2], c=[3])


@pytest.mark.parametrize("call, error", [
    (lambda: f.variations(lambda: None), ValueError),
    (lambda: f.variations(lambda gap: None, gap=35), TypeError),
    (lambda: f.variations(lambda gap: None, gap="35"), TypeError),
    (lambda: f.variations(lambda gap: None, gap=[]), ValueError),
    (lambda: f.variations("study", gap=[1]), TypeError),
])
def test_bad_calls_are_explained(sketch, call, error):
    f.size(400, 200)
    with pytest.raises(error, match="f.variations"):
        call()


def test_an_error_in_the_study_leaves_the_canvas_as_it_was(sketch):
    f.size(400, 200)
    f.fill("navy")

    def broken(k):
        f.fill("red")
        f.translate(5, 5)
        raise ZeroDivisionError

    with pytest.raises(ZeroDivisionError):
        f.variations(broken, k=[1, 2])
    assert sketch.style.fill.rgba[:3] == (0, 0, 128)
    assert not exploring._cells
    f.background("white")                                    # not refused: no mark or cell is left open


def test_variations_in_setup_and_in_draw():
    def draw():
        f.background("white")
        f.variations(dots, size=[4, 8])

    sketch = api.active_sketch()
    sketch.run_namespace({"setup": lambda: (f.size(300, 200), f.variations(dots, size=[3])), "draw": draw},
                         max_frames=3)
    assert sketch.frame_count == 3
    assert [op.text for op in sketch.last_ops if type(op) is ir.Text] == ["size = 4", "size = 8"]


# ---------------------------------------------------------------- keep
KEEP_SCRIPT = """
import funground as f
f.size(200, 100, margin=10)
f.random_seed(77)
f.background("white")
f.circle(100, 50, 40)
first = f.keep("one", gap=35)
f.circle(20, 20, 10)
second = f.keep("two", pdf=True, colours=["red", "blue"], scale=0.5)
"""


def test_keep_numbers_continue_across_calls_and_existing_files(tmp_path, capsys):
    ns = run_file(tmp_path, KEEP_SCRIPT)
    studio = tmp_path / "studio"
    assert ns["first"] == str(studio / "001") and ns["second"] == str(studio / "002")
    assert sorted(p.name for p in studio.iterdir()) == ["001.json", "001.png", "001.py",
                                                         "002.json", "002.pdf", "002.png", "002.py"]
    assert "kept" in capsys.readouterr().out
    (studio / "041.png").write_bytes(b"")                    # a gap and a higher number already there
    api.use_sketch(Sketch())
    ns = run_file(tmp_path, KEEP_SCRIPT)
    assert ns["first"].endswith("042") and ns["second"].endswith("043")


def test_keep_writes_a_copy_of_the_source_and_a_picture(tmp_path):
    run_file(tmp_path, KEEP_SCRIPT)
    studio = tmp_path / "studio"
    assert (studio / "001.py").read_text(encoding="utf-8") == KEEP_SCRIPT
    assert (studio / "001.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert (studio / "002.pdf").read_bytes()[:5] == b"%PDF-"
    assert not (studio / "001.pdf").exists()


def test_keep_record_fields(tmp_path):
    run_file(tmp_path, KEEP_SCRIPT)
    record = json.loads((tmp_path / "studio" / "002.json").read_text(encoding="utf-8"))
    assert record["note"] == "two"
    assert record["settings"] == {"colours": ["red", "blue"], "scale": 0.5}
    assert record["seed"] == 77 and record["seed_chosen_by"] == "you"
    assert record["size"] == [200, 100] and record["margin"] == [10, 10, 10, 10]
    assert record["page"] == 1 and record["frame_count"] is None
    assert record["sketch"] == "sketch.py"
    assert record["funground"] == f.__version__
    for key in ("date", "python", "platform", "fonts_used", "files_read", "not_captured", "controls",
                "noise_seed"):
        assert key in record
    assert record["not_captured"] and all(isinstance(s, str) for s in record["not_captured"])


def test_keep_records_files_read_and_fonts_used(tmp_path):
    (tmp_path / "shape.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20">'
                                        '<rect width="10" height="10"/></svg>', encoding="utf-8")
    font = PACKAGE / "fonts" / "DejaVuSans-Bold.ttf"
    run_file(tmp_path, f"""
import funground as f
f.size(200, 100)
f.image(f.load_svg("shape.svg"), 0, 0)
f.text_font(f.load_font({str(font)!r}), 14)
f.text("hi", 10, 10)
f.keep()
""")
    record = json.loads((tmp_path / "studio" / "001.json").read_text(encoding="utf-8"))
    read = {r["path"]: r for r in record["files_read"]}
    assert read["shape.svg"]["kind"] == "SVG" and read["shape.svg"]["bytes"] == (tmp_path / "shape.svg").stat().st_size
    assert read[str(font)]["kind"] == "font"
    assert [(u["family"], u["file"]) for u in record["fonts_used"]] == [("DejaVu Sans", "DejaVuSans-Bold.ttf")]


class KeyAt(HeadlessPlatform):
    def __init__(self, at: int, key: str) -> None:
        super().__init__()
        self.at, self.key, self.polls = at, key, 0

    def poll(self):
        if self.polls == self.at:
            self.post(InputEvent("key_pressed", key=self.key, key_code=ord(self.key)))
        self.polls += 1
        return super().poll()


def test_keep_from_key_pressed_keeps_the_frame_with_controls(tmp_path):
    source = """
import funground as f

def setup():
    global spin, solid
    f.size(120, 80)
    spin = f.create_slider(0, 10, 3, label="spin")
    solid = f.create_checkbox("solid", True)

def draw():
    f.background("white")
    f.circle(60, 40, 30)

def key_pressed():
    if f.key == "k":
        f.keep("from a key")
"""
    path = tmp_path / "anim.py"
    path.write_text(source, encoding="utf-8")
    sketch = api.use_sketch(Sketch(platform=KeyAt(2, "k")))
    ns = {"__name__": "__main__", "__file__": str(path)}
    exec(compile(source, str(path), "exec"), ns)
    sketch.run_namespace(ns, max_frames=4)
    record = json.loads((tmp_path / "studio" / "001.json").read_text(encoding="utf-8"))
    assert record["controls"] == [{"kind": "slider", "label": "spin", "value": 3},
                                  {"kind": "checkbox", "label": "solid", "value": True}]
    assert record["frame_count"] == 2 and record["page"] is None
    assert (tmp_path / "studio" / "001.png").read_bytes()[:4] == b"\x89PNG"


def test_keep_is_refused_inside_a_mark(sketch):
    f.size(200, 100)
    with pytest.raises(RuntimeError, match=r"f\.keep\(\) cannot be used inside"):
        with f.mark():
            f.keep("no")


def test_keep_is_refused_inside_a_variations_cell(sketch):
    f.size(200, 100)
    with pytest.raises(RuntimeError, match=r"f\.keep\(\)"):
        f.variations(lambda k: f.keep("no"), k=[1])


def test_keep_needs_text_for_the_note(tmp_path):
    with pytest.raises(TypeError, match="note is text"):
        run_file(tmp_path, "import funground as f\nf.size(100, 100)\nf.keep(35)\n")


# ---------------------------------------------------------------- the recorded seed
def test_a_run_without_random_seed_records_one_that_repeats_it():
    sketch = api.use_sketch(Sketch())                         # fresh: no random_seed() call
    assert sketch._seed_chosen_by == "funground" and isinstance(sketch._seed, int)
    seed = sketch._seed
    first = [f.random(100) for _ in range(5)]
    api.use_sketch(Sketch())
    f.random_seed(seed)
    assert [f.random(100) for _ in range(5)] == first


def test_random_seed_none_still_records_a_seed():
    f.random_seed(None)
    sketch = api.canvas_sketch()
    seed, first = sketch._seed, [f.random() for _ in range(3)]
    assert sketch._seed_chosen_by == "funground"
    f.random_seed(seed)
    assert [f.random() for _ in range(3)] == first


def test_unseeded_noise_records_a_seed_that_repeats_it():
    sketch = api.use_sketch(Sketch())
    first = [f.noise(i * 0.1, 2.5) for i in range(10)]
    seed = sketch._noise.seed_value
    assert sketch._noise.seed_chosen_by == "funground" and isinstance(seed, int)
    api.use_sketch(Sketch())
    f.noise_seed(seed)
    assert [f.noise(i * 0.1, 2.5) for i in range(10)] == first


def test_the_recorded_seeds_do_not_touch_pythons_random_module():
    import random

    random.seed(3)
    expected = random.random()
    random.seed(3)
    api.use_sketch(Sketch())
    f.random_seed(None)
    f.noise(1.5)
    assert random.random() == expected


def test_keep_records_the_automatic_seed(tmp_path):
    api.use_sketch(Sketch())
    run_file(tmp_path, "import funground as f\nf.size(100, 100)\nf.noise(0.3)\nf.keep()\n")
    record = json.loads((tmp_path / "studio" / "001.json").read_text(encoding="utf-8"))
    sketch = api.canvas_sketch()
    assert record["seed"] == sketch._seed and record["seed_chosen_by"] == "funground"
    assert record["noise_seed"] == sketch._noise.seed_value and record["noise_seed_chosen_by"] == "funground"


# ---------------------------------------------------------------- both forms and the naming trap
def test_the_namespace_holds_the_same_two_functions():
    assert f.play.variations is f.variations and f.play.keep is f.keep
    assert "play" in f.__all__ and "variations" in f.__all__ and "keep" in f.__all__


def test_both_forms_draw_the_same_sheet(sketch):
    f.size(300, 200)
    f.variations(dots, size=[4, 8])
    flat = list(sketch.frame.ops)
    sketch.frame.clear()
    f.play.variations(dots, size=[4, 8])
    assert list(sketch.frame.ops) == flat


def test_no_submodule_hides_a_public_name():
    """A submodule is set as an attribute of the package when it is imported, so a funground/play.py would
    replace f.play. The two old clashes, color and noise, are re-bound by __init__ after their modules load."""
    modules = {m.name for m in pkgutil.iter_modules([str(PACKAGE)])}
    assert not {"play", "variations", "keep"} & modules
    assert modules & set(f.__all__) == {"color", "noise"}
    assert (PACKAGE / "exploring.py").exists()
    for name in sorted(modules):
        importlib.import_module(f"funground.{name}")
    assert isinstance(f.play, api.Play)
    assert callable(f.variations) and callable(f.keep)
