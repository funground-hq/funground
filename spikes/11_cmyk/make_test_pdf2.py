"""Probe 1b: harder case: layers, a gradient with transparent stops (soft mask), a radial gradient, shadow, overlay blend, CMYK-hostile pure colours."""
import os, sys
os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, r"C:\Projects\playground-0.2")
import funground as f
f.size(480, 640); f.background(255); f.no_stroke()
with f.layer("bg"):
    f.fill(f.linear_gradient(0, 0, 480, 0, [(255, 0, 0, 255), (0, 0, 255, 0)])); f.rect(0, 0, 480, 300)
    f.fill(f.linear_gradient(0, 300, 0, 640, ["white", "black"])); f.rect(0, 300, 480, 340)
with f.layer("art"):
    f.shadow(6, 8, blur=10, color=(0, 0, 0, 120)); f.fill("lime"); f.circle(150, 150, 80); f.no_shadow()
    f.blend_mode("overlay"); f.fill(255, 128, 0); f.circle(220, 170, 80); f.blend_mode("normal")
    f.fill(128); f.rect(40, 400, 120, 60); f.fill(0); f.rect(180, 400, 120, 60)
with f.layer("words"):
    f.fill(f.linear_gradient(0, 520, 480, 520, ["cyan", "magenta", "yellow"])); f.text_size(60); f.text("Gradient text", 20, 520)
f.save(sys.argv[1])
