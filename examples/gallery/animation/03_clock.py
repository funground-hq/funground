"""A clock

hour(), minute() and second() read the computer's clock; day(), month() and year() the date.
millis() counts milliseconds since the sketch started and frame_rate() says how many frames per
second it is really drawing.
"""
# gallery: time-dependent
import playground as p


def setup():
    p.size(640, 400)


def hand(angle, length, width, colour):
    with p.saved_state():
        p.translate(200, 200)
        p.rotate(angle - 90)             # 0 degrees points right; clock hands start at 12
        p.stroke(colour)
        p.stroke_width(width)
        p.line(0, 0, length, 0)


def draw():
    p.background("white")
    p.fill("whitesmoke")
    p.stroke("black")
    p.stroke_width(4)
    p.circle(200, 200, 320)
    hand((p.hour() % 12) * 30 + p.minute() * 0.5, 90, 10, "black")
    hand(p.minute() * 6, 130, 6, "black")
    hand(p.second() * 6, 140, 2, "tomato")

    p.fill("black")
    p.text_size(20)
    p.text(f"{p.day():02d}.{p.month():02d}.{p.year()}", 400, 150)
    p.text(f"{p.hour():02d}:{p.minute():02d}:{p.second():02d}", 400, 190)
    p.text_size(14)
    p.text(f"running for {p.millis() / 1000:.1f} s at {p.frame_rate():.0f} fps", 400, 240)


p.run()
