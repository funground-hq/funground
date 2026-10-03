"""Event poster series

One list of events becomes a whole series of posters. Each event gets its own page, with a
gradient background, a burst of shapes joined and cut with path booleans, a rounded panel, a
bold headline, the details, a line in Hindi and an emoji. The three layers are called
"background", "art" and "words".

The script saves events.pdf (every page, real text), events_1.svg, events_2.svg and so on (live
text, for editing) and events_final_1.svg and so on (text="shapes", for handing over).
The gallery picture shows the last page.

Add an event to EVENTS and run the script again to make another poster.
"""
import math

import funground as f

WIDTH, HEIGHT = 480, 680

# Each event: its words, an emoji, and a colour theme (top, bottom, accent, panel text).
EVENTS = [
    {"title": "Book Fair", "date": "Sat 14 March, 10 am", "place": "Town Library, Hall B",
     "line": "किताबें पढ़ो, सपने गढ़ो", "emoji": "📚", "points": 10,
     "theme": ((38, 70, 140), (120, 70, 170), (255, 196, 61), (38, 40, 90))},
    {"title": "Music Night", "date": "Fri 21 March, 7 pm", "place": "Riverside Garden",
     "line": "सुर और ताल की शाम", "emoji": "🎶", "points": 14,
     "theme": ((20, 90, 90), (40, 150, 120), (255, 140, 105), (10, 60, 60))},
    {"title": "Spring Mela", "date": "Sun 30 March, 11 am", "place": "School Playground",
     "line": "वसंत मेले में आइए", "emoji": "🎪", "points": 18,
     "theme": ((170, 40, 90), (240, 120, 60), (255, 230, 120), (110, 20, 60))},
]


def burst(cx, cy, outer, inner, points):
    """A star with many points, as a path."""
    corners = []
    for i in range(points * 2):
        r = outer if i % 2 == 0 else inner
        angle = math.radians(-90 + i * 180 / points)
        corners.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return f.path().polygon(corners)


def background_layer(top, bottom):
    with f.layer("background"):
        f.no_stroke()
        f.fill(f.linear_gradient(0, 0, 0, HEIGHT, [top, bottom]))
        f.rect(0, 0, WIDTH, HEIGHT)


def art_layer(event):
    top, bottom, accent, ink = event["theme"]
    with f.layer("art"):
        f.no_stroke()
        # A glow: a big burst joined to a disc.
        glow = burst(240, 250, 200, 145, event["points"]) | f.path().circle(240, 250, 330)
        f.fill(accent[0], accent[1], accent[2], 70)
        f.draw_path(glow)
        # A ring: a disc with a smaller disc cut out of it.
        ring = f.path().circle(240, 250, 300) - f.path().circle(240, 250, 290)
        f.fill(255, 255, 255, 120)
        f.draw_path(ring)
        # A sun: a bright burst with a crescent bitten out of it.
        sun = burst(240, 250, 150, 112, event["points"]) - f.path().circle(290, 215, 120)
        f.fill(f.linear_gradient(0, 100, 0, 400, [accent, (255, 255, 255)]))
        f.draw_path(sun)
        # The rounded panel for the details.
        f.fill(255, 255, 255, 235)
        f.rect(36, 440, 408, 200, 34)
        f.fill(accent)
        f.rect(200, 456, 80, 6, 3)


def words_layer(event):
    top, bottom, accent, ink = event["theme"]
    with f.layer("words"):
        f.no_stroke()
        # The headline mixes a bold word with an italic one in the accent colour.
        words = event["title"].split(" ")
        headline = f.FormattedString()
        headline.append(words[0] + " ", size=54, style="bold", color=(255, 255, 255))
        headline.append(" ".join(words[1:]), size=54, style="bold_italic", color=accent)
        f.text_align("center", "top")
        f.text(headline, 240, 40)
        # The emoji sits in the middle of the sun.
        f.fill(ink)
        f.text_size(90)
        f.text_align("center", "center")
        f.text(event["emoji"], 240, 250)
        # The details, wrapped in a box.
        details = f.FormattedString()
        details.append(event["date"] + "\n", size=24, style="bold", color=ink)
        details.append(event["place"], size=20, color=ink)
        f.text_align("center", "top")
        f.text_box(details, 56, 474, 368, 80)
        # A line in another script. The built-in fallback fonts draw it.
        f.fill(ink)
        f.text_size(24)
        f.text_align("center", "center")
        f.text(event["line"], 240, 600)


def make_poster(event):
    top, bottom = event["theme"][0], event["theme"][1]
    background_layer(top, bottom)
    art_layer(event)
    words_layer(event)


# Each event is one page. The first new_page starts the document.
for event in EVENTS:
    f.new_page(WIDTH, HEIGHT)
    make_poster(event)

f.save("events.pdf")                        # one PDF, every page, layers and real text
f.save("events.svg")                        # events_1.svg, events_2.svg, ... live text
f.save("events_final.svg", text="shapes")   # for handing over: every letter is a shape
f.save("events_final.pdf", text="shapes")
f.show()
