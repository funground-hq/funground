// S-231 step 3: runs one ORT-web job at a time in headless Chrome (fresh context each), logs every request host.
//   node measure.mjs --tasks pose,hand --ep wasm --threads 1 [--iso] [--gpu-flags] [--version 1.31.1] [--out file.json]
// Serves this folder, the models (MODELS) and the 640 x 480 frames (FRAMES) from 127.0.0.1. Never starts chrome by hand.
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
const { chromium } = await import("file:///C:/Projects/funground-hq.github.io/tools/codemirror/node_modules/playwright-core/index.mjs");
const HERE = path.dirname(fileURLToPath(import.meta.url));
const SP = "C:/Users/samirj/AppData/Local/Temp/claude/C--Projects-playground/0b7d35bf-76e3-4108-a4ee-56915dd6bc0f/scratchpad";
const MODELS = `${SP}/models_onnx`, FRAMES = `${SP}/models_web/frames`;
const CHROME = "C:/Users/samirj/AppData/Local/Google/Chrome/Application/chrome.exe";
const arg = (n, d = null) => (process.argv.includes(n) ? process.argv[process.argv.indexOf(n) + 1] : d);
const TASKS = arg("--tasks", "pose").split(","), EP = arg("--ep", "wasm"), THREADS = +arg("--threads", "1"), VERSION = arg("--version", "1.31.1");
const ISO = process.argv.includes("--iso"), OUT = path.join(HERE, arg("--out", "web_results.json"));
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".png": "image/png", ".json": "application/json" };
const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://x"), name = path.basename(url.pathname);
  const file = url.pathname.startsWith("/models/") ? path.join(MODELS, name) : url.pathname.startsWith("/frames/") ? path.join(FRAMES, name) : path.join(HERE, name || "page.html");
  if (!existsSync(file)) { res.writeHead(404).end(); return; }
  const h = { "Content-Type": TYPES[path.extname(file)] ?? "application/octet-stream" };
  if (ISO) { h["Cross-Origin-Opener-Policy"] = "same-origin"; h["Cross-Origin-Embedder-Policy"] = "require-corp"; }   // lets wasm threads run
  res.writeHead(200, h).end(readFileSync(file));
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;
const args = ["--headless=new"];
if (process.argv.includes("--gpu-flags")) args.push("--enable-unsafe-webgpu", "--enable-features=Vulkan,WebGPU");
const browser = await chromium.launch({ executablePath: CHROME, headless: true, args });   // Playwright makes a temporary profile
const results = [];
const hostOf = (u) => { const h = new URL(u).host; return h.startsWith("127.0.0.1") ? "127.0.0.1 (ours)" : h; };
for (const task of TASKS) {
  const context = await browser.newContext({ viewport: { width: 800, height: 600 } });
  const page = await context.newPage();
  const requests = [];
  context.on("requestfinished", async (r) => { try { const s = await r.sizes(); requests.push({ url: r.url(), host: hostOf(r.url()), bytes: s.responseBodySize }); } catch { /* closed */ } });
  context.on("requestfailed", (r) => requests.push({ url: r.url(), host: hostOf(r.url()), failed: r.failure()?.errorText }));
  const logs = []; page.on("console", (m) => logs.push(`${m.type()}: ${m.text()}`.slice(0, 300)));
  let outcome;
  try {
    await page.goto(`${ORIGIN}/page.html?task=${task}&ep=${EP}&threads=${THREADS}&version=${VERSION}`);
    await page.waitForFunction(() => window.__done != null, null, { timeout: 280000, polling: 500 });
    outcome = await page.evaluate(() => window.__done);
  } catch (e) { outcome = { ok: false, error: "timeout or crash: " + e.message }; }
  await new Promise((r) => setTimeout(r, 400)); await context.close();
  const hosts = {}; for (const r of requests) hosts[r.host] = (hosts[r.host] ?? 0) + 1;
  const rec = { task, ep: EP, threads: THREADS, iso: ISO, ...outcome, hosts, requests: requests.map(({ url, bytes, failed }) => ({ url: url.replace(ORIGIN, ""), bytes, failed })), logs: logs.slice(0, 8) };
  results.push(rec); const r = rec.result;
  console.log(rec.ok ? `${task} ${EP} t${THREADS}${ISO ? " iso" : ""}: first ${(r.first_result_ms / 1000).toFixed(1)} s, ${r.fps.toFixed(1)} fps, median ${r.median_ms.toFixed(1)}, p90 ${r.p90_ms.toFixed(1)}, found ${r.found}; hosts ${JSON.stringify(hosts)}` : `${task}: FAILED ${String(rec.error).slice(0, 400)}`);
  writeFileSync(OUT, JSON.stringify({ date: new Date().toISOString(), chrome: browser.version(), ort_web: VERSION, jobs: results }, null, 1));
}
await browser.close(); server.close();
