// S-231 speech and sounds: runs one worker job in headless Chrome (fresh context, Playwright makes a temporary profile), logs every request host.
//   node measure_web.mjs --task whisper|yamnet --models DIR --audio DIR [--threads 1] [--version 1.30.0] [--iso] [--out file.json]
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
const { chromium } = await import("file:///C:/Projects/funground-hq.github.io/tools/codemirror/node_modules/playwright-core/index.mjs");
const HERE = path.dirname(fileURLToPath(import.meta.url));
const CHROME = "C:/Users/samirj/AppData/Local/Google/Chrome/Application/chrome.exe";
const arg = (n, d = null) => (process.argv.includes(n) ? process.argv[process.argv.indexOf(n) + 1] : d);
const TASK = arg("--task", "whisper"), MODELS = arg("--models"), AUDIO = arg("--audio"), THREADS = +arg("--threads", "1"), VERSION = arg("--version", "1.30.0");
const ISO = process.argv.includes("--iso"), OUT = path.join(HERE, arg("--out", `web_${TASK}.json`));
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json", ".wav": "audio/wav" };
const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://x"), rel = decodeURIComponent(url.pathname);
  const file = rel.startsWith("/m/") ? path.join(MODELS, rel.slice(3)) : rel.startsWith("/a/") ? path.join(AUDIO, rel.slice(3)) : path.join(HERE, path.basename(rel) || "page.html");
  if (!existsSync(file)) { res.writeHead(404).end(); return; }
  const h = { "Content-Type": TYPES[path.extname(file)] ?? "application/octet-stream" };
  if (ISO) { h["Cross-Origin-Opener-Policy"] = "same-origin"; h["Cross-Origin-Embedder-Policy"] = "require-corp"; }
  res.writeHead(200, h).end(readFileSync(file));
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ["--headless=new"] });
const hostOf = (u) => { const h = new URL(u).host; return h.startsWith("127.0.0.1") ? "127.0.0.1 (ours)" : h; };
const context = await browser.newContext({ viewport: { width: 800, height: 600 } }), page = await context.newPage();
const requests = [];
context.on("requestfinished", async (r) => { try { const s = await r.sizes(); requests.push({ url: r.url(), host: hostOf(r.url()), bytes: s.responseBodySize }); } catch { /* closed */ } });
context.on("requestfailed", (r) => requests.push({ url: r.url(), host: hostOf(r.url()), failed: r.failure()?.errorText }));
const logs = []; page.on("console", (m) => logs.push(`${m.type()}: ${m.text()}`.slice(0, 300)));
let outcome;
try {
  await page.goto(`${ORIGIN}/page.html?task=${TASK}&threads=${THREADS}&version=${VERSION}`);
  await page.waitForFunction(() => window.__done != null, null, { timeout: 500000, polling: 500 });
  outcome = await page.evaluate(() => window.__done);
} catch (e) { outcome = { ok: false, error: "timeout or crash: " + e.message }; }
await new Promise((r) => setTimeout(r, 400)); await context.close();
const hosts = {}; for (const r of requests) hosts[r.host] = (hosts[r.host] ?? 0) + 1;
const rec = { date: new Date().toISOString(), chrome: browser.version(), iso: ISO, ...outcome, hosts, requests: requests.map(({ url, bytes, failed }) => ({ url: url.replace(ORIGIN, ""), bytes, failed })), logs: logs.slice(0, 8) };
writeFileSync(OUT, JSON.stringify(rec, null, 1));
const brief = (v) => v.text ?? v.top;
console.log(rec.ok ? JSON.stringify({ import_ms: rec.result.import_ms, ready_ms: rec.result.ready_ms, hosts, clips: Object.fromEntries(Object.entries(rec.result.clips).map(([k, v]) => [k, brief(v)])), perf: Object.fromEntries(Object.entries(rec.result.clips).map(([k, v]) => [k, v.rtf ?? v.ms_per_window])) }, null, 1) : "FAILED " + String(rec.error).slice(0, 800));
await browser.close(); server.close();
