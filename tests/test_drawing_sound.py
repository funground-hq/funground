"""Drawing sound (S-111; contract A7; D-061).

draw_wave, draw_spectrum and draw_pitch_line draw with ordinary drawing calls, so the tests read the ops
they record. spectrogram makes a picture from pixels. Time is driven by replacing `funground.sound.clock`
(as in test_making_sound.py), so nothing sleeps. No real device is opened.
"""
from __future__ import annotations

import math

import pytest

import funground as f
from funground import api, ir, sound as sound_module
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

RATE = 44100


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds: float):
        self.now += seconds


@pytest.fixture
def clock(monkeypatch):
    fake = FakeClock()
    monkeypatch.setattr(sound_module, "clock", fake)
    return fake


@pytest.fixture(autouse=True)
def headless(monkeypatch):
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")


def script(w=400, h=300) -> Sketch:
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.size(w, h)
    return s


def sine(hz, seconds=1.0, amp=0.5):
    return [amp * math.sin(2 * math.pi * hz * i / RATE) for i in range(int(seconds * RATE))]


def ops_of(kind, sketch=None):
    return [op for op in (sketch or api.active_sketch()).frame.ops if isinstance(op, kind)]


def points(path):
    return [seg[1] for seg in path.segments if seg[0] in ("move", "line")]


class Singer:
    """A stand-in source: pitch() gives the next number in the list."""

    def __init__(self, pitches):
        self.pitches = list(pitches)

    def pitch(self):
        return self.pitches.pop(0) if self.pitches else None


# ---------------------------------------------------------------- draw_wave
def test_a_tone_is_drawn_inside_its_box_at_its_own_height():
    script()
    snd = f.create_sound(sine(440, amp=0.5))
    f.draw_wave(snd, 10, 20, 100, 40)
    fills = ops_of(ir.FillPath)
    assert len(fills) == 1
    pts = points(fills[0].path)
    assert len(pts) == 200                                    # a top and a bottom point for each column
    assert all(10 <= x <= 110 and 20 <= y <= 60 for x, y in pts)
    assert min(y for _, y in pts) == pytest.approx(30, abs=0.3)      # half the height: a quarter of the box
    assert max(y for _, y in pts) == pytest.approx(50, abs=0.3)
    assert min(x for x, _ in pts) == pytest.approx(10.5) and max(x for x, _ in pts) == pytest.approx(109.5)


def test_the_wave_uses_the_current_fill_and_stroke():
    script()
    f.fill(255, 0, 0)
    f.stroke(0, 0, 255)
    f.stroke_width(3)
    f.draw_wave(f.create_sound(sine(220)), 0, 0, 50, 20)
    assert ops_of(ir.FillPath)[0].color.rgba == (255, 0, 0, 255)
    stroke = ops_of(ir.StrokePath)[0]
    assert stroke.color.rgba == (0, 0, 255, 255) and stroke.width == 3


def test_the_playhead_moves_with_the_clock(clock):
    script()
    snd = f.create_sound(sine(440, seconds=2.0))
    f.draw_wave(snd, 10, 20, 100, 40)
    assert ops_of(ir.Line) == []                              # not playing: no playhead
    snd.play()
    api.active_sketch().frame.clear()
    f.draw_wave(snd, 10, 20, 100, 40)
    first = ops_of(ir.Line)[-1]
    clock.advance(0.5)
    api.active_sketch().frame.clear()
    f.draw_wave(snd, 10, 20, 100, 40)
    second = ops_of(ir.Line)[-1]
    assert (first.x1, first.y1, first.x2, first.y2) == (10, 20, 10, 60)
    assert (second.x1, second.y1, second.x2, second.y2) == (35, 20, 35, 60)   # a quarter of 2 s in
    clock.advance(5)                                          # finished: the sound has stopped
    api.active_sketch().frame.clear()
    f.draw_wave(snd, 10, 20, 100, 40)
    assert ops_of(ir.Line) == []


def test_a_list_of_samples_is_drawn_and_has_no_playhead():
    script()
    f.draw_wave([0, 1, 0, -1] * 25, 0, 0, 40, 20)
    pts = points(ops_of(ir.FillPath)[0].path)
    assert len(pts) == 80 and min(y for _, y in pts) == 0 and max(y for _, y in pts) == 20
    assert ops_of(ir.Line) == []


