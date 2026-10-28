"""Measuring aid only (HACK): import this first so mediapipe.tasks.python.vision imports without cv2/matplotlib."""
import sys, types
for _n in ("cv2", "matplotlib", "matplotlib.pyplot"):
    sys.modules.setdefault(_n, types.ModuleType(_n))
sys.modules["matplotlib"].pyplot = sys.modules["matplotlib.pyplot"]
