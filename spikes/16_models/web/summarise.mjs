// Prints the tables for results.md from results.json (and gpu.json if present): node summarise.mjs
import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const load = (name) => (existsSync(path.join(HERE, name)) ? JSON.parse(readFileSync(path.join(HERE, name), "utf8")) : { jobs: [] });
const cpu = load("results.json");
const gpu = load("gpu.json");
const mb = (n) => (n / 1e6).toFixed(2);

console.log("chrome", cpu.chrome, "date", cpu.date);
console.log("| task | mode | model MB (wire) | wasm MB (wire) | first result ms | fps | median ms | p90 ms | found |");
console.log("|---|---|---|---|---|---|---|---|---|");
for (const j of [...cpu.jobs, ...gpu.jobs]) {
  if (!j.ok) { console.log(`| ${j.task} | ${j.mode} ${j.delegate} | | | | | | | FAILED: ${String(j.error).split("\n")[0].slice(0, 120)} |`); continue; }
  const r = j.result;
  const model = j.requests.filter((q) => /mediapipe-models/.test(q.url)).reduce((a, q) => a + (q.bytes ?? 0), 0);
  const wasm = j.requests.filter((q) => /\.wasm$/.test(q.url)).reduce((a, q) => a + (q.bytes ?? 0), 0);
  console.log(`| ${j.task} | ${j.mode} ${j.delegate} | ${mb(model)} | ${mb(wasm)} | ${r.first_result_ms.toFixed(0)} | ${r.fps.toFixed(1)} | ${r.median_ms.toFixed(1)} | ${r.p90_ms.toFixed(1)} | ${r.found} |`);
}
const hosts = {};
for (const j of [...cpu.jobs, ...gpu.jobs]) for (const q of j.requests) hosts[q.host] = (hosts[q.host] ?? new Set()).add(new URL(q.url).pathname.split("/").slice(0, 3).join("/"));
console.log("\nhosts:");
for (const [h, p] of Object.entries(hosts)) console.log(h, [...p].slice(0, 8).join(" "));