def test_a_microphone_draws_the_last_half_second():
    script()
    mic = f.microphone()
    mic.start()
    mic._feed(sine(100, seconds=0.1, amp=1.0))                # loud, then (below) it is overwritten...
    mic._feed([0.0] * (RATE // 2))                            # ...by half a second of silence
    f.draw_wave(mic, 0, 0, 50, 20)
    pts = points(ops_of(ir.FillPath)[0].path)
    assert all(y == pytest.approx(10) for _, y in pts)        # all quiet: a flat line in the middle
    mic._feed(sine(100, seconds=0.5, amp=1.0))
    api.active_sketch().frame.clear()
    f.draw_wave(mic, 0, 0, 50, 20)
    pts = points(ops_of(ir.FillPath)[0].path)
    assert min(y for _, y in pts) == pytest.approx(0, abs=0.3)


def test_a_silent_headless_microphone_draws_a_flat_line():
    script()
    mic = f.microphone()
    mic.start()
    f.draw_wave(mic, 0, 0, 30, 10)
    assert {y for _, y in points(ops_of(ir.FillPath)[0].path)} == {5}


def test_a_sounds_envelope_is_made_once_for_each_width():
    script()
    snd = f.create_sound(sine(300))
    calls = []
    real = snd.samples
    snd.samples = lambda: calls.append(1) or real()
    f.draw_wave(snd, 0, 0, 100, 20)
    f.draw_wave(snd, 5, 5, 100, 20)                           # same width, other place: the cache is used
    assert len(calls) == 1
    f.draw_wave(snd, 0, 0, 60, 20)
    assert len(calls) == 2


def test_draw_wave_checks_its_arguments():
    script()
    with pytest.raises(ValueError, match="sound, a microphone or a list"):
        f.draw_wave(42, 0, 0, 10, 10)
    with pytest.raises(ValueError, match="empty"):
        f.draw_wave([], 0, 0, 10, 10)
    with pytest.raises(ValueError, match="w and h must be more than 0"):
        f.draw_wave([0.5], 0, 0, 0, 10)
    with pytest.raises(ValueError, match="x must be a number"):
        f.draw_wave([0.5], "a", 0, 10, 10)


# ---------------------------------------------------------------- draw_spectrum
def test_spectrum_bar_heights_match_spectrum(clock):
    script()
    snd = f.create_sound(sine(440, seconds=1.0, amp=0.8))
    snd.play()
    clock.advance(0.5)
    expected = snd.spectrum(16)
    assert max(expected) > 0.5
    f.draw_spectrum(snd, 10, 20, 160, 50, bands=16)
    bars = ops_of(ir.Rect)
    assert len(bars) == 16
    for i, (bar, v) in enumerate(zip(bars, expected)):
        assert bar.height == pytest.approx(50 * v)
        assert bar.y + bar.height == pytest.approx(70)         # standing on the bottom of the box
        assert bar.x == pytest.approx(10 + i * 10)


def test_bars_stand_on_the_box_even_in_centre_rect_mode(clock):
    script()
    snd = f.create_sound(sine(440))
    snd.play()
    clock.advance(0.2)
    f.rect_mode("center")
    f.draw_spectrum(snd, 0, 0, 64, 10)
    assert ops_of(ir.Rect)[0].x == 0
    f.rect(50, 50, 4, 4)
    assert ops_of(ir.Rect)[-1].x == 48                        # and the mode is still centre afterwards


def test_a_sound_that_is_not_playing_gives_flat_bars():
    script()
    f.draw_spectrum(f.create_sound(sine(440)), 0, 0, 32, 10, bands=4)
    assert [bar.height for bar in ops_of(ir.Rect)] == [0, 0, 0, 0]


def test_draw_spectrum_checks_the_source_and_bands():
    script()
    with pytest.raises(ValueError, match="sound or a microphone"):
        f.draw_spectrum([0.1, 0.2], 0, 0, 10, 10)
    with pytest.raises(ValueError, match="bands"):
        f.draw_spectrum(f.create_sound(sine(440)), 0, 0, 10, 10, bands=0)


# ---------------------------------------------------------------- spectrogram
def brightest_row(picture, column):
    values = [picture.get(column, row).r for row in range(picture.height)]
    return max(range(len(values)), key=values.__getitem__), max(values)


def test_spectrogram_is_a_picture_of_the_right_size_with_the_tone_at_the_right_height():
    script()
    snd = f.create_sound(sine(440, seconds=1.0, amp=0.8))
    picture = f.spectrogram(snd, 60, 100)
    assert (picture.width, picture.height) == (60, 100)
    row, value = brightest_row(picture, 30)
    expected = 100 - 100 * math.log(440 / 40) / math.log(16000 / 40)
    assert abs(row - expected) <= 3
    assert value > 200
    assert picture.get(30, 5).r < 30                          # far above the tone: dark
    assert picture.get(30, 30).r < 80
    assert picture.get(30, row).a == 255


def test_a_higher_tone_is_higher_in_the_picture():
    script()
    low = brightest_row(f.spectrogram(f.create_sound(sine(220)), 10, 120), 5)[0]
    high = brightest_row(f.spectrogram(f.create_sound(sine(1760)), 10, 120), 5)[0]
    assert high < low                                         # row 0 is the top
    octave = 120 * math.log(2) / math.log(400)
    assert (low - high) == pytest.approx(3 * octave, abs=4)


def test_time_runs_across_a_tone_then_silence():
    script()
    snd = f.sequence(f.create_sound(sine(440, seconds=0.5, amp=0.8)), f.create_sound([0.0] * (RATE // 2)))
    picture = f.spectrogram(snd, 40, 80)
    assert brightest_row(picture, 5)[1] > 150                 # the tone is on the left
    assert brightest_row(picture, 35)[1] == 0                 # silence on the right is black


def test_spectrogram_brightest_colour_is_the_current_fill():
    script()
    f.fill(255, 128, 0)
    picture = f.spectrogram(f.create_sound(sine(440, amp=0.9)), 10, 60)
    row, _ = brightest_row(picture, 5)
    c = picture.get(5, row)
    assert c.r > 200 and 0.4 < c.g / c.r < 0.6 and c.b == 0


def test_spectrogram_is_a_sound_made_at_any_rate():
    script()
    values = [0.8 * math.sin(2 * math.pi * 440 * i / 8000) for i in range(8000)]
    picture = f.spectrogram(f.create_sound(values, rate=8000), 10, 100)
    row, _ = brightest_row(picture, 5)
    assert abs(row - (100 - 100 * math.log(440 / 40) / math.log(400))) <= 3
    assert picture.get(5, 5).r == 0                           # above 4 kHz a sound at 8 kHz holds nothing


def test_spectrogram_checks_its_arguments():
    script()
    with pytest.raises(ValueError, match="give it a sound"):
        f.spectrogram([0.1], 10, 10)
    with pytest.raises(ValueError, match="width must be a whole number"):
        f.spectrogram(f.create_sound(sine(440)), 0, 10)


def test_spectrogram_inside_a_layer_still_makes_a_picture():
    script()
    snd = f.create_sound(sine(440))
    with f.layer("a"):
        picture = f.spectrogram(snd, 8, 8)
    assert (picture.width, picture.height) == (8, 8)


# ---------------------------------------------------------------- draw_pitch_line
A4_DOWN = 1 - math.log2(440 / 130.8127826502993) / 3          # how far down the box an A4 is


def feed(source, count, clock, step=0.1, **kw):
    for _ in range(count):
        api.active_sketch().frame.clear()
        f.draw_pitch_line(source, 10, 20, 200, 100, **kw)
        clock.advance(step)


def test_a_fed_pitch_is_drawn_at_its_height_on_the_note_scale(clock):
    script()
    singer = Singer([440, 440, 440])
    feed(singer, 3, clock, seconds=5)
    strokes = [op for op in ops_of(ir.StrokePath) if len(points(op.path)) >= 2]
    assert len(strokes) == 1
    ys = {round(y, 6) for _, y in points(strokes[0].path)}
    assert ys == {round(20 + 100 * A4_DOWN, 6)}
    xs = [x for x, _ in points(strokes[0].path)]
    assert xs == sorted(xs) and xs[-1] == pytest.approx(210)    # the newest reading is "now": the right edge


def test_low_and_high_notes_are_the_bottom_and_top_of_the_box(clock):
    script()
    f.draw_pitch_line(Singer([f.note_to_frequency("C3")]), 0, 0, 100, 60)
    point = ops_of(ir.Point)
    assert len(point) == 1 and point[0].y == pytest.approx(60)  # C3 is the bottom
    api.active_sketch().frame.clear()
    f.draw_pitch_line(Singer([f.note_to_frequency("C6")]), 0, 0, 100, 60)
    assert ops_of(ir.Point)[0].y == pytest.approx(0)            # C6 is the top
    api.active_sketch().frame.clear()
    f.draw_pitch_line(Singer([f.note_to_frequency("C4")]), 0, 0, 100, 60, low="C4", high="C5")
    assert ops_of(ir.Point)[0].y == pytest.approx(60)           # low and high can be changed


def test_none_leaves_a_gap(clock):
    script()
    singer = Singer([440, 440, None, 440, 440])
    feed(singer, 5, clock, seconds=5)
    strokes = [op for op in ops_of(ir.StrokePath) if len(points(op.path)) >= 2]
    assert len(strokes) == 2                                   # two pieces of line, not one
    left, right = (points(s.path) for s in strokes)
    assert max(x for x, _ in left) < min(x for x, _ in right)


def test_a_long_wait_also_leaves_a_gap(clock):
    script()
    singer = Singer([440, 440, 440, 440])
    f.draw_pitch_line(singer, 0, 0, 100, 60)
    clock.advance(0.1)
    f.draw_pitch_line(singer, 0, 0, 100, 60)
    clock.advance(1.0)                                         # the sketch stalled
    f.draw_pitch_line(singer, 0, 0, 100, 60)
    clock.advance(0.1)
    api.active_sketch().frame.clear()
    f.draw_pitch_line(singer, 0, 0, 100, 60)
    strokes = [op for op in ops_of(ir.StrokePath) if len(points(op.path)) >= 2]
    assert len(strokes) == 2


def test_the_line_scrolls_and_old_readings_leave_the_box(clock):
    script()
    singer = Singer([440] * 10)
    f.draw_pitch_line(singer, 0, 0, 100, 60, seconds=1)
    clock.advance(0.5)
    api.active_sketch().frame.clear()
    f.draw_pitch_line(singer, 0, 0, 100, 60, seconds=1)
    xs = sorted(op.x for op in ops_of(ir.Point)) or sorted(x for op in ops_of(ir.StrokePath) for x, _ in points(op.path))
    assert xs[0] == pytest.approx(50)                          # the first reading is half way across
    clock.advance(0.6)
    api.active_sketch().frame.clear()
    f.draw_pitch_line(singer, 0, 0, 100, 60, seconds=1)
    drawn = [op for op in ops_of(ir.Point)] + [op for op in ops_of(ir.StrokePath)]
    xs = [op.x for op in ops_of(ir.Point)] + [x for op in ops_of(ir.StrokePath) for x, _ in points(op.path)]
    assert min(xs) > 0                                         # the first reading (1.1 s old) is gone
    assert drawn


def test_guides_are_labelled_with_notes_and_with_swaras_when_sa_is_given(clock):
    script()
    f.draw_pitch_line(Singer([]), 0, 0, 300, 400)
    names = [op.text for op in ops_of(ir.Text)]
    assert names[0] == "C3" and "A4" in names and names[-1] == "C6" and "C#4" not in names
    assert len(names) == 22                                    # every white key from C3 to C6
    api.active_sketch().frame.clear()
    f.draw_pitch_line(Singer([]), 0, 0, 300, 400, sa="C4")
    swaras = [op.text for op in ops_of(ir.Text)]
    assert "S" in swaras and "P" in swaras and "S'" in swaras and "S," in swaras
    assert not any(name in swaras for name in ("C4", "A4", "C3"))


def test_a_short_box_labels_only_the_main_guides(clock):
    script()
    f.draw_pitch_line(Singer([]), 0, 0, 300, 60)
    assert [op.text for op in ops_of(ir.Text)] == ["C3", "C4", "C5", "C6"]
    api.active_sketch().frame.clear()
    f.draw_pitch_line(Singer([]), 0, 0, 300, 60, sa="C4")
    assert all(op.text.startswith("S") for op in ops_of(ir.Text))


def test_guides_leave_the_drawing_style_alone(clock):
    script()
    f.fill(10, 20, 30)
    f.stroke(200, 100, 50)
    f.text_size(33)
    f.draw_pitch_line(Singer([440]), 0, 0, 100, 60)
    assert api.active_sketch().style.fill.rgba == (10, 20, 30, 255)
    assert api.active_sketch().style.stroke.rgba == (200, 100, 50, 255)
    assert api.active_sketch().style.text_size == 33


def test_the_history_is_kept_on_the_source_and_read_once_a_frame(clock):
    s = script()
    singer = Singer([440, 880, 220])
    s.frame_count = 7
    f.draw_pitch_line(singer, 0, 0, 100, 60)
    f.draw_pitch_line(singer, 0, 0, 100, 60)                   # the same frame: no new reading
    assert singer._pitch_history == [(1000.0, 440)]
    clock.advance(0.1)
    s.frame_count = 8
    f.draw_pitch_line(singer, 0, 0, 100, 60)
    assert singer._pitch_history == [(1000.0, 440), (1000.1, 880)]
    clock.advance(40)
    s.frame_count = 9
    f.draw_pitch_line(singer, 0, 0, 100, 60)
    assert [hz for _, hz in singer._pitch_history] == [220]    # old readings are forgotten


def test_a_microphone_and_a_sound_have_their_own_history(clock):
    script()
    mic = f.microphone()
    mic.start()
    mic._feed(sine(440, seconds=0.5))
    snd = f.create_sound(sine(220, seconds=2))
    snd.play()
    clock.advance(0.5)
    f.draw_pitch_line(mic, 0, 0, 100, 60)
    f.draw_pitch_line(snd, 0, 0, 100, 60)
    assert mic._pitch_history[0][1] == pytest.approx(440, rel=0.01)
    assert snd._pitch_history[0][1] == pytest.approx(220, rel=0.01)


def test_draw_pitch_line_checks_its_arguments():
    script()
    with pytest.raises(ValueError, match="sound or a microphone"):
        f.draw_pitch_line(42, 0, 0, 10, 10)
    with pytest.raises(ValueError, match="seconds must be more than 0"):
        f.draw_pitch_line(Singer([]), 0, 0, 10, 10, seconds=0)
    with pytest.raises(ValueError, match="higher note"):
        f.draw_pitch_line(Singer([]), 0, 0, 10, 10, low="C5", high="C4")
    with pytest.raises(ValueError, match="note"):
        f.draw_pitch_line(Singer([]), 0, 0, 10, 10, low="H9")


# ---------------------------------------------------------------- layers, transforms and files
def test_the_views_draw_into_the_open_layer_not_the_canvas(clock):
    script(60, 40)
    f.background(255, 255, 255)
    with f.layer("view"):
        f.no_stroke()
        f.fill(255, 0, 0)
        f.draw_wave([1.0, -1.0] * 25, 0, 0, 25, 20)
    assert ops_of(ir.FillPath) == []                          # the canvas recorded nothing
    c = f.get(12, 10)
    assert (c.r, c.g, c.b) == (255, 0, 0)
    assert f.get(25, 30).g == 255                             # outside the box the canvas shows


def test_the_other_views_work_in_a_layer(clock):
    script(100, 80)
    snd = f.create_sound(sine(440))
    snd.play()
    clock.advance(0.2)
    with f.layer("view"):
        f.draw_spectrum(snd, 0, 0, 50, 20)
        f.draw_pitch_line(snd, 0, 30, 100, 40)
    assert ops_of(ir.Rect) == [] and ops_of(ir.Text) == []


def test_the_views_follow_the_transform():
    script()
    f.translate(100, 50)
    f.draw_wave([1.0, -1.0] * 10, 0, 0, 40, 20)
    assert ops_of(ir.Concat)                                   # the transform is the sketch's own, not ours


def test_the_views_save_as_vectors_in_svg_and_pdf(tmp_path, clock):
    script()
    snd = f.create_sound(sine(440, seconds=1))
    snd.play()
    clock.advance(0.3)
    f.background(255, 255, 255)
    f.draw_wave(snd, 10, 10, 200, 50)
    f.draw_spectrum(snd, 10, 70, 200, 50, bands=16)
    f.draw_pitch_line(Singer([440, 440]), 10, 130, 200, 100)
    f.draw_pitch_line(Singer([440, 440]), 10, 130, 200, 100)
    f.save(str(tmp_path / "views.svg"))
    f.save(str(tmp_path / "views.pdf"))
    svg = (tmp_path / "views.svg").read_text(encoding="utf-8")
    assert svg.count("<path") >= 20 and "<image" not in svg
    assert (tmp_path / "views.pdf").read_bytes().startswith(b"%PDF")


def test_the_spectrogram_is_pixels_in_a_file(tmp_path):
    script()
    picture = f.spectrogram(f.create_sound(sine(440)), 20, 20)
    f.image(picture, 0, 0)
    f.save(str(tmp_path / "s.svg"))
    assert "<image" in (tmp_path / "s.svg").read_text(encoding="utf-8")
    picture.save(str(tmp_path / "s.png"))
    assert (tmp_path / "s.png").read_bytes().startswith(b"\x89PNG")


def test_a_view_adds_nothing_to_the_canvas_until_drawn_and_the_old_api_is_unchanged():
    script()
    f.rect(0, 0, 5, 5)
    assert [type(op) for op in api.active_sketch().frame.ops] == [ir.Rect]
