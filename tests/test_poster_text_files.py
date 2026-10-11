"""Justified text and soft hyphens in saved files (stories S-159 and S-160, contract rows T22 and T23).

A justified line is stretched by its spaces: PDF text is placed glyph by glyph where the picture has the
letters, and an SVG line carries `word-spacing`. In both the words copy as words, with no extra spaces and no
soft hyphens, and a hyphen is there only where a line broke.
"""
from __future__ import annotations

import pytest

pytest.importorskip("pypdfium2")

import funground as f  # noqa: E402

from test_pdf_text import CELL_LIMIT, MEAN_LIMIT, difference, render, save_both, script, texts, words  # noqa: E402
from test_svg_text import content, script as svg_script, texts as svg_texts  # noqa: E402

SHY = "\N{SOFT HYPHEN}"
STORY = ("Posters are read from far away, so the words must be easy to find. A justified column has "
         "two straight edges.")
HYPHENATED = f"Wonderful co{SHY}op{SHY}er{SHY}a{SHY}tion between the inter{SHY}na{SHY}tion{SHY}al committees"


def lines_of(page_text: str) -> list[str]:
    return [" ".join(line.split()) for line in page_text.splitlines() if line.strip()]


def unwrapped(lines: list[str]) -> str:
    """The lines read as one text again: a line that ends in a hyphen goes on without a space."""
    return "".join(line[:-1] if line.endswith("-") else line + " " for line in lines).strip()


# ---------------------------------------------------------------- PDF
def test_justified_text_copies_as_normal_words(tmp_path):
    script(240, 200)
    f.text_size(16)
    f.text_align("justify")
    f.text_box(STORY, 20, 10, 200)
    f.save(str(tmp_path / "a.pdf"))
    for engine in texts(tmp_path / "a.pdf"):
        assert words(engine[0]) == STORY


def test_justified_text_is_where_the_picture_has_it(tmp_path, monkeypatch):
    script(240, 200)
    f.text_size(16)
    f.text_align("justify")
    f.text_box(STORY, 20, 10, 200)
    real, outline = save_both(tmp_path, monkeypatch)
    mean, worst = difference(render(real), render(outline))
    assert mean < MEAN_LIMIT and worst < CELL_LIMIT


def test_a_justified_pdf_line_reaches_the_right_edge(tmp_path):
    import pypdfium2

    script(240, 200)
    f.text_size(16)
    f.text_align("justify")
    f.text_box(STORY, 20, 10, 200)
    f.save(str(tmp_path / "a.pdf"))
    doc = pypdfium2.PdfDocument(str(tmp_path / "a.pdf"))
    textpage = doc[0].get_textpage()
    rights = {}
    for index in range(textpage.count_chars()):
        left, bottom, right, top = textpage.get_charbox(index, loose=True)      # the glyph's own advance box
        if textpage.get_text_range(index, 1).strip():
            rights[round(top)] = max(rights.get(round(top), 0), right)
    doc.close()
    *body, last = (rights[key] for key in sorted(rights, reverse=True))
    assert len(body) >= 3
    for right in body:
        assert right == pytest.approx(220, abs=0.05)
    assert last < 200


def test_soft_hyphens_are_not_in_the_pdf_text(tmp_path):
    script(300, 60)
    f.text_size(20)
    f.text(f"co{SHY}op{SHY}eration", 10, 10)
    f.save(str(tmp_path / "a.pdf"))
    by_pypdf, by_pdfium = texts(tmp_path / "a.pdf")
    assert by_pypdf[0].strip() == "cooperation"
    assert by_pdfium[0].strip() == "cooperation"
    assert SHY not in by_pypdf[0] + by_pdfium[0]


