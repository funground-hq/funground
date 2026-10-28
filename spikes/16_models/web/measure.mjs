// Measures MediaPipe Tasks Vision in headless Chrome, one job at a time (never in parallel).
//   node measure.mjs [--only pose_lite,hand] [--modes main,worker] [--gpu] [--out file.json]
// Each job gets a fresh browser context (empty cache), so the network log shows real downloads.
// Needs the pictures in IMAGES (downloaded by hand from storage.googleapis.com/mediapipe-assets; never committed).
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const { chromium } = await import("file:///C:/Projects/funground-hq.github.io/tools/codemirror/node_modules/playwright-core/index.mjs");
const HERE = path.dirname(fileURLToPath(import.meta.url));
const IMAGES = "C:/Users/samirj/AppData/Local/Temp/claude/C--Projects-playground/0b7d35bf-76e3-4108-a4ee-56915dd6bc0f/scratchpad/models_web";
const CHROME = "C:/Users/samirj/AppData/Local/Google/Chrome/Application/chrome.exe";
const arg = (name) => (process.argv.includes(name) ? process.argv[process.argv.indexOf(name) + 1] : null);
const TASKS = (arg("--only") ?? "pose_lite,pose_full,hand,face,segment,objects,classify").split(",");
const MODES = (arg("--modes") ?? "main,worker").split(",");
const OUT = path.join(HERE, arg("--out") ?? "results.json");

const TYPES = { ".html": "text/html", ".js": "text/javascript", ".jpg": "image/jpeg" };
const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://x");
  const base = path.basename(url.pathname);
  const file = url.pathname.startsWith("/img/") ? path.join(IMAGES, base) : path.join(HERE, base || "page.html");
  if (!existsSync(file)) { res.writeHead(404).end(); return; }
  res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] ?? "application/octet-stream" }).end(readFileSync(file));
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ["--headless=new"] });
const chromeVersion = browser.version();
const results = [];

async function job(task, mode, delegate) {
  const context = await browser.newContext({ viewport: { width: 800, height: 600 } });
  const page = await context.newPage();
  const requests = [];
  context.on("requestfinished", async (request) => {
    try {
      const s = await request.sizes();
      requests.push({ url: request.url(), host: new URL(request.url()).host, type: request.resourceType(), bytes: s.responseBodySize, header_bytes: s.responseHeadersSize });
    } catch { /* page closed */ }
  });
  context.on("requestfailed", (request) => requests.push({ url: request.url(), host: new URL(request.url()).host, failed: request.failure()?.errorText }));
  const logs = [];
  page.on("console", (m) => logs.push(`${m.type()}: ${m.text()}`.slice(0, 300)));
  page.on("pageerror", (e) => logs.push(`pageerror: ${e.message}`.slice(0, 300)));
  const began = Date.now();
  let outcome;
  try {
    await page.goto(`${ORIGIN}/page.html?task=${task}&mode=${mode}&delegate=${delegate}`);
    await page.waitForFunction(() => window.__done !== null && window.__done !== undefined, null, { timeout: 300000, polling: 500 });
    outcome = await page.evaluate(() => window.__done);
  } catch (error) {
    outcome = { ok: false, error: `timeout or crash: ${error.message}` };
  }
  await new Promise((r) => setTimeout(r, 400));            // let the last requestfinished land
  await context.close();
  const rec = { task, mode, delegate, wall_s: (Date.now() - began) / 1000, ...outcome, requests, logs: logs.slice(0, 12) };
  results.push(rec);
  const r = rec.result;
  console.log(rec.ok
    ? `${task} ${mode} ${delegate}: first ${r.first_result_ms.toFixed(0)} ms, ${r.fps.toFixed(1)} fps, median ${r.median_ms.toFixed(1)}, p90 ${r.p90_ms.toFixed(1)}, found ${r.found}`
    : `${task} ${mode} ${delegate}: FAILED ${String(rec.error).slice(0, 300)}`);
  writeFileSync(OUT, JSON.stringify({ date: new Date().toISOString(), chrome: chromeVersion, mediapipe: "@mediapipe/tasks-vision 1.2.0", jobs: results }, null, 1));
}

try {
  if (process.argv.includes("--gpu")) {
    for (const mode of MODES) await job("pose_lite", mode, "GPU");
  } else {
    for (const task of TASKS) for (const mode of MODES) await job(task, mode, "CPU");
  }
} finally {
  await browser.close();
  server.close();
}
