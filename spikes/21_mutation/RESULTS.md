# Spike 21: mutation testing — where the tests would miss a real bug

Branch: `cloud/mutation-gaps`, from `origin/main` at `bc651ca`. Started 07:28 UTC, 2026-11-05.

## Plan

1. Set up a venv (Python 3.11, constraints file), without funground-ml.
2. For each target module, find the test files that exercise it and time them.
3. Try mutmut; if it does not run here within 10 minutes, use a small AST mutator (`mutate.py` here):
   swap comparison operators, swap `+`/`-`, change numeric constants by one, flip boundaries.
4. Four workers, each on its own copy of the repository. Timeout is 3 × the clean test time; a timeout counts as killed.
5. Targets in order: vector, color, geometry, noise, pathops, paths, sound/_swaras, sound/_synth.
6. Triage survivors: equivalent / real gap / unclear. Real gaps get tests in the existing test file, one commit per module,
   each naming the document that states the behaviour.

Results are filled in below as each module finishes.
