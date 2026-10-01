"""File-size cost of the invisible layer on a text-heavy page (40 lines, ~2,400 characters)."""
from common import *
from exp2_invisible_layer import add_invisible_layer
words = "The quick brown fox jumps over the lazy dog while fifty office staff file final affluent reports. ".split()
lines = []
for i in range(40):
    lines.append(" ".join(words[(i * 7 + k) % len(words)] for k in range(9)))
import common
base = os.path.join(OUT, "exp5_base.pdf"); runs = make_base(base, samples=lines)
lay = os.path.join(OUT, "exp5_layered.pdf"); add_invisible_layer(base, lay, runs, actual_text=False, mode="tm")
b, l = os.path.getsize(base), os.path.getsize(lay)
print(f"{sum(len(x) for x in lines)} chars; outlines only {b:,} B; with invisible layer {l:,} B; cost {l-b:,} B (+{(l-b)/b:.0%})")
