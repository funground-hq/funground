# Releasing funground

How funground gets from this repository to `pip install funground`. Written for the maintainer and
for future contributors who take over releases. Nothing secret is stored here: publishing uses
**trusted publishing**, so there are no passwords or API tokens to keep anywhere.

## The pieces

| Piece | Value |
|---|---|
| Package name on PyPI and TestPyPI | `funground` |
| PyPI account that owns it | `maverick27`, linked to the GitHub account `samir-joshi` |
| PyPI organisation | `funground`, requested; until it is approved the project lives under `maverick27` and is transferred later |
| GitHub repository | `funground-hq/funground` |
| Release workflow | `.github/workflows/release.yml` |
| GitHub environments | `testpypi` (no rules), `pypi` (protected by a required reviewer: the maintainer) |
| Version | `[project] version` in `pyproject.toml`; the release tag is `v` plus that version, e.g. `v0.1.0` |

## One-time set-up

### 1. Accounts

- An account on **pypi.org** and a separate one on **test.pypi.org**. They are two different sites with separate logins, and both need two-factor authentication.
- Optional: request a PyPI **organisation**. It is not needed to publish (see step 5).

### 2. Pending publishers (trusted publishing)

A *pending publisher* tells PyPI: "the first upload of this project name will come from this GitHub workflow; trust it".
PyPI shows it as **pending** until that first upload succeeds; then it becomes a normal project owned by the
account. Until then the name is not strictly reserved, so do not leave it pending for months.

On **pypi.org**, go to Account settings → Publishing → *Add a new pending publisher* → GitHub, and enter:

| Field | Value |
|---|---|
| PyPI project name | `funground` |
| Owner | `funground-hq` |
| Repository name | `funground` |
| Workflow name | `release.yml` |
| Environment name | `pypi` |

On **test.pypi.org**, enter the same values, except the environment name is `testpypi`.

### 3. GitHub environments

In the GitHub repository, go to Settings → Environments:
- Create `testpypi`. It needs no rules.
- Create `pypi`, then under *Required reviewers* add the maintainer. The PyPI upload then waits for an explicit *Approve* click.

GitHub would create both environments by itself on first use, but without the reviewer rule.

### 4. Nothing else

No tokens, no `~/.pypirc`, no secrets in the repository. The workflow asks PyPI for a short-lived credential
each time it runs (`permissions: id-token: write`).

### 5. Later: move the project into the organisation

When the `funground` organisation is approved, transfer the project on pypi.org: Your projects → `funground` →
Settings. The name, releases and history stay as they are.

## What the workflow does

`release.yml` runs in two ways.

| Trigger | Steps |
|---|---|
| **Run workflow** by hand (Actions → release) | build the sdist and wheel → `twine check` → upload to **TestPyPI** → on Windows, macOS and Linux, install from TestPyPI and run a smoke test (draw, save PDF/SVG/PNG, read the PDF's text, a sargam melody, `python -m funground.gallery --list`) |
| **Push a tag** `v*` | the same, plus: check that the tag matches the version → upload to **PyPI** (waiting for the reviewer's approval) |

A version can be uploaded only **once** to each index. A dry run of `0.1.0.dev0` uses up that version on
TestPyPI, not on PyPI. For another dry run, bump the dev version first (`0.1.0.dev1`).

## Making a release

1. **Sprint sign-off:** the maintainer signs off the sprint that completes the release.
2. **Checklist:** every item in `sprints/sprint-11/release_checklist.md` is ticked, the maintainer's checks included.
3. **Prepare it in one commit:**
   - `pyproject.toml`: the version without `.devN`, e.g. `0.1.0`;
   - `CHANGELOG.md`: "Unreleased" becomes `0.1.0 — <date>`;
   - `README.md`: the install line is `pip install funground`, and image links are absolute, so they show on PyPI.
4. **CI:** green on all 12 cells for that commit.
5. **Dry run:** "Run workflow" on the commit, if the version was not dry-run before (see the note above).
6. **Go-ahead:** the maintainer gives it. Then the main session tags and pushes:
   ```text
   git tag -a v0.1.0 -m "funground 0.1.0"
   git push origin v0.1.0
   ```
7. **Approve:** the maintainer clicks *Approve* on the `pypi` environment. The release is then on PyPI.
8. **Check:** in a fresh virtual environment, `pip install funground`, run the smoke test and `python -m funground.gallery`.
9. **Open the next version:** set it to `0.2.0.dev0`, with a new "Unreleased" section in the changelog.

Tagging and publishing are irreversible and public. Per `docs/PROCESS.md`, they happen only in the main session,
after the maintainer's go-ahead.

## If something goes wrong

| Symptom | Likely cause |
|---|---|
| "invalid-publisher" or 403 on upload | The pending publisher's fields do not match exactly: owner, repository, workflow file name or environment name |
| "File already exists" | That version was uploaded before; bump the version (PyPI never allows re-uploading a version) |
| The smoke test cannot find the package | TestPyPI takes a minute to index; the step retries 5 times, 30 s apart |
| Tag/version check fails | The tag is not `v` plus the `pyproject.toml` version |
| A bad release reached PyPI | You cannot overwrite it. *Yank* it on pypi.org (it stays installable only by exact pin) and release a fixed `.post1` or the next patch |
| Pushes to GitHub time out | On the maintainer's Jio connection GitHub was blocked twice; switching network fixed it |
