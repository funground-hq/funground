"""Smooth noise, ported from p5.js (S-047, contract H4).

The algorithm, the lattice size, the octave rule and the seeding generator are
p5's, so ``noise_seed(n)`` then ``noise(x, y, z)`` gives the same numbers as
``noiseSeed(n)`` / ``noise(x, y, z)`` in p5.js. Without a seed the lattice is
random, as in p5. Negative inputs are mirrored (p5 takes the absolute value).
"""
from __future__ import annotations

import math
import random

PERLIN_YWRAPB = 4
PERLIN_YWRAP = 1 << PERLIN_YWRAPB
PERLIN_ZWRAPB = 8
PERLIN_ZWRAP = 1 << PERLIN_ZWRAPB
PERLIN_SIZE = 4095

_LCG_M, _LCG_A, _LCG_C = 4294967296, 1664525, 1013904223


class Noise:
    def __init__(self) -> None:
        self.octaves = 4
        self.falloff = 0.5
        self._perlin: list[float] | None = None

    def seed(self, value: int | None) -> None:
        """p5's noiseSeed: a linear congruential generator fills the lattice."""
        z = (int(value) if value is not None else int(random.random() * _LCG_M)) & 0xFFFFFFFF
        table = []
        for _ in range(PERLIN_SIZE + 1):
            z = (_LCG_A * z + _LCG_C) % _LCG_M
            table.append(z / _LCG_M)
        self._perlin = table

    def detail(self, octaves: int, falloff: float | None = None) -> None:
        if octaves > 0:
            self.octaves = int(octaves)
        if falloff is not None and falloff > 0:
            self.falloff = float(falloff)

    def __call__(self, x: float, y: float = 0.0, z: float = 0.0) -> float:
        perlin = self._perlin
        if perlin is None:
            perlin = self._perlin = [random.random() for _ in range(PERLIN_SIZE + 1)]
        cos, pi, size = math.cos, math.pi, PERLIN_SIZE      # locals: this loop is the hot path
        x, y, z = abs(x), abs(y), abs(z)
        xi, yi, zi = math.floor(x), math.floor(y), math.floor(z)
        xf, yf, zf = x - xi, y - yi, z - zi
        r = 0.0
        ampl = 0.5
        for _ in range(self.octaves):
            of = xi + (yi << PERLIN_YWRAPB) + (zi << PERLIN_ZWRAPB)
            rxf = 0.5 * (1.0 - cos(xf * pi))
            ryf = 0.5 * (1.0 - cos(yf * pi))
            n1 = perlin[of & size]
            n1 += rxf * (perlin[(of + 1) & size] - n1)
            n2 = perlin[(of + PERLIN_YWRAP) & size]
            n2 += rxf * (perlin[(of + PERLIN_YWRAP + 1) & size] - n2)
            n1 += ryf * (n2 - n1)
            of += PERLIN_ZWRAP
            n2 = perlin[of & size]
            n2 += rxf * (perlin[(of + 1) & size] - n2)
            n3 = perlin[(of + PERLIN_YWRAP) & size]
            n3 += rxf * (perlin[(of + PERLIN_YWRAP + 1) & size] - n3)
            n2 += ryf * (n3 - n2)
            n1 += 0.5 * (1.0 - cos(zf * pi)) * (n2 - n1)
            r += n1 * ampl
            ampl *= self.falloff
            xi <<= 1
            xf *= 2
            yi <<= 1
            yf *= 2
            zi <<= 1
            zf *= 2
            if xf >= 1.0:
                xi += 1
                xf -= 1
            if yf >= 1.0:
                yi += 1
                yf -= 1
            if zf >= 1.0:
                zi += 1
                zf -= 1
        return r
