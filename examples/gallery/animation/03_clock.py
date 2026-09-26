"""A clock

hour(), minute() and second() read the computer's clock; day(), month() and year() the date.
millis() counts milliseconds since the sketch started and frame_rate() says how many frames per
second it is really drawing.
"""
# gallery: time-dependent
import funground as f


def setup():
    f.size(640, 400)


def hand(angle, length, width, colour):
    with f.saved_state():
        f.translate(200, 200)
        f.rotate(angle - 90)             # 0 degrees points right; clock hands start at 12
        f.stroke(colour)
        f.stroke_width(width)
        f.line(0, 0, length, 0)


def draw():
    f.background("white")
    f.fill("whitesmoke")
    f.stroke("black")
    f.stroke_width(4)
    f.circle(200, 200, 320)
    hand((f.hour() % 12) * 30 + f.minute() * 0.5, 90, 10, "black")
    hand(f.minute() * 6, 130, 6, "black")
    hand(f.second() * 6, 140, 2, "tomato")

    f.fill("black")
    f.text_size(20)
    f.text(f"{f.day():02d}.{f.month():02d}.{f.year()}", 400, 150)
    f.text(f"{f.hour():02d}:{f.minute():02d}:{f.second():02d}", 400, 190)
    f.text_size(14)
    f.text(f"running for {f.millis() / 1000:.1f} s at {f.frame_rate():.0f} fps", 400, 240)


f.run()
