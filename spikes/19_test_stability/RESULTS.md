# Spike 19: test stability before 0.2

Branch: `cloud/test-stability` (the session accepted this name), from origin/main `bc651ca`. Linux cloud
session (kernel 6.18, 4 CPUs), 2026-11-05, 07:27 to about 08:10 UTC. Every commit carries `[skip ci]`.

Versions unless stated: pygame-ce 2.5.8 (SDL 2.32.10), pycairo 1.29.1, pytest 9.1.1, pytest-timeout 2.4.0, all
from `tests/constraints.txt`. Environment: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`, as CI.

**Update, 5 Nov, on the maintainer's Windows machine (Python 3.14, the main session).** The deadlock happens on Windows too. A fixed
20 ms stop missed it in 900 rounds; varied timing (10 to 80 ms) froze in 3 of 3 runs at `self._device.pause(1)`, and collecting
froze in 1 of 1. The fix did not take the ctypes route below: the audio thread pauses its own device (S-251, D-128). That this was
the CI hang is still unproven. `faulthandler_timeout = 330` is now in `pyproject.toml`: on Windows, with the GIL held in a C call
and `--timeout=2`, it printed every thread's stack at 3 s, so the next hang says where it stopped.

## Summary

| Question | Answer |
|---|---|
| Why did CI hang in `16_sound`? | **A deadlock between SDL's audio thread and the GIL**, in the microphone. Reproduced on Linux every time in a small script; not reproduced in 50 runs of the guide examples themselves. Mechanism measured; that it is *the* CI hang is the best-reasoned cause, unverified on Windows. |
| Why did the 5-minute timeout not fire? | Both pytest-timeout methods need the GIL, and the stuck main thread holds it inside a C call. **Measured**: with `--timeout=5`, neither `thread` nor `signal` fired; a C-level faulthandler watchdog ended the run at 20 s. |
| The unidentified S-245 failure | Not identified. Best candidates: wall-clock budget tests (margins measured below). Unverified. |
| Order and load | One order-dependent test (`test_fallback.py`, fixed, shortest order given); one load-dependent failure (the reverb time budget, 2.41 s against 2.0 s); one error from my own first fix (fixed). |
| Local runs that follow AGENTS.md | **9 tests failed** with `FUNGROUND_HEADLESS=1` set, as AGENTS.md suggests. Fixed (test isolation). |

## 1. Baseline (Python 3.11.18)

`FUNGROUND_HEADLESS=1 .venv/bin/python -m pytest -o addopts="" -q -p no:cacheprovider --timeout=300 --durations=50 --junitxml=... tests`

Result: **9 failed, 4475 passed, 131 skipped in 317.83 s**. All 9 passed when `FUNGROUND_HEADLESS` was unset:
`test_hidpi` (2), `test_paths` (2), `test_sound::test_no_device_falls_back_to_a_silent_sound`,
`test_text_on_path::test_it_works_in_a_running_frame`, `test_transforms` (3). They expect a window, and CI never
sets the variable, so CI was green while a local run that follows AGENTS.md ("Run without a window:
`FUNGROUND_HEADLESS=1`") was red. **Fixed** in `tests/conftest.py`: the autouse fixture clears it (commits
`2c07a0e`, corrected in the next commit, see section 3). Tests that want headless already set it themselves.

Also noted: `test_making_sound.py::test_save_errors` raises an unraisable `AttributeError: 'Wave_write' object has
no attribute '_file'` in `wave.py`'s `__del__` (a warning, not a failure): a `wave.open` that fails half-way is
collected later. Harmless today; a candidate for a tidy `try/finally` in the product.

## 2. The hang in `16_sound`

### What the examples do

Examples 5, 6 and 8 of `docs/guide/16_sound.md` (on both sides of #7) call `sound.microphone()` and `mic.start()`.
`tests/test_guide.py` runs them through `conftest.run_sketch` for 3 frames. **CI does not set
`FUNGROUND_HEADLESS`** (`.github/workflows/tests.yml` sets only the two SDL drivers), so on CI these examples open a
real SDL capture device on the dummy driver. (Locally, with `FUNGROUND_HEADLESS=1`, they get a silent microphone and
never touch SDL, which is one reason local runs never saw this.)

`funground/sound/_microphone.py` opens `pygame._sdl2.audio.AudioDevice(..., callback=on_audio)`. SDL calls
`on_audio` on its own audio thread every 512 samples (11.6 ms); pygame-ce takes the GIL to call it. SDL runs the
callback **while holding the device's lock**.

### The deadlock

```
main thread (holds the GIL)                    SDL audio thread
---------------------------                    ----------------
                                               locks the device
                                               wants the GIL to call on_audio  ...waits
