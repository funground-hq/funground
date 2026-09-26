"""Blend modes, opacity and shadows

p.blend_mode() changes how new drawing mixes with what is already on the canvas: "multiply"
darkens like overlapping inks, "screen" lightens like overlapping lights. p.opacity() makes
everything after it see-through, and p.shadow() gives it a soft shadow.
"""
import playground as p


def trio(x, y, mode, label_colour="black"):
    p.blend_mode(mode)
    p.no_stroke()
    for dx, dy, colour in [(0, 0, "red"), (40, 0, "lime"), (20, 34, "blue")]:
        p.fill(colour)
        p.circle(x + dx, y + dy, 70)
    p.blend_mode("normal")
    p.fill(label_colour)
    p.text_align("center")
    p.text(mode, x + 20, y + 80)
    p.text_align("left")


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill((40, 40, 40))
    p.rect(320, 0, 320, 200)                          # a dark half, so "screen" and "add" show
    p.text_size(16)
    trio(60, 60, "normal")
    trio(200, 60, "multiply")
    trio(390, 60, "screen", "white")
    trio(530, 60, "add", "white")

    for i, amount in enumerate([255, 170, 85]):
        p.opacity(amount)
        p.fill("seagreen")
        p.rect(40 + i * 60, 230, 90, 90)
    p.opacity(255)
    p.fill("black")
    p.text("opacity 255, 170, 85", 40, 340)

    p.shadow(6, 8, blur=10)
    p.fill("gold")
    p.stroke("darkgoldenrod")
    p.stroke_width(3)
    p.rect(350, 230, 110, 90)
    p.no_stroke()
    p.fill("tomato")
    p.text_size(32)
    p.text("Shadow", 485, 255)
    p.no_shadow()


p.run()
