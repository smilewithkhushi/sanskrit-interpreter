"""Small, dependency-free Language Server Protocol server for Sanskrit REPL."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import sys
import unicodedata

if not (Path(__file__).resolve().parent / "sanskrit_repl").is_dir():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sanskrit_repl.interpreter import Interpreter, KEYWORDS, normalize
from sanskrit_repl.converter import ConversionError, convert_to_sanskrit


BUILTINS = set(Interpreter()._builtins)
EXTRA_KEYWORDS = {
    "स्थापय": "Declare a variable (optional).",
    "let": "Declare a variable (optional).",
    "def": "Define a function.",
    "if": "Run a block when its condition is true.",
    "elif": "Test another condition.",
    "else": "Run the fallback block.",
    "while": "Repeat while a condition is true.",
    "for": "Iterate over a collection.",
    "in": "Test membership or iterate over a collection.",
    "return": "Return from a function.",
    "break": "Leave a loop.",
    "continue": "Continue with the next loop iteration.",
    "pass": "An empty statement.",
    "and": "Logical and.",
    "or": "Logical or.",
    "not": "Logical not.",
    "True": "Boolean true.",
    "False": "Boolean false.",
    "None": "The empty value.",
}
COMMANDS = {
    "गणय": "Calculate and print an expression.",
    "दर्शय": "Print an expression.",
    "calculate": "Calculate and print an expression.",
    "show": "Print an expression.",
}


def documentation(word: str) -> str | None:
    if word in COMMANDS:
        return COMMANDS[word]
    if word in KEYWORDS:
        return f"`{word}` is the Sanskrit spelling of `{KEYWORDS[word]}`."
    if word in EXTRA_KEYWORDS:
        return EXTRA_KEYWORDS[word]
    if word in BUILTINS:
        return f"`{word}` is a built-in function."
    return None


def utf16_length(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def character_index(value: str, utf16_column: int) -> int:
    count = 0
    for index, char in enumerate(value):
        if count >= utf16_column:
            return index
        count += utf16_length(char)
    return len(value)


def identifier_char(char: str) -> bool:
    return char == "_" or bool(char and unicodedata.category(char)[0] in "LMN")


def word_at(source: str, position: dict) -> str:
    lines = source.splitlines()
    line_number = position.get("line", 0)
    if not isinstance(line_number, int) or not 0 <= line_number < len(lines):
        return ""
    line = lines[line_number]
    column = character_index(line, max(0, position.get("character", 0)))
    if column == len(line) or not identifier_char(line[column]):
        column -= 1
    if column < 0 or not identifier_char(line[column]):
        return ""
    start = column
    end = column + 1
    while start > 0 and identifier_char(line[start - 1]):
        start -= 1
    while end < len(line) and identifier_char(line[end]):
        end += 1
    return line[start:end]


def diagnostics(source: str) -> list[dict]:
    try:
        ast.parse(normalize(source), mode="exec")
        return []
    except SyntaxError as error:
        lines = [line.rstrip("\r") for line in source.split("\n")]
        line_number = min(max((error.lineno or 1) - 1, 0), len(lines) - 1)
        line = lines[line_number]
        start = utf16_length(line) - utf16_length(line.lstrip())
        end = max(start + 1, utf16_length(line))
        return [{
            "range": {
                "start": {"line": line_number, "character": start},
                "end": {"line": line_number, "character": end},
            },
            "severity": 1,
            "source": "Sanskrit REPL",
            "message": error.msg,
        }]


def completions(source: str) -> list[dict]:
    items = []
    words = {**EXTRA_KEYWORDS, **{word: documentation(word) for word in KEYWORDS}}
    words.update(COMMANDS)
    for word in sorted(words):
        items.append({"label": word, "kind": 14, "detail": words[word]})
    for word in sorted(BUILTINS):
        items.append({"label": word, "kind": 3, "detail": "Built-in function"})
    # Names declared in this document are useful even while its syntax is incomplete.
    for word in sorted(set(re.findall(r"(?:^|\n)\s*(?:कार्य|func|def)\s+([^\W\d][\w\u0900-\u097f]*)", source))):
        if word not in words and word not in BUILTINS:
            items.append({"label": word, "kind": 3, "detail": "Function in this file"})
    return items


def read_message() -> dict | None:
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        name, _, value = line.decode("ascii", "replace").partition(":")
        headers[name.lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0 or length > 10_000_000:
        return None
    payload = sys.stdin.buffer.read(length)
    if len(payload) != length:
        return None
    return json.loads(payload)


def send(message: dict) -> None:
    payload = json.dumps(message, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii") + payload)
    sys.stdout.buffer.flush()


def main() -> None:
    documents: dict[str, str] = {}
    while (message := read_message()) is not None:
        method = message.get("method")
        params = message.get("params") or {}
        request_id = message.get("id")
        if method == "initialize":
            send({"jsonrpc": "2.0", "id": request_id, "result": {
                "capabilities": {
                    "textDocumentSync": 1,
                    "completionProvider": {},
                    "hoverProvider": True,
                },
                "serverInfo": {"name": "Sanskrit REPL", "version": "0.3.0"},
            }})
        elif method == "shutdown":
            send({"jsonrpc": "2.0", "id": request_id, "result": None})
        elif method == "exit":
            return
        elif method == "textDocument/didOpen":
            document = params["textDocument"]
            uri = document["uri"]
            documents[uri] = document["text"]
            send({"jsonrpc": "2.0", "method": "textDocument/publishDiagnostics", "params": {
                "uri": uri, "version": document.get("version"), "diagnostics": diagnostics(document["text"]),
            }})
        elif method == "textDocument/didChange":
            uri = params["textDocument"]["uri"]
            changes = params.get("contentChanges", [])
            if changes:
                documents[uri] = changes[-1]["text"]
                send({"jsonrpc": "2.0", "method": "textDocument/publishDiagnostics", "params": {
                    "uri": uri, "version": params["textDocument"].get("version"),
                    "diagnostics": diagnostics(documents[uri]),
                }})
        elif method == "textDocument/didClose":
            uri = params["textDocument"]["uri"]
            documents.pop(uri, None)
            send({"jsonrpc": "2.0", "method": "textDocument/publishDiagnostics", "params": {
                "uri": uri, "diagnostics": [],
            }})
        elif method == "textDocument/completion":
            uri = params["textDocument"]["uri"]
            send({"jsonrpc": "2.0", "id": request_id, "result": completions(documents.get(uri, ""))})
        elif method == "textDocument/hover":
            uri = params["textDocument"]["uri"]
            word = word_at(documents.get(uri, ""), params["position"])
            help_text = documentation(word)
            result = {"contents": help_text} if help_text else None
            send({"jsonrpc": "2.0", "id": request_id, "result": result})
        elif method == "sanskrit/convert":
            try:
                converted = convert_to_sanskrit(params["text"])
                send({"jsonrpc": "2.0", "id": request_id, "result": converted})
            except (KeyError, TypeError, ConversionError) as error:
                send({"jsonrpc": "2.0", "id": request_id, "error": {
                    "code": -32602, "message": str(error),
                }})
        elif request_id is not None:
            send({"jsonrpc": "2.0", "id": request_id, "error": {
                "code": -32601, "message": f"Method not found: {method}",
            }})


if __name__ == "__main__":
    main()
