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

- [ ] CI green on all 12 cells for the release commit. GitHub was unreachable on 2 Oct; push first.
- [ ] Relative image links in `README.md` do not render on PyPI.
  - Make them absolute (`https://raw.githubusercontent.com/funground-hq/funground/main/...`).
  - Or keep the PyPI description text-only.
- [ ] `CHANGELOG.md`: turn "Unreleased" into "0.1.0 — <date>".
- [ ] Root `README.md` install line: switch from the git URL to `pip install funground`. Guide chapter 1 already says that.
- [ ] Version `0.1.0.dev0` → `0.1.0` in `pyproject.toml`, in a commit of its own.
- [ ] Build again from a clean checkout of the tagged commit, then run `twine check`.
- [ ] Dry run: run `release.yml` by hand → TestPyPI upload plus install and smoke test on Windows, macOS and Linux (`smoke-test` job).

## Maintainer decisions and checks

- [ ] **Sprint 10 and Sprint 11 signed off.**
- [x] **D-045 = B:** ffmpeg on the PATH, else the optional `funground[video]` extra.
- [x] **Ship the examples and the gallery browser in the package?** Yes (D-049, built in S-103): `python -m funground.gallery`; the examples, their data, the pictures and the CC0 licence are in the wheel.
- [ ] **Manual run on a real macOS and a real Linux desktop** (Roadmap prerequisite): the gallery browser, a window with HiDPI, full screen, keyboard and mouse, the controls panel, and sound.
- [ ] **Microphone, once per system (Windows, macOS, Linux)** — with the gallery's tuner (`python -m funground.gallery`, Sound → Tuner): sing or play a note and check the name and needle; on macOS also check the permission prompt and the message after "Don't allow". Not needed per learner or per microphone.
- [ ] **Live SVG text in Illustrator and Inkscape** (T19, D-059): open a saved SVG with Hindi and Latin text, check it is editable and shaped correctly (Illustrator: World-Ready Paragraph Composer).
- [x] **PyPI account:** maverick27 (linked to GitHub samir-joshi). Organisation `funground` requested, pending approval; not needed to publish (transfer the project later).
- [ ] **Pending publishers** (trusted publishing, no tokens), matching `.github/workflows/release.yml`:
  - pypi.org → Account → Publishing → pending publisher: project `funground`, owner `funground-hq`, repository `funground`, workflow `release.yml`, environment `pypi`;
  - test.pypi.org: the same with environment `testpypi`;
  - optional: in GitHub, Settings → Environments → `pypi` → required reviewer = you, so publishing waits for your click.
  - The name was free on both indexes on 4 Oct 2026.
- [ ] **Go-ahead to publish.** Then Claude tags `v0.1.0` and pushes the tag; `release.yml` builds, checks, publishes to TestPyPI, smoke-tests on three systems and publishes to PyPI (after your approval click if the environment is protected).
- [ ] **Raga data spot-check** (`funground/data/ragas.json`) by you or a music teacher.
- [ ] **Listening check** of the sound examples after S-118.
