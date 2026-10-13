"""Probe 1: make a funground PDF with text, a gradient, an image, a blend mode and opacity."""
import os, sys
os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, r"C:\Projects\playground-0.2")
import funground as f

f.size(480, 640)
f.background(255)
f.no_stroke()
f.fill(f.linear_gradient(0, 0, 0, 640, ["midnightblue", "darkorchid", "tomato"]))
f.rect(0, 0, 480, 640)
photo = f.load_image(r"C:\Projects\playground-0.2\examples\gallery\images\data\photo.jpg")
f.image(photo, 40, 300, 200, 150)
f.blend_mode("multiply")
for dx, c in [(0, "red"), (40, "lime"), (20, "blue")]:
    f.fill(c); f.circle(300 + dx, 150, 60)
f.blend_mode("normal")
f.fill(255, 255, 255, 170); f.rect(260, 330, 180, 100, 20)
f.fill("gold"); f.stroke("black"); f.stroke_width(3); f.circle(100, 100, 50)
f.no_stroke(); f.fill("white"); f.text_size(40); f.text("Open Day", 40, 520)
f.fill(0, 0, 0); f.text_size(18); f.text("Black text, real text", 40, 570)
f.save(sys.argv[1])
