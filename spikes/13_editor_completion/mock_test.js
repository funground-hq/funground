// Runs completion_prototype.js against a tiny fake of the vscode API (NOT a real editor).
const Module = require("module"); const fs = require("fs");
const reg = [];
const vscode = {
  Uri: { joinPath: (...a) => a.join("/") },
  workspace: { fs: { readFile: async () => fs.readFileSync(process.argv[2]) } },
  CompletionItem: class { constructor(l, k) { this.label = l; this.kind = k; } },
  CompletionItemKind: new Proxy({}, { get: (_, k) => k }),
  SnippetString: class { constructor(v) { this.value = v; } },
  MarkdownString: class { constructor(v = "") { this.value = v; } appendCodeblock(c) { this.value += c; return this; } appendMarkdown(c) { this.value += c; return this; } },
  Hover: class { constructor(c) { this.contents = c; } },
  SignatureHelp: class {}, SignatureInformation: class { constructor(l) { this.label = l; } }, ParameterInformation: class { constructor(l) { this.label = l; } },
  languages: new Proxy({}, { get: (_, k) => (lang, prov, ...trig) => (reg.push({ k, prov, trig }), { dispose() {} }) }),
};
const orig = Module._load; Module._load = (r, ...x) => r === "vscode" ? vscode : orig(r, ...x);
const { loadData, registerFunground } = require("./completion_prototype.js");
const doc = (line) => ({ getText: (r) => r ? "circle" : "import funground as f\n" + line, lineAt: () => ({ text: line }), getWordRangeAtPosition: () => ({ start: { character: line.indexOf("circle") } }) });
(async () => {
  const data = await loadData({ extensionUri: "x" }); registerFunground({ subscriptions: [] }, data);
  console.log("providers:", reg.map((r) => r.k + " " + JSON.stringify(r.trig)).join("; "));
  const [dot, quote, hover, sig] = reg.map((r) => r.prov);
  const pos = (l) => ({ character: l.length });
  let l = "f."; let items = dot.provideCompletionItems(doc(l), pos(l));
  const c = items.find((i) => i.label === "circle"); console.log("f. ->", items.length, "items; circle:", c.detail, "|", c.documentation.value);
  l = 'f.fill("re'; items = quote.provideCompletionItems(doc(l), pos(l)); console.log('f.fill("re ->', items.length, "colours, first", items[0].label, items[0].detail);
  l = 'f.blend_mode("'; items = quote.provideCompletionItems(doc(l), pos(l)); console.log('f.blend_mode(" ->', items.slice(0, 4).map((i) => i.label).join(","));
  l = "f.circle(10, "; const s = sig.provideSignatureHelp(doc(l), pos(l)); console.log("sig:", s.signatures[0].label, "active", s.activeParameter);
  l = "f.circle(1,2,3)"; const h = hover.provideHover(doc(l), { character: 3 }); console.log("hover:", h.contents.value.replace(/\n/g, " / "));
})();
