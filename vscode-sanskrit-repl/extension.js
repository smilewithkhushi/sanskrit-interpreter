"use strict";

const vscode = require("vscode");
const { spawn } = require("child_process");
const path = require("path");

let server;
let diagnostics;
let output;
let pending = new Map();
let nextId = 1;
let incoming = Buffer.alloc(0);

function send(message) {
  if (!server || !server.stdin.writable) throw new Error("Sanskrit language server is unavailable");
  const body = Buffer.from(JSON.stringify({ jsonrpc: "2.0", ...message }), "utf8");
  server.stdin.write(Buffer.from(`Content-Length: ${body.length}\r\n\r\n`, "ascii"));
  server.stdin.write(body);
}

function request(method, params) {
  const id = nextId++;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    try { send({ id, method, params }); }
    catch (error) { pending.delete(id); reject(error); }
  });
}

function notify(method, params) {
  try { send({ method, params }); }
  catch (error) { output.appendLine(error.message); }
}

function handle(message) {
  if (Object.prototype.hasOwnProperty.call(message, "id")) {
    const waiting = pending.get(message.id);
    if (!waiting) return;
    pending.delete(message.id);
    if (message.error) waiting.reject(new Error(message.error.message));
    else waiting.resolve(message.result);
    return;
  }
  if (message.method === "textDocument/publishDiagnostics") {
    const params = message.params;
    const uri = vscode.Uri.parse(params.uri);
    const items = params.diagnostics.map(item => {
      const start = item.range.start;
      const end = item.range.end;
      const diagnostic = new vscode.Diagnostic(
        new vscode.Range(start.line, start.character, end.line, end.character),
        item.message,
        vscode.DiagnosticSeverity.Error
      );
      diagnostic.source = item.source || "Sanskrit REPL";
      return diagnostic;
    });
    diagnostics.set(uri, items);
  }
}

function receive(chunk) {
  incoming = Buffer.concat([incoming, chunk]);
  while (true) {
    const separator = incoming.indexOf("\r\n\r\n");
    if (separator < 0) return;
    const headers = incoming.subarray(0, separator).toString("ascii");
    const match = /(?:^|\r\n)Content-Length:\s*(\d+)/i.exec(headers);
    if (!match) { incoming = incoming.subarray(separator + 4); continue; }
    const length = Number(match[1]);
    if (incoming.length < separator + 4 + length) return;
    const body = incoming.subarray(separator + 4, separator + 4 + length);
    incoming = incoming.subarray(separator + 4 + length);
    try { handle(JSON.parse(body.toString("utf8"))); }
    catch (error) { output.appendLine(`Language server response: ${error.message}`); }
  }
}

function isSanskrit(document) {
  return document.languageId === "sanskrit-repl";
}

async function activate(context) {
  diagnostics = vscode.languages.createDiagnosticCollection("sanskrit-repl");
  output = vscode.window.createOutputChannel("Sanskrit REPL");
  context.subscriptions.push(diagnostics, output);

  const python = vscode.workspace.getConfiguration("sanskritRepl").get("pythonPath", "python3");
  server = spawn(python, [path.join(__dirname, "server.py")], { stdio: ["pipe", "pipe", "pipe"] });
  server.stdout.on("data", receive);
  server.stderr.on("data", chunk => output.append(chunk.toString("utf8")));
  server.on("error", error => {
    output.appendLine(`Could not start Python: ${error.message}`);
    vscode.window.showErrorMessage("Sanskrit language server could not start. Check sanskritRepl.pythonPath.");
  });
  server.on("exit", () => {
    for (const waiting of pending.values()) waiting.reject(new Error("Language server stopped"));
    pending.clear();
    diagnostics.clear();
    server = undefined;
  });

  try {
    await request("initialize", { processId: process.pid, rootUri: null, capabilities: {} });
  } catch (error) {
    output.appendLine(`Language server initialization failed: ${error.message}`);
    return;
  }
  notify("initialized", {});
  for (const document of vscode.workspace.textDocuments) {
    if (isSanskrit(document)) notify("textDocument/didOpen", { textDocument: {
      uri: document.uri.toString(), languageId: document.languageId,
      version: document.version, text: document.getText(),
    } });
  }
  context.subscriptions.push(vscode.workspace.onDidOpenTextDocument(document => {
    if (isSanskrit(document)) notify("textDocument/didOpen", { textDocument: {
      uri: document.uri.toString(), languageId: document.languageId,
      version: document.version, text: document.getText(),
    } });
  }));
  context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(event => {
    const document = event.document;
    if (isSanskrit(document)) notify("textDocument/didChange", {
      textDocument: { uri: document.uri.toString(), version: document.version },
      contentChanges: [{ text: document.getText() }],
    });
  }));
  context.subscriptions.push(vscode.workspace.onDidCloseTextDocument(document => {
    if (isSanskrit(document)) notify("textDocument/didClose", {
      textDocument: { uri: document.uri.toString() },
    });
  }));

  const selector = { language: "sanskrit-repl" };
  context.subscriptions.push(vscode.languages.registerCompletionItemProvider(selector, {
    async provideCompletionItems(document) {
      const result = await request("textDocument/completion", {
        textDocument: { uri: document.uri.toString() },
      });
      return result.map(item => {
        const kind = item.kind === 3 ? vscode.CompletionItemKind.Function
          : vscode.CompletionItemKind.Keyword;
        const completion = new vscode.CompletionItem(item.label, kind);
        completion.detail = item.detail;
        return completion;
      });
    },
  }));
  context.subscriptions.push(vscode.languages.registerHoverProvider(selector, {
    async provideHover(document, position) {
      const result = await request("textDocument/hover", {
        textDocument: { uri: document.uri.toString() }, position,
      });
      return result ? new vscode.Hover(result.contents) : undefined;
    },
  }));
  context.subscriptions.push(vscode.commands.registerCommand("sanskritRepl.convertToSanskrit", async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor || !isSanskrit(editor.document)) {
      vscode.window.showInformationMessage("Open a Sanskrit REPL .skt or .sanskrit file first.");
      return;
    }
    try {
      const converted = await request("sanskrit/convert", { text: editor.document.getText() });
      const preview = await vscode.workspace.openTextDocument({ language: "sanskrit-repl", content: converted });
      await vscode.window.showTextDocument(preview, { preview: true, viewColumn: vscode.ViewColumn.Beside });
    } catch (error) {
      vscode.window.showErrorMessage(`Conversion failed: ${error.message}`);
    }
  }));
}

function deactivate() {
  if (server) {
    server.kill();
    server = undefined;
  }
}

module.exports = { activate, deactivate };
