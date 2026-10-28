"""Measure spike S-227: S-218's cut-out, then (a) tidy, (b) outline, (b)+(d) snapped to edges.

For each scene and each tolerance it reports, for every stage: IoU against the true mask, false-positive pixels
(specks), false-negative pixels (holes), connected parts, time in ms (median of 50 runs) and points in the outline.
It also runs the moving take (30 frames) to time (a) per frame. Results go to results.json and out/*.png.

Run:  FUNGROUND_HEADLESS=1 .venv/Scripts/python spikes/14_cutout/measure.py
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

import pygame

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import funground as f                                  # noqa: E402

import cutout                                          # noqa: E402
import make_photos                                     # noqa: E402

W, H = 640, 480
RUNS = 50
TOLERANCES = (30, 50, 15)
POINTS = 200
RADIUS = 4
OUT = HERE / "out"


def median_ms(fn, runs: int = RUNS, prepare=None) -> float:
    """The median time of fn() in milliseconds. *prepare* makes a fresh argument for each run, outside the timer."""
    times = []
    for _ in range(runs):
        arg = prepare() if prepare else None
        start = time.perf_counter()
        fn(arg) if prepare else fn()
        times.append((time.perf_counter() - start) * 1000)
    return round(statistics.median(times), 3)


def load_truth(path: Path) -> pygame.mask.Mask:
    return pygame.mask.from_threshold(pygame.image.load(str(path)), (255, 255, 255), (127, 127, 127, 255))


# ------------------------------------------------------------------------------------------ pictures
def sheet_panel(cut: pygame.Surface, label: str, outline=None, font=None) -> pygame.Surface:
    """A cut-out over a green checkerboard at half size, with an optional outline and a label."""
    board = pygame.Surface((W, H))
    for y in range(0, H, 16):
        for x in range(0, W, 16):
            board.fill((40, 200, 120) if (x + y) // 16 % 2 else (30, 160, 96), (x, y, 16, 16))
    board.blit(cut, (0, 0))
    panel = pygame.transform.smoothscale(board, (W // 2, H // 2))
    if outline:
        scaled = [(x / 2, y / 2) for x, y in outline]
        pygame.draw.lines(panel, (255, 230, 0), True, scaled, 1)
        for p in scaled:
            pygame.draw.circle(panel, (230, 30, 30), p, 2)
    panel.blit(font.render(label, True, (255, 255, 255), (0, 0, 0)), (4, 4))
    return panel


def save_sheet(path: Path, panels: list[pygame.Surface]) -> None:
    sheet = pygame.Surface((len(panels) * (W // 2), H // 2))
    for i, panel in enumerate(panels):
        sheet.blit(panel, (i * (W // 2), 0))
    pygame.image.save(sheet, str(path))


# ------------------------------------------------------------------------------------------ one scene
def measure_scene(scene: make_photos.Scene, font) -> dict:
    name = scene.name
    empty = f.load_image(str(HERE / "scenes" / f"{name}_empty.jpg"))
    shot = f.load_image(str(HERE / "scenes" / f"{name}_person.jpg"))
    truth = load_truth(HERE / "scenes" / f"{name}_truth.png")
    results: dict = {"person_pixels": truth.count()}
    for tol in TOLERANCES:
        def cut():
            picture = shot.copy()
            picture.remove_background(empty, tolerance=tol)
            return picture

        raw = cut()
        t_remove = median_ms(lambda p: p.remove_background(empty, tolerance=tol), prepare=shot.copy)
        raw_mask = cutout.mask_from_picture(raw)
        t_to_mask = median_ms(lambda: cutout.mask_from_picture(raw))

        stages = {"S-218": {**cutout.fit(raw_mask, truth), "ms": t_remove}}

        click = (scene.person_x + 25, 250)                  # a click on the shirt
        variants = {"": None, "@click": click}                # keep the largest part, or the part that was clicked
        sweep: dict = {}
        for suffix, at in variants.items():
            tidy_mask = cutout.tidy(raw_mask, at=at)
            stages[f"a_tidy{suffix}"] = {**cutout.fit(tidy_mask, truth),
                                         "ms": median_ms(lambda: cutout.tidy(raw_mask, at=at))}
            if not suffix:
                stages["a_tidy"].update(
                    convert_to_mask_ms=t_to_mask,
                    convert_from_mask_ms=median_ms(lambda: cutout.mask_to_picture(shot, tidy_mask), runs=10))

            points = cutout.outline_points(tidy_mask, POINTS)
            poly = cutout.polygon_to_mask(points, (W, H))
            via_path = cutout.fit(cutout.mask_from_picture(cutout.cut_out_with_path(shot, points)), truth)
            stages[f"b_outline{suffix}"] = {
                **cutout.fit(poly, truth), "ms": median_ms(lambda: cutout.outline_points(tidy_mask, POINTS)),
                "points": len(points), "iou_vs_tidy_mask": cutout.fit(poly, tidy_mask)["iou"],
                "iou_funground_path": via_path["iou"]}

            snapped = cutout.snap_to_edges(points, shot, RADIUS)
            poly_snapped = cutout.polygon_to_mask(snapped, (W, H))
            stages[f"bd_snapped{suffix}"] = {
                **cutout.fit(poly_snapped, truth), "points": len(snapped),
                "ms": median_ms(lambda: cutout.snap_to_edges(points, shot, RADIUS), runs=10)}

            # How the fit depends on the number of points (on the tidied mask).
            sweep[f"by_points{suffix}"] = {
                count: cutout.fit(cutout.polygon_to_mask(cutout.outline_points(tidy_mask, count), (W, H)), truth)["iou"]
                for count in (20, 40, 80, 120, 200, 400)}

            panels = [
                sheet_panel(cutout.picture_to_surface(shot), f"{name}: the shot", font=font),
                sheet_panel(cutout.picture_to_surface(raw), f"S-218 tol {tol}", font=font),
                sheet_panel(cutout.picture_to_surface(cutout.mask_to_picture(shot, tidy_mask)),
                            "(a) tidy" + (" (click)" if suffix else ""), font=font),
                sheet_panel(cutout.picture_to_surface(cutout.cut_out_with_path(shot, points)),
                            f"(b) {len(points)} points", points, font),
                sheet_panel(cutout.picture_to_surface(cutout.cut_out_with_path(shot, snapped)),
                            "(b)+(d) snapped", snapped, font),
            ]
            save_sheet(OUT / f"{name}_tol{tol}{suffix.replace('@', '_')}.png", panels)
        results[f"tol{tol}"] = {"stages": stages, **sweep}
    return results


# ------------------------------------------------------------------------------------------ the moving take
def measure_take(font) -> dict:
    scene = make_photos.SCENES[0]
    empty = f.load_image(str(HERE / "scenes" / f"{scene.name}_empty.jpg"))
    take = make_photos.make_take(30)
    rows = []
    for index, (surface, truth) in enumerate(take):
        picture = cutout.surface_to_picture(surface)
        t0 = time.perf_counter()
        picture.remove_background(empty, tolerance=30)
        t1 = time.perf_counter()
        mask = cutout.mask_from_picture(picture)
        t2 = time.perf_counter()
        tidy = cutout.tidy(mask)
        t3 = time.perf_counter()
        points = cutout.outline_points(tidy, POINTS)
        t4 = time.perf_counter()
        rows.append({
            "remove_ms": (t1 - t0) * 1000, "to_mask_ms": (t2 - t1) * 1000, "tidy_ms": (t3 - t2) * 1000,
            "outline_ms": (t4 - t3) * 1000,
            "iou_raw": cutout.fit(mask, truth)["iou"], "iou_tidy": cutout.fit(tidy, truth)["iou"],
            "iou_outline": cutout.fit(cutout.polygon_to_mask(points, (W, H)), truth)["iou"],
        })
        if index in (0, 14, 29):
            panels = [sheet_panel(surface, f"take frame {index}", font=font),
                      sheet_panel(cutout.picture_to_surface(picture), "S-218 tol 30", font=font),
                      sheet_panel(cutout.picture_to_surface(cutout.mask_to_picture(
                          cutout.surface_to_picture(surface), tidy)), "(a) tidy", font=font)]
            save_sheet(OUT / f"take_frame{index:02d}.png", panels)
    summary = {}
    for key in rows[0]:
        values = [r[key] for r in rows]
        summary[key] = {"median": round(statistics.median(values), 3), "max": round(max(values), 3),
                        "min": round(min(values), 3)}
    return {"frames": len(rows), "summary": summary}


# ------------------------------------------------------------------------------------------ report
def print_table(results: dict) -> None:
    head = f"{'scene':16}{'tol':>4}  {'stage':17}{'IoU':>7}{'FP':>7}{'FN':>7}{'parts':>6}{'ms':>9}{'points':>7}"
    print(head)
    print("-" * len(head))
    for scene, data in results["scenes"].items():
        for key, block in data.items():
            if not key.startswith("tol"):
                continue
            for stage, row in block["stages"].items():
                print(f"{scene:16}{key[3:]:>4}  {stage:17}{row['iou']:7.3f}{row['false_positive']:7d}"
                      f"{row['false_negative']:7d}{row['parts']:6d}{row['ms']:9.3f}{row.get('points', ''):>7}")
    print()
    for scene, data in results["scenes"].items():
        for key, block in data.items():
            if key.startswith("tol"):
                a = block["stages"]["a_tidy"]
                print(f"{scene} {key}: convert to mask {a['convert_to_mask_ms']} ms, "
                      f"from mask (Python, a whole picture) {a['convert_from_mask_ms']} ms; "
                      f"IoU by points {block['by_points']}; with a click {block['by_points@click']}")
    print("\nmoving take (30 frames):")
    for key, v in results["take"]["summary"].items():
        print(f"  {key:12} median {v['median']:8.3f}  min {v['min']:8.3f}  max {v['max']:8.3f}")


def main() -> None:
    pygame.font.init()
    font = pygame.font.Font(None, 20)
    f.size(W, H)
    OUT.mkdir(exist_ok=True)
    results = {"runs": RUNS, "tolerances": TOLERANCES, "pygame_ce": pygame.version.ver,
               "scenes": {s.name: measure_scene(s, font) for s in make_photos.SCENES}}
    results["take"] = measure_take(font)
    (HERE / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print_table(results)


if __name__ == "__main__":
    main()
