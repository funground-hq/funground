# Spike 20: fuzzing the public API like a thousand confused beginners

**Branch note.** The task named `cloud/api-fuzz`. This cloud session is pinned to the branch
`claude/nifty-sagan-2vk7nl` and may push only there, so all work is on that branch.

Started 07:28 UTC, 2026-11-05. Base: origin/main `bc651ca`.

## Plan

1. Enumerate `funground._PUBLIC_NAMES` plus `sound`, `sangeet`, `camera`; record signatures; list skips.
2. `harness.py`: each case runs in a forked worker with `resource.setrlimit` (address space 2 GB, CPU),
   a 10 s wall-clock kill, 4 workers in parallel. Failing cases are appended to `findings.jsonl` as they happen.
3. Arguments: valid values, edges, then beginner mistakes (None, nan, inf, strings, emoji, RTL, Devanagari,
   lone surrogates, long strings, wrong arity, colour typos).
4. Stateful programs with Hypothesis (push/pop imbalance, open shapes, layers, saving partway).
5. Each program that runs saves PNG, PDF, SVG, GIF; read back with Pillow, pypdf, ElementTree.
6. Classify: crash > hang/memory > corrupt output > leak. Group by exception and top funground frame.

Status: in progress.