mic.stop() -> device.pause(1)
  SDL_PauseAudioDevice: wants the device lock  ...waits
          (pygame does not let go of the GIL here)
```

Neither can move. The same happens with `device.close()` (SDL waits for the audio thread to end) and when the
`AudioDevice` is **garbage-collected**: its dealloc calls `SDL_CloseAudioDevice` with the GIL held.

### Why nothing ever closes it, and why "near #7"

`Microphone.close()` says "funground calls it when a sketch ends", but nothing in `funground/` calls it
(`grep -rn "close()" funground/sketch.py funground/sound/`). So after example 5 or 6 the device stays open, its
thread keeps asking for the GIL every 11.6 ms, and it is freed only when the cyclic garbage collector collects the
example's namespace (a sketch's globals and functions form a cycle), at an unpredictable moment: in example 6, 7 or
a later test. That fits "near example 7" and "passed on the rerun". It is unverified that this is what happened on
Windows.

### Measurements

| Experiment | Command | Result |
|---|---|---|
| Stop while busy | `timeout -s KILL 60 .venv/bin/python spikes/19_test_stability/mic_deadlock.py 300` (start, 20 ms busy loop, `close()`; up to 300 rounds) | **Hung in 6 of 6 runs.** faulthandler: main thread in `_microphone.py:208` (`self._device.pause(1)`), audio thread in C. |
| Collected while busy | `mic_gc_deadlock.py 300` (start, busy, drop, `gc.collect()`) | **Hung in 5 of 5 runs**, in `gc.collect()`. |
| Does pytest-timeout fire? | `pytest --timeout=5 --timeout-method={thread,signal} spikes/19_test_stability/probe_mic_hang.py` | **Neither fired.** Both runs ended at 21 s by the script's `faulthandler.dump_traceback_later(20, exit=True)`. With `-s`, the log shows only faulthandler's `Timeout (0:00:20)!`. |
| The guide examples as CI runs them | `repeat_guide_sound.sh .venv/bin/python 50 ...` (no `FUNGROUND_HEADLESS`, `--timeout-method=thread`, 3 at once, outer `timeout -s KILL 90`) | **50 of 50 passed.** Linux did not reproduce the CI hang itself. |
| Candidate fix | `mic_fix_prototype.py 300 close` and `... 300 gc`, 3 runs each | **No hang in 1,800 stop/collect cycles.** |

Why pytest-timeout cannot fire here: the `thread` method (always used on Windows) is a Python `threading.Timer`; to
print stacks and exit it must take the GIL. The `signal` method's handler runs only when the main thread returns to
the interpreter. The stuck main thread holds the GIL inside SDL, so both wait for ever. Only a watchdog written in C,
such as `faulthandler.dump_traceback_later`, can act. The job's own `timeout-minutes: 30` was the only limit left,
which matches a 25-minute hang being cancelled by hand.

### The candidate fix (prototype only, not in the product)

`spikes/19_test_stability/mic_fix_prototype.py`: pause the device through `ctypes`, calling the
`SDL_PauseAudioDevice` that pygame-ce bundles, with `device.deviceid`. ctypes lets go of the GIL during the call, so
a callback that is waiting finishes; once paused, SDL calls no more callbacks, so pygame's own `close()` and the
dealloc are then safe. Written for Linux (it finds `pygame_ce.libs/libSDL2-2*.so`); Windows and macOS keep SDL in
other places, so it is not ready for the product. Not committed to the product because it reaches past pygame into
SDL (a provider-boundary question) and cannot be tested on Windows here.

What would settle the CI cause (needs Windows):
1. Run `spikes/19_test_stability/mic_deadlock.py` on Windows with the dummy driver. If it hangs with the main
   thread in `_microphone.py` `stop`, the mechanism is the same there.
2. In CI, add a C-level watchdog so that the next hang prints every thread's stack: for example
   `-o faulthandler_timeout=330` (prints stacks, does not exit) or a conftest `faulthandler.dump_traceback_later(330, exit=True)`
   re-armed per test. And lower the job's `timeout-minutes` so a hang costs less.

## 3. Order and timing

`pytest-randomly 5.0.0` and `pytest-xdist 3.8.0` in `.venv` only. `spikes/19_test_stability/run_seeds.sh`: whole
suite, `-n 4`, `--randomly-seed=S`, no `FUNGROUND_HEADLESS`, outer hard timeout 900 s. While the version runs below
were also running, so the machine had 7+ test processes on 4 CPUs (load average above 7): this doubled as the load
test.

| Seed | conftest | Result |
|---|---|---|
| 1 | origin/main's | 4484 passed, 131 skipped, 124 s |
| 2 | my first fix (`2c07a0e`) | 4484 passed, **1 error**: teardown of `test_capabilities.py::test_unknown_renderer_name_is_an_error` |
| 3 | my first fix | 4483 passed, the same teardown error, and **1 failed: `test_making_sound.py::test_reverb_of_five_seconds_is_quick`**, `assert (1079.636872726 - 1077.224527774) < 2.0`: `reverb(1)` took **2.41 s** against a 2.0 s budget, on worker gw2, load average 8 to 11 on 4 CPUs. It passes alone. It is load, not order: no shorter order makes it fail. |
| 2 again | conftest fixed | 4483 passed, **1 failed: `test_fallback.py::test_the_bundled_fonts_load_only_when_needed`**, `assert set() == {'NotoEmoji-Regular.ttf'}`. Order-dependent: see below. |
| 4 | conftest fixed | **4484 passed**, 131 skipped |
| 5 | conftest fixed | **4484 passed**, 131 skipped, 114 s |
| 6 | both fixes | **4484 passed**, 131 skipped, 102 s |
| 2 again | both fixes | **4484 passed**, 131 skipped, 105 s: the seed that found the order-dependent test is now clean |

**The order-dependent failure.** `test_the_bundled_fonts_load_only_when_needed` clears `typography._bundled_cache`
and checks that shaping an emoji loads Noto Emoji. But `typography._ITEMISE_CACHE` memoises the answer for a whole
text. Guide example `06_text#9` draws `"Hello \U0001F680"`, the same text; if it ran earlier in the same process,
the memo answered and `_bundled()` was never called. Shortest failing order (fails before the fix, passes after):

