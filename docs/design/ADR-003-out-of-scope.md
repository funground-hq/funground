# ADR-003: Deliberately out of scope

**Status:** Accepted 26 September 2026. Records the scope agreed in the roadmap (D-014, 25 September
2026); no new call was needed. Story S-058.
**Date:** 26 September 2026

## Context

Playground aims at the 2D surface of Processing, p5.js and DrawBot (Roadmap, D-014). All three have
features Playground will not copy. Leaving them unstated invites two problems: learners coming from
those tools file "missing feature" reports for things we chose to leave out, and contributors add
them one at a time until the scope drifts. This ADR names each exclusion, why it is excluded, and
what a learner uses instead. The User Guide's "Coming from p5/Processing" and "Coming from DrawBot"
chapters link here.

## Options

1. **Record the exclusions here** and point the guide at them.
2. **Leave scope implicit** in the roadmap tables, as before this ADR.

## Decision

Option 1. The following are out of scope. "Before 1.0" items are directional work for after 1.0;
the rest have no plan at all.

| Excluded | Found in | Why not | Use instead |
|---|---|---|---|
| **CMYK and print colour spaces**, colour profiles, spot colours | DrawBot `cmykFill`, `cmykStroke` | Print production needs colour management end to end (profiles, proofing), which a teaching library cannot do properly. Half-done CMYK gives files that look right and print wrong | Design in RGB; convert for print in a layout tool (Scribus, InDesign, Affinity) |
| **Sound synthesis**: oscillators, envelopes, effects | Processing Sound, p5.sound | A synthesis engine is a project of its own. Phase 3 plans playback and analysis only (E-17) | `pyo`, or `sounddevice` with numpy |
| **Large image-filter libraries** | DrawBot's Core Image filters (100+), Processing `filter()` extras | Each filter is a maintained dependency with its own semantics. Phase 3 adds a handful through Pillow (blur, invert, threshold, grey) | Pillow's `ImageFilter` and `ImageOps`; scikit-image for image processing |
| **Processing's data, serial, network and video libraries**: `loadTable`, `loadJSON`, `Serial`, `Client`/`Server`, `Movie`, `Capture` | Processing, p5.js | Plain Python already does these well. Wrapping them adds names to learn and code to maintain, with no teaching gain | `csv`, `json`, `urllib`, `socket` from the standard library; `pyserial`; `opencv-python` for camera and video |
| **3D before 1.0**: `P3D`, `WEBGL`, meshes, cameras, lights | Processing, p5.js | 1.0 means the 2D surface (D-014). The draw-op IR is backend-neutral, so 3D stays possible later (E-21) | `pyglet`, `moderngl`, `vpython` |
| **Running in the browser before 1.0** | p5.js | Proven feasible (Spike 08) but directional until after 1.0 (D-014, E-31; plan in `Browser_Mode_Note.md`) | Run Playground on the desktop; use p5.js for browser pieces |
| **Source compatibility with p5/Processing/DrawBot** | — | Playground borrows names where the meaning matches, in Python style (snake_case), and says where it differs. It never claims to run their code unchanged | The guide's "Coming from…" chapters list every deliberate difference |

## Consequences

- A request for any item above is answered with a link to this ADR, not a backlog story.
- Reopening an item means a new ADR that supersedes this one for that row, with a maintainer decision.
- The guide's chapters 14 and 15 link here, so learners see the "use instead" column.
- Directional items (3D, browser) keep their epics (E-21, E-31) so the architecture stays open to them.
