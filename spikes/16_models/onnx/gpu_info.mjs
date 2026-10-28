// Prints the WebGPU adapter headless Chrome gives (a software adapter would explain slow WebGPU numbers).
const { chromium } = await import("file:///C:/Projects/funground-hq.github.io/tools/codemirror/node_modules/playwright-core/index.mjs");
const b = await chromium.launch({ executablePath: "C:/Users/samirj/AppData/Local/Google/Chrome/Application/chrome.exe", headless: true, args: ["--headless=new"] });
const p = await b.newPage(); await p.goto("about:blank");
console.log(await p.evaluate(async () => { const a = await navigator.gpu?.requestAdapter(); if (!a) return "no adapter"; const i = a.info; return { vendor: i.vendor, architecture: i.architecture, device: i.device, description: i.description, isFallback: a.isFallbackAdapter }; }));
await b.close();
