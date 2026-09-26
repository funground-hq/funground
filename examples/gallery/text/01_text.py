"""Text

text_size sets the size in pixels; text is placed by its top-left corner. text_width measures a
message, which is how you centre it.
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("black")
    f.text_size(40)
    message = "Hello, Playground!"
    x = (f.width - f.text_width(message)) / 2      # centred
    f.text(message, x, 60)

    f.text_size(18)
    f.fill("gray40")
    f.text("placed by the top-left corner", 40, 160)
    f.text(3.14159, 40, 200)                        # numbers become text
    f.text(f"frame {f.frame_count}", 40, 240, color="tomato")


f.run()