def test_a_broken_word_has_its_hyphen_in_the_pdf_text_and_nothing_else(tmp_path, monkeypatch):
    script(200, 200)
    f.text_size(18)
    f.text_box(HYPHENATED, 10, 10, 110)
    real, outline = save_both(tmp_path, monkeypatch)
    page = texts(real)[0][0]
    assert SHY not in page
    shown = lines_of(page)
    assert any(line.endswith("-") for line in shown)
    assert unwrapped(shown) == HYPHENATED.replace(SHY, "")
    mean, worst = difference(render(real), render(outline))
    assert mean < MEAN_LIMIT and worst < CELL_LIMIT


def test_justified_and_hyphenated_together(tmp_path, monkeypatch):
    script(200, 200)
    f.text_size(18)
    f.text_align("justify")
    f.text_box(HYPHENATED, 10, 10, 150)
    real, outline = save_both(tmp_path, monkeypatch)
    page = texts(real)[0][0]
    assert SHY not in page and "-" in page
    mean, worst = difference(render(real), render(outline))
    assert mean < MEAN_LIMIT and worst < CELL_LIMIT


def test_a_formatted_string_justified_and_hyphenated(tmp_path, monkeypatch):
    script(260, 200)
    fs = (f.FormattedString().append("Wonderful ", size=16)
          .append(f"co{SHY}op{SHY}er", size=16, style="bold").append(f"a{SHY}tion", size=16, style="italic")
          .append(" between the ", size=16).append(f"inter{SHY}na{SHY}tion{SHY}al", size=16, style="bold")
          .append(" committees.", size=16))
    f.text_align("justify")
    f.text_box(fs, 10, 10, 160)
    real, outline = save_both(tmp_path, monkeypatch)
    page = texts(real)[0][0]
    assert SHY not in page
    assert "".join(unwrapped(lines_of(page)).split()) == "Wonderfulcooperationbetweentheinternationalcommittees."
    mean, worst = difference(render(real), render(outline))
    assert mean < MEAN_LIMIT and worst < CELL_LIMIT


# ---------------------------------------------------------------- SVG
def test_a_justified_svg_line_carries_the_word_spacing(tmp_path):
    svg_script(240, 200)
    f.text_size(16)
    f.text_align("justify")
    f.text_box(STORY, 20, 10, 200)
    f.save(str(tmp_path / "a.svg"))
    lines = svg_texts(tmp_path / "a.svg")
    spacing = [t.get("word-spacing") for t in lines]
    assert " ".join(content(t) for t in lines) == STORY
    assert all(s is not None for s in spacing[:-1]) and spacing[-1] is None      # the last line is left
    assert all(float(s) > 0 for s in spacing[:-1])


def test_the_svg_word_spacing_is_what_the_picture_added(tmp_path):
    svg_script(240, 200)
    f.text_size(16)
    f.text_align("justify")
    f.text_box("Posters are read from far away", 20, 10, 190)
    f.save(str(tmp_path / "a.svg"))
    from funground import typography

    line, _ = svg_texts(tmp_path / "a.svg")
    natural = typography.default_font().shape(content(line), 16).advance
    assert float(line.get("word-spacing")) == pytest.approx((190 - natural) / content(line).count(" "), abs=0.001)


def test_svg_text_has_no_soft_hyphen_and_a_hyphen_only_at_a_break(tmp_path):
    svg_script(200, 200)
    f.text_size(18)
    f.text_box(HYPHENATED, 10, 10, 110)
    f.save(str(tmp_path / "a.svg"))
    lines = [content(t) for t in svg_texts(tmp_path / "a.svg")]
    assert all(SHY not in line for line in lines)
    assert any(line.endswith("-") for line in lines)
    assert unwrapped(lines) == HYPHENATED.replace(SHY, "")


def test_a_line_of_only_soft_hyphens_writes_nothing_to_either_file(tmp_path):
    script(200, 80)
    f.text(SHY, 10, 10)
    f.text("after", 10, 40)
    f.save(str(tmp_path / "a.pdf"))
    f.save(str(tmp_path / "a.svg"))
    assert words(texts(tmp_path / "a.pdf")[0][0]) == "after"
    assert [content(t) for t in svg_texts(tmp_path / "a.svg")] == ["after"]
