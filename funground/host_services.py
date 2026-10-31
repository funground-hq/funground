"""What the host running the sketch supplies (S-246, ADR-007).

On a computer the host supplies nothing: the sound library opens pygame's mixer and SDL's input itself, and the camera
library opens pygame.camera. In a web page the runner (``web.py``) supplies a mixer, a microphone and a camera, and sets them here for as long as its Session runs. The
libraries read this registry when they need a device, so the core never imports a library.

Each name is None when the host supplies nothing (the camera joined them in S-247).
This is not learner API.
"""
from __future__ import annotations

mixer = None        # the page's mixer (platform/browser_audio.HostMixer), else None: pygame's mixer is used
microphone = None   # the page's microphone (platform/browser_audio.HostMicrophone), else None: SDL's input is used
camera = None       # the page's camera (platform/browser_camera.HostCamera), else None: pygame.camera is used
