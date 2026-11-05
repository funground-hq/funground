#!/bin/bash
# Second geometry pass: only the first pass's survivors, with the tests that use flattening, sampling and
# measuring added. Runs beside run_sound.sh (8 test processes on 4 CPUs), so the timeout is 60 s, not 3x.
# Four tests fail on clean main here (conftest.py:86, 'HeadlessPlatform' object has no attribute 'target')
# and are deselected.
cd "$(dirname "$0")"
export MUT_WORK=/tmp/claude-0/mutwork_geo MUT_IDS=results_geometry.json
P=../../.venv/bin/python
$P mutate.py funground/geometry.py 60 results_geometry_pass2.json tests/test_geometry.py tests/test_shapes.py tests/test_rounded.py tests/test_curves.py tests/test_text_points.py tests/test_text_on_path.py tests/test_text_path.py tests/test_transforms.py tests/test_path_booleans.py tests/test_path_outlines.py --deselect tests/test_text_on_path.py::test_it_works_in_a_running_frame --deselect tests/test_transforms.py::test_unbalanced_push_warns_naming_the_count_and_does_not_leak --deselect tests/test_transforms.py::test_top_level_transform_resets_at_the_start_of_the_next_frame --deselect tests/test_transforms.py::test_reset_matrix_keeps_the_hidpi_scale
echo GEO2_DONE
