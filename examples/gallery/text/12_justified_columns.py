"""Justified columns with hyphens

A poster column with two straight edges. f.text_align("justify") stretches the spaces of each line so that
the words reach both sides, and soft hyphens let long words break at the end of a line.

How it works:
- f.text_align("justify") works in f.text_box(). Every line is stretched to the box's width by making
  the spaces between words wider. The letters are never changed.
- The last line of a paragraph stays on the left, and so does a line with one word in it.
- A soft hyphen is a character you cannot see: "\u00ad" in Python. A long word may break there, and a
  hyphen is drawn only at the end of a line that breaks there. Where the word is not broken, nothing shows.
- This sketch writes the soft hyphens as "|" in the story, to make it easy to read, and swaps every "|"
  for a soft hyphen before it draws.
- A line breaks at a space whenever it can. It uses a soft hyphen when a word does not fit in the rest of
  the line.
- f.text_box() hands back the words that did not fit, so the story flows from the first column into the
  second. The thin lines show the columns.

Make it yours:
- Change COLUMN_WIDTH, or the text size in f.text_size(), and watch the breaks move.
- Take out the "|" marks from a word and see it move to the next line, leaving a big gap.
- Change f.text_align("justify") to "left" to see the ragged edge it replaces.
- Write your own story in STORY. Put a "|" inside every long word where it may break.
"""
import funground as f

SOFT_HYPHEN = "\u00ad"
STORY = (
    "A poster is read in a few seconds, from across a room. Its words must be easy to find, so "
    "the column is set with care. An ex|traor|di|nary amount of work goes into the shape of "
    "a para|graph: the space be|tween the words, the length of the lines and the way "
    "a word is bro|ken at the edge.\n"
    "A justified column has two straight edges. It looks tidy, and it makes a good use of the "
    "paper. The price is in the spaces, which grow and shrink from line to line. Hy|phen|ation "
    "helps: with a few well chosen breaks in the long words, the spaces stay even, and the "
    "co|op|er|a|tion of the type|face, the page and the reader is plain to see.\n"
    "Look at the last line of each paragraph. It is not stretched, because there is nothing after it to "
    "line up with. It is the one place where the right edge is allowed to be ragged: the break "
    "tells the eye that a new thought is about to start."
).replace("|", SOFT_HYPHEN)

MARGIN = 40
COLUMN_WIDTH = 270
GUTTER = 40
TOP = 130
HEIGHT = 290


def setup():
    f.size(640, 440)


def draw():
    f.background("ivory")

    f.fill("firebrick")
    f.text_style("bold")
    f.text_size(44)
    f.text("Straight edges", MARGIN, 36)
    f.text_style("normal")
    f.fill("darkslategray")
    f.text_size(16)
    f.text("Justified columns, broken with soft hyphens", MARGIN, 90)

    f.stroke("lightgray")
    f.stroke_width(1)
    f.line(MARGIN, 112, f.width - MARGIN, 112)
    f.no_fill()
    f.rect(MARGIN, TOP, COLUMN_WIDTH, HEIGHT)                       # the edges of the two columns
    f.rect(MARGIN + COLUMN_WIDTH + GUTTER, TOP, COLUMN_WIDTH, HEIGHT)

    f.no_stroke()
    f.fill("black")
    f.text_size(15)
    f.text_align("justify")
    rest = f.text_box(STORY, MARGIN, TOP, COLUMN_WIDTH, HEIGHT)                    # returns what did not fit...
    rest = f.text_box(rest, MARGIN + COLUMN_WIDTH + GUTTER, TOP, COLUMN_WIDTH, HEIGHT)    # ...which flows on
    if rest:
        f.fill("firebrick")
        f.text_align("left")
        f.text("(more did not fit)", MARGIN, f.height - 22)


f.run()
