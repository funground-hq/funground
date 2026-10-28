// S-231 step 4: Transformers.js pipelines in a module worker, headless Chrome, one job at a time, every request host logged.
//   node measure_tjs.mjs --jobs classify:cdn:q8,objects:local:fp32 [--runs 30] [--device webgpu] [--out file.json]
// job = task:mode:dtype. Modes are explained in tjs_worker.js. Serves this folder, /hf (models), /tjs (library, wasm), /frames from 127.0.0.1.
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
const { chromium } = await import("file:///C:/Projects/funground-hq.github.io/tools/codemirror/node_modules/playwright-core/index.mjs");
const HERE = path.dirname(fileURLToPath(import.meta.url));
const SP = "C:/Users/samirj/AppData/Local/Temp/claude/C--Projects-playground/0b7d35bf-76e3-4108-a4ee-56915dd6bc0f/scratchpad";
const CHROME = "C:/Users/samirj/AppData/Local/Google/Chrome/Application/chrome.exe";
const arg = (n, d = null) => (process.argv.includes(n) ? process.argv[process.argv.indexOf(n) + 1] : d);
const JOBS = arg("--jobs").split(","), RUNS = +arg("--runs", "30"), DEVICE = arg("--device", ""), OUT = path.join(HERE, arg("--out", "tjs_results.json"));
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".png": "image/png", ".json": "application/json", ".wasm": "application/wasm" };
const server = http.createServer((req, res) => {
  const url = new URL(decodeURIComponent(req.url), "http://x"), p = url.pathname;
  const file = p.startsWith("/hf/") ? path.join(SP, "hf_local", p.slice(4)) : p.startsWith("/tjs/") ? path.join(SP, "tjs_local", p.slice(5)) : p.startsWith("/frames/") ? path.join(SP, "models_web/frames", path.basename(p)) : path.join(HERE, path.basename(p) || "tjs_page.html");
  if (!existsSync(file)) { res.writeHead(404).end(); return; }
  res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] ?? "application/octet-stream" }).end(readFileSync(file));
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ["--headless=new"] });
const results = [];
const hostOf = (u) => { const h = new URL(u).host; return h.startsWith("127.0.0.1") ? "127.0.0.1 (ours)" : h; };
for (const spec of JOBS) {
  const [task, mode, dtype] = spec.split(":");
  const context = await browser.newContext({ viewport: { width: 800, height: 600 } });   // fresh context = empty cache
  const page = await context.newPage();
  const requests = [];
  context.on("requestfinished", async (r) => { try { const s = await r.sizes(); requests.push({ url: r.url(), host: hostOf(r.url()), status: (await r.response())?.status(), bytes: s.responseBodySize }); } catch { /* closed */ } });
  context.on("requestfailed", (r) => requests.push({ url: r.url(), host: hostOf(r.url()), failed: r.failure()?.errorText }));
  const logs = []; page.on("console", (m) => logs.push(`${m.type()}: ${m.text()}`.slice(0, 300)));
  let outcome;
  try {
    await page.goto(`${ORIGIN}/tjs_page.html?task=${task}&mode=${mode}&dtype=${dtype}&runs=${RUNS}&device=${DEVICE}`);
    await page.waitForFunction(() => window.__done != null, null, { timeout: 280000, polling: 500 });
    outcome = await page.evaluate(() => window.__done);
  } catch (e) { outcome = { ok: false, error: "timeout or crash: " + e.message }; }
  await new Promise((r) => setTimeout(r, 400)); await context.close();
  const hosts = {}; for (const r of requests) hosts[r.host] = (hosts[r.host] ?? 0) + 1;
  const rec = { spec, ...outcome, hosts, requests: requests.map(({ url, bytes, status, failed }) => ({ url: url.replace(ORIGIN, ""), bytes, status, failed })), logs: logs.slice(0, 8) };
  results.push(rec); const r = rec.result;
  console.log(rec.ok ? `${spec}: first ${(r.first_result_ms / 1000).toFixed(1)} s, ${r.fps.toFixed(1)}/s, median ${r.median_ms.toFixed(0)} ms, p90 ${r.p90_ms.toFixed(0)}; hosts ${JSON.stringify(hosts)}; ${JSON.stringify(r.found).slice(0, 200)}` : `${spec}: FAILED ${String(rec.error).slice(0, 500)}`);
  writeFileSync(OUT, JSON.stringify({ date: new Date().toISOString(), chrome: browser.version(), transformers_js: "4.3.2", jobs: results }, null, 1));
}
await browser.close(); server.close();
