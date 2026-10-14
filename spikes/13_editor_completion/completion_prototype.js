// S-197 prototype (route B). Not part of the extension repo. Call registerFunground(context) from activate().
// Data: completions.json from funground (bundled at media/completions.json in the .vsix, read like hasBundledRuntime reads
// manifest.json: vscode.workspace.fs.readFile(Uri.joinPath(context.extensionUri, "media", "completions.json"))).
const vscode = require("vscode");

async function loadData(context) {
  const bytes = await vscode.workspace.fs.readFile(vscode.Uri.joinPath(context.extensionUri, "media", "completions.json"));
  return JSON.parse(new TextDecoder().decode(bytes));
}

const DOCS = "https://funground-hq.github.io/";    // `url` is "reference/API.md#fn-circle"; MkDocs serves it as reference/API/#fn-circle
const KIND = { function: "Function", class: "Class", value: "Variable", constant: "Constant" };

function registerFunground(context, data) {
  const byName = new Map(data.names.map((n) => [n.name, n]));
  const colorParams = new Map();                                   // "fill" -> Set("color")
  for (const { function: fn, parameter } of data.color_params) {
    if (!colorParams.has(fn)) colorParams.set(fn, new Set());
    colorParams.get(fn).add(parameter);
  }
  const doc = (n) => {
    const md = new vscode.MarkdownString(`${n.summary}\n\n[Reference](${DOCS}${n.url})`);
    md.isTrusted = false;
    return md;
  };

  // The alias used for funground in this file: `import funground as f` -> "f". "from funground import *" -> no alias needed.
  const aliasOf = (text) => /^\s*import\s+funground\s+as\s+(\w+)/m.exec(text)?.[1] ?? (/^\s*import\s+funground\b/m.test(text) ? "funground" : null);
  const starImport = (text) => /^\s*from\s+funground\s+import\s+\*/m.test(text);

  // 1. After `f.` : every public name, detail = signature, documentation = summary + link.
  const dotProvider = vscode.languages.registerCompletionItemProvider("python", {
    provideCompletionItems(document, position) {
      const alias = aliasOf(document.getText());
      const before = document.lineAt(position).text.slice(0, position.character);
      if (!alias || !new RegExp(String.raw`(?:^|[^\w.])${alias}\.\w*$`).test(before)) return undefined;
      return data.names.map((n) => {
        const item = new vscode.CompletionItem(n.name, vscode.CompletionItemKind[KIND[n.kind] ?? "Function"]);
        item.detail = n.signature;
        item.documentation = doc(n);
        if (n.kind === "function") item.insertText = new vscode.SnippetString(`${n.name}($0)`);
        return item;
      });
    },
  }, ".");

  // 2. Inside quotes of a colour parameter -> colour names; of an option parameter -> its words.
  const quoteProvider = vscode.languages.registerCompletionItemProvider("python", {
    provideCompletionItems(document, position) {
      const before = document.lineAt(position).text.slice(0, position.character);
      const m = /(?:\b\w+\.)?(\w+)\(([^()]*?)(["'])(\w*)$/.exec(before);   // fn( ... "partial
      if (!m) return undefined;
      const [, fn, args] = m;
      const argIndex = args.split(",").length - 1;
      const entry = byName.get(fn);
      const sig = entry?.detail ?? "";
      const params = sig.replace(/^\(|\).*$/g, "").split(",").map((p) => p.trim().split(/[:=]/)[0].replace("*", "").trim());
      const param = params[argIndex];
      const items = [];
      if (colorParams.get(fn)?.has(param)) {
        for (const c of data.colors) {
          const item = new vscode.CompletionItem(c.name, vscode.CompletionItemKind.Color);
          item.detail = c.hex;
          items.push(item);
        }
      }
      for (const o of entry?.options?.[param] ?? []) {
        const item = new vscode.CompletionItem(o.word, vscode.CompletionItemKind.EnumMember);
        item.documentation = o.meaning;
        items.push(item);
      }
      return items.length ? items : undefined;
    },
  }, '"', "'");

  // 3. Hover on `f.circle` or a bare `circle` (when `from funground import *` is present).
  const hover = vscode.languages.registerHoverProvider("python", {
    provideHover(document, position) {
      const range = document.getWordRangeAtPosition(position);
      if (!range) return undefined;
      const word = document.getText(range);
      const text = document.getText();
      const alias = aliasOf(text);
      const line = document.lineAt(position).text;
      const qualified = alias && line.slice(0, range.start.character).endsWith(`${alias}.`);
      const n = byName.get(word);
      if (!n || !(qualified || starImport(text))) return undefined;
      const md = new vscode.MarkdownString().appendCodeblock(`${n.signature}`, "python").appendMarkdown(`\n${n.summary}`);
      return new vscode.Hover(md, range);
    },
  });

  // 4. Signature help while typing arguments.
  const signature = vscode.languages.registerSignatureHelpProvider("python", {
    provideSignatureHelp(document, position) {
      const before = document.lineAt(position).text.slice(0, position.character);
      const m = /(?:\b\w+\.)?(\w+)\(([^()]*)$/.exec(before);
      const n = m && byName.get(m[1]);
      if (!n) return undefined;
      const help = new vscode.SignatureHelp();
      const info = new vscode.SignatureInformation(n.signature, n.summary);
      info.parameters = n.signature.replace(/^[^(]*\(|\)$/g, "").split(",").filter(Boolean).map((p) => new vscode.ParameterInformation(p.trim()));
      help.signatures = [info];
      help.activeParameter = Math.min(m[2].split(",").length - 1, Math.max(0, info.parameters.length - 1));
      return help;
    },
  }, "(", ",");

  context.subscriptions.push(dotProvider, quoteProvider, hover, signature);
}

module.exports = { loadData, registerFunground };
