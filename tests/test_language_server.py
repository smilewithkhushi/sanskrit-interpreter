"""Exercise the stdio protocol used by the VS Code extension."""

import json
from pathlib import Path
import subprocess
import sys
import unittest


SERVER = Path(__file__).resolve().parents[1] / "vscode-sanskrit-repl" / "server.py"


class LanguageServerTests(unittest.TestCase):
    def test_language_features(self):
        process = subprocess.Popen(
            [sys.executable, str(SERVER)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=SERVER.parents[1],
        )

        def send(message):
            body = json.dumps(message, ensure_ascii=False).encode("utf-8")
            process.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
            process.stdin.flush()

        def receive():
            headers = {}
            while line := process.stdout.readline():
                if line == b"\r\n":
                    break
                name, value = line.decode().split(":", 1)
                headers[name.lower()] = value.strip()
            return json.loads(process.stdout.read(int(headers["content-length"])))

        try:
            send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
            capabilities = receive()["result"]["capabilities"]
            self.assertTrue(capabilities["hoverProvider"])
            self.assertEqual(capabilities["textDocumentSync"], 1)

            uri = "file:///demo.skt"
            text = "कार्य वर्ग(n):\n    प्रत्यावर्तय n * n\nमुद्रय(वर्ग(2))"
            send({"jsonrpc": "2.0", "method": "textDocument/didOpen", "params": {
                "textDocument": {"uri": uri, "version": 1, "text": text},
            }})
            self.assertEqual(receive()["params"]["diagnostics"], [])

            send({"jsonrpc": "2.0", "id": 2, "method": "textDocument/completion", "params": {
                "textDocument": {"uri": uri}, "position": {"line": 2, "character": 0},
            }})
            labels = {item["label"] for item in receive()["result"]}
            self.assertTrue({"यदि", "मुद्रय", "वर्ग"} <= labels)

            send({"jsonrpc": "2.0", "id": 3, "method": "textDocument/hover", "params": {
                "textDocument": {"uri": uri}, "position": {"line": 1, "character": 7},
            }})
            self.assertIn("return", receive()["result"]["contents"])

            send({"jsonrpc": "2.0", "id": 4, "method": "sanskrit/convert", "params": {
                "text": "func square(n):\n    return n * n\n",
            }})
            self.assertEqual(receive()["result"], "कार्य square(n):\n    प्रत्यावर्तय n * n\n")

            send({"jsonrpc": "2.0", "method": "textDocument/didChange", "params": {
                "textDocument": {"uri": uri, "version": 2},
                "contentChanges": [{"text": "यदि सत्यम्:\n"}],
            }})
            diagnostics = receive()["params"]["diagnostics"]
            self.assertEqual(len(diagnostics), 1)
            self.assertEqual(diagnostics[0]["range"]["start"]["line"], 0)

            send({"jsonrpc": "2.0", "method": "textDocument/didChange", "params": {
                "textDocument": {"uri": uri, "version": 3},
                "contentChanges": [{"text": "मुद्रय(2)\nimport os\n"}],
            }})
            diagnostics = receive()["params"]["diagnostics"]
            self.assertEqual(len(diagnostics), 1)
            self.assertIn("Unsupported Import", diagnostics[0]["message"])
            self.assertEqual(diagnostics[0]["range"]["start"], {"line": 1, "character": 0})

            send({"jsonrpc": "2.0", "method": "textDocument/didClose", "params": {
                "textDocument": {"uri": uri},
            }})
            self.assertEqual(receive()["params"]["diagnostics"], [])
        finally:
            process.stdin.close()
            process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()


if __name__ == "__main__":
    unittest.main()
