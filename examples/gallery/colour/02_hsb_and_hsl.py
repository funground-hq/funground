"""Hue-based colour: hsb, hsl and colour objects

f.hsb(hue, saturation, brightness) and f.hsl(hue, saturation, lightness) make colours by hue:
0 red, 120 green, 240 blue, and around again. A tuple always means red, green, blue. f.color()
makes a colour you can read (.hue, .brightness ...), and lerp_color mixes two colours.
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.no_stroke()
    for i in range(24):                               # the colour wheel as a strip
        f.fill(f.hsb(i * 15, 90, 95))
        f.rect(20 + i * 25, 30, 25, 60)
    for i in range(11):                               # one hue, lightness from dark to light
        f.fill(f.hsl(200, 70, i * 10))
        f.rect(20 + i * 54, 110, 54, 60)

    start, end = f.color("tomato"), f.color("royalblue")
    for i in range(11):                               # a blend from one colour to another
        f.fill(f.lerp_color(start, end, i / 10))
        f.circle(47 + i * 54, 230, 44)

    tomato = f.color(255, 99, 71)
    f.fill("black")
    f.text_size(16)
    f.text(f"tomato: red {tomato.red}, green {tomato.green}, blue {tomato.blue}, alpha {tomato.alpha}", 20, 290)
    f.text(f"hue {tomato.hue:.0f}, saturation {tomato.saturation:.0f}, "
           f"brightness {tomato.brightness:.0f}, lightness {tomato.lightness:.0f}", 20, 320)
    f.fill(f.hsb(f.frame_count * 4, 80, 90, 160))   # hue wraps around past 360
    f.circle(560, 330, 70)


f.run()
