# Stress: a long text, drawn at a new size every frame.
import funground as f
f.size(600, 400)
WORDS = "the quick brown fox jumps over the lazy dog and keeps on running " * 20
def draw():
    f.background(255)
    f.text_size(8 + (f.frame_count * 0.37) % 60)
    f.text(WORDS[:400] + str(f.frame_count), 10, 50)
f.run()
