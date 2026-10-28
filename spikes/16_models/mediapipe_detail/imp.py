"""Import-check: python -I imp.py  -> prints the first import error or OK."""
import traceback
try:
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision, audio
    print("OK", mp.__version__)
except Exception as e:
    print("FAIL", type(e).__name__, e)
