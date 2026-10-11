import unittest
import io
import json

from sanskrit_repl import Interpreter, SanskritError


class InterpreterTests(unittest.TestCase):
    def test_demo(self):
        from pathlib import Path
        source = Path("examples/demo.skt").read_text(encoding="utf-8")
        result = Interpreter().execute(source)
        self.assertIn("योग: 15", result)
        self.assertIn("[1, 4, 9]", result)

    def test_persistent_functions_and_control_flow(self):
        engine = Interpreter()
        engine.execute("कार्य वर्ग(n):\n    प्रत्यावर्तय n*n\n")
        self.assertEqual(engine.execute("मुद्रय(वर्ग(5))"), "25\n")
        self.assertEqual(engine.execute("x := 0\nयावत् x < 3:\n    x += 1\nx"), "3\n")

    def test_strings_are_not_rewritten(self):
        self.assertEqual(Interpreter().execute('मुद्रय("यदि", "true")'), "यदि true\n")

    def test_spoken_intent(self):
        self.assertEqual(Interpreter().execute("गणय दो जोड़ तीन"), "5\n")
        self.assertEqual(Interpreter().execute("calculate २ plus 3"), "5\n")

    def test_rejects_host_access(self):
        with self.assertRaises(SanskritError):
            Interpreter().execute("import os")
        with self.assertRaises(SanskritError):
            Interpreter().execute("(1).__class__")

    def test_limit(self):
        with self.assertRaisesRegex(SanskritError, "Execution limit"):
            Interpreter(max_steps=100).execute("यावत् सत्यम्:\n    pass")

    def test_browser_endpoint_without_socket(self):
        from sanskrit_repl.web import Handler
        handler = Handler.__new__(Handler)
        body = json.dumps({"source": "मुद्रय(योग([1, 2, 3]))"}).encode()
        handler.path = "/run"
        handler.headers = {"Content-Length": str(len(body))}
        handler.rfile = io.BytesIO(body)
        handler.wfile = io.BytesIO()
        handler.send_response = lambda code: None
        handler.send_header = lambda key, value: None
        handler.end_headers = lambda: None
        handler.do_POST()
        self.assertEqual(json.loads(handler.wfile.getvalue())["output"], "6\n")


if __name__ == "__main__":
    unittest.main()
