"""Rotating squares

Five squares spin at different sizes. Each one is moved to its own spot, turned, then drawn at the
origin.

How it works:
- f.translate() moves the origin, the point (0, 0), to a new place. Everything drawn afterwards is
  measured from there.
- f.rotate() turns everything drawn afterwards, in degrees. f.frame_count * 3 makes it spin.
- f.scale() grows or shrinks what comes next. Here each square is a little bigger than the last.
- The square is drawn with f.rect(-25, -25, 50, 50), so its middle is at the origin and it spins on
  its middle.
- f.push() saves the current transform and style. f.pop() brings them back, so each square starts
  fresh.

Make it yours:
- Change the 3 in f.frame_count * 3: a bigger number spins faster, a negative one spins back.
- Change 18 in i * 18 to make the squares start at different angles.
- Draw an oblong, f.rect(-25, -25, 50, 25), and see that it still spins around the origin.
- Spin around a corner: draw f.rect(0, 0, 50, 50) instead of f.rect(-25, -25, 50, 50).
- Make more squares: change range(5) to range(8), and the 120 in f.translate() to 75.
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.no_stroke()
    for i in range(5):
        f.push()
        f.translate(80 + i * 120, 200)
        f.rotate(f.frame_count * 3 + i * 18)
        f.scale(1 + i * 0.2)
        f.fill((40 + i * 50, 90, 200))
        f.rect(-25, -25, 50, 50)
        f.pop()


f.run()
