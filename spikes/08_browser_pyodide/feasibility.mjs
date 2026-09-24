// Spike 08, Part 1: can Playground's pure-Python core run under Pyodide, and how fast?
// Usage:  node feasibility.mjs            (writes results.json, prints one JSON line)
// Needs network once: pyodide.loadPackage("fonttools") pulls the wheel from the Pyodide CDN.
import { loadPyodide } from "pyodide";
import { readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..");
const pkgDir = join(repo, "playground");
// Desktop-only modules (pygame, cairo) and caches never go to the browser.
const SKIP = new Set(["platform/pygame_platform.py", "renderers/cairo2d.py", "export", "__pycache__"]);

const now = () => performance.now();
const R = { pyodide: "0.28.3", node: process.version, platform: `${process.platform}-${process.arch}` };

// (a) load Pyodide
let t = now();
const pyodide = await loadPyodide();
R.pyodide_load_ms = +(now() - t).toFixed(1);

// (b) fontTools (pure-Python wheel from the Pyodide CDN; network)
t = now();
await pyodide.loadPackage("fonttools", { messageCallback: () => {} });
R.fonttools_install_ms = +(now() - t).toFixed(1);

// (c) mount playground/ into the Pyodide FS
t = now();
let files = 0, bytes = 0;
function mount(dir) {
  for (const name of readdirSync(dir)) {
    const abs = join(dir, name);
    const rel = relative(pkgDir, abs).split(sep).join("/");
    if (SKIP.has(rel) || SKIP.has(name)) continue;
    const dest = `/playground/playground/${rel}`;
    if (statSync(abs).isDirectory()) { pyodide.FS.mkdirTree(dest); mount(abs); continue; }
    const data = readFileSync(abs);
    pyodide.FS.writeFile(dest, new Uint8Array(data));
    files++; bytes += data.length;
  }
}
pyodide.FS.mkdirTree("/playground/playground");
mount(pkgDir);
R.mount_ms = +(now() - t).toFixed(1);
R.mounted_files = files;
R.mounted_bytes = bytes;

// (d)(e)(f) everything else runs in Python; see feasibility.py
t = now();
const py = readFileSync(join(here, "feasibility.py"), "utf8");
const inner = JSON.parse(pyodide.runPython(py));
R.python_total_ms = +(now() - t).toFixed(1);
Object.assign(R, inner);

writeFileSync(join(here, "results.json"), JSON.stringify(R, null, 2) + "\n");
console.log(JSON.stringify(R));
