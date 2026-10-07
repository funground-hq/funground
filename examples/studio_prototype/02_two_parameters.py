"""A flower in nine versions: petals by size (Play prototype)

Two choices make this flower: how many petals it has, and how big it is. f.variations() with two
parameters tries every pair. Each row is one petal count and each column is one size, so the
sheet reads like a table.

How it works:
- flower(petals, size) makes the flower as a mark, then places it in the middle of the canvas.
- f.variations(flower, petals=[...], size=[...]) gives 3 rows (petals) by 3 columns (size).
- Every cell is shrunk by the same amount, so the big flowers really look bigger.
- Each label names both values, such as "petals = 8, size = 140".
"""
import funground as f

f.size(600, 600, margin=20)
f.background("#efe9df")


def flower(petals, size):
    with f.mark() as bloom:
        f.no_stroke()
        for k in range(petals):
            with f.saved_state():
                f.rotate(k * 360 / petals)
                f.fill("#e07a5f")
                f.ellipse(0, -size * 0.32, size * 0.22, size * 0.6)
        f.fill("#f2cc8f")
        f.circle(0, 0, size * 0.3)
    f.background("#fdf6ec")
    bloom.place(f.ground.cx, f.ground.cy)


f.variations(flower, petals=[5, 8, 13], size=[120, 200, 280])
f.show()
