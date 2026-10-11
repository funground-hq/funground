from funground import *

SOFT_HYPHEN = "­"
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
COLUMN_TOP = 130
HEIGHT = 290


def setup():
    size(640, 440)


def draw():
    background(colors.IVORY)

    fill(colors.FIREBRICK)
    text_style(BOLD)
    text_size(44)
    text("Straight edges", MARGIN, 36)
    text_style(NORMAL)
    fill(colors.DARKSLATEGRAY)
    text_size(16)
    text("Justified columns, broken with soft hyphens", MARGIN, 90)

    stroke(colors.LIGHTGRAY)
    stroke_width(1)
    line(MARGIN, 112, width - MARGIN, 112)
    no_fill()
    rect(MARGIN, COLUMN_TOP, COLUMN_WIDTH, HEIGHT)                       # the edges of the two columns
    rect(MARGIN + COLUMN_WIDTH + GUTTER, COLUMN_TOP, COLUMN_WIDTH, HEIGHT)

    no_stroke()
    fill(colors.BLACK)
    text_size(15)
    text_align(JUSTIFY)
    rest = text_box(STORY, MARGIN, COLUMN_TOP, COLUMN_WIDTH, HEIGHT)                    # returns what did not fit...
    rest = text_box(rest, MARGIN + COLUMN_WIDTH + GUTTER, COLUMN_TOP, COLUMN_WIDTH, HEIGHT)    # ...which flows on
    if rest:
        fill(colors.FIREBRICK)
        text_align(LEFT)
        text("(more did not fit)", MARGIN, height - 22)
