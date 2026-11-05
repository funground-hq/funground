"""Spike 19: a started microphone, then pygame.quit() while the GIL is busy (tests/conftest.py's _fresh_state calls
pygame.quit() after every test). Usage: python mic_quit_deadlock.py ROUNDS"""
import faulthandler, os, sys, time
os.environ.setdefault("SDL_AUDIODRIVER", "dummy"); os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.pop("FUNGROUND_HEADLESS", None)
import pygame
from funground.sound import _microphone as m
rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 200
keep = []
for i in range(rounds):
    faulthandler.dump_traceback_later(20, exit=True)
    mic = m.make(); mic.start(); keep.append(mic)      # kept alive: only pygame.quit() can stop its device
    t = time.perf_counter()
    while time.perf_counter() - t < 0.02:
        sum(range(2000))
    pygame.quit()
faulthandler.cancel_dump_traceback_later()
print("ok", rounds)
