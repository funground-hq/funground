# Lesson 6 — Type, words and hierarchy
[← Repetition, rhythm and variation](05_rhythm_variation.md) · [Course index](README.md#the-lessons) · [Make a cover →](07_cover.md)

**Initial lesson draft.** This page has the course's first explanation and assignment. Its worked examples and practice sequence will be expanded to the depth of Lessons 1 and 2.

## The idea

Typography is the design of written language. A type choice can suggest a voice, but the first job of type is to let the reader find and understand the words. Size, weight, spacing, alignment and position create hierarchy.

Try reading a design at three distances: close up, at normal size and as a small thumbnail. A title that works only when enlarged may not work as a poster or cover. Use fewer type styles than you think you need; contrast between two well-chosen sizes is often enough.

## Experiment: one title, three hierarchies

Use a short phrase, such as **NIGHT GARDEN**. Make three versions: large title and small detail; title and detail at similar sizes; small title with a large visual mark. Keep the words and colour fixed.

```python
import funground as f


def title_card(title_size, detail_size, title_y):
    f.fill("#1d3557")
    f.text_size(title_size)
    f.text_style("bold")
    f.text_align("left", "top")
    f.text("NIGHT GARDEN", 40, title_y)

    f.fill("#e76f51")
    f.text_size(detail_size)
    f.text_style("normal")
    f.text("A small exhibition of plants after dark", 40, 210)


def setup():
    f.size(640, 300)


def draw():
    f.background("#f4f1de")
    title_card(54, 16, 55)


f.run()
```

Change the title and detail sizes, then move the title. To compare three versions at once, copy the card into three panels and adjust the x positions. Keep the text readable while changing emphasis.

## Assignment

Choose a short phrase and design a title card for it. Make three hierarchy studies before choosing one. Then make a second card for a different audience using the same words. What changed: the type scale, the spacing, the voice, or the supporting image?

## Look back

Cover the design and reveal it from top to bottom. What do you notice first? Ask a viewer to read the words in order. If they skip a detail you consider essential, make its role clearer.

## Refer to the guide

[Text](../guide/06_text.md) explains text functions, alignment and styles. [Saving your work](../guide/13_saving_your_work.md) explains exporting images and vector files.


---

[← Repetition, rhythm and variation](05_rhythm_variation.md) · [Course index](README.md#the-lessons) · [Make a cover →](07_cover.md)
