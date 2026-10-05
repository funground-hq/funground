# Adding a feature

The end-to-end recipe for one story that adds a public feature. Every step below is something a
test or a tool checks, or a rule in [PROCESS](../PROCESS.md). Follow the order. The "Done"
definition in PROCESS says a story that adds a public feature also adds its gallery example and
its guide section in the same story.

Before you start, read [Architecture.md](Architecture.md) so you know where the code belongs, and
[Testing.md](Testing.md) so you know what each test checks.

## 0. Is it a decision?

Ask first. Anything that changes a pinned contract row, adds or removes a runtime dependency,
changes the base install, changes a public name or signature, picks between providers, or
regenerates a golden is a decision (PROCESS, "When something is a decision"). It gets a row in
[Decision_Log.md](../design/Decision_Log.md), and an ADR if it is long-lived. Under D-034 routine
design calls can be taken by the main session and logged as "decided by Claude". New dependencies,
changes to the frozen v0.5 API, and scope changes still go to the maintainer. Sub-agents stop and
report on these.

## 1. Pin a contract row first

Add a row to [Semantic_Contract.md](../design/Semantic_Contract.md) before any code. The row says
what the feature does, in the exact words the tests will check: arguments, defaults, errors, what
goes in the IR, and how it behaves in PDF and SVG. Mark it **Pinned** and name the story and the
decision (for example "S-092, D-041"). Tests and code follow the row, never the other way round.

## 2. Write the code behind the facade

- Put the behaviour in the right layer (see [Architecture.md](Architecture.md)). Drawing becomes
  ops in `funground/ir.py` and is replayed by `CairoRenderer`. State goes in `GraphicsState`.
  Helpers with no state get their own module.
- A **new field** on an op or on `GraphicsState` needs a default and an entry in
  `ir.OMIT_WHEN_DEFAULT`, so old IR snapshots stay byte-identical. See Architecture, "Key
  invariants".
- A **new backend import** is allowed only in its provider. If you need a new library, that is a
  decision (step 0). Add it to `ALLOWED` in `tests/test_boundaries.py` in the same change.
- Add a `Sketch` method that checks arguments, applies modes, and records ops. Errors are plain
  English and name the function and what to do instead.
- Add the facade function in `funground/api.py`. It is a thin wrapper. Give it a docstring and full
  type hints, because the contract test compares the signature text. **Pick the accessor on
  purpose** (the layers rule in Architecture, "Key invariants"): a function that draws calls
  `active_sketch()`, so it lands in an open `with f.layer(...)` block. Every other function (size,
  save, input, time, randomness, loop control) calls `canvas_sketch()`.
- **Name the module carefully.** A new submodule must not share a name with a public function (the
  naming trap in Architecture). Check the name against `__all__` first.

## 3. Make the name public

1. Import the name from `.api` and list it in `__all__` in `funground/__init__.py`.
2. Add its exact signature to `ADDED_FUNCTIONS` in `tests/test_api_contract.py`.

`test_public_all_is_exactly_the_contract` fails until both are done. A live value (such as
`f.width`) goes in `LIVE_NAMES` in `api.py` and in `LIVE_VALUES` in the test instead.

## 4. Unit tests

Add `tests/test_<topic>.py`, or extend the file for that subject. Test each clause of the contract
row: the normal case, each default, each error message, the IR that is recorded, and the PDF or
SVG result if the row says something about it. Use the fixtures described in
[Testing.md](Testing.md). A test font comes from `tests/fontmaker.py`, never from the network.

## 5. A gallery example

Write `examples/gallery/<area>/NN_name.py`. It is an ordinary complete sketch. Its docstring is the
gallery text, and it follows a standard that `tests/test_example_docs.py` enforces for **every**
example (S-120, D-065):

```text
Title line

What you see: one short paragraph.

How it works:
- 3 to 6 bullets: the idea, and the funground functions that do it.

Make it yours:
- 3 to 5 bullets: ideas to extend it, easiest first.
```

A bullet may carry on over the next lines, indented. Every `f.<name>` in the docstring must be a real
name in `funground.__all__`, and every `sound.<name>`, `picture.<name>`, `path.<name>` or
`microphone.<name>` must be a real method of that kind of object. Write it in plain English. The
gallery browser and `docs/gallery/README.md` show these parts, so a missing part fails the test.

