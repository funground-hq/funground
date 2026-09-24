"""Spike 07 harness: run in each engine's venv:  venv_<engine>/Scripts/python bench.py <engine>

Feeds the same IR frames (scenes.py) to the engine's adapter, presents through
pygame (hidden window) and records per-scene per-resolution timings, PNGs,
feature flags, export replay (Cairo only) and the gradient/native-font checks.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import time
import traceback

os.environ.setdefault("SDL_VIDEODRIVER", "windows")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scenes  # noqa: E402  (also puts the repo root on sys.path)

engine = sys.argv[1]
ad = importlib.import_module(f"adapter_{engine}")
Renderer = getattr(ad, {"cairo": "CairoRenderer", "skia": "SkiaRenderer", "blend2d": "Blend2DRenderer"}[engine])

import pygame  # noqa: E402

RES = ((640, 400), (1280, 720))
FRAMES = 30
results = {"engine": engine, "features": ad.FEATURES, "scenes": {}, "python": sys.version.split()[0]}

pygame.init()
for (w, h) in RES:
    try:
        screen = pygame.display.set_mode((w, h), pygame.HIDDEN)
    except Exception:
        os.environ["SDL_VIDEODRIVER"] = "dummy"; pygame.display.quit(); pygame.display.init()
        screen = pygame.display.set_mode((w, h))
    for name, make in scenes.SCENES.items():
        key = f"{name}@{w}x{h}"
        try:
            # IR generation cost is excluded: frames are built up front.
            frames = [make(w, h, i) for i in range(FRAMES)]
            n_ops = len(frames[0])
            r = Renderer(w, h)
            t_first = time.perf_counter(); r.render(frames[0]); t_first = time.perf_counter() - t_first
            t_draw = t_present = 0.0
            for fr in frames:
                t0 = time.perf_counter(); r.render(fr); t1 = time.perf_counter()
                buf, fmt = r.buffer()
                screen.blit(pygame.image.frombuffer(buf, (w, h), fmt), (0, 0)); pygame.display.flip()
                t2 = time.perf_counter()
                t_draw += t1 - t0; t_present += t2 - t1
            if hasattr(r, "end"): r.end()
            buf, fmt = r.buffer()
            pygame.image.save(pygame.image.frombuffer(buf, (w, h), fmt), os.path.join(HERE, f"{engine}_{name}_{w}x{h}.png"))
            results["scenes"][key] = {
                "ops": n_ops, "draw_ms": round(t_draw / FRAMES * 1000, 2), "present_ms": round(t_present / FRAMES * 1000, 2),
                "first_frame_ms": round(t_first * 1000, 2), "fps": round(FRAMES / (t_draw + t_present), 1),
                "unsupported_ops": getattr(r, "unsupported_ops", 0),
            }
        except Exception as e:
            results["scenes"][key] = {"error": repr(e), "trace": traceback.format_exc()[-800:]}
        print(key, json.dumps(results["scenes"][key])[:200], flush=True)

# gradient support (native API), timed
try:
    t0 = time.perf_counter(); ad.gradient_demo(640, 400); results["gradients_ms_50_rects"] = round((time.perf_counter() - t0) * 1000, 2)
except Exception as e:
    results["gradients_error"] = repr(e)

# export replay through cairo (only meaningful for the cairo adapter; other engines rely on it)
if engine == "cairo":
    ex = {}
    for name in ("A_primitives", "B_paths", "E_text"):
        fr = scenes.SCENES[name](640, 400, 7)
        for kind in ("pdf", "svg"):
            p = os.path.join(HERE, f"export_{name}.{kind}")
            t0 = time.perf_counter(); ad.export(fr, 640, 400, p); ex[f"{name}.{kind}"] = {"bytes": os.path.getsize(p), "ms": round((time.perf_counter() - t0) * 1000, 1)}
    results["export_replay"] = ex

if engine == "blend2d":
    try:
        results["native_font"] = ad.native_font_check(scenes.FONT)
    except Exception as e:
        results["native_font"] = {"ok": False, "error": repr(e)}

pygame.quit()
json.dump(results, open(os.path.join(HERE, f"results_{engine}.json"), "w"), indent=1)
print("done", engine)
