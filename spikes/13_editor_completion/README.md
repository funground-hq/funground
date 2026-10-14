# Spike 13: suggestions in github.dev and vscode.dev (S-197, 14 October 2026)

**Question.** In github.dev and vscode.dev there is no Python environment. Can `f.` list funground's functions
with their signatures in a sketchbook sketch? Route A: the browser's Pylance reads stubs carried by the sketchbook
(`typings/funground/__init__.pyi`). Route B: the funground web extension supplies suggestions itself from
`completions.json` (S-195).

**Criteria, set before the work.** P1: in real github.dev, `f.` lists functions with signatures, `f.width` is known
and `f.fill("` offers colour names (needs a browser; the maintainer's check, steps below). P2: primary sources on what
Pylance does in the browser. P3: a local proxy for A (Pyright 1.1.390, an empty venv, a generated stub). P4: a
prototype of B run against a stand-in for the VS Code API.

## Results

**P2: Pylance in the browser reads one file only.** It runs on vscode.dev and github.dev in a reduced mode.
pylance-release [#4926](https://github.com/microsoft/pylance-release/issues/4926), a maintainer, 1 Sept 2026: "we're
not going ahead with the experiment to support web based Pylance to read other documents. It will be only able to
read a single file at a time." Also [#5768](https://github.com/microsoft/pylance-release/issues/5768) (2024, "by
design") and [#7202](https://github.com/microsoft/pylance-release/issues/7202) (2025, "Pylance can't read files from
the web"). Only its bundled typeshed stubs work. No source mentions `typings` on the web: whether it is read is
**unverified**, but the single-file statements say it is not.

**P3: a stub works where Pylance can read it.** `gen_stub.py` writes a 591-line, 25.8 KB stub from
`inspect.signature` of `_PUBLIC_NAMES` plus the typed live values. With no funground installed, Pyright reveals
`f.width` as `int`, `f.mouse_x` as `float`, `f.circle` as `(x: float, y: float, diameter: float) -> None`, bare
`circle` and `width` in the star style, and flags a missing argument and `f.not_a_function`. One warning,
`reportMissingModuleSource`, is silenced by a setting. Rough edges of the spike stub: `Color` as `Any`, classes
without their methods. This helps desktop VS Code without funground installed; it does not prove the browser.

**P4: the extension can suggest by itself.** `completion_prototype.js` registers completion (after `.`, and inside
quotes for colours and option words), hover and signature help. Against `mock_test.js` (a stand-in for the VS Code
API, not a real editor) with the real `completions.json`: `f.` gives 205 names, `circle` shows
`circle(x, y, diameter)` with its sentence and link, `f.fill("re` the colour names, `f.blend_mode("` its modes, and
signature help and hover work. `completions.json` is 103,642 bytes (16.8 KB gzipped); the `.vsix` today is 39.8 KB.
The extension already reads its bundled files with `workspace.fs.readFile` and activates on Python files.

## Recommendation

**B, as the floor that works everywhere the extension runs** (github.dev, vscode.dev, desktop VS Code): about 100
lines in `extension.js`, `completions.json` copied into `media/` by `build.py`, and each extension release carries
the file of the funground version its runtime has. A only as an extra, and only if the maintainer's check shows the
browser reads `typings/`: a stub writer in `tools/make_api_reference.py` (from `gen_stub.py`) and a copy in the
sketchbook per release. Proposed story for Sprint 26: the extension's suggestions (B), with the browser check.

## P1, the check in a real browser

1. Open the sketchbook repository on github.com and press `.` (github.dev). Install the funground extension and Pylance.
2. Open a sketch with `import funground as f`. Type `f.`: do functions appear with signatures? Hover `f.width`; type
   `f.circle(`; type `f.fill("`.
3. Today, without B, expect nothing from funground (this confirms P2). With a build of B: the list, the hint and the
   colours.
4. Route A: disable the extension, add `typings/funground/__init__.pyi` (from `gen_stub.py`), reload, type `f.` again.
