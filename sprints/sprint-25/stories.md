# Sprint 25 — 0.2: a smooth start (E-35)

**Dates:** planned 14 October 2026, on a branch of `main` (with `funground-web`, `funground-hq.github.io` and
`funground-hq/sketchbook`). Runs while 0.1.0 waits for the maintainer's Mac test.

**Goal:** the editor suggests what to type, in VS Code, in github.dev and in Play: `f.` lists every function with
its arguments and a sentence, `f.width` is a number, `f.fill("` offers the colour names, and the star style is
not flagged. The first chapter shows, with a picture and a live sketch, where things go on the canvas.

**Decisions:** D-102 accepted (a): Play suggests from funground's own generated list.
D-090 (constants) is accepted, so S-174 can start.

| Story | Value | Status |
|---|---|---|
| S-130 | Typing that editors read: `py.typed`, explicit re-exports, a literal `__all__`, typed live values | done: literal `__all__` (one hand-written list; `_PUBLIC_NAMES` derived), the four left-out names re-exported, 15 live values typed, every public function annotated, `tests/test_typing.py`; Pyright: `f.width` int, `f.filter` exported, no errors |
| S-174 | Named constants and `f.colors` (D-090), with `Literal[...]` option words | planned |
| S-195 | `completions.json`, generated with the API reference | planned |
| S-196 | Completion in Play (after D-102) | planned |
| S-197 | Spike: completion in github.dev and vscode.dev | planned |
| S-198 | VS Code on the desktop: quiet star style, an editable install Pylance can follow, choosing the interpreter | planned |
| S-199 | A gentle first chapter: where things are, with a picture, a live sketch and a gallery example | done: chapter 1 "Where things are" rewritten, examples `basics-05_where_things_are` and `basics-06_mouse_position` with goldens; originality checked |

Order: S-130 first (the evidence is in E-35; small and unblocks the rest), S-198 and S-199 alongside, then S-174,
S-195, S-196; S-197 when S-195 exists. S-200 (Play's first visit) is planned for Sprint 26.

Acceptance for the sprint: the full suite green; a Pyright probe of a sketch in both styles reports the right
types with no export or wildcard warnings under the recommended settings; Play suggests after `f.` and inside
colour quotes (headless checks); the new chapter section and example run on the desktop and in Play; no golden
or snapshot changed except the new example's.

- [x] S-130
- [ ] S-174
- [ ] S-195
- [ ] S-196
- [ ] S-197
- [ ] S-198
- [x] S-199
