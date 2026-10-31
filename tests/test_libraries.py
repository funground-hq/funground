"""The sound, sangeet and camera libraries (S-246, S-247, ADR-007, D-123): moved names, imports, the registry of host
services and the registry of inputs the sketch serves each frame."""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

import funground as f
from funground import camera, frame_inputs, host_services, sangeet, sound
from conftest import ROOT

MOVED = sorted(f._MOVED)


def test_there_are_27_moved_names_and_183_left():
    assert len(MOVED) == 27
    assert len(f._PUBLIC_NAMES) == 183
    assert not set(MOVED) & set(f._PUBLIC_NAMES)


# `camera` is both a moved name and the library: once any test has imported the library, f.camera is the module. That
# case is tested in a fresh interpreter below.
@pytest.mark.parametrize("name", [n for n in MOVED if n != "camera"])
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


# ---- the camera library (S-247)

def test_the_camera_names_are_what_the_design_says():
    assert camera.__all__ == ["open", "names", "load_clip"]
    sentence = {n: f.moved_message(n) for n in ("camera", "cameras", "load_clip")}
    assert "camera.open()" in sentence["camera"] and "camera.names()" in sentence["cameras"]
    assert "camera.load_clip()" in sentence["load_clip"]
    assert all("from funground import camera" in m for m in sentence.values())


def _fresh(script: str):
    return subprocess.run([sys.executable, "-I", "-c", f"import sys; sys.path.insert(0, sys.argv[1]); {script}", str(ROOT)],
                          capture_output=True, text=True, timeout=300, env={**os.environ, "FUNGROUND_HEADLESS": "1"})


def test_f_camera_before_the_library_is_imported_gives_the_sentence():
    done = _fresh("import funground as f\n"
                  "try:\n    f.camera()\nexcept AttributeError as e:\n    print(e)\n"
                  "else:\n    print('no error')")
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == ("f.camera() has moved to the camera library: add `from funground import camera` "
                                   "and write camera.open().")


def test_f_camera_after_the_library_is_imported_is_a_module_that_gives_the_same_sentence():
    done = _fresh("import funground as f\nfrom funground import camera\n"
                  "assert f.camera is camera, 'f.camera is not the library'\n"
                  "try:\n    f.camera()\nexcept TypeError as e:\n    print(e)\n"
                  "else:\n    print('no error')\n"
                  "try:\n    camera()\nexcept TypeError as e:\n    print(e)")
    assert done.returncode == 0, done.stderr
    sentence = ("f.camera() has moved to the camera library: add `from funground import camera` "
                "and write camera.open().")
    assert done.stdout.strip().splitlines() == [sentence, sentence]


def test_the_library_module_is_callable_only_to_say_so():
    with pytest.raises(TypeError, match=r"camera\.open\(\)"):
        camera()


def test_naming_the_camera_camera_gets_one_plain_sentence():
    """`camera = camera.open()` hides the library; the next `camera.open()` reaches the Camera object."""
    cam = camera.open()
    for name in ("open", "names", "load_clip"):
        with pytest.raises(AttributeError, match=r"camera\.%s\(\) is called on the library.*cam = camera\.open\(\)" % name):
            getattr(cam, name)
    with pytest.raises(AttributeError, match="no attribute 'nothing'"):
        cam.nothing                                                      # other missing names are as plain as before


def test_the_camera_library_imports_cleanly_in_a_fresh_interpreter():
    for line in ("from funground import camera", "import funground.camera"):
        done = _fresh(line)
        assert done.returncode == 0, done.stderr


def test_importing_funground_does_not_import_the_camera_library():
    done = _fresh("import funground; print('funground.camera' in sys.modules)")
    assert done.returncode == 0 and done.stdout.strip() == "False", done.stderr


def test_the_host_registry_has_a_camera_slot_that_starts_empty():
    assert host_services.camera is None


def test_the_frame_inputs_registry_serves_and_stops_what_is_registered():
    calls = []
    pair = (lambda sketch: calls.append(("take", sketch)), lambda: calls.append(("stop",)))
    before = list(frame_inputs._inputs)
    try:
        frame_inputs.register(*pair)
        frame_inputs.register(*pair)                                    # twice is the same as once
        frame_inputs.take_all("a sketch")
        frame_inputs.stop_all()
        assert calls == [("take", "a sketch"), ("stop",)]
    finally:
        frame_inputs._inputs[:] = before


def test_the_camera_library_registered_itself_with_the_core():
    assert (camera._device.take_frames, camera._device.stop_all) in frame_inputs._inputs
