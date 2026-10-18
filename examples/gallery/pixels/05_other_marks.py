"""From pixels to marks, step 5: other marks

The dots are only one choice. Press 1, 2 or 3 to change the mark: letters chosen by brightness, so the picture is
written in characters; short lines that turn with brightness, like strokes of a pen; or the words of a sentence,
one per cell, sized by darkness. Each mark gives the same photo a different voice.

How it works:
- MARKS is a string of characters from light to dark. The brightness picks one by its position in the string,
  so dark cells get dense characters like @ and light cells get a dot or a space.
- A line is drawn inside f.saved_state(): f.translate() moves to the cell's centre and f.rotate() turns it by
  an angle that comes from brightness, then f.line() draws it.
- The words come round again and again: the cell's number, modulo the number of words, picks one.
- key_pressed() remembers the chosen mark in a variable; draw() asks which mark to draw.

Make it yours:
- Change MARKS to your own characters, from light to dark.
- Write your own sentence in WORDS.
- Make the lines longer, or let brightness change their width with f.stroke_width().
- Add a fourth mark: a small shape you draw, chosen with the key 4.
"""
import funground as f

WIDTH, HEIGHT = 400, 300
CELL = 14
MARKS = " .:-=+*#%@"                          # from light to dark
WORDS = "light falls on the hills and the house holds the evening".split()
photo = f.load_image("data/photo.jpg")      # used when there is no camera
cam = None
mark = "letters"


def setup():
    global cam
    f.size(WIDTH, HEIGHT)
    f.text_align("center", "center")
    try:
        cam = f.camera()
        cam.start(WIDTH, HEIGHT)
    except RuntimeError:
        cam = None


def key_pressed():
    global mark
    mark = {"1": "letters", "2": "lines", "3": "words"}.get(f.key, mark)


def draw():
    picture = cam.picture() if cam is not None and cam.is_ready() else photo
    f.background("white")
    number = 0
    for y in range(0, HEIGHT, CELL):
        for x in range(0, WIDTH, CELL):
            darkness = 1 - picture.get(min(x + CELL // 2, WIDTH - 1), min(y + CELL // 2, HEIGHT - 1)).brightness / 100
            cx, cy = x + CELL / 2, y + CELL / 2
            if mark == "letters":
                f.fill("black")
                f.text_size(CELL)
                f.text(MARKS[min(len(MARKS) - 1, int(darkness * len(MARKS)))], cx, cy)
            elif mark == "lines":
                with f.saved_state():
                    f.translate(cx, cy)
                    f.rotate(darkness * 180)
                    f.stroke("black")
                    f.stroke_width(1 + 2 * darkness)
                    f.line(-CELL / 2, 0, CELL / 2, 0)
            else:
                f.fill("black")
                f.text_size(4 + darkness * 12)
                f.text(WORDS[number % len(WORDS)], cx, cy)
            number += 1
    f.no_stroke()
    f.fill(0, 0, 0, 170)
    f.rect(0, HEIGHT - 22, WIDTH, 22)
    f.fill("white")
    f.text_size(13)
    f.text(f"{mark}   (keys 1, 2, 3)", WIDTH / 2, HEIGHT - 11)


f.run(fps=12)
