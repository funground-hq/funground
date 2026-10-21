"""Bundled fonts fetched on first use by the browser host (S-211, D-114): typography._ensure_bundled and Session(fetch_font=...).

The real fonts are never touched: FONT_DIR points at a temporary folder.
"""
from __future__ import annotations

import hashlib
import os

import pytest

from funground import typography
from funground.web import Session


@pytest.fixture
def fonts_folder(tmp_path, monkeypatch):
    folder = tmp_path / "fonts"
    monkeypatch.setattr(typography, "FONT_DIR", str(folder))
    monkeypatch.setattr(typography, "_font_fetcher", None)
    return folder


def test_a_missing_font_is_fetched_once_and_written(fonts_folder):
    calls = []
    typography.set_font_fetcher(lambda name: calls.append(name) or b"font bytes")
    path = os.path.join(typography.FONT_DIR, "Some.ttf")
    typography._ensure_bundled(path)
    typography._ensure_bundled(path)
    assert calls == ["Some.ttf"]
    assert (fonts_folder / "Some.ttf").read_bytes() == b"font bytes"


def test_without_a_fetcher_nothing_happens(fonts_folder):
    typography._ensure_bundled(os.path.join(typography.FONT_DIR, "Some.ttf"))
    assert not fonts_folder.exists()


def test_a_file_outside_the_font_folder_is_not_fetched(fonts_folder, tmp_path):
    typography.set_font_fetcher(lambda name: pytest.fail("fetched"))
    typography._ensure_bundled(str(tmp_path / "Mine.ttf"))


def test_a_font_that_is_there_is_not_fetched(fonts_folder):
    fonts_folder.mkdir()
    (fonts_folder / "Some.ttf").write_bytes(b"x")
    typography.set_font_fetcher(lambda name: pytest.fail("fetched"))
    typography._ensure_bundled(os.path.join(typography.FONT_DIR, "Some.ttf"))


def session_with(fetch, manifest, monkeypatch):
    monkeypatch.setattr(typography, "_font_fetcher", None)
    Session(100, 100, fetch_font=fetch, fonts=manifest)


def test_session_checks_size_and_hash(fonts_folder, monkeypatch):
    data = b"0123456789"
    good = {"Some.ttf": {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}}
    session_with(lambda name: data, good, monkeypatch)
    assert typography._font_fetcher("Some.ttf") == data
    session_with(lambda name: data + b"!", good, monkeypatch)
    with pytest.raises(OSError, match="Some.ttf"):
        typography._font_fetcher("Some.ttf")
    session_with(lambda name: b"9876543210", good, monkeypatch)
    with pytest.raises(OSError, match="Some.ttf"):
        typography._font_fetcher("Some.ttf")


def test_session_without_fetch_font_installs_nothing(monkeypatch):
    session_with(None, None, monkeypatch)
    assert typography._font_fetcher is None


def test_a_failed_download_is_one_plain_error(fonts_folder, monkeypatch):
    def offline(name):
        raise RuntimeError("HTTP 0")
    session_with(offline, {}, monkeypatch)
    with pytest.raises(OSError, match="Some.ttf could not be downloaded"):
        typography._font_fetcher("Some.ttf")
