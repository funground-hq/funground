"""Run one sketch file in its own process: python run_sketch.py sketches/1_1_circle.py out_dir
Runs the sketch headless, then saves the canvas as SVG and PNG."""
import os
import runpy
import sys

os.environ["FUNGROUND_HEADLESS"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import funground as f   # noqa: E402
f.random_seed(7)          # the book needs the same picture every build
sketch, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
os.makedirs(outdir, exist_ok=True)
stem = os.path.splitext(os.path.basename(sketch))[0]
runpy.run_path(sketch, run_name="__main__")      # the sketch ends with f.show(), which returns at once when headless
f.save(os.path.join(outdir, stem + ".svg"))
f.save(os.path.join(outdir, stem + ".png"), dpi=300)
print("ok", stem, f.width, f.height)
