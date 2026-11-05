"""Regressions found by the API fuzz spike (spikes/20_api_fuzz): calls a beginner can write that hung
or put nan into a saved file. Each must finish quickly, and either draw or raise a learner error."""
from __future__ import annotations

import threading

import pytest

import funground as f


def _finishes(call, seconds=5.0):
    """Run *call* in a thread; fail if it is still running after *seconds* (a hang)."""
    out = {}

    def target():
        try:
            out["value"] = call()
        except BaseException as e:  # noqa: BLE001 - reported to the test
            out["error"] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(seconds)
    assert not t.is_alive(), "the call did not finish: it hangs"
    return out


@pytest.mark.parametrize("start, stop", [
    (1e12, 270), (2 ** 63, 270), (0, -1e12), (float("inf"), 270), (0, -float("inf")), (1e308, 270),
])
def test_arc_with_huge_angles_does_not_hang(canvas, start, stop):
    out = _finishes(lambda: f.arc(100, 50, 80, 80, start, stop, "pie"))
    err = out.get("error")
    if err is not None:
        assert isinstance(err, ValueError) and "f.arc()" in str(err)


def test_arc_still_wraps_stop_before_start(canvas, sketch):
    f.arc(100, 50, 80, 80, 270, -630, "pie")      # -630 + 3 * 360 = 450: the right half, as before
    f.arc(100, 50, 80, 80, 270, 90, "pie")
