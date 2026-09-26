"""GraphicsState and its stack (story S-015)."""
from __future__ import annotations

import pytest

from funground.color import BLACK, WHITE, Color
from funground.state import GraphicsState, StateStack


def test_defaults_match_contract_row_s3():
    s = GraphicsState()
    assert (s.fill, s.stroke, s.stroke_width, s.text_size) == (WHITE, BLACK, 1, 20)


def test_state_is_immutable():
    s = GraphicsState()
    with pytest.raises(AttributeError):
        s.fill = None  # type: ignore[misc]
    t = s.with_(fill=None, stroke_width=4)
    assert s.fill is WHITE and t.fill is None and t.stroke_width == 4


def test_stack_save_restore_nesting():
    st = StateStack()
    st.update(fill=Color(1, 1, 1))
    st.save()
    st.update(fill=Color(2, 2, 2), stroke_width=9)
    st.save()
    st.update(stroke=None)
    assert st.depth == 2
    st.restore()
    assert st.current.stroke == BLACK and st.current.stroke_width == 9
    st.restore()
    assert st.current.fill == Color(1, 1, 1) and st.current.stroke_width == 1
    assert st.depth == 0


def test_restore_without_save_is_an_error():
    with pytest.raises(RuntimeError):
        StateStack().restore()


def test_unwind_restores_the_bottom_state_and_reports_the_count():
    st = StateStack()
    st.update(fill=Color(1, 1, 1))
    base = st.current
    st.save(); st.update(fill=Color(2, 2, 2))
    st.save(); st.update(stroke_width=7)
    assert st.unwind() == 2
    assert st.current == base and st.depth == 0
    assert st.unwind() == 0 and st.current == base   # nothing open: a no-op
