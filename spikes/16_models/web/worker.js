// Module worker: runs the same benchmark as the page, off the main thread.
import { bench } from "./bench.js";

self.onmessage = async (event) => {
  try {
    const result = await bench(event.data);
    result.worker_resources = performance.getEntriesByType("resource").map((e) => ({ url: e.name, transfer: e.transferSize, encoded: e.encodedBodySize }));
    self.postMessage({ ok: true, result });
  } catch (error) {
    self.postMessage({ ok: false, error: String(error?.stack ?? error) });
  }
};
