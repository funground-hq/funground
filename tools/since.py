"""Which release a public name arrives in (S-229, D-116): the one place that knows.

funground/released_names.json holds the public API of each release (tools/make_released_names.py writes it).
A name or class member in the first release listed there shows nothing, because everything is "since 0.1" by
default. One that is in none of the releases arrives in the upcoming version, which is pyproject.toml's version
without ``.devN``. A name in a later release listed here shows that release.

Used by tools/make_api_reference.py (API.md, completions.json, llms.txt), tools/make_gallery.py and
tests/test_since.py. The marker text for a guide section or a gallery example is MARKER, here and only here.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASED = ROOT / "funground" / "released_names.json"
COMPLETIONS = ROOT / "funground" / "completions.json"

# The line under a heading in the guide, and under an example in the gallery. {v} is the short version, such as 0.2.
MARKER = "> **Since {v}.** In Play now; on your computer with funground {v}."
# The compact marker at the end of a Quick Reference row.
ROW_MARKER = "*({v})*"
# A short sentence for the API reference and the notes for assistants.
API_LINE = "Since {v}."
# The same as a badge right under a heading of the API reference; the site styles the class (funground.css, .fg-since).
API_BADGE = '<p class="fg-since">Since {v}.</p>'

# Option words that arrive later than the function that takes them. Written by hand: tests/test_since.py checks each
# word is still accepted, so an entry cannot outlive its word.
LATER_WORDS = {"filter": {"kind": {"edges": "0.2"}}, "apply_filter": {"kind": {"edges": "0.2"}}}
WORD_VERSIONS = {word: v for args in LATER_WORDS.values() for words in args.values() for word, v in words.items()}


def version_key(version: str) -> list[int]:
    return [int(p) for p in version.split(".")]


def short(version: str) -> str:
    """0.1.0 -> 0.1; 0.2.0.dev0 -> 0.2."""
    return ".".join(version.split(".")[:2])


def released() -> dict[str, dict]:
    data = json.loads(RELEASED.read_text(encoding="utf-8")) if RELEASED.exists() else {}
    return dict(sorted(data.items(), key=lambda kv: version_key(kv[0])))


def upcoming() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    return short(re.search(r'^version\s*=\s*"([^"]+)"', text, re.M).group(1))


def _first_release_with(present) -> str | None:
    """The short version of the earliest release for which present(release) is true; None for the first release
    in the file (it shows nothing); the upcoming version when no release has it."""
    data = released()
    for i, (version, release) in enumerate(data.items()):
        if present(release):
            return None if i == 0 else short(version)
    return upcoming()


def name_since(name: str) -> str | None:
    return _first_release_with(lambda r: name in r["names"])


def member_since(cls: str, member: str) -> str | None:
    return _first_release_with(lambda r: member in r["classes"].get(cls, []))


def class_since(name: str) -> str | None:
    return _first_release_with(lambda r: name in r["classes"])


def word_since(function: str, argument: str, word: str) -> str | None:
    """The version a later option word arrives in (see LATER_WORDS), or None."""
    return LATER_WORDS.get(function, {}).get(argument, {}).get(word)


def marker(version: str) -> str:
    return MARKER.format(v=version)


def row_marker(version: str) -> str:
    return ROW_MARKER.format(v=version)


def api_line(version: str) -> str:
    return API_LINE.format(v=version)


def api_badge(version: str) -> str:
    return API_BADGE.format(v=version)


# ---- finding later names in text (the guide, the gallery, the Quick Reference)

def later_tables() -> tuple[dict[str, str], dict[str, str], set[str]]:
    """(later public names, later class members that no earlier name shares, those members that are properties),
    each with its version, read from completions.json."""
    data = json.loads(COMPLETIONS.read_text(encoding="utf-8"))
    names = {e["name"]: e["since"] for e in data["names"] if "since" in e}
    old = {e["name"] for e in data["names"] if "since" not in e}
    members: dict[str, str] = {}
    properties: set[str] = set()
    for cls in data["classes"].values():
        for m in cls["members"]:
            if "since" in m:
                members[m["name"]] = m["since"]
                if m["kind"] == "property":
                    properties.add(m["name"])
            else:
                old.add(m["name"])
    return names, {n: v for n, v in members.items() if n not in old}, properties


def latest(versions: list[str]) -> str | None:
    return max(versions, key=version_key) if versions else None


def later_use(text: str, row: bool = False) -> str | None:
    """The newest version needed by the names in *text* (a section, an example's code or a Quick Reference row), or None.
    It looks for ``f.name``, ``.method(`` and ``.property`` of members no earlier class has, and the later option
    words in quotes. In a table *row*, a method written as the lead cell, such as `` `.square(x, y)` ``, counts too."""
    names, members, properties = later_tables()
    found = [v for n, v in names.items() if re.search(rf"\bf\.{n}\b", text)]
    for n, v in members.items():
        pattern = rf"\.{n}\b" if n in properties else rf"\.{n}\("
        if re.search(pattern, text):
            found.append(v)
    found += [v for w, v in WORD_VERSIONS.items() if re.search(rf"""["']{w}["']""", text)]
    return latest(found)


# ---- the sections of a guide page

class Section:
    """A guide section: the lines under one ``##`` or ``###`` heading, up to the next one."""

    def __init__(self, heading: str, line: int) -> None:
        self.heading, self.line = heading, line       # line: the heading's number, counted from 1
        self.body: list[str] = []
        self.code: list[str] = []

    @property
    def first_line(self) -> str:
        """The first line under the heading that is not blank (where the marker goes)."""
        return next((ln for ln in self.body if ln.strip()), "")

    def needs(self) -> str | None:
        """The newest version needed by the code in the section. A later name in a table row of the prose is marked on
        that row (ROW_MARKER) instead, so a section that mostly works in an earlier release is not marked as a whole."""
        return later_use("\n".join(self.code))

    def rows(self) -> list[tuple[str, str]]:
        """(row, version) for each table row outside code that names something later."""
        return [(line, version) for line in self.body
                if line.startswith("|") and line not in self.code and (version := later_use(line, row=True))]


def sections(text: str) -> list[Section]:
    found: list[Section] = []
    fenced = False
    for number, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        if re.match(r"\s*(```|~~~)", line):
            fenced = not fenced
        elif not fenced and re.match(r"#{2,3} \S", line):
            found.append(Section(line, number))
            continue
        if found:
            found[-1].body.append(line)
            if fenced or re.match(r"\s*(```|~~~)", line):
                found[-1].code.append(line)
    return found
