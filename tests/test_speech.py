import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from sanskrit_repl import speech
from sanskrit_repl.web import Handler


class SpeechTests(unittest.TestCase):
    def _handler(self, path, body=b"", headers=None):
        handler = Handler.__new__(Handler)
        handler.path = path
        handler.headers = headers or {}
        handler.rfile = io.BytesIO(body)
        handler.wfile = io.BytesIO()
        codes = []
        handler.send_response = codes.append
        handler.send_header = lambda key, value: None
        handler.end_headers = lambda: None
        return handler, codes

    def test_transcription_uses_local_model_and_removes_upload(self):
        paths = []

        class Model:
            def transcribe(self, path, **options):
                paths.append(Path(path))
                self_options = options
                self.assert_options = self_options
                return iter([type("Segment", (), {"text": " मुद्रय दो "})()]), None

        model = Model()
        with patch("sanskrit_repl.speech._model", return_value=model):
            text = speech.transcribe_audio(b"audio bytes", "hi-IN", "audio/webm;codecs=opus")
        self.assertEqual(text, "मुद्रय दो")
        self.assertEqual(model.assert_options["language"], "hi")
        self.assertFalse(paths[0].exists())

    def test_rejects_invalid_audio_input(self):
        with self.assertRaisesRegex(speech.SpeechError, "Choose"):
            speech.transcribe_audio(b"sound", "xx", "audio/webm")
        with self.assertRaisesRegex(speech.SpeechError, "empty"):
            speech.transcribe_audio(b"", "hi-IN", "audio/webm")
        with self.assertRaisesRegex(speech.SpeechError, "Unsupported"):
            speech.transcribe_audio(b"sound", "hi-IN", "text/plain")

    def test_http_transcription_endpoint(self):
        handler, codes = self._handler("/transcribe", b"audio", {
            "Content-Length": "5", "Content-Type": "audio/webm",
            "X-Speech-Language": "sa-IN", "Host": "127.0.0.1:8765",
            "Origin": "http://127.0.0.1:8765",
        })
        with patch("sanskrit_repl.web.transcribe_audio", return_value="मुद्रय(2)") as transcribe:
            handler.do_POST()
        self.assertEqual(codes, [200])
        transcribe.assert_called_once_with(b"audio", "sa-IN", "audio/webm")
        self.assertEqual(json.loads(handler.wfile.getvalue())["text"], "मुद्रय(2)")

    def test_status_and_cross_origin_rejection(self):
        handler, codes = self._handler("/speech/status")
        with patch("sanskrit_repl.web.available", return_value=False):
            handler.do_GET()
        self.assertEqual(codes, [200])
        self.assertFalse(json.loads(handler.wfile.getvalue())["available"])

        handler, codes = self._handler("/healthz")
        handler.do_GET()
        self.assertEqual(codes, [200])
        self.assertEqual(json.loads(handler.wfile.getvalue()), {"ok": True})

        handler, codes = self._handler("/transcribe", b"audio", {
            "Content-Length": "5", "Content-Type": "audio/webm",
            "Host": "127.0.0.1:8765", "Origin": "https://example.com",
        })
        with patch("sanskrit_repl.web.transcribe_audio") as transcribe:
            handler.do_POST()
        self.assertEqual(codes, [403])
        transcribe.assert_not_called()


if __name__ == "__main__":
    unittest.main()
