# Lesson 4 — Shape, figure and ground
[← Contrast and colour](03_contrast_colour.md) · [Course index](README.md#the-lessons) · [Repetition, rhythm and variation →](05_rhythm_variation.md)

**Initial lesson draft.** This page has the course's first explanation and assignment. Its worked examples and practice sequence will be expanded to the depth of Lessons 1 and 2.

## The idea

A viewer reads a shape in relation to its background. The shape they attend to is the **figure**; the surrounding area is the **ground**. In a silhouette, the outside contour does much of the communicating. A simple shape can suggest an object or idea if its outline is distinctive and the surrounding space supports the reading.

Abstraction means keeping some features and leaving others out. It does not mean making something vague at random. Decide which feature carries the idea: outline, proportion, direction, colour or relationship to another shape.

## Experiment: how few marks are enough?

Draw a simple symbol from two or three shapes. For example, a plant might be a stem and two leaves; a house might be a roof and a doorway. Change its scale and remove one part at a time.

```python
import funground as f


def plant(x, y, scale, colour):
    f.no_fill()
    f.stroke(colour)
    f.stroke_width(5 * scale)
    f.line(x, y, x, y - 70 * scale)
    f.line(x, y - 38 * scale, x - 28 * scale, y - 58 * scale)
    f.line(x, y - 48 * scale, x + 28 * scale, y - 66 * scale)

    f.no_stroke()
    f.fill(colour)
    f.ellipse(x - 38 * scale, y - 68 * scale, 30 * scale, 14 * scale)
    f.ellipse(x + 38 * scale, y - 76 * scale, 30 * scale, 14 * scale)


def setup():
    f.size(600, 300)


def draw():
    f.background("#f3efe6")
    plant(150, 230, 1.0, "#264653")
    plant(300, 230, 0.7, "#e76f51")
    plant(465, 230, 1.2, "#2a9d8f")


f.run()
```

Compare the three plants. Does a smaller version still read as a plant? Which line or leaf could you remove without losing the idea? Try reversing the figure and ground: draw a dark background and make the plant light.

## Assignment

Create a small set of three symbols for a place, club or fictional service. Use the same visual language for all three. Show each symbol at a large and a small size, and simplify until each remains recognisable.

## Look back

Ask someone what they think each symbol means before giving them the answer. Which contour or relationship helped? Which caused a different reading?

## Refer to the guide

Use [Shapes](../guide/03_shapes.md) for primitive geometry and [Paths, clipping and pictures](../guide/09_paths_and_clipping.md) when you want to build or combine custom outlines.


---

[← Contrast and colour](03_contrast_colour.md) · [Course index](README.md#the-lessons) · [Repetition, rhythm and variation →](05_rhythm_variation.md)
