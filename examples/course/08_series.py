# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

EVENTS = [
    ("READ", "Sunday · 6 pm", "#e76f51", 3),
    ("DRAW", "Monday · 5 pm", "#2a9d8f", 4),
    ("WALK", "Tuesday · 7 am", "#b77e15", 2),
]

def poster(event):
    title, date, accent, count = event
    f.no_stroke()
    f.fill("#f4f1de")
    f.rect(0, 0, 420, 560)
    f.fill(accent)
    for index in range(count):
        f.circle(70 + index*70, 225, 42)
    f.fill("#1d3557")
    f.text_align("left", "top")
    f.text_style("bold")
    f.text_size(68)
    f.text(title, 30, 55)
    f.text_style("normal")
    f.text_size(22)
    f.text(date, 30, 410)
    f.text_size(18)
    f.text("Town library · all welcome", 30, 465)

f.size(900, 410)
f.background("#ded8cc")
for index, event in enumerate(EVENTS):
    with f.saved_state():
        f.translate(20 + index*295, 20)
        f.scale(0.64)
        poster(event)
f.save("08_series.png")
f.show()
