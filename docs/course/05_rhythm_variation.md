# Lesson 5 — Repetition, rhythm and variation
[← Shape, figure and ground](04_shape_figure_ground.md) · [Course index](README.md#the-lessons) · [Type, words and hierarchy →](06_type_hierarchy.md)

**Initial lesson draft.** This page has the course's first explanation and assignment. Its worked examples and practice sequence will be expanded to the depth of Lessons 1 and 2.

## The idea

Repetition creates order. A repeated mark can also create rhythm: the eye senses a beat, pause or acceleration as size, spacing or direction changes. **Variation** makes a pattern feel alive, but too much variation can hide the rule.

A useful way to design a pattern is to choose one stable rule and one variable. For example, keep the spacing fixed and vary size; or keep size fixed and vary spacing. Code is helpful because it can repeat a mark consistently while you concentrate on the visual rule.

## Experiment: change the beat

Run the sketch and compare the rows. Each uses the same marks; the spacing changes.

```python
import funground as f


def row(y, gaps, sizes, colour):
    x = 40
    f.no_stroke()
    f.fill(colour)
    for gap, size in zip(gaps, sizes):
        x += gap
        f.circle(x, y, size)
        x += size / 2


def setup():
    f.size(640, 300)


def draw():
    f.background("#f3efe6")
    row(70, [24] * 8, [18] * 8, "#264653")
    row(145, [12, 24, 36, 48, 36, 24, 12, 24], [18] * 8, "#e76f51")
    row(220, [24] * 8, [10, 14, 18, 26, 34, 26, 18, 14], "#2a9d8f")


f.run()
```

The first row has a steady beat. The second changes the gaps. The third changes the size. You can make the pattern regular or irregular, but decide what the change should do: build energy, make a pause, point to an accent or suggest a natural variation.

## Assignment

Design a border, textile swatch or small album artwork from one repeated mark. Make three versions: steady, gradually changing and interrupted by a deliberate accent. Save the versions together so they can be compared.

## Look back

Which rule is easiest to notice? Does the accent feel intentional? If the pattern feels messy, reduce the number of things that vary.

## Refer to the guide

[Animation and time](../guide/07_animation_and_time.md) and [Randomness and noise](../guide/11_randomness_and_noise.md) show how repetition can extend into motion and procedural variation.


---

[← Shape, figure and ground](04_shape_figure_ground.md) · [Course index](README.md#the-lessons) · [Type, words and hierarchy →](06_type_hierarchy.md)
