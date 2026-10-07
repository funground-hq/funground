"""Rhythm: five spacings side by side (Play prototype)

A row of bars is a rhythm. The space between the bars decides whether it feels tight, calm or
broken up. f.variations() draws the same study five times, once for each gap, as a labelled
contact sheet, so the five rhythms can be compared at a glance.

How it works:
- rhythm(gap) draws one version on the whole canvas, as if it were alone.
- f.variations(rhythm, gap=[...]) calls it once for each gap and shrinks each drawing into a cell.
- Each bar's height comes from f.random(). Every cell starts from the same random seed, so bar 1
  has the same height in every cell. Only the gap changes.
- No f.random_seed() is called, so funground picks a seed and prints it. Put that number in
  f.random_seed() at the top to get this sheet again.
"""
import funground as f

f.size(720, 400, margin=24)
f.background("#f4f1ea")


def rhythm(gap):
    area = f.ground.content
    f.background("#fbfaf6")
    f.no_stroke()
    x = area.left + 20
    count = 0
    while x < area.right - 20:
        tall = 60 + f.random(0, 120)
        f.fill("#d1495b" if count % 4 == 0 else "#2b4c7e")
        f.rect(x, area.cy - tall / 2, 16, tall, 4)
        x += gap
        count += 1


f.variations(rhythm, gap=[20, 28, 36, 50, 72])
f.show()
