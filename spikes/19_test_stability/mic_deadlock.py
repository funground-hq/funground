"""Spike 19: does stopping/closing an SDL capture device while its Python callback waits for the GIL deadlock?

Run in a child with a hard outer timeout; faulthandler dumps every thread if it hangs.
Usage: python mic_deadlock.py ROUNDS
"""
import faulthandler, os, sys, time
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.pop("FUNGROUND_HEADLESS", None)          # CI does not set it: the guide opens a real capture device
faulthandler.dump_traceback_later(20, exit=True)    # a C-level watchdog: needs no GIL
from funground.sound import _microphone as m

rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 200
for i in range(rounds):
    mic = m.make()
    mic.start()
    t = time.perf_counter()
    while time.perf_counter() - t < 0.02:            # keep the GIL busy, like drawing frames
        sum(range(2000))
    mic.close()                                       # pause(1) then close(): SDL locks the device / joins its thread
    faulthandler.dump_traceback_later(20, exit=True)
print("ok", rounds)
