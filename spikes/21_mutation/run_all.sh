#!/bin/bash
# Runs the mutator over each target in order. Clean times measured 07:40 UTC on this container (4 CPUs).
cd "$(dirname "$0")"
export MUT_WORK=/tmp/claude-0/mutwork
DS="--deselect tests/test_paths.py::test_shape_left_open_at_frame_end_is_dropped_with_a_warning --deselect tests/test_paths.py::test_clip_persists_only_for_the_frame_when_used_without_push"
P=../../.venv/bin/python
$P mutate.py funground/vector.py 7 results_vector.json tests/test_vector.py tests/test_semantics.py tests/test_helpers.py
$P mutate.py funground/noise.py 7 results_noise.json tests/test_noise.py tests/test_semantics.py
$P mutate.py funground/color.py 16 results_color.json tests/test_color.py tests/test_colour_objects.py tests/test_cmyk.py tests/test_color_mode.py tests/test_gradients.py
$P mutate.py funground/pathops.py 6 results_pathops.json tests/test_path_booleans.py tests/test_path_outlines.py
$P mutate.py funground/paths.py 7 results_paths.json tests/test_paths.py tests/test_curves.py $DS
$P mutate.py funground/geometry.py 9 results_geometry.json tests/test_geometry.py tests/test_shapes.py tests/test_rounded.py tests/test_curves.py
echo ALL_DONE
