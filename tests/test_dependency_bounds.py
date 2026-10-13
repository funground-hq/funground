"""Library versions (D-100): every dependency has an upper bound, and the tested versions fit inside the bounds.

pyproject.toml says which versions learners may get; tests/constraints.txt says which versions CI tests (and is
published with each release). If a pin moves outside a bound, or a dependency is added without one, this fails.
"""
from __future__ import annotations

import tomllib

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from conftest import ROOT


def requirements() -> list[Requirement]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    found = [Requirement(r) for r in project["dependencies"]]
    for name in ("extras", "video"):
        found += [Requirement(r) for r in project["optional-dependencies"][name]]
    return found


def pins() -> dict[str, str]:
    pinned = {}
    for line in (ROOT / "tests" / "constraints.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            name, version = line.split("==")
            pinned[canonicalize_name(name)] = version
    return pinned


def test_every_dependency_has_a_lower_and_an_upper_bound():
    for req in requirements():
        operators = {spec.operator for spec in req.specifier}
        assert ">=" in operators and "<" in operators, f"{req}: give it >= and < (D-100)"


def test_every_dependency_is_pinned_for_ci_inside_its_bounds():
    pinned = pins()
    for req in requirements():
        name = canonicalize_name(req.name)
        assert name in pinned, f"{req.name} is not in tests/constraints.txt"
        assert req.specifier.contains(pinned[name]), f"{req.name}=={pinned[name]} is outside {req.specifier}"


# ---- the golden tolerance of the weekly newest-versions run
def test_the_golden_tolerance_takes_invisible_edges_and_refuses_a_visible_change(monkeypatch):
    import conftest
    monkeypatch.setattr(conftest, "GOLDEN_TOLERANCE", True)
    base = bytes([200, 100, 50]) * 1000
    edge = bytearray(base)
    edge[0:3] = bytes([212, 100, 50])                          # one pixel moved by 12 of 255: an anti-aliased edge
    assert conftest.golden_matches(base, bytes(edge))
    visible = bytearray(base)
    visible[0:3] = bytes([255, 100, 50])                       # one pixel 55 of 255 away: a real change (over 32)
    assert not conftest.golden_matches(base, bytes(visible))
    many = bytearray(base)
    for i in range(0, 3 * 20, 3):                              # 2% of the pixels, each a little: too many
        many[i] = 201
    assert not conftest.golden_matches(base, bytes(many))
    monkeypatch.setattr(conftest, "GOLDEN_TOLERANCE", False)
    assert not conftest.golden_matches(base, bytes(edge))      # and without the tolerance, exact
