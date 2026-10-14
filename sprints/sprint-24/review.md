# Sprint 24 review — the website's identity and the Play editor (E-34)

**Dates:** 13 October 2026, on `funground-hq.github.io` branch `design/site-identity`, merged by site PR #7
(`349f074`, 13 Oct) and deployed. **Signed off 14 October 2026.**

## Outcome

Goal met for the stories built: the site looks like a sketchbook (paper, ink, tomato; the logo; hosted fonts),
the home page shows the first sketch beside its picture, and Play is the editor alone, with the code and the
picture given the screen.

| Story | Result |
|---|---|
| S-184 Play's duplicate id | fixed; the editor test now carries the heading and fails on the old bug |
| S-185 Stylesheet, fonts, logo | `funground.css` tokens, three OFL families hosted, the logo mark; strict build, links, no sideways scroll |
| S-186 The home page | the revised design plus the maintainer's changes: "Three ways to run it", the course card, "Made for learning and teaching", "Coded mostly by AI under human guidance", Windows now and Mac and Linux coming soon, the PyPI install line |
| S-187 The Play layout | editor only (no sidebars, footer or tab row), split with a drag handle, zoom, messages above the picture, help popover, status with a spinner, keys, the restart notice; `design/Play_Layout_Note.md`; `test_editor.mjs` 12 of 12 |
| S-190 The gallery index | **not started**: back to the backlog |
| S-191 Sketch panels on example pages | **not started**: back to the backlog |

Also landed the same day, outside the sprint's stories: one navigation with Learn holding the guide and the
course; the Showcase removed; the course "Creative practice with funground" (S-194, funground PR #1); the
runner's restart notice (funground-web PR #6, funground-run PR #3); `f.run(fps)` fixed.

**Tests:** `test_editor.mjs` 12 of 12; the site's pull-request build (strict MkDocs) green; screenshots of the
built site checked locally with `tools/design_shots.mjs`.

## Decisions

- **D-096** identity, **D-097** logo, **D-098** hosted fonts, **D-099** navigation: all accepted (b) on 13 Oct after
  the maintainer reviewed local previews.

## Findings that change later work

1. Visual work went fastest as design package → local previews → the maintainer's review → changes, with a
   story per commit. Keep it for S-188 to S-191.
2. The daily site build is scheduled for 03:17 UTC but GitHub has started it 5½ to 7½ hours late every day this
   week (14 Oct: 08:48 UTC). A fix that must be live sooner needs a manual run.
3. The 13 Oct scheduled build showed 3 h 9 min, but it waited in the queue: the build job ran 29 s and the deploy
   10 s (10:42 created, 13:40 started). Queued time is not billed; nothing to fix.

## Built by

The main session, from the design package made in claude.ai.

## Carried over

S-190 and S-191 return to the backlog with S-188 and S-189, for a later site sprint.

## Retrospective

- Deciding the four identity questions (D-096 to D-099) from real previews, not mockups, made them quick.
- The sprint grew on the day (navigation, Showcase, course card): fine for a design sprint, but the review
  only lists it afterwards; next time the additions go into the sprint table as they are agreed.

## Sign-off

**Signed off by the maintainer, 14 October 2026** ("Sign off pending sprints"). Sprint closed.