```
pytest -p no:randomly "tests/test_guide.py::test_complete_examples_run_as_printed[06_text#9]" \
  "tests/test_fallback.py::test_the_bundled_fonts_load_only_when_needed"
```

The product is right (the font had been loaded, earlier). **Fixed** in the test: it clears both caches (commit
`0fcbfab`). In the normal file order `test_fallback.py` runs before `test_guide.py`, which is why CI never saw it;
with `pytest-xdist` it would appear at random.

The seed-2 error was mine: my first fix took the test's own `monkeypatch` in the autouse fixture, so the fixture's
teardown ran before the test's `FUNGROUND_RENDERER=crayon` was undone. It failed alone too, in any order. Fixed in
the next commit with a private `pytest.MonkeyPatch.context()`; `tests/test_capabilities.py` then passed and the 9
headless tests passed with `FUNGROUND_HEADLESS=1` set.

Wall-clock budgets (the most likely cause of a one-off failure on a slow runner; unverified). Measured 6 times
under the load above:

| Test | Budget | Measured under load |
|---|---:|---:|
| `test_making_sound.py::test_reverb_of_five_seconds_is_quick` (the `reverb` call only is timed) | 2.0 s | whole test 0.84 to 1.51 s |
| `test_making_sound.py::test_three_second_tone_is_quick` (per wave) | 0.5 s | whole test 0.21 to 0.36 s |
| `test_rhythm_harmony.py::test_a_three_minute_song_is_quick_enough` | 30 s | 4.9 to 7.1 s |
| `test_pages.py` lines 362 and 419 | 1 s, 10 s | not timed separately |
| `test_pixels.py` line 509 | 2.0 s | not timed separately |

