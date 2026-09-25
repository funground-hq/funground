"""Hue-based colour: hsb, hsl and colour objects

p.hsb(hue, saturation, brightness) and p.hsl(hue, saturation, lightness) make colours by hue:
0 red, 120 green, 240 blue, and around again. A tuple always means red, green, blue. p.color()
makes a colour you can read (.hue, .brightness ...), and lerp_color mixes two colours.
"""
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.no_stroke()
    for i in range(24):                               # the colour wheel as a strip
        p.fill(p.hsb(i * 15, 90, 95))
        p.rect(20 + i * 25, 30, 25, 60)
    for i in range(11):                               # one hue, lightness from dark to light
        p.fill(p.hsl(200, 70, i * 10))
        p.rect(20 + i * 54, 110, 54, 60)

    start, end = p.color("tomato"), p.color("royalblue")
    for i in range(11):                               # a blend from one colour to another
        p.fill(p.lerp_color(start, end, i / 10))
        p.circle(47 + i * 54, 230, 44)

    tomato = p.color(255, 99, 71)
    p.fill("black")
    p.text_size(16)
    p.text(f"tomato: red {tomato.red}, green {tomato.green}, blue {tomato.blue}, alpha {tomato.alpha}", 20, 290)
    p.text(f"hue {tomato.hue:.0f}, saturation {tomato.saturation:.0f}, "
           f"brightness {tomato.brightness:.0f}, lightness {tomato.lightness:.0f}", 20, 320)
    p.fill(p.hsb(p.frame_count * 4, 80, 90, 160))   # hue wraps around past 360
    p.circle(560, 330, 70)


p.run()
