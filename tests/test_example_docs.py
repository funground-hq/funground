"""Every gallery example explains itself (S-120, D-065).

The standard for an example's docstring:

    Title line

    What you see: one short paragraph.

    How it works:
    - 3 to 6 bullets: the idea, and the funground functions that do it.

    Make it yours:
    - 3 to 5 bullets: ideas to extend it, easiest first.

A bullet may carry on over the next lines (indented). Every ``f.<name>`` written in a docstring
must be a real name in ``funground.__all__``, and ``sound.<name>``, ``picture.<name>``,
``path.<name>`` or ``microphone.<name>`` must be a real method of that kind of object.

For now the standard is enforced only on the examples listed in ``EXPLAINED``. The list grows as
each area is done (S-120.2); the last step replaces it with every example (see ``ENFORCED``).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

import funground
from funground import gallery
from funground.geometry import Path as GeometryPath
from funground.microphone_input import Microphone
from funground.paths import PathBuilder
from funground.picture import Picture
from funground.sound import Sound

from conftest import ROOT

GALLERY = ROOT / "examples" / "gallery"

# Examples that have the full standard. Add an example here when its docstring is done.
EXPLAINED = [
    "basics/02_setup_and_draw.py",
    "paths/05_booleans.py",
    "music/04_hear_a_raga.py",
    "projects/02_rangoli.py",
]

# The one switch: when every example is done, make ENFORCED = ALL and delete EXPLAINED.
ALL = gallery.list_examples(GALLERY)
ENFORCED = [GALLERY / name for name in EXPLAINED]

HOW_RANGE = range(3, 7)       # 3 to 6 bullets
MAKE_RANGE = range(3, 6)      # 3 to 5 bullets

OBJECTS = {"sound": [Sound], "picture": [Picture], "path": [PathBuilder, GeometryPath],
           "microphone": [Microphone]}


def docstring(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    return source.split('"""')[1] if source.lstrip().startswith('"""') else ""


def names_written_in(doc: str) -> tuple[set[str], set[tuple[str, str]]]:
    """The ``f.<name>`` names, and the ``<object>.<method>`` pairs, a docstring mentions."""
    module_names = set(re.findall(r"\bf\.([A-Za-z_]\w*)", doc))
    pairs = set(re.findall(r"\b(" + "|".join(OBJECTS) + r")\.([A-Za-z_]\w*)", doc))
    return module_names, pairs


def test_the_pilot_files_exist_and_are_gallery_examples():
    assert all(path in ALL for path in ENFORCED)


@pytest.mark.parametrize("path", ENFORCED, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_the_docstring_follows_the_standard(path: Path):
    parts = gallery.explanation(path)
    where = f"{path.parent.name}/{path.name}"
    assert parts.title and parts.title != path.stem, f"{where}: needs a title line"
    assert parts.description, f"{where}: needs a paragraph after the title"
    assert gallery.HOW_HEADING in docstring(path), f"{where}: needs a 'How it works:' heading"
    assert gallery.MAKE_HEADING in docstring(path), f"{where}: needs a 'Make it yours:' heading"
    assert len(parts.how) in HOW_RANGE, f"{where}: 'How it works:' needs 3 to 6 bullets, has {len(parts.how)}"
    assert len(parts.make) in MAKE_RANGE, f"{where}: 'Make it yours:' needs 3 to 5 bullets, has {len(parts.make)}"
    assert all(len(point) > 20 for point in parts.how + parts.make), f"{where}: a bullet is too short to help"


@pytest.mark.parametrize("path", ENFORCED, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_the_names_in_the_docstring_exist(path: Path):
    module_names, pairs = names_written_in(docstring(path))
    missing = sorted(name for name in module_names if name not in funground.__all__)
    assert not missing, f"{path.name}: not in funground.__all__: {missing}"
    bad = sorted(f"{kind}.{name}" for kind, name in pairs
                 if not any(hasattr(cls, name) for cls in OBJECTS[kind]))
    assert not bad, f"{path.name}: not a method or attribute of that object: {bad}"


def test_the_markers_survive():
    assert gallery.is_time_dependent(GALLERY / "music" / "04_hear_a_raga.py")


def test_the_parser_reads_bullets_that_carry_on(tmp_path):
    example = tmp_path / "area" / "01_x.py"
    example.parent.mkdir()
    example.write_text('"""A title\n\nOne line\nand another.\n\nHow it works:\n- first point\n  goes on\n- second\n\n'
                       'Make it yours:\n- an idea\n"""\nprint(1)\n', encoding="utf-8")
    parts = gallery.explanation(example)
    assert (parts.title, parts.description) == ("A title", "One line and another.")
    assert parts.how == ("first point goes on", "second")
    assert parts.make == ("an idea",)
    assert gallery.title_and_description(example) == ("A title", "One line and another.")


def test_an_older_docstring_has_no_sections(tmp_path):
    example = tmp_path / "area" / "01_x.py"
    example.parent.mkdir()
    example.write_text('"""A title\n\nJust a paragraph.\n"""\n', encoding="utf-8")
    parts = gallery.explanation(example)
    assert parts.how == () and parts.make == () and parts.description == "Just a paragraph."


def test_the_checker_catches_a_made_up_name():
    names, pairs = names_written_in("Use f.circle() and f.fly_to_the_moon(), then sound.reverb() and sound.nope().")
    assert "fly_to_the_moon" in names and "fly_to_the_moon" not in funground.__all__
    assert ("sound", "nope") in pairs and not hasattr(Sound, "nope") and hasattr(Sound, "reverb")
