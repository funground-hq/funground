# 11. Randomness and noise

## Random numbers

| Helper | What it gives |
|---|---|
| `p.random(high)` / `p.random(low, high)` | a random decimal number in the range |
| `p.random_gaussian(mean, sd)` | a number from a bell curve: most near `mean`, about two thirds within `sd` of it |
| `p.random_choice(items)` | one item from a list, tuple or string |
| `p.random_seed(n)` | makes all of the above repeat exactly — the same "random" picture every run |

![Confetti](../gallery/images/randomness-01_confetti.png)

![Bell curve and choices](../gallery/images/randomness-02_gaussian_and_choice.png)

## Noise: smooth randomness

`p.random()` jumps anywhere every time. `p.noise(x)` gives a number from 0 to 1 that changes
**smoothly** as `x` changes — like hills instead of static. Walk slowly along it (small steps in
`x`) for gentle change, quickly for rough change.

| Helper | What it does |
|---|---|
| `p.noise(x)`, `p.noise(x, y)`, `p.noise(x, y, z)` | Smooth value from 0 to 1; with two inputs, a smooth pattern across the window; the third is often time |
| `p.noise_seed(n)` | Picks the pattern, so it repeats every run. The same seed gives the same values as p5.js |
| `p.noise_detail(octaves, falloff)` | Fewer octaves (layers) is smoother and faster; the default is 4 |

```python
import playground as p


def setup():
    p.size(640, 200)
    p.noise_seed(1)


def draw():
    p.background("white")
    p.no_fill()
    p.stroke("tomato")
    p.stroke_width(3)
    p.begin_shape()
    for x in range(0, 641, 4):
        p.vertex(x, 20 + p.noise(x * 0.01, p.frame_count * 0.01) * 160)
    p.end_shape()


p.run()
```

![Noise](../gallery/images/randomness-03_noise.png)

**Speed.** Each `noise()` call takes a few microseconds, so about 1,500 calls per frame keep a
sketch at 60 frames per second. For big textures, use fewer octaves or bigger tiles.
