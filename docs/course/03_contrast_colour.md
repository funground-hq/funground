# Lesson 3 — Contrast and colour
[← Visual weight, balance and hierarchy](02_weight_balance_hierarchy.md) · [Course index](README.md#the-lessons) · [Shape, figure and ground →](04_shape_figure_ground.md)

**Initial lesson draft.** This page has the course's first explanation and assignment. Its worked examples and practice sequence will be expanded to the depth of Lessons 1 and 2.

## The idea

Contrast is a visible difference: light against dark, large against small, smooth against rough, quiet against busy. Contrast can make an element stand out, but too many competing contrasts make a page noisy.

Colour is one kind of contrast. A useful first step is to separate **hue** (the colour family) from **value** (how light or dark it is). Two colours can have different hues but similar values, so text may be hard to read. A limited palette helps the parts of a design belong together.

## Experiment: test the same message in two palettes

Use the same shapes and layout in both panels. Change only the colours. Which version has clearer contrast? Which one feels warmer, calmer or more urgent?

```python
import funground as f


def panel(left, paper, ink, accent):
    f.no_stroke()
    f.fill(paper)
    f.rect(left, 0, 280, 260)

    f.fill(accent)
    f.circle(left + 72, 82, 56)

    f.fill(ink)
    f.rect(left + 122, 54, 116, 10)
    f.rect(left + 122, 78, 84, 10)
    f.rect(left + 42, 158, 196, 50)


def setup():
    f.size(600, 300)


def draw():
    f.background("#ded8cc")
    panel(10, "#f4f1de", "#1d3557", "#e76f51")
    panel(310, "#274c5e", "#d5e4d5", "#e9c46a")


f.run()
```

The bars stand in for text: the test is about which elements separate clearly from their background. When you replace them with real words, check the reading at a small size too.

## Try these changes

1. Keep the palette, but swap the ink and accent roles.
2. Make the background and ink closer in value. Notice when the bars stop being easy to see.
3. Use only two colours, then add one accent. Give that accent a job: highlight a date, button or key idea.

## Assignment

Choose a mood—**festive**, **serious**, **gentle**, or **warning**—and make two colour treatments for the same simple card. Keep the layout fixed. Write down which colour decision carries most of the mood and which information must remain readable.

## Look back

Check the design from farther away or as a small thumbnail. Does the important element still stand out? If you have a printer, compare a colour print with a black-and-white version.

## Refer to the guide

The [Colour](../guide/04_colour.md) chapter covers colour values and modes. The [Text](../guide/06_text.md) chapter helps check readable text.


---

[← Visual weight, balance and hierarchy](02_weight_balance_hierarchy.md) · [Course index](README.md#the-lessons) · [Shape, figure and ground →](04_shape_figure_ground.md)