The reverb budget **did fail once** under load (seed 3 above, 2.41 s). A Windows runner is slower than this machine, so the first two have little room. Measuring CPU time
(`time.process_time()`) instead of wall time would keep the budgets just as strict and stop other load counting
against them. That is a change to what the tests measure, so it is for the maintainer.

## 4. Versions

Whole suite, one process, `--timeout=300`, constraints from `tests/constraints.txt`, no `FUNGROUND_HEADLESS`. These
started with my first conftest fix, so the `test_capabilities` teardown error from section 3 is expected in them
and is not a version problem.

| Python | Libraries | Result | Time |
|---|---|---|---:|
| 3.11.18 | pinned | 4475 passed, 9 failed only because `FUNGROUND_HEADLESS=1` was set (section 1) | 318 s |
| 3.12.3 | pinned | **4484 passed**, 131 skipped, plus the known teardown error | 628 s (machine overloaded) |
| 3.13.18 | pinned | first run killed by the kernel for memory at 95% (exit 137, not a test failure); rerun with the final conftest fix: **4484 passed**, 131 skipped, no error | |
| 3.14.6 | pinned | **4484 passed**, 131 skipped, plus the known teardown error | 618 s (machine overloaded) |
| 3.14.6 | newest inside the bounds: pycairo 1.29.2, fonttools 4.68.0, pypdf 6.21.4, uharfbuzz 0.57.0 (pygame-ce, skia-pathops, svgelements unchanged) | **4484 passed**, 131 skipped, plus the known teardown error | 480 s |

No failure depends on the Python version or on the newest libraries. Pixel goldens are compared on Windows only,
so pycairo 1.29.2's known Windows edge change (constraints.txt) cannot show here.

ml: a second venv (Python 3.11, core pinned, then `pip install -e ml`: onnxruntime 1.31.1, numpy 2.4.6).
`pytest ml/tests --timeout=300`: **90 passed in 10.0 s**, no skips, with the real models downloaded to the
git-ignored `ml/tests/.models/`. `pytest tests/test_gallery.py -k models` in that venv: **5 passed, 2 skipped**.
Model files (SHA-256):

```
db0898ae717b76b075d9bf563af315b29562e11f8df5027a1ef07b02bef6d81c  handpose_estimation_mediapipe_2023feb.onnx
3241ac4ad8aa35bdaf33946776db29f7c283a413aa0b0dacb9483594b4531aad  mediapipe_selfie_segmentation.onnx
78ff51c38496b7fc8b8ebdb6cc8c1abb02fa6c38427c6848254cdaba57fcce7c  palm_detection_mediapipe_2023feb.onnx
47fd5599d6fa17608f03e0eb0ae230baa6e597d7e8a2c8199fe00abea55a701f  person_detection_mediapipe_2023mar.onnx
9d89c599319a18fb7d2e28451a883476164543182bafca5f09eb2cf767ed2f3f  pose_estimation_mediapipe_2023mar.onnx
```

## 5. CI cost

From the 3.11 baseline's junit XML (`spikes/19_test_stability/timings.py`): 4615 tests, 310 s inside test bodies,
318 s wall.

4615 tests, 310 s in test bodies

