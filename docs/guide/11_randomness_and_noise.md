# 11. Randomness and noise

*Noise is added in Sprint 5 (S-047).*

## Random numbers

| Helper | What it gives |
|---|---|
| `p.random(high)` / `p.random(low, high)` | a random decimal number in the range |
| `p.random_gaussian(mean, sd)` | a number from a bell curve: most near `mean`, about two thirds within `sd` of it |
| `p.random_choice(items)` | one item from a list, tuple or string |
| `p.random_seed(n)` | makes all of the above repeat exactly — the same "random" picture every run |

![Confetti](../gallery/images/randomness-01_confetti.png)

![Bell curve and choices](../gallery/images/randomness-02_gaussian_and_choice.png)
