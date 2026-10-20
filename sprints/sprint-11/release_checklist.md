# Release 0.1: checklist

Prepared under S-073. **Publishing is the maintainer's act.** Claude prepares and verifies; the
maintainer says "publish", and every public step happens in the main session (PROCESS.md,
irreversible actions).

## Done (2 Oct 2026)

- [x] Wheel and sdist build with `python -m build`; `twine check` passes on both.
- [x] A clean venv on Windows / Python 3.14 installs the wheel. The smoke test works:
  - text, a circle, PNG and PDF saves;
  - `pypdf` reads the PDF's text back;
  - GIF export gives the friendly "install `funground[extras]`" error without Pillow, and works with `[extras]`.
- [x] PyPI metadata added: authors, keywords, classifiers, and project URLs.
- [x] The bundled font and its licence ship in the wheel (`package-data`).

## Before publishing (Claude)

- [ ] CI green on the release run for the release commit (D-116: Windows 3.11 to 3.14, Linux 3.11 to 3.14, macOS 3.11 and 3.14; branch `rc/0.1.0` at `19dd280`, run 39472067389, 20 Oct 2026).
- [x] Relative image links in `README.md` do not render on PyPI. (0.1.0: the README has no images; every link is absolute to the `v0.1.0` tag.)
  - Make them absolute (`https://raw.githubusercontent.com/funground-hq/funground/main/...`).
  - Or keep the PyPI description text-only.
- [x] `CHANGELOG.md`: turn "Unreleased" into "0.1.0 — <date>". (14 Oct; changed to the tag day if later.)
- [x] Root `README.md` install line: switch from the git URL to `pip install funground`. Guide chapter 1 already says that.
- [x] Version `0.1.0` in `pyproject.toml` and `funground.__version__` (from 0.1.0a1; one release commit, as Releasing.md says).
- [ ] Build again from a clean checkout of the tagged commit, then run `twine check`.
- [x] Dry run: run `release.yml` by hand → TestPyPI upload plus install and smoke test on Windows, macOS and Linux (`smoke-test` job). Passed 5 Oct 2026 with 0.1.0.dev1 (run 37274058907); the first run found the Linux Cairo prerequisite, now installed in the smoke test as the docs say.

## Maintainer decisions and checks

- [x] **Sprint 10 and Sprint 11 signed off.** (both closed 3 Oct 2026)
- [x] **D-045 = B:** ffmpeg on the PATH, else the optional `funground[video]` extra.
- [x] **Ship the examples and the gallery browser in the package?** Yes (D-049, built in S-103): `python -m funground.gallery`; the examples, their data, the pictures and the CC0 licence are in the wheel.
- [x] **Dropped 20 Oct 2026 (D-116, maintainer: "I could not test on Linux or Mac, please do the minimal tests required on GitHub CI and let's release"): the release CI run on macOS and Linux stands in for it, and a macOS desktop by hand joins "Not yet tested".** Was: **Manual run on a real macOS desktop, by the maintainer: a gate for 0.1.0** (maintainer, 14 Oct 2026: "0.1 can be released only when we have tested on local Mac first"): the gallery browser, a window on a high-resolution screen, full screen, keyboard and mouse, the controls panel, sound and the microphone. **Linux** is covered by the release CI run (the full suite and the smoke test, without a screen); a Linux desktop by hand stays under "Not yet tested". **The candidate is `main` at `19dd280`** (the merge of release PR #5, 14 Oct): test that commit (`git checkout 19dd280`), and tag it `v0.1.0`. Merges to `main` go on meanwhile (maintainer, 14 Oct: "the Mac test should hold the release but not merges"); `main` is `0.2.0.dev0` from Sprint 25.
- [x] **Microphone, once per system (Windows, macOS, Linux)** — with the gallery's tuner (`python -m funground.gallery`, Sound → Tuner): sing or play a note and check the name and needle; on macOS also check the permission prompt and the message after "Don't allow". Not needed per learner or per microphone. Done by the maintainer on Windows, 12 Oct 2026; macOS and Linux **not tested for 0.1**.
- [x] **Out of 0.1 (D-116, 20 Oct 2026), listed as not tested.** **Live SVG text in Illustrator and Inkscape** (T19, D-059): open a saved SVG with Hindi and Latin text, check it is editable and shaped correctly (Illustrator: World-Ready Paragraph Composer). **Not tested for 0.1** (maintainer, 12 Oct 2026): listed under "Not yet tested" in the release notes.
- [x] **PyPI account:** maverick27 (linked to GitHub samir-joshi). Organisation `funground` requested, pending approval; not needed to publish (transfer the project later).
- [x] **Pending publishers** (trusted publishing, no tokens), matching `.github/workflows/release.yml`: Done by the maintainer, 12 Oct 2026 (PyPI); the GitHub environments `testpypi` and `pypi` (required reviewer) exist.
  - pypi.org → Account → Publishing → pending publisher: project `funground`, owner `funground-hq`, repository `funground`, workflow `release.yml`, environment `pypi`;
  - test.pypi.org: the same with environment `testpypi`;
  - optional: in GitHub, Settings → Environments → `pypi` → required reviewer = you, so publishing waits for your click.
  - The name was free on both indexes on 4 Oct 2026.
- [x] **Go-ahead to publish** (maintainer, 20 Oct 2026: "let's release"). Then Claude tags `v0.1.0` and pushes the tag; `release.yml` builds, checks, publishes to TestPyPI, smoke-tests on three systems and publishes to PyPI (after your approval click if the environment is protected).
- [x] **Not tested for 0.1, as decided.** **Raga data spot-check** (`funground/data/ragas.json`) by you or a music teacher. **Not tested for 0.1** (maintainer, 12 Oct 2026): listed under "Not yet tested" in the release notes.
- [x] **Listening check** of the sound examples after S-118. Done by the maintainer, 12 Oct 2026.
- [x] **The web parts** (the Play page) tried by the maintainer, 12 Oct 2026. Found: after Run was pressed again
  during a run (the space bar on the focused Run button), Stop was disabled while the sketch played on. Fixed in
  funground-run.github.io#2 and funground-hq.github.io#6, waiting to be merged.
