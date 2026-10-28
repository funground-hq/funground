"""Spike S-225: the test chapter's spreads as pages for the site, one spread a page, with Previous and Next.

Run after build.py:

    .venv/Scripts/python spikes/15_book/make/site_pages.py

It writes docs/book/ in this repository (README.md and spread_<n>.md, and the spread pictures in docs/book/images/).
The site's assemble.py copies docs/book/ to book/. The Square trim is shown, day and night; the PDFs of both trims
are linked. Standard library only.
"""

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
ROOT = HERE.parents[2]
BOOK = ROOT / "docs" / "book"
TRIM = "Square"            # the trim shown on the site, until the maintainer chooses one
PDFS = "../../spikes/15_book/make/out"   # from docs/book/; the site rewrites these links to GitHub

# (title, what the spread shows): the spreads in build.py's PAGES order, two pages each
SPREADS = [
    ("The opener", "A picture drawn by a funground sketch, and the chapter's first page: its title, one sentence and "
                   "what is in it."),
    ("1.1 One circle", "Show: the whole sketch on the left, with notes beside its lines; its picture on the right."),
    ("1.2 Add a square: predict", "Predict: two new lines in gold. The right page is an empty frame: draw what you "
                                  "think the picture will be, then turn the page."),
    ("1.2 Add a square: reveal", "Reveal: the real picture, then a Compare strip that changes one value, and a Try "
                                 "this task for Play."),
    ("1.3 Somewhere random", "Show: the same circle at a random place, drawn many times."),
    ("1.4 Your page", "An empty canvas and a prompt, and the colophon: how the book was made."),
]


def nav(n: int, bottom: bool) -> list[str]:
    parts = []
    if n > 1:
        parts.append(f"[‹ Previous: {SPREADS[n - 2][0]}](spread_{n - 1}.md){{ rel=prev }}")
    if bottom:
        parts.append("[All spreads](README.md)")
    if n < len(SPREADS):
        parts.append(f"[Next: {SPREADS[n][0]} ›](spread_{n + 1}.md){{ rel=next }}")
    return ['<nav class="fg-walk fg-walk--steps" aria-label="Previous and next spread" markdown>', "",
            " ".join(parts), "", "</nav>", ""]


def spread_page(n: int) -> str:
    title, about = SPREADS[n - 1]
    lines = ["---", "hide:", "  - navigation", "---", "",
             '<nav class="fg-walk fg-walk--crumb" aria-label="Breadcrumb" markdown>', "",
             f"[A funground book](README.md) › Spread {n} of {len(SPREADS)}", "", "</nav>", ""]
    lines += nav(n, bottom=False)
    lines += [f"# {title}", "", about, "",
              f"![Spread {n}, day: {title}](images/spread_{n}.png)", "",
              "**Night**, for reading on a screen:", "",
              f"![Spread {n}, night: {title}](images/spread_{n}_night.png)", ""]
    if n == 2:
        lines += ["The same spread at night with the sketch's own background in midnightblue, to compare:", "",
                  "![Spread 2, night, with a midnightblue sketch](images/spread_2_night_2b.png)", ""]
    lines += nav(n, bottom=True)
    return "\n".join(lines)


def index_page() -> str:
    lines = [
        "# A funground book: Chapter 1",
        "",
        "A test chapter of a book for learning to draw with code, laid out and drawn entirely by funground. It is "
        "work in progress (story S-225): the page size and the details may change.",
        "",
        "Each spread is two facing pages. The pictures are made by running the sketches the pages show, so the code "
        "and its picture always agree.",
        "",
        "## The spreads",
        "",
    ]
    lines += [f"{n}. [{title}](spread_{n}.md)" for n, (title, _) in enumerate(SPREADS, 1)]
    lines += [
        "",
        "## The PDFs",
        "",
        "Two page sizes are being tried: Square (21 cm) and B5 (17.6 x 25 cm). The pages above are Square.",
        "",
        "| | Square | B5 |",
        "|---|---|---|",
        f"| Day, for screen | [PDF]({PDFS}/chapter_Square_screen.pdf) | [PDF]({PDFS}/chapter_B5_screen.pdf) |",
        f"| Night, for screen | [PDF]({PDFS}/chapter_Square_screen_night.pdf) | "
        f"[PDF]({PDFS}/chapter_B5_screen_night.pdf) |",
        "",
        "In a PDF reader, choose the two-page view with the cover shown on its own, to see the spreads.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    images = BOOK / "images"
    images.mkdir(parents=True, exist_ok=True)
    for n in range(1, len(SPREADS) + 1):
        shutil.copyfile(OUT / f"spread_{TRIM}_{n}.png", images / f"spread_{n}.png")
        shutil.copyfile(OUT / f"spread_{TRIM}_night_{n}.png", images / f"spread_{n}_night.png")
        (BOOK / f"spread_{n}.md").write_text(spread_page(n), encoding="utf-8")
    shutil.copyfile(OUT / f"spread_{TRIM}_night_2b.png", images / "spread_2_night_2b.png")
    (BOOK / "README.md").write_text(index_page(), encoding="utf-8")
    print(f"wrote {BOOK.relative_to(ROOT)}: {len(SPREADS)} spreads")


if __name__ == "__main__":
    main()