**It must be original, and it is published as CC0** (D-026).
Never copy or translate an example, in whole or in part, from p5.js, Processing, DrawBot, py5, a
website, a book or a tutorial, whatever its licence. Write it from the feature it shows. Ideas and
standard algorithms are free. Their written expression is not.

Then:

1. Run the gallery tests **twice**. The first run writes the golden
   (`tests/golden/gallery/<area>-<name>.png`) and the IR snapshot
   (`tests/snapshots/gallery/<area>-<name>.json`) and skips. The second must pass.

   ```sh
   .venv/Scripts/python -m pytest -o addopts="" -q tests/test_gallery.py
   .venv/Scripts/python -m pytest -o addopts="" -q tests/test_gallery.py
   ```

   Look at the new picture. Never overwrite an existing golden or snapshot.
2. Run the **originality check** and record the result:

   ```sh
   .venv/Scripts/python tools/check_originality.py --corpus <corpus-folder> examples/gallery/<area>/NN_name.py
   ```

   The tool compares your code against corpora of well-known creative-coding collections.
   `--corpus` names a local folder of corpus files (give it more than once for more folders).
   `--fetch DIR` clones the pinned corpora into `DIR` and exits; it needs the network. The
   maintainer's copy is outside the repository, in `C:\Projects\funground-corpora`.
   `--report FILE` writes the result table as Markdown. Exit code 0 means nothing was flagged, 1 means
   something was. With no paths it checks all example code.
   Record the result in [docs/qa/Example_Provenance.md](../qa/Example_Provenance.md). The tool
   cannot see books or videos, and it finds copied expression, not a similar idea.
3. If the example is time-dependent (it uses the clock, the microphone or anything else that varies
   from run to run), add the line `# gallery: time-dependent`. It is then smoke-tested only: no
   golden, no snapshot, and `make_gallery.py` keeps its committed picture unless you pass `--force`.
4. A new area folder must be added to `AREAS` in `funground/gallery.py`, or it is listed last. That
   is the one list: the browser and `tools/make_gallery.py` both read it.
5. A script example (no `draw()`, ends in `f.show()`) is pictured with its layers composited, as
   `f.show()` and a save would show it. You do nothing for this, but do not expect the golden to be the
   bare canvas.
6. If the feature needs a data file, put it beside the example (for example `data/`). A relative
   path is found next to the sketch file first.

If the example listens to a microphone, read the quiet-microphone rule in
[Testing.md](Testing.md) too: it must work when the room is very quiet.

`tests/test_gallery.py` also demands that every public name is used (`f.<name>`) by some gallery
example. `NOT_YET_IN_GALLERY` may only shrink.

## 6. Build the gallery images and index

```sh
.venv/Scripts/python tools/make_gallery.py
```

This renders every example headless and writes `docs/gallery/images/<area>-<name>.png` and the
index `docs/gallery/README.md` from the examples' docstrings. **Run it without `--force`.** A
time-dependent example already has a committed picture, and the tool keeps it (it prints
"time-dependent, kept"), so the run changes only the pictures that are new. `--force` re-renders the
time-dependent pictures too. Use it only when you mean to change one, and say so in your report.
`--index` rewrites the index only. `test_index_is_up_to_date` and
`test_every_example_has_a_gallery_image` fail until you have run it. The tool never draws by hand,
so a picture cannot drift from its code.

The tool imports `AREAS` and the other helpers from `funground/gallery.py`. You can look at the
result with the browser: `python -m funground.gallery` (`--list` prints the examples with no window).

## 7. A guide section

Add the feature to the right chapter in `docs/guide/` (or a new numbered chapter, listed in
`docs/guide/README.md`). The guide is for learners: plain English, short sentences, British spelling
in prose, American spelling in names.

