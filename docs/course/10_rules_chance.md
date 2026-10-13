# Lesson 10 — Rules, chance and generative work
[← Motion and interaction](09_motion_interaction.md) · [Course index](README.md#the-lessons) · [Make a small visual world →](11_capstone.md)

**Initial lesson draft.** This page has the course's first explanation and assignment. Its worked examples and practice sequence will be expanded to the depth of Lessons 1 and 2.

## The idea

A generative artwork is made with a set of rules. The maker chooses the rules, decides what may vary, and selects what to keep. Randomness can help produce alternatives, but it does not make the design decisions for you.

Use **constraints** to give the work a character. For example: only circles and lines; three colours; a fixed grid; one mark that can rotate but not change size. Change one rule and notice how the family of results changes.

## Experiment: build a small edition

Choose a mark, a page, a palette and one rule for variation. Make a set of outputs. If the results use randomness, record a seed so you can return to a version you like. Compare the outputs and select a small group that feels related without being identical.

```python
import funground as f


def setup():
    f.size(500, 500)
    f.random_seed(12)


def draw():
    f.random_seed(12)  # keep this edition still; change the seed to make another
    f.background("#f3efe6")
    f.no_stroke()

    colours = ["#264653", "#2a9d8f", "#e9c46a", "#e76f51"]
    for row in range(8):
        for col in range(8):
            x = 40 + col * 60
            y = 40 + row * 60
            size = f.random(12, 42)
            colour = f.random_choice(colours)

            f.fill(colour)
            f.circle(x, y, size)


f.run()
```

Run it again with the same seed: the result should repeat. Then change the seed to make another version. The grid stays fixed, so you can focus on how scale and colour vary. Next, restrict the palette or use only three sizes. A rule can make the set more coherent than adding more randomness.

## Assignment

Make a collection of 12 related images from your own rules. Save the code and the outputs. Select three images for a small edition, give the edition a title, and write down why those three belong together.

## Look back

Which decisions came from your rules? Which came from your selection? If every image looks interchangeable, add a constraint. If each image looks unrelated, reduce the number of variables.

## Refer to the guide

[Randomness and noise](../guide/11_randomness_and_noise.md) explains repeatable random values and smooth variation. [Saving your work](../guide/13_saving_your_work.md) covers image, vector and motion exports.


---

[← Motion and interaction](09_motion_interaction.md) · [Course index](README.md#the-lessons) · [Make a small visual world →](11_capstone.md)