| File | Tests | Seconds | Share |
|---|---:|---:|---:|
| tests.test_gallery | 353 | 96.4 | 31.1% |
| tests.test_gallery_browser | 24 | 40.5 | 13.0% |
| tests.test_quiet_microphone | 18 | 26.9 | 8.7% |
| tests.test_rhythm_harmony | 155 | 17.0 | 5.5% |
| tests.test_web_fonts_download | 61 | 15.4 | 5.0% |
| tests.test_ragas | 49 | 12.4 | 4.0% |
| tests.test_guide | 95 | 9.1 | 2.9% |
| tests.test_svg_text | 37 | 6.2 | 2.0% |
| tests.test_making_sound | 112 | 5.4 | 1.7% |
| tests.test_pdf_text | 29 | 4.3 | 1.4% |
| tests.test_gallery_package | 12 | 3.6 | 1.2% |
| tests.test_course | 56 | 3.4 | 1.1% |
| tests.test_print_resolution | 26 | 3.0 | 1.0% |
| tests.test_script_mode | 59 | 3.0 | 1.0% |
| tests.test_text_points | 19 | 2.9 | 0.9% |
| tests.test_color_mode | 70 | 2.5 | 0.8% |
| tests.test_since | 14 | 2.4 | 0.8% |
| tests.test_fit_text | 43 | 2.1 | 0.7% |
| tests.test_poster_text_files | 11 | 1.8 | 0.6% |
| tests.test_ops_snapshot | 15 | 1.8 | 0.6% |
| tests.test_examples_golden | 28 | 1.7 | 0.5% |
| tests.test_web_sound | 27 | 1.7 | 0.5% |
| tests.test_text_shapes | 25 | 1.7 | 0.5% |
| tests.test_libraries | 42 | 1.6 | 0.5% |
| tests.test_layer_files | 26 | 1.6 | 0.5% |

| Slowest 30 tests | Seconds |
|---|---:|
| tests.test_rhythm_harmony::test_a_three_minute_song_is_quick_enough | 4.49 |
| tests.test_gallery_browser::test_previous_stops_at_the_first_example_and_next_at_the_last | 4.18 |
| tests.test_gallery_browser::test_each_run_gets_its_own_folder | 3.87 |
| tests.test_quiet_microphone::test_the_practice_bird_follows_the_settings | 3.36 |
| tests.test_gallery_browser::test_an_example_that_saves_nothing_gives_no_message_and_o_does_nothing | 3.30 |
| tests.test_gallery::test_example_runs_headless[music-11_piano_roll] | 3.19 |
| tests.test_quiet_microphone::test_the_practice_bird_rises_with_speech | 3.15 |
| tests.test_gallery_browser::test_o_and_the_folder_button_open_the_folder_when_asked | 2.92 |
| tests.test_quiet_microphone::test_the_marks_move_with_the_sliders_and_the_keys | 2.87 |
| tests.test_gallery::test_example_runs_headless[sound-03_sargam_over_a_drone] | 2.85 |
| tests.test_gallery_package::test_the_wheel_carries_the_examples_pictures_and_licence | 2.84 |
| tests.test_gallery_browser::test_nothing_is_opened_until_the_learner_asks | 2.67 |
| tests.test_gallery_browser::test_a_saved_file_is_named_in_the_status_with_its_folder | 2.58 |
| tests.test_gallery::test_example_runs_headless[sound-02_write_a_tune] | 2.55 |
| tests.test_gallery::test_example_runs_headless[music-02_see_a_chord] | 2.49 |
| tests.test_gallery_browser::test_clicks_and_keys_move_between_views | 2.45 |
| tests.test_ragas::test_tonic_over_a_drone | 2.44 |
| tests.test_gallery_browser::test_long_area_names_are_cut_to_fit_the_sidebar | 2.44 |
| tests.test_text_points::test_points_lie_on_a_curved_outline | 2.43 |
| tests.test_gallery::test_example_runs_headless[pixels-04_grid_and_contrast] | 2.40 |
| tests.test_quiet_microphone::test_starting_the_game_uses_the_chosen_settings | 2.24 |
| tests.test_gallery::test_example_ops_match_snapshot[pixels-04_grid_and_contrast] | 2.18 |
| tests.test_gallery::test_example_runs_headless[music-04_hear_a_raga] | 2.10 |
| tests.test_gallery_browser::test_wheel_scrolls_the_grid_and_the_code | 2.10 |
| tests.test_quiet_microphone::test_the_tuner_names_a_quiet_voice | 2.03 |
| tests.test_gallery::test_example_matches_golden[pixels-04_grid_and_contrast] | 2.02 |
| tests.test_ragas::test_match_ranks_bhupali_first_and_shows_the_limit | 1.98 |
| tests.test_quiet_microphone::test_the_sliders_show_on_the_setup_screen_and_hide_in_play | 1.92 |
| tests.test_ragas::test_swara_histogram_of_yaman | 1.72 |
| tests.test_pdf_text::test_a_text_heavy_page_is_much_smaller | 1.68 |

