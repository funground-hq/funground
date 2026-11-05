#!/bin/bash
# Sound modules. Clean times measured 07:42 UTC: ragas+constants 20.4 s; synth set about 12 s.
# tests/test_sound.py::test_no_device_falls_back_to_a_silent_sound fails on clean main on this Linux
# container ("sound support is not available on this computer"), so it is deselected.
cd "$(dirname "$0")"
export MUT_WORK=/tmp/claude-0/mutwork
P=../../.venv/bin/python
$P mutate.py funground/sound/_swaras.py 62 results_swaras.json tests/test_ragas.py tests/test_constants.py
$P mutate.py funground/sound/_synth.py 38 results_synth.json tests/test_making_sound.py tests/test_drawing_sound.py tests/test_sound.py --deselect tests/test_sound.py::test_no_device_falls_back_to_a_silent_sound
echo SOUND_DONE
