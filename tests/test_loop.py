"""Loop control and clock (S-048, contract R10)."""
from __future__ import annotations

import datetime

import playground as p
from playground import api
from playground.platform.headless import HeadlessPlatform
from playground.sketch import Sketch


def run(ns, frames=5):
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    ns.setdefault("setup", lambda: p.size(50, 50))
    s.run_namespace(ns, max_frames=frames)
    return s


def test_no_loop_in_setup_still_draws_once():
    calls = []

    def setup():
        p.size(50, 50)
        p.no_loop()

    run({"setup": setup, "draw": lambda: calls.append(p.frame_count)}, frames=6)
    assert calls == [0]
    assert p.frame_count == 1 and not p.is_looping()


def test_redraw_draws_exactly_once_more():
    calls = []

    def setup():
        p.size(50, 50)
        p.no_loop()

    def draw():
        calls.append(p.frame_count)
        if len(calls) == 1:
            p.redraw()

    run({"setup": setup, "draw": draw}, frames=6)
    assert calls == [0, 1]


def test_loop_resumes():
    calls = []

    def draw():
        calls.append(p.frame_count)
        if p.frame_count == 1:
            p.no_loop()
            p.redraw()          # one more frame, which turns looping back on
        if p.frame_count == 2:
            p.loop()

    run({"draw": draw}, frames=6)
    assert calls[:3] == [0, 1, 2] and len(calls) >= 4 and p.is_looping()


def test_max_frames_counts_iterations_so_a_non_looping_sketch_ends():
    s = run({"draw": lambda: p.no_loop()}, frames=4)
    assert s.last_frame is not None and p.frame_count == 1


def test_millis_and_frame_rate():
    seen = []
    run({"draw": lambda: seen.append((p.millis(), p.frame_rate()))}, frames=4)
    assert all(isinstance(ms, int) and ms >= 0 for ms, _ in seen)
    assert seen[0][1] == 0.0 and seen[-1][1] > 0


def test_exit_is_stop():
    calls = []

    def draw():
        calls.append(1)
        p.exit()

    run({"draw": draw}, frames=10)
    assert calls == [1]


def test_clock_helpers_follow_the_local_clock():
    now = datetime.datetime.now()
    assert p.year() in (now.year, now.year + 1)
    assert 1 <= p.month() <= 12 and 1 <= p.day() <= 31
    assert 0 <= p.hour() <= 23 and 0 <= p.minute() <= 59 and 0 <= p.second() <= 59