- A ```` ```python ```` block must be a **complete** sketch or script. It must call `f.run(` or
  `f.show(`. `tests/test_guide.py` runs every one for three frames, exactly as printed.
- Use a ```` ```py ```` fence for a fragment that is shown but not run.
- Links must resolve. The test checks relative links and images.
- Code blocks are CC0 and original, like examples.
- If the feature matches a p5.js or DrawBot name, add or update the row in chapter 14
  (`14_coming_from_p5_processing.md`) or 15 (`15_coming_from_drawbot.md`).

## 8. A Quick Reference row

Add a row to `docs/reference/Quick_Reference.md`: the call, one plain sentence of what it does,
and an example call. Mark it **New:** for a name added since v0.5. `tests/test_reference.py` checks
that `f.<name>` appears for every name in `__all__`. If you add a reference sketch under
`examples/reference/`, embed its source word for word in the Quick Reference, and make its picture
with `tools/make_reference_images.py` (or `... 05_text` for one).

## 9. A CHANGELOG line

Add a line to the "Unreleased" section of [CHANGELOG.md](../../CHANGELOG.md), under "Added" or
"Changed from v0.5". Say what a learner can now do, in plain words. End with the story and the
contract row, and the decision if there was one, for example `(S-092, contract P11)`. Say
**New dependency:** if there is one (D-nnn).

## 10. Where p5 or DrawBot names were checked

When a funground name copies a p5.js, Processing or DrawBot name, say where you checked its meaning:

- in the contract row (for example "p5 `rect(x, y, w, h, r)`");
- in the decision-log row, if a choice was made (D-035, D-038, D-042 and D-044 show the form);
- in the guide's chapter 14 or 15 row for that name.

Check names and meanings in the other tool's public documentation or source. That is research, and
it is allowed. Copying code or example text is not. Name the page or the source file.

## 11. Design notes and these docs

A story that adds a subsystem, a new dependency or a non-obvious mechanism gets a design note
`docs/design/<Topic>_Note.md`: problem, design, rejected alternatives, invariants, limits, and where
the tests are. Update [Architecture.md](Architecture.md) in the same change if a layer, a boundary
or an invariant moved, and add the note to the index in [docs/design/README.md](../design/README.md).

## 12. Parallel builders

When several builders work at the same time:

- **The brief names each builder's files and example numbers.** In Sprint 14 every builder created
  the `music/` area and numbered its examples from 01, so the review had to renumber them. Say, for
  example, "builder A: `music/01` to `music/03`; builder B: `music/04` to `music/06`".
- **Builders in the same folder never overlap on files.** Work that might overlap goes to a worktree.
- **Scratch scripts get unique names**, so a builder never runs another's stale helper.
- **Shared files are merged by the main session**: `funground/__init__.py` (`__all__`),
  `funground/api.py`, `tests/test_api_contract.py`, the Quick Reference, the CHANGELOG and `AREAS`.
  To merge a worktree, take its new files as they are and merge the shared files by hand. Then run
  the gallery tests twice and `tools/make_gallery.py`. A golden written in a worktree is new evidence:
  look at it, and check it was written on Windows.
- **Stage named files only** when committing, never a whole folder another builder is writing in.

## 13. The review checklist

The main session reviews every diff, reruns the suite and commits. Use this list before you hand
over, and expect it afterwards.

- [ ] A contract row is pinned, and the code does what the row says.
- [ ] No existing file in `tests/golden/` or `tests/snapshots/` is changed, deleted or regenerated.
  New golden and snapshot files exist only for new gallery examples.
- [ ] New fields are in `OMIT_WHEN_DEFAULT`; every old snapshot is untouched.
- [ ] Backend imports are only in their provider; `tests/test_boundaries.py` passes.
- [ ] `__all__` and `tests/test_api_contract.py` agree.
- [ ] Unit tests cover each clause of the contract row, including errors.
- [ ] The gallery example is original, CC0, and has a golden and a snapshot. Its docstring follows
  the standard (`tests/test_example_docs.py`). The originality check
  was run, and the result is in `docs/qa/Example_Provenance.md`.
- [ ] `tools/make_gallery.py` was run without `--force`; the images and the index are current, and
  no existing time-dependent picture changed unless that was the point.
- [ ] A new drawing function uses `active_sketch()`; any other new function uses `canvas_sketch()`.
- [ ] A new module's name is not a public function's name.
- [ ] The guide section's code blocks run; the Quick Reference row exists; the CHANGELOG line exists.
- [ ] p5 or DrawBot names are cited with where they were checked.
- [ ] Learner-facing text is plain English with British spelling in prose and American spelling in
  names (`color=`).
- [ ] Nothing is added to `src_v0.5/`, `spikes/`, old sprint folders, ADRs or the decision log
  that rewrites history. Decision-log rows are added, not edited.
- [ ] No new runtime dependency and no change to the frozen v0.5 API without the maintainer.
- [ ] The full suite passes:
  `timeout 400 .venv/Scripts/python -m pytest -o addopts="" -q`
- [ ] Nothing is committed by the builder. `resume.txt` is untouched.
