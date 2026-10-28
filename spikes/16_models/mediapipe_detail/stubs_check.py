"""HACK (labelled): run tasks_check.py with empty stand-ins for cv2 and matplotlib.
mediapipe.tasks.python.vision imports drawing_utils, which imports both at top level but needs them only to draw.
Usage: python -I stubs_check.py MODELS_DIR IMAGES_DIR"""
import sys, types, runpy, os
for name in ("cv2", "matplotlib", "matplotlib.pyplot"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["matplotlib"].pyplot = sys.modules["matplotlib.pyplot"]
sys.argv[0] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks_check.py")
runpy.run_path(sys.argv[0], run_name="__main__")
