"""The sound and sangeet libraries (S-246, ADR-007, D-123): moved names, imports and the registry of host services."""
from __future__ import annotations

import subprocess
import sys

import pytest

import funground as f
from funground import host_services, sangeet, sound
from conftest import ROOT

MOVED = sorted(f._MOVED)


def test_there_are_24_moved_names_and_186_left():
    assert len(MOVED) == 24
    assert len(f._PUBLIC_NAMES) == 186
    assert not set(MOVED) & set(f._PUBLIC_NAMES)


@pytest.mark.parametrize("name", MOVED)
def test_a_moved_name_on_f_gives_one_plain_sentence(name):
    assert not hasattr(f, name)
    library, new = f._MOVED[name]
    with pytest.raises(AttributeError) as info:
        getattr(f, name)
    message = str(info.value)
    assert f"f.{name}() has moved to the {library} library" in message
    assert f"from funground import {library}" in message and f"{library}.{new}()" in message


def test_create_and_load_are_the_new_spellings():
    assert "sound.create()" in str(pytest.raises(AttributeError, lambda: f.create_sound).value)
    assert "sound.load()" in str(pytest.raises(AttributeError, lambda: f.load_sound).value)


def test_create_and_load_work(tmp_path):
    made = sound.create([0.0, 0.5, -0.5] * 100)
    assert made.duration() > 0
    path = tmp_path / "a.wav"
    made.save(str(path))
    assert sound.load(str(path)).duration() == pytest.approx(made.duration(), abs=0.01)


def test_the_library_names_are_what_the_design_says():
    assert len(sound.__all__) == 18 and len(sangeet.__all__) == 6
    assert sangeet.tala("Teentaal").duration() > 0 and sangeet.raga("Yaman").name == "Yaman"


def test_the_libraries_import_cleanly_in_a_fresh_interpreter():
    for line in ("from funground import sound", "from funground import sangeet", "import funground.sound, funground.sangeet"):
        done = subprocess.run([sys.executable, "-I", "-c", f"import sys; sys.path.insert(0, sys.argv[1]); {line}", str(ROOT)],
                              capture_output=True, text=True, timeout=300)
        assert done.returncode == 0, done.stderr


def test_the_registry_starts_empty():
    assert host_services.mixer is None and host_services.microphone is None
