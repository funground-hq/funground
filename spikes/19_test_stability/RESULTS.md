# Spike 19: test stability before 0.2

Branch: `cloud/test-stability` (from origin/main `bc651ca`). Linux cloud session, 4 CPUs, started 07:27 UTC 2026-11-05.

## Plan

1. Baseline: whole suite on Python 3.11, `--timeout=300 --durations=50 --junitxml`.
2. The hang in `16_sound` guide example: read `funground/sound/_engine.py` and `tests/test_guide.py`; explain why
   pytest-timeout might not fire; repeat the sound examples 50+ times with faulthandler, CPU load, thread method,
   outer hard timeout.
3. Order and timing: pytest-randomly + pytest-xdist (venv only), 3+ seeds in parallel.
4. Versions: 3.12, 3.13, 3.14 with constraints; 3.14 newest; ml/tests in a second venv.
5. CI cost: time per file, 30 slowest tests, savings.

Status: in progress.
