"""Small browser REPL with optional speech recognition."""

import json
from collections import OrderedDict
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib.resources import files
from pathlib import Path
from secrets import token_urlsafe

from .interpreter import Interpreter, SanskritError
from .speech import MAX_AUDIO_BYTES, SpeechError, SpeechUnavailable, available, model_name, transcribe_audio


def example_catalog():
    """Return the project examples, or the bundled copy in an installed package."""
    root = Path(__file__).resolve().parent.parent / "examples"
    if root.is_dir():
        examples = []
        for path in sorted(root.rglob("*.skt")):
            relative = path.relative_to(root)
            stem = path.name.removesuffix(".skt")
            variant = "English" if stem.endswith(".english") else "Sanskrit" if stem.endswith(".sanskrit") else None
            title = stem.removesuffix(".english").removesuffix(".sanskrit").replace("_", " ").title()
            source = path.read_text(encoding="utf-8")
            description = next((line.lstrip("# ").strip() for line in source.splitlines() if line.startswith("#")), "")
            examples.append({
                "id": relative.as_posix(),
                "title": title,
                "group": "Conversion pairs" if relative.parts[0] == "conversion" else "Core examples",
                "variant": variant,
                "description": description,
                "source": source,
            })
        return examples
    return json.loads(files("sanskrit_interpreter").joinpath("example_catalog.json").read_text(encoding="utf-8"))


class Handler(BaseHTTPRequestHandler):
    sessions = OrderedDict()
    max_sessions = 128

    def _same_origin(self):
        origin = self.headers.get("Origin")
        host = self.headers.get("Host")
        return not origin or (host and origin in (f"http://{host}", f"https://{host}"))

    def _session(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            pass
        morsel = cookie.get("sanskrit_session")
        session_id = morsel.value if morsel else None
        if session_id not in self.sessions:
            session_id = token_urlsafe(24)
            self.sessions[session_id] = Interpreter()
            self._new_session = session_id
            while len(self.sessions) > self.max_sessions:
                self.sessions.popitem(last=False)
        self.sessions.move_to_end(session_id)
        return session_id, self.sessions[session_id]

    def _session_header(self):
        if session_id := getattr(self, "_new_session", None):
            self.send_header("Set-Cookie", f"sanskrit_session={session_id}; HttpOnly; SameSite=Strict; Path=/")

    def _json_response(self, response, status=200):
        data = json.dumps(response, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self._session_header()
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/healthz":
            self._json_response({"ok": True})
            return
        if self.path == "/speech/status":
            self._json_response({"available": available(), "model": model_name()})
            return
        if self.path == "/examples":
            self._json_response({"examples": example_catalog()})
            return
        if self.path == "/sanskrit-interpreter.png":
            data = files("sanskrit_interpreter").joinpath("sanskrit-interpreter.png").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path != "/":
            self.send_error(404)
            return
        data = files("sanskrit_interpreter").joinpath("index.html").read_bytes()
        self._session()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self._session_header()
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path == "/transcribe":
            self._transcribe()
            return
        if self.path != "/run":
            self.send_error(404)
            return
        if not self._same_origin():
            self._json_response({"output": "", "error": "Code must come from this local page"}, 403)
            return
        session_id, engine = self._session()
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 100_000:
                self.send_error(413)
                return
            request = json.loads(self.rfile.read(length))
            if not isinstance(request, dict):
                raise SanskritError("Request must be an object")
            if request.get("reset"):
                self.sessions[session_id] = Interpreter()
                response = {"output": "State cleared.", "error": None}
            else:
                source = request.get("source")
                if not isinstance(source, str):
                    raise SanskritError("source must be text")
                if request.get("fresh"):
                    engine = Interpreter()
                    self.sessions[session_id] = engine
                try:
                    response = {"output": engine.execute(source), "error": None}
                except SanskritError as exc:
                    response = {"output": "".join(engine.output), "error": str(exc)}
        except (ValueError, UnicodeDecodeError, SanskritError) as exc:
            response = {"output": "", "error": str(exc)}
        self._json_response(response)

    def _transcribe(self):
        if not self._same_origin():
            self._json_response({"text": "", "error": "Audio must come from this local page"}, 403)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_AUDIO_BYTES:
                raise SpeechError("Audio is empty or too large")
            data = self.rfile.read(length)
            if len(data) != length:
                raise SpeechError("Audio upload was incomplete")
            text = transcribe_audio(
                data,
                self.headers.get("X-Speech-Language", "hi-IN"),
                self.headers.get("Content-Type", ""),
            )
            self._json_response({"text": text, "error": None})
        except SpeechUnavailable as error:
            self._json_response({"text": "", "error": str(error)}, 503)
        except (ValueError, SpeechError) as error:
            self._json_response({"text": "", "error": str(error)}, 400)
        except Exception as error:
            self._json_response({"text": "", "error": f"Transcription failed: {error}"}, 500)


def serve(port=8765, host="127.0.0.1"):
    server = HTTPServer((host, port), Handler)
    print(f"Serving Sanskrit Interpreter on {host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
