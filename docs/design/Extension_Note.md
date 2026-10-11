# Design note: the funground extension for github.dev, vscode.dev and VS Code (0.2)

**Status:** describes what is built, 11 October 2026 (stories S-156 spike, S-158, S-155; decisions D-079 to
D-084). Code: `funground-hq/funground-web`, folder `vscode-extension/` (developer README there), using the
browser runner in `runner/` (`Web_Runner_Note.md`). Measurements: `vscode-extension/RESULTS.md` and
`spikes/S-156_RESULTS.md` in funground-web.

## Why an extension

D-079: learners edit and save their sketches in **github.dev**, GitHub's own editor, and see the sketch run on
the same page. github.dev cannot be framed by another site (it redirects to vscode.dev, which sends
`frame-ancestors 'none'`), so our page cannot hold it. What github.dev does allow is **extensions**: it is VS
Code running in the browser, and it runs "web extensions". So the sketch's picture comes to the editor, as a
panel beside the code, rather than the editor coming to our page. Editing, saving (a commit), the file tree and
the GitHub sign-in stay GitHub's; we hold no token and run no server.

## How a VS Code extension works (the parts we use)

- **Manifest.** An extension is a folder with a `package.json`: who publishes it (`publisher`), what it is
  (`name`, `version`), which VS Code it needs (`engines.vscode`), what it adds to the editor
  (`contributes`), when it starts (`activationEvents`) and where its code is (`main` for desktop Node code,
  `browser` for code that runs in a browser).
- **Contributions are declarations.** Commands, their titles, a keybinding, a button in the editor's title
  bar and the extension's settings are all declared in the manifest. VS Code shows them before any of our
  code has run (which is why a broken install still showed "command 'funground.run' not found": the
  declaration was there, the code was not).
- **Activation.** Our code is loaded only when needed: when a Python file is opened (`onLanguage:python`) or
  when one of our commands is run. `activate(context)` then registers the commands' handlers and listens to
  editor events.
- **The extension host.** Extension code does not run in the editor's page. On the desktop it runs in a Node
  process; in the browser (github.dev, vscode.dev) it runs in a **web worker**, which is why a web extension
  may use only browser APIs, no Node (`browser` entry, no `main`). It talks to the editor only through the
  `vscode` API: documents and their text, editor and save events, the file system (`workspace.fs`, which in
  github.dev reads the repository through GitHub), diagnostics (the red underlines), output channels.
- **Webviews.** An extension can open a **webview panel**: an HTML page in an iframe on its own origin
  (`*.vscode-cdn.net` on vscode.dev), with its own Content Security Policy, isolated from the editor. The
  extension and the page exchange messages (`webview.postMessage` / `onDidReceiveMessage`), nothing else. The
  page's own files are loaded from the extension's folder through `asWebviewUri`, limited to
  `localResourceRoots`.
- **Extension kind.** An extension with only a `browser` entry is a *web* extension; the package says so
  (`ExtensionKind: web`) and only such extensions are offered in github.dev and vscode.dev.
- **Workspace trust and virtual workspaces.** github.dev's files are virtual (not on a disk) and a repository
  may be untrusted. The manifest declares that the extension works in both (`virtualWorkspaces`,
  `untrustedWorkspaces`), because it never runs sketch code with the editor's rights.
- **Packaging and the Marketplace.** `vsce` packs the folder into a `.vsix` (a zip with a manifest). The
  Visual Studio Marketplace hosts it under the publisher `funground-hq`; github.dev and vscode.dev install
  from there (from the Marketplace's own servers; see "How learners get it").

## Our architecture

```
github.dev page (GitHub's origin)                          webview panel (its own origin, our CSP)
┌ editor: sketches/bounce.py ──────────────────────┐       ┌ media/preview.js ─────────────────────────┐
│ typing ─ 400 ms pause ─┐                          │       │  createRunner({reuse, microphoneRefusal}) │
│ Ctrl+S ────────────────┤                          │ run   │    runner.js ── worker (blob:) ───────────┤
│ another sketch opened ─┤  extension.js            ├──────►│      Pyodide + funground + Cairo wheels   │
│                        └► (extension host, a web  │ {text,│      (loaded from funground-hq.github.io/ │
│ data/ files, helpers ◄── workspace.fs            │ files}│       runtime/0.2-dev/)                   │
│ red underline ◄──────── diagnostics  ◄───────────┤◄──────┤    canvas · Web Audio · output            │
└───────────────────────── worker; no Node) ────────┘ error └───────────────────────────────────────────┘
Save = GitHub's commit (Source Control). Sketch code runs only in the panel.
```

Two pieces, each about 300 lines:

- **`extension.js`** (extension host). Registers **funground: Run** (Ctrl+Enter, ▷) and **funground: Stop**;
  opens one panel beside the editor; decides *when* to run and *what* to send.
  - When: on the Run command; 400 ms after the last change to the sketch (`funground.autoRunDelay`); at once
    on save; when the learner switches to another runnable sketch. A repeat of exactly what already ran is
    skipped.
  - What: the sketch's text (as in the editor, saved or not), every file under `data/` beside it (read with
    `workspace.fs`, bytes), and the other `.py` files in its folder (so `import palette` works), capped at
    32 MB.
  - Which file: the panel follows the active editor only to a **runnable sketch**, a file with a top-level
    `run()` or `show()` call. A helper such as `palette.py` has neither, so opening it keeps its sketch in the
    panel, and editing it re-runs that sketch. Run (Ctrl+Enter) still runs any Python file.
  - Errors: a traceback's line in the sketch becomes a diagnostic in the document the run came from.
  - Where Python comes from (D-081): the `funground.runtimeUrl` setting if set; else a copy inside the
    extension if one was built in; else `https://funground-hq.github.io/runtime/<fungroundRuntime>/`, the
    version named in `package.json`.
