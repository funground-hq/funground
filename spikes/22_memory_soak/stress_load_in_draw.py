# Stress: a learner loads an image and a font inside draw(), every frame.
import os
import funground as f
HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = os.path.join(HERE, "..", "..", "examples", "gallery", "images", "data", "photo.jpg")
FONT = os.path.join(HERE, "..", "..", "funground", "fonts", "NotoSansDevanagari-Regular.ttf")
f.size(400, 300)
def draw():
    f.background(240)
    photo = f.load_image(PHOTO)
    f.image(photo, 10, 10, 160, 120)
    f.text_font(f.load_font(FONT))
    f.text("frame " + str(f.frame_count), 20, 200)
f.run()