Where time could be saved without testing less:
- **Run with `pytest-xdist -n auto`.** The suite took 102 to 224 s on 4 workers (102 to 114 s when the machine was not shared) against 318 s in one process here,
  and it passed in random order, so it does not depend on order (with the fix above). GitHub's Windows runners
  have 4 CPUs. Measured on Linux only.
- **`test_gallery.py` is 31% of the time** (353 tests, 96 s). Each example is run headless, then again for the
  ops snapshot, then again for the golden. Running each example once and checking all three from that one run
  would cut most of it; unmeasured.
- **`test_gallery_browser.py`** (24 tests, 40 s, 1.7 s each) and **`test_quiet_microphone.py`** (18 tests, 27 s)
  start a whole sketch per test; a module-scoped start where the tests only read state would save most of it;
  unmeasured.
- `test_web_fonts_download.py` (15 s) is worth a look for real network waits.

## For the main session

**Found**
1. The `16_sound` hang is, by best reasoning, a GIL deadlock in `funground/sound/_microphone.py`: stopping,
   closing or collecting an SDL capture device while its Python callback waits for the GIL. Reproduced on Linux in
   every run of a small script (`mic_deadlock.py`, `mic_gc_deadlock.py`); not reproduced in 50 runs of the guide
   examples. That it is the Windows CI hang is **unverified**.
2. pytest-timeout cannot stop such a hang, with either method (measured). Only a C-level watchdog can.
3. `Microphone.close()` promises "funground calls it when a sketch ends"; nothing does. Open devices outlive their
   sketch and their test. This is a product bug, but closing them today would hit the deadlock more often, so it
   should land together with the deadlock fix.
4. One order-dependent test (`test_fallback.py`, fixed). It would have made a switch to `pytest-xdist` flaky.
5. CI runs the microphone guide examples on a real (dummy-driver) capture device, while local runs that follow
   AGENTS.md run them silent. The two runs test different code.
6. Wall-clock budget tests fail under load: `test_reverb_of_five_seconds_is_quick` failed once in a random-order
   run on a loaded machine (2.41 s against 2.0 s). This is the most likely cause of the unidentified S-245 failure
   (S-245's suite ran in parallel parts); that it was this test is unverified.
7. Memory: a single-process run of the whole suite reached about 2.9 GB resident (`ps` at 75 to 95%, Python 3.12
   and 3.14). Running four suites at once on 15 GB got one killed by the kernel (exit 137). The cause of the growth
   was not looked into.
8. 100 runs of the `16_sound` guide examples as CI runs them (50 idle, 50 at load average 8 to 11) all passed;
   `pygame.quit()` with a started microphone did not deadlock in 900 rounds (`mic_quit_deadlock.py`).

**Fixed (in this branch)**
- `tests/conftest.py`: every test starts without `FUNGROUND_HEADLESS`, so the 9 tests that failed locally with it
  set now pass, and local runs match CI. Test isolation only; no test weakened.
- `tests/test_fallback.py`: the lazy-loading test also clears `_ITEMISE_CACHE`, so it no longer fails after guide
  example `06_text#9`. Test isolation only; it checks the same thing.

**Needs the maintainer**
- Decide the microphone fix: pause through ctypes into pygame-ce's SDL (prototype in `mic_fix_prototype.py`, needs a
  Windows and macOS library lookup), or ask pygame-ce to release the GIL in `AudioDevice.pause`/`close`; then make
  sketches close their microphones, as documented.
- Add a C-level watchdog to CI (`faulthandler_timeout` or a conftest `dump_traceback_later(..., exit=True)`) and a
  lower job timeout, so the next hang prints stacks and costs minutes, not 25.
- Whether budget tests should measure CPU time.
- Whether CI should use `pytest-xdist` (a dev dependency change, so `pyproject.toml`).

**Commits to review** (all `[skip ci]`): see `git log origin/main..cloud/test-stability`.
- `b292ae8` plan.
- `2c07a0e` and the commit after it: the conftest isolation fix (review them together; the second corrects the
  first, whose teardown order broke `test_capabilities`).
- `0fcbfab`: the `test_fallback` isolation fix.
- The rest: spike scripts and this file.
