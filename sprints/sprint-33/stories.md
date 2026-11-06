# Sprint 33 — Models you hear and teach; Play's sketchbook (E-37, E-38)

**Dates:** planned 2 November 2026. Scope from D-127 (maintainer, 2 Nov: "let's wait for the ML and Play editor stories
to get completed and we can include it in 0.2"; then "write sprint 32 review and start S-234"). Work in funground,
`funground-web` and `funground-hq.github.io`. Each story ships when it is checked.

**Goal:** the rest of release 0.2: speech, sounds and a model the learner teaches, on the desktop and in Play; the
guide chapter on models; Play's sketchbook, embed, stop without restarting, several files and the shape editor's
prototype.

**Decisions:** D-126 (`ml.words`, `ml.sound`, `ml.teach`, `ml.guess`) and D-127 accepted. Needed during the sprint:
each story's arguments and result, pinned in its contract row before it is built (inside D-126; a change of meaning
goes back to the maintainer); D-118 from S-238. S-238 needs the maintainer for the GitHub App and the Cloudflare
Worker (Wrangler on this machine needs a fresh `wrangler login`).

**Release gates for 0.2** (maintainer, 2 Nov: "we should have the documentation and guide updated. I too need to do
testing"): the guide, reference, gallery and course current for every name in the release; the maintainer's own test
pass, on the desktop and in Play, before the tag.

| Story | Value | Status |
|---|---|---|
| S-234 | Words you say: `ml.words(mic)`, speech to words on the device, the same on the desktop and in Play | done 5 Nov (#63, web #23); a real microphone in Play is for the maintainer's test pass |
| S-251 | A microphone stops without freezing the sketch (found by spike 19; added 5 Nov, before S-234, which rests on it) | done |
| S-252 | The test suite can be trusted before 0.2 (spike 19; added 5 Nov) | done (#65) |
| S-253 | Nonsense numbers cannot hang a sketch or spoil a saved file (spike 20; added 5 Nov) | built; PR open |
| S-250 | Sounds: `ml.sound(mic)`, the most likely sound with how sure, and the next guesses | built 5 Nov; a real microphone is for the maintainer's test pass |
| S-235 | A model you teach: `ml.teach(...)` and `ml.guess(...)`, a few examples of each kind from the camera | planned |
| S-236 | The guide chapter on models: what a model is, what it learnt from, why it is wrong, what stays on your computer | planned |
| S-238 | Spike: signing in to GitHub from Play (carried over from sprint 32) | done 5 Nov: passed on a laptop and a phone; D-118 awaits the maintainer |
| S-239 | The sketchbook in Play (after S-238 and D-118) | planned |
| S-240 | Embed: only the code and the picture, for the guide and the course | planned |
| S-241 | Spike: stop without restarting | planned |
| S-242 | Several files in one sketch | planned |
| S-243 | Spike: the shape editor's prototype | planned |
| Release | `funground-ml` release job and PyPI publishers; release checklist; the maintainer's test pass | planned |

Order: S-234 first (it builds the microphone's route to the model in Play, which S-250 reuses), then S-250, S-235 and
S-236; S-240 and S-242 between heavy jobs; S-238 as soon as the accounts exist. One heavy job at a time.

## S-234 tasks

- [x] Contract row: what `ml.words(mic)` takes and gives, when it answers (a phrase after a pause), to the maintainer if it changes D-126's meaning
- [x] Desktop: Whisper tiny.en q8 in `funground-ml`, pinned and checked by SHA-256; the spike's decode loop as product code
- [x] The microphone's samples to the model in Play, without `async` in the sketch
- [x] Desktop and Play give the same words for the same recording, by test
- [x] Reference, gallery example and golden, guide section, Quick Reference row
