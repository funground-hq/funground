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
- [ ] Install from TestPyPI in clean venvs on Windows, macOS and Linux, and run the smoke test. CI can do Linux and macOS headless.

## Maintainer decisions and checks

- [ ] **Sprint 10 and Sprint 11 signed off.**
- [x] **D-045 = B:** ffmpeg on the PATH, else the optional `funground[video]` extra.
- [ ] **Ship the examples and the gallery browser in the package?** Today they are in the repository only.
  - Option: a `funground.examples` sub-package.
  - Option: `python -m funground.gallery`.
  - Option: leave them on GitHub.
- [ ] **Manual run on a real macOS and a real Linux desktop** (Roadmap prerequisite): the gallery browser, a window with HiDPI, full screen, keyboard and mouse, the controls panel, and sound.
- [ ] **PyPI account and trusted publishing** set up for `funground` under the `funground-hq` organisation. The name was checked as free under D-020; check again just before publishing.
- [ ] **Go-ahead to publish.** Then Claude tags `v0.1.0`, pushes the tag, and publishes. Trusted publishing from CI is preferred over a local upload.
