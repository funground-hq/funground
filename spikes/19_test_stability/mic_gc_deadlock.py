"""Spike 19: a started microphone that nobody closes, dropped and collected by the cyclic GC while the GIL is busy.
This is what happens to a guide example's microphone: its sketch namespace is a reference cycle, freed later.
Usage: python mic_gc_deadlock.py ROUNDS"""
import faulthandler, gc, os, sys, time
os.environ.setdefault("SDL_AUDIODRIVER", "dummy"); os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.pop("FUNGROUND_HEADLESS", None)
from funground.sound import _microphone as m
rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 200
for i in range(rounds):
    faulthandler.dump_traceback_later(20, exit=True)
    ns = {"mic": m.make()}
    ns["self"] = ns                                   # a cycle, like a sketch's globals
    ns["mic"].start()
    t = time.perf_counter()
    while time.perf_counter() - t < 0.02:
        sum(range(2000))
    del ns
    gc.collect()                                      # frees the AudioDevice: SDL_CloseAudioDevice with the GIL held
print("ok", rounds)