- **`media/preview.js`** (the panel's page). Loads the runner, runs what it is sent, reports `ready`,
  `error` (with the traceback), and keeps a record of runs for the tests. Everything about Python, drawing,
  sound and input is the **unchanged website runner** (`runner/`): the panel is one more host of
  `funground.web.Session`, beside the website's Play page.

### Runner options the panel uses

The runner is shared with the website, so the panel's needs are options, all off by default:

- `pyodideUrl`, `runtimeUrl`: load from the runtime folder on our site.
- A worker started from a `blob:` URL when the runner's files are on another origin (a webview's own files are).
- `reuse` (D-083): the next run uses the same Python; the sketch is stopped (its `finish()` runs) and a new
  `Session` starts it afresh. A re-run takes about 0.4 s from the last key, nearly all of it the deliberate
  pause; without reuse each run waited 6 to 24 s for a new Python. funground S-157 tests that a later
  Session draws byte-identical frames and forgets fonts and modules loaded from the sketch's folder. A
  sketch that does not stop within 250 ms (`while True:`) still has its worker ended.
- Each run gets a fresh folder (the last one deleted, since a reused Python keeps files in memory), first on
  `sys.path` as `python sketch.py` does; no bytecode is written, so an edited helper is always re-read.
- `microphoneRefusal`: the panel cannot use the microphone (below), so a sketch that starts it gets one
  plain line instead of a browser prompt.

## Safety

- Sketch code runs only in the webview: its own origin, no access to the editor, the GitHub session or
  other extensions, and a network limited by our Content Security Policy to the extension's files and our
  runtime site.
- The policy (`extension.js`, `previewHtml`): `default-src 'none'`; scripts only from the page's one
  inline module (by nonce), the extension and the runtime site, plus `'wasm-unsafe-eval'` for WebAssembly.
- **One exception, D-080:** `'unsafe-eval'` in this panel only, because pygame-ce's WebAssembly modules
  (which decode pictures, ADR-004) are linked with `eval`. The panel already runs the learner's Python, in
  its own origin, so the exception adds little; it is named at the line. The website runner does not have it.

## How learners get it (D-082)

Tried in the real github.dev and vscode.dev (10 and 11 October):

| Route | Result |
|---|---|
| Carried by the sketchbook template in `.vscode/extensions/` | Offered and installed, but its code cannot be loaded from the repository's virtual file system ("Failed to fetch") |
| *Install Extension from Location* with an address on our site | Refused: vscode.dev's own policy downloads extensions only from the Marketplace's servers and `localhost` |
| *Install Extension from Location* from `localhost` (`serve.py`) | Works: installs, loads Python from the site, draws (headers needed: CORS, and `Cross-Origin-Resource-Policy` because the panel is cross-origin isolated). For testers |
| **Visual Studio Marketplace**, publisher `funground-hq` | The route for learners: Extensions view, search, Install; and the template's `.vscode/extensions.json` recommendation makes github.dev offer it when a sketchbook is opened |

## Testing

- `vscode-extension/test/run_tests.mjs` drives VS Code for the web (from `@vscode/test-web`) in headless
  Chrome as a learner would: opens files, types, saves. It checks four sketches byte-identical to
  funground's goldens, a picture's pixels, sound, a WAV, an edited helper, an error's line, the live re-run
  time, in three runtime modes (bundled, a local site, the published address answered locally).
- The real vscode.dev was driven the same way for the install routes. VS Code's test server does not apply
  vscode.dev's security policy, which is why the first "install from our site" check passed locally and
  failed for real: **a check that matters for learners runs against the real product.**

## Limits now

- No microphone in the panel: VS Code's webview frame does not allow it. Listening sketches run on the
  website's Play page or the desktop.
- Chrome first; Edge should match (same engine); Firefox and Safari untested.
- One panel, one sketch at a time; output is text only.
- The extension's code and the website's runtime version must match: `fungroundRuntime` in `package.json`
  names the folder; the site keeps publishing it.

## Future possibilities

Roughly in order of value for learners:

1. **Publish and recommend** (next): the Marketplace listing, the template's recommendation, the sketchbook
   README reduced to "press Install".
2. **Keep old runtime versions on the site** (`runtime/0.2-dev/`, later `0.2.0/` ...), so an installed
   extension keeps working when funground moves on; the site build then publishes a list of versions.
3. **Help while typing**: completion and hover documentation for `f.` functions, by shipping funground's
   type stubs for the Python language features github.dev already has, or a small completion provider.
4. **Errors in place**: all tracebacks as diagnostics (helpers too), and a "What does this error mean?" link
   to the guide's error page.
5. **Save a picture**: a panel button that writes the canvas (PNG) or a GIF into the repository with
   `workspace.fs`, so it is committed with the sketch; and `f.save()` writing into the workspace.
6. **Controls panel**: funground's sliders (S-101) as webview controls beside the canvas.
7. **Share**: a link that opens a sketch on the website's Play page or the editor (S-151 part 2).
8. **Microphone**: open the running sketch in a browser tab on our site (`openExternal`) when it listens, or
   ask VS Code to allow the microphone in webviews (an upstream issue).
9. **Open VSX** as a second registry (VSCodium, Gitpod, Theia users), and desktop VS Code polish (the same
   extension already runs there).
10. **Offline**: a build with the runtime inside (22 MB) for classrooms without reliable internet.

## Decisions behind it

D-079 (github.dev as the editor), D-080 (`'unsafe-eval'` in the panel only), D-081 (runtime from the site,
versioned), D-082 (how learners get it; outcome above), D-083 (re-run in the same Python), D-084 (LGPL-2.1-only).
