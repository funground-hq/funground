# Sprint 8 review — Phase 3b: documents and pages

**Dates:** 1 October 2026 (draft for the maintainer — not yet signed off)
**Goal:** DrawBot-style documents — pages of any size in one multi-page PDF, `show()` flipping
through them — and the script follow-ups from Sprint 7.

## Outcome

Both stories are done; nothing is carried over. **Checkpoint met:** no golden, snapshot or gallery
image that existed before the sprint changed (`git diff -M --diff-filter=MD 675e889..HEAD -- tests/golden
tests/snapshots docs/gallery/images docs/reference/images` is empty). **3 public names added**
(142 → 145): `new_page`, `page_count`, `page_size`. No v0.5 API change: `size()` keeps its signature.

| Story | Result | Built by |
|---|---|---|
| S-084 Pages | `new_page` (sizes or names such as `"A4"`, `"A5Landscape"`), `page_count`, `page_size`; one multi-page PDF with each page at its own size; numbered PNG/SVG files; `show()` flips pages with the arrow keys; new gallery area "Documents and pages" | Sonnet sub-agent |
| S-085 Script follow-ups | `full_screen()` in a script sizes the canvas to the display without a window, and `show()` opens it full screen; script memory measured and documented | Sonnet sub-agent |

## Test results

```
1166 passed   (Sprint 7 close: 1116)
CI: 12/12 green on every story commit
```

## Measurements

- **Multi-page PDF:** pages of 420×595, 420×595 and 842×595 points read back with exactly those
  `/MediaBox` sizes.
- **Script memory:** about 100 bytes per kept shape (1 000 circles ≈ 90 KB, 10 000 ≈ 950 KB), so a
  million shapes take about 100 MB. The first estimate in the contract (1 KB per hundred) was ten
  times too low and was corrected.

## Findings

1. **Pinning first still pays.** The page API (D-036) was decided under D-034 and both stories
   built straight from the contract rows. Review added only clarifications: what `size()` does to
   earlier pages, a size name with extra numbers, page flipping at the ends.
2. **Builders flag what they cannot check.** The pages builder said its DrawBot function names came
   from memory; they were checked against DrawBot's own documentation and are right.
3. **Real-desktop testing is still missing.** CI runs macOS and Linux only headless. A manual run on
   real desktops is now a release prerequisite in the Roadmap.

## Decisions

| ID | Outcome | By |
|---|---|---|
| D-036 | Page API: DrawBot names, pages belong to scripts, `size()` unchanged | Claude, under D-034 |
| D-037 | Path-boolean library for Sprint 9 | **pending — the maintainer's call** (a new dependency) |

## Sign-off

Sprint 8 closes when the maintainer has read this review and the reviewer's guide.

## Retrospective

- **Went well:** small sprint, clean stories; every brief stated timeouts and the process rule, and
  no builder stalled or overreached.
- **Went badly:** one estimate (script memory) was pinned before it was measured.
- **Change for Sprint 9:** measure first, then pin numbers in the contract.

## AI-USAGE log entry

Added to `AI-USAGE.md` under Sprint 8.
