Spike S-156 for funground 0.2: render a funground sketch beside github.dev.

Follow the funground-sdlc skill in .claude/skills (this is a spike: question, pass/fail criteria set
first, measurements, recommendation; work on a branch and push it; never change other repositories).

Read first, in funground-hq/funground branch release-0.2-web: docs/design/Editor_Note.md (the last
section lists the questions Q1-Q6 and pass criteria) and docs/design/Web_Runner_Note.md. In this repo
(funground-web), branch feature/runner: runner/ (worker.js, runner.js, audio.js,
microphone-worklet.js, README.md, RESULTS.md) is the browser runner the extension should reuse, and
tools/build_runtime.py builds its runtime/ folder (wheels from the funground-cairo-wasm v0.1.0-wasm
release plus a funground wheel built from a funground checkout).

Decision D-079 (maintainer): learners edit and save their sketches in github.dev (GitHub's own web
editor) and the sketch renders on the same page. Find out how:
1. Q1: can github.dev or vscode.dev be framed by another site? Record the response headers.
2. Build, in a new folder vscode-extension/ on a branch spike/s156-github-dev, a minimal VS Code web
   extension ("browser" entry point, no Node APIs): a "funground: Run" command and a preview webview
   beside the editor that runs the runner on the active .py file, re-runs on edit (debounced) and on
   save, shows print output and errors with line numbers, plays sound (Web Audio) and, if possible, uses
   the microphone; data/ files read through vscode.workspace.fs. Decide whether the runtime (Pyodide,
   wheels) ships inside the extension or loads from a site with CORS, and measure both if quick.
3. Test it with @vscode/test-web (headless Chromium) against a sample sketchbook folder: a Session-1
   sketch and a gallery example render (compare the frame to the funground golden: byte-identical as in
   S-153), a sound example produces audio buffers, a data/ picture loads, live update time after the
   first load. Check the webview's Content Security Policy is satisfiable without weakening safety.
4. Q5: document the install path (sideload with "Install Extension from Location" for testing;
   Marketplace and Open VSX publishing needs, which are the maintainer's act) and how a sketchbook
   template's .vscode/extensions.json recommendation appears in github.dev.
5. Write spikes/S-156_RESULTS.md: criteria, results, sizes, timings, limits, a recommendation, and the
   steps for the maintainer to try it in real github.dev. Commit and push the branch.
