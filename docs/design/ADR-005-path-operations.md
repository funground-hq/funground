# ADR-005: Path booleans and stroke expansion use skia-pathops

**Status:** Accepted 1 October 2026 (D-037 = A, the maintainer's choice).
**Date:** 1 October 2026

## Context

Sprint 9 brings DrawBot's path tools to funground:
- the boolean operations: union, intersection, difference, exclusion;
- removing overlaps;
- turning a stroke into a fillable outline;
- testing whether a point is inside a shape.

Cairo draws paths but cannot compute new outlines, so a geometry library is needed. Under D-034
a new dependency is the maintainer's decision.

## Options

The trade-offs are in the decision log, D-037.

- **A. `skia-pathops` in the base install.** It is a cut-down build of Skia's path maths: BSD-3,
  no other dependencies, 1.8 MB to download on Windows (2.9 MB macOS, 3.3 MB Linux), with
  wheels for every supported system and Python.
- **B. `booleanOperations` + `pyclipper`**, DrawBot's own engine. It is smaller, but it flattens
  curves and fits them back afterwards, and it has no stroke expansion.
- **C. Either one as the optional extra.**
- **D. No path booleans in 0.1.**

## Decision

**A.**

- **One module, `funground/pathops.py`, imports `pathops`.** The provider boundary test enforces
  this, so the library stays replaceable.
- **funground's `Path` geometry is converted to and from Skia paths** at that boundary.
- **Booleans, `remove_overlap`, `expand_stroke`, `contains` and bounds** all come from it.
- **Curves stay exact.** Skia returns quadratic or cubic segments, and funground keeps them.

## Consequences

- **The base install grows** by about 2–3 MB.
- **Results are Skia's, not DrawBot's, so they can differ.** The point order in a result and the
  way a self-touching outline is split may not match DrawBot's. The drawn shape is the same, and
  the contract pins only the drawn result.
- **`THIRD_PARTY_LICENSES.md` lists skia-pathops (BSD-3).**
