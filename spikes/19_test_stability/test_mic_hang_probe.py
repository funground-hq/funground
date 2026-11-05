"""Spike 19: does pytest-timeout fire when the main thread is stuck in SDL holding the GIL? Not part of the suite."""
import os, subprocess, sys
from pathlib import Path

def test_probe():
    os.environ.pop("FUNGROUND_HEADLESS", None)
    import runpy
    sys.argv = ["x", "300"]
    runpy.run_path(str(Path(__file__).with_name("mic_deadlock.py")), run_name="__main__")
