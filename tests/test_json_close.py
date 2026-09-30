"""assert_json_documents_close (S-039): structural JSON comparison with float tolerance.

Used by test_ops_snapshot.py and test_gallery.py so IR snapshots compare equal across
platforms whose maths library rounds sin/cos in the last digit differently.
"""
from __future__ import annotations

import pytest

from conftest import assert_json_documents_close


def test_equal_documents_pass():
    doc = {"a": 1, "b": [1.5, "x", True, None], "c": {"d": 2.0}}
    assert_json_documents_close(doc, doc)


def test_last_digit_float_noise_passes():
    a = {"x": 138.65993248815553}
    b = {"x": 138.65993248815556}
    assert_json_documents_close(a, b)


def test_changed_float_fails():
    with pytest.raises(AssertionError, match=r"\$\.x"):
        assert_json_documents_close({"x": 1.0}, {"x": 1.001})


def test_changed_string_fails():
    with pytest.raises(AssertionError, match=r"\$\.name"):
        assert_json_documents_close({"name": "circle"}, {"name": "square"})


def test_int_vs_float_fails():
    with pytest.raises(AssertionError, match=r"\$\.x"):
        assert_json_documents_close({"x": 1}, {"x": 1.0})


def test_missing_key_fails():
    with pytest.raises(AssertionError, match=r"\$: keys differ"):
        assert_json_documents_close({"a": 1}, {"a": 1, "b": 2})


def test_nested_path_is_named_in_the_message():
    a = {"ops": [{"kind": "circle", "args": {"r": 5.0}}]}
    b = {"ops": [{"kind": "circle", "args": {"r": 6.0}}]}
    with pytest.raises(AssertionError, match=r"\$\.ops\[0\]\.args\.r"):
        assert_json_documents_close(a, b)
