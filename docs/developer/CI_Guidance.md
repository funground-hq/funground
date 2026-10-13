# Spending CI wisely

How funground uses GitHub Actions without waste. The maintainer asked for it on 13 October 2026, after
the first half of October used 33,589 runner minutes, $796 at list price. It cost nothing because the
repository is public, but the waste was real: long queues, slow results, and one run that hung for 6
hours. The rules here apply to every funground-hq repository; the `funground-sdlc` skill points to
this note.

## The idea

**The maintainer's machines are the first CI.** The full suite runs on the Windows machine before
every push (the process already requires it), and on the maintainer's Mac before a release. GitHub
adds only what those cannot: another Python version, Linux, a clean install. Problems are found and
fixed locally, never by pushing to see what CI says. Each system is tried on GitHub only once the one
before it has passed, and all three only for a release.

## What runs when

| When | What runs | Jobs |
|---|---|---|
| A push that changes only records or prose (`sprints/`, `docs/design/`, `docs/backlog/`, `docs/developer/`, `docs/releases/`, `README.md`, `CHANGELOG.md` …) | nothing | 0 |
| A push or a pull request that changes code, tests, examples, tools, the guide, the reference, the gallery, `pyproject.toml` or a workflow | Windows, Python 3.11 (the local run covers 3.14) | 1 |
| **Run workflow**, as chosen: tick the systems, list the Python versions (default: Windows, `["3.11"]`) | only those, Windows → Linux → macOS in that order | as chosen |
| **Run workflow** with *release* ticked, for a release only | Windows 3.11 to 3.14 → then Linux 3.11 to 3.14 → then macOS 3.11 and 3.14 | 10 |
| A release tag `v*` | no `ci` run (the tagged commit was tested before it was tagged); `release.yml` builds and smoke-tests on the three systems, about a minute each | 3 small |

Each stage starts only when the stage before it has passed (`needs:`), and inside a stage the first
failure cancels the rest (`fail-fast`). macOS gets two Python versions, not four: its minutes cost
about 10 times Linux's, and the versions in between are covered by Windows and Linux.

While a problem is being fixed, CI runs on **one system and one Python version**: the one that
showed it. Run workflow → `ci` → tick only that system, give only that version.

Always on:
- **A 30-minute limit per job** and **a 5-minute limit per test** (`pytest-timeout`), so a hang
  costs half an hour and names the test that hung.
- **A newer push cancels the older run** on the same branch or pull request.
- **Failed reference pictures are kept** for 7 days as a run artifact, so a golden failure can be
  looked at without running it again.

## Habits

- **Push in groups.** Commit as often as useful, but push when a story or a batch of records is
  complete and the local suite is green. Records go with the code they describe.
- **Do not use CI to debug.** Reproduce locally. If only GitHub's machine shows it, make the test
  say more (a message, a kept file), then run the failing cell once: **Re-run failed jobs**, never
  the whole run.
- **Prepare a release with one full run:** *Run workflow* → `ci` → tick *release*, on the commit to
  be tagged. Before it, the maintainer runs the suite on the Mac; when that passes and macOS is not
  what changed, the release run may be a chosen run of Windows and Linux only.
- **Pin the test libraries.** CI installs the exact versions in `tests/constraints.txt` (the
  maintainer's machine's), so a library's new release cannot turn CI red overnight, as pypdfium2
  5.14 and pycairo 1.29.2 did in October 2026. Learners still get the newest versions. Update the
  pins on purpose: in one change, after the full suite passes locally with the new versions.
- **Look at the usage once a month** (or before a busy week):

  ```text
  gh api organizations/funground-hq/settings/billing/usage
  ```

  It lists minutes per system and month, the list price and the discount. The aim is to stay **under
  $50 a month at list price** even though the bill is $0.

## What it costs (list prices from GitHub's usage data, October 2026)

| Runner | Per minute | One full-suite job (about) |
|---|---|---|
| Linux | $0.006 | 8 min = $0.05 |
| Windows | $0.010 | 8 min = $0.08 |
| macOS | $0.062 | 13 min = $0.81 |

| Pattern | Per push |
|---|---|
| Before (12 jobs on every push, and again on a tag) | about $3.70, about 116 runner minutes |
| Everyday push now (1 Windows job) | about $0.08 |
| A chosen run while fixing (1 job) | $0.08 Windows, $0.05 Linux, $0.81 macOS |
| Release run now (10 jobs, if all pass) | about $2.10 |
| Prose-only push now | $0 |

## Other repositories

- `funground-hq.github.io` builds the website on Linux on each push to `main` and once a day: about
  a minute each, so leave it.
- `funground-cairo-wasm` builds the browser wheels on Linux (up to 90 minutes) on a push to `main` or a
  `claude/**` branch; it is pushed rarely, and it already cancels older runs.
- `funground-web` and `funground-run.github.io` have no test workflows; their browser tests run on
  the maintainer's machine.
- A new workflow in any repository follows the same rules: path filters, a time limit, cancel older
  runs, macOS last and only when it is needed.
