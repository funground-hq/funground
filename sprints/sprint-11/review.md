# Sprint 11 review — Phase 3e: sound, motion, controls, release prep

**Dates:** 2 October 2026, planned and built under D-034 while Sprint 10 awaited sign-off.
**Draft for the maintainer's sign-off.**

**Goal:**
- sound playback and analysis;
- GIF and MP4 export;
- sliders, checkboxes and buttons;
- the gallery and guide completed;
- release 0.1 prepared, but not published.

## Outcome

Five stories are done. S-073 (release) is done up to the point that needs you: see
`release_checklist.md`.

**Checkpoint met.** No golden, snapshot or gallery image that existed before the sprint changed:

```
git diff -M --diff-filter=MD 6dca498..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images
```

That diff is empty.

**No new runtime dependency.** Sound uses pygame-ce's mixer. GIF uses Pillow, which was already the
`extras` extra. MP4 uses an ffmpeg found on the PATH, and D-045 decides whether there is also an
extra for it.

**Public surface: 152 → 159 names.** The new ones are:
- `load_sound`;
- `create_slider`, `create_checkbox`, `create_button`;
- `save_gif`, `save_movie`, `frame_duration`.

No v0.5 API changed.

| Story | Result | Built by |
|---|---|---|
| S-098 Sound playback | `f.load_sound()`: play, loop, pause, stop, volume, current time. Plays silently, keeping time, when there is no audio device, so headless runs work | Sonnet sub-agent |
| S-099 Sound analysis | `level()` and `spectrum(bands)` in pure Python (1.3 ms a call), cached per frame | Sonnet sub-agent |
| S-100 GIF and MP4 | Scripts: pages become frames, with `frame_duration`. Animated sketches: `save_gif`/`save_movie` record a number of seconds | Sonnet sub-agent |
| S-101 Controls | `create_slider`/`checkbox`/`button` in a panel below the canvas. The panel is never in the canvas, saves or the IR | Sonnet sub-agent, in a worktree |
| S-072 Gallery and guide | A showcase page; the guide read end to end, with stale lines and internal IDs removed; Quick Reference refreshed; every public name used in an example | Sonnet sub-agent |
| S-073 Release prep | Wheel and sdist build and pass `twine check`. Installed and smoke-tested in a clean venv. PyPI metadata added. Checklist written | Claude (main session) |

## Test results

```
1649 passed, 1 skipped   (Sprint 10 close: 1518; the skip is a real-ffmpeg smoke test)
CI: not run - GitHub unreachable from this machine all of 2 Oct; 13 commits wait to be pushed
```

## Findings

1. **Real windows were never seen.** Controls, sound and full screen were tested only with SDL's
   dummy drivers. The release checklist already requires a manual desktop run; this sprint adds
   two things to try:
   - the controls panel, by hand;
   - sound through speakers.
2. **MP4 has never been made with a real ffmpeg.** There is none on this machine. The tests check
   the exact command line through a stand-in program. CI on Ubuntu may have ffmpeg, which would run
   the one real test. This is unverified until CI runs.
3. **Choices builders made, pinned in review:**
   - **A1:** sounds also report `current_time()` and `get_volume()`, as p5 names them.
   - **U1:** `clicked()` is a flag, not a counter. "Script" means a top-level `size()` that has
     drawn. Controls made after `full_screen()` get no panel.
   - **M1:** see-through frames are put on white. An unfinished recording writes nothing. A size
     change during a recording is an error.
4. **Unverified p5 names.** The p5.sound names (`setVolume`, `Amplitude.getLevel`, `FFT.analyze`)
   are not in our corpus, because p5.sound is a separate repository. The guide cites them from
   knowledge, and you may want to check them.
5. **Untidy items left for after 0.1:**
   - Sound is guide chapter 16, after the two "Coming from" chapters.
   - Chapter 9 is long.
   - The Quick Reference's "What changed since v0.5" section is aimed at a version learners never
     had.

## Decisions

| ID | Outcome | By |
|---|---|---|
| D-045 | **Pending:** how learners get ffmpeg (recommended: B, PATH plus an optional `funground[video]`) | maintainer |
| D-046 | Sound API: p5 names on one sound object; `level()`/`spectrum()` on the sound | Claude, under D-034 |
| D-047 | Controls API: p5's `create_*` objects in a panel below the canvas | Claude, under D-034 |
| D-048 | Motion export: DrawBot's pages-as-frames in scripts, p5's `save_gif` plus `save_movie` in sketches | Claude, under D-034 |

## Sign-off

*Awaiting the maintainer, after Sprint 10.* Push and check CI first.

## Retrospective

- **Went well:**
  - Five stories in a day.
  - Two builders ran in parallel, one in a worktree, and merged with one trivial conflict.
  - Every builder's own choices came back listed and were pinned in review, following the
    Sprint 10 retro rule.
- **Went badly:**
  - Working without CI for a whole day: thirteen commits are unverified on macOS and Linux.
  - Sprint 11 started before Sprint 10 was signed off. That is allowed under D-034, but it stacks
    up review work for you.
- **Change for next time:** if GitHub is unreachable for more than a few commits, stop opening new
  stories and say so.

## AI-USAGE log entry

Added to `AI-USAGE.md` under Sprint 11.
