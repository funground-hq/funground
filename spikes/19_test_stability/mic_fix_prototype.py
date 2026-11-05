"""Spike 19: a candidate fix, tried outside the product. Pause the capture device through ctypes, which lets go of
the GIL during the call, so SDL's audio thread can finish a callback that is waiting for the GIL. Once paused, SDL
calls no callback, so pygame's own close() (and the device's dealloc) can no longer deadlock.
Same loop as mic_deadlock.py. Linux only as written (finds pygame-ce's bundled SDL2). Usage: mic_fix_prototype.py ROUNDS [gc]"""
import ctypes, faulthandler, gc, glob, os, sys, time
os.environ.setdefault("SDL_AUDIODRIVER", "dummy"); os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.pop("FUNGROUND_HEADLESS", None)
import pygame
from funground.sound import _microphone as m
libdir = os.path.join(os.path.dirname(os.path.dirname(pygame.__file__)), "pygame_ce.libs")
sdl = ctypes.CDLL(glob.glob(os.path.join(libdir, "libSDL2-2*"))[0])       # the copy pygame already loaded
sdl.SDL_PauseAudioDevice.argtypes = [ctypes.c_uint32, ctypes.c_int]

def pause_without_gil(device, on):
    sdl.SDL_PauseAudioDevice(device.deviceid, on)                       # ctypes releases the GIL here

rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 200
use_gc = len(sys.argv) > 2 and sys.argv[2] == "gc"
for i in range(rounds):
    faulthandler.dump_traceback_later(20, exit=True)
    mic = m.make(); mic.start()
    t = time.perf_counter()
    while time.perf_counter() - t < 0.02:
        sum(range(2000))
    pause_without_gil(mic._device, 1)
    if use_gc:
        ns = {"mic": mic}; ns["self"] = ns; del mic, ns; gc.collect()
    else:
        mic.close()
faulthandler.cancel_dump_traceback_later()
print("ok", rounds)
