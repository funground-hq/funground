# Stress: a new off-screen picture and a new layer name every frame.
import funground as f
f.size(400, 300)
def draw():
    f.background(255)
    g = f.create_graphics(200, 150)
    g.background(200, 0, 0)
    g.circle(100, 75, 50)
    f.image(g, f.frame_count % 200, 50)
    with f.layer("trail " + str(f.frame_count)):
        f.circle(f.frame_count % 400, 200, 5)
f.run()
