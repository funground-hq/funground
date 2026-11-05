"""Random stateful beginner programs, generated with Hypothesis (derandomised, so a seed repeats them)."""
from __future__ import annotations

from hypothesis import HealthCheck, given, settings, strategies as st

NUM = st.one_of(
    st.integers(-50, 400).map(str),
    st.sampled_from(["0", "-1", "1e9", "1e-9", "float('nan')", "float('inf')", "-float('inf')", "0.5", "True"]),
)
TXT = st.sampled_from(["'hi'", "''", "'🎨😀'", "'שלום'", "'नमस्ते दुनिया'", "'\\ud800'", "'a' * 2000",
                       "'line\\nbreak'", "'\\t'", "42", "None"])
COL = st.sampled_from(["'tomato'", "'tomatoe'", "'#fff'", "'#12'", "(255, 0, 0)", "(255, 0)", "300", "-5",
                       "None", "f.hsb(200, 50, 50)", "f.cmyk(0, 80, 90, 0)", "float('nan')"])


import os
if os.environ.get("FUZZ_SANE"):
    NUM = st.integers(-20, 300).map(str)
    TXT = st.sampled_from(["'hi'", "''", "'🎨😀'", "'שלום'", "'नमस्ते दुनिया'", "'a' * 300", "'line\\nbreak'", "42"])
    COL = st.sampled_from(["'tomato'", "'#FF8800'", "(255, 0, 0)", "(0, 0, 255, 128)", "f.hsb(200, 50, 50)",
                           "f.cmyk(0, 80, 90, 0)", "120"])


def _n(k):
    return st.tuples(*([NUM] * k)).map(", ".join)


STEP = st.one_of(
    st.just("f.push()"), st.just("f.pop()"),
    st.just("f.begin_shape()"), st.just("f.end_shape()"), st.just("f.end_shape(close=True)"),
    st.just("f.begin_contour()"), st.just("f.end_contour()"),
    _n(2).map(lambda a: f"f.vertex({a})"), _n(2).map(lambda a: f"f.curve_vertex({a})"),
    _n(6).map(lambda a: f"f.bezier_vertex({a})"), _n(4).map(lambda a: f"f.quadratic_vertex({a})"),
    _n(3).map(lambda a: f"f.circle({a})"), _n(4).map(lambda a: f"f.rect({a})"),
    _n(4).map(lambda a: f"f.line({a})"), _n(6).map(lambda a: f"f.arc({a})"),
    _n(1).map(lambda a: f"f.rotate({a})"), _n(2).map(lambda a: f"f.translate({a})"),
    _n(1).map(lambda a: f"f.scale({a})"), _n(1).map(lambda a: f"f.stroke_width({a})"),
    _n(1).map(lambda a: f"f.text_size({a})"), _n(1).map(lambda a: f"f.text_leading({a})"),
    _n(1).map(lambda a: f"f.text_tracking({a})"),
    st.sampled_from(["f.text_font(None)", "f.text_font('serif')", "f.text_font('Comic Sans')", "f.text_style('bold')"]),
    st.tuples(TXT, _n(2)).map(lambda a: f"f.text({a[0]}, {a[1]})"),
    st.tuples(TXT, _n(4)).map(lambda a: f"f.text_box({a[0]}, {a[1]})"),
    COL.map(lambda c: f"f.fill({c})"), COL.map(lambda c: f"f.stroke({c})"), COL.map(lambda c: f"f.background({c})"),
    st.just("f.no_fill()"), st.just("f.no_stroke()"),
    _n(1).map(lambda a: f"f.opacity({a})"),
    st.sampled_from(["f.layer('a').__enter__()", "f.new_page()", "f.save('mid.png')", "f.save('mid.pdf')",
                     "f.save('mid.svg')", "f.size(120, 90)", "f.resize_canvas(150, 100)",
                     "f.clip(f.path().circle(50, 50, 40))", "f.no_clip()", "f.shadow(3, 3, 4, 'black')",
                     "f.blend_mode('multiply')", "f.erase()", "f.no_erase()", "f.apply_filter('blur', 2)",
                     "f.load_pixels()", "f.update_pixels()", "f.stroke_dash(4, 2)", "f.stroke_dash(0)",
                     "f.color_mode('hsb')", "f.color_mode('rgb', 1)", "f.rect_mode('center')"]),
)

BLOCK = st.recursive(
    STEP.map(lambda s: [s]),
    lambda inner: st.one_of(
        st.tuples(st.sampled_from(["with f.layer('L'):", "with f.saved_state():", "with f.layer('L2'):"]),
                  st.lists(inner, min_size=1, max_size=4)).map(
            lambda t: [t[0]] + ["    " + ln for blk in t[1] for ln in blk]),
    ),
    max_leaves=6,
)

PROG = st.tuples(
    st.sampled_from(["f.size(200, 150)", "f.size(200, 150)", "f.size('A5')", ""]),
    st.lists(BLOCK, min_size=1, max_size=20),
    st.booleans(),
)


def make_programs(n, seed):
    progs = []

    @settings(max_examples=n, derandomize=True, database=None, deadline=None,
              suppress_health_check=list(HealthCheck))
    @given(PROG)
    def collect(p):
        head, blocks, animated = p
        body = [ln for b in blocks for ln in b]
        if animated:
            src = ["def setup():", "    " + (head or "pass"), "    f.save_gif('out.gif', 0.1)",
                   "def draw():"] + ["    " + ln for ln in body] + ["f.run(max_frames=8)"]
        else:
            src = ([head] if head else []) + body
        progs.append({"name": "program", "kind": "animated" if animated else "script",
                      "src": "\n".join(src), "seed": seed})

    collect()
    return progs[:n]
