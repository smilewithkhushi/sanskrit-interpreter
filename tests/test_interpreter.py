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

    def test_errors_point_to_original_source(self):
        for source, expected in [
            ("यदि सत्यम्:\n    मुद्रय(गुप्त)", "Unknown name: गुप्त at line 2, column 12"),
            ("x := 3\nमुद्रय(x / 0)", "ZeroDivisionError: division by zero at line 2, column 8"),
            ("import os", "Unsupported Import at line 1, column 1"),
            ("मुद्रय(१)", "at line 1, column 8"),
        ]:
            with self.subTest(source=source), self.assertRaises(SanskritError) as error:
                Interpreter().execute(source)
            self.assertIn(expected, str(error.exception))

    def test_recursion_scope_unicode_names_and_loops(self):
        source = (
            "मूल := 3\n"
            "कार्य तथ्य(n):\n"
            "    यदि n <= 1:\n"
            "        प्रत्यावर्तय 1\n"
            "    प्रत्यावर्तय n * तथ्य(n - 1)\n"
            "कार्य छाया():\n"
            "    मूल := 9\n"
            "    प्रत्यावर्तय मूल\n"
            "योगफल := 0\n"
            "प्रत्येक संख्या मध्ये परास(5):\n"
            "    यदि संख्या == 3:\n"
            "        विराम\n"
            "    योगफल += संख्या\n"
            "अन्यथा:\n"
            "    योगफल := 99\n"
            "मुद्रय(तथ्य(5), छाया(), मूल, योगफल)\n"
        )
        self.assertEqual(Interpreter().execute(source), "120 9 3 3\n")

    def test_collection_builtins_and_partial_state_after_error(self):
        engine = Interpreter()
        self.assertEqual(engine.execute(
            'items := [1, 2]\nnew_items := जोड़ो(items, 3)\n'
            'other := बनाओ("सूची", 2)\ncount := प्रतिलिपि(other, new_items)\n'
            'मुद्रय(items, new_items, other, count, क्षमता(other))'
        ), "[1, 2] [1, 2, 3] [1, 2] 2 2\n")
        with self.assertRaises(SanskritError):
            engine.execute("saved := 42\nमुद्रय(missing)")
        self.assertEqual(engine.execute("मुद्रय(saved)"), "42\n")

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

    def test_browser_accepts_same_host_https_origin(self):
        from sanskrit_repl.web import Handler
        handler = Handler.__new__(Handler)
        body = json.dumps({"source": "मुद्रय(7)"}).encode()
        handler.path = "/run"
        handler.headers = {
            "Content-Length": str(len(body)),
            "Host": "sanskrit.example",
            "Origin": "https://sanskrit.example",
        }
        handler.rfile = io.BytesIO(body)
        handler.wfile = io.BytesIO()
        codes = []
        handler.send_response = codes.append
        handler.send_header = lambda key, value: None
        handler.end_headers = lambda: None
        handler.do_POST()
        self.assertEqual(codes, [200])
        self.assertEqual(json.loads(handler.wfile.getvalue())["output"], "7\n")

    def test_browser_sessions_are_isolated(self):
        from sanskrit_repl.web import Handler
        Handler.sessions.clear()

        def request(payload, cookie=None):
            handler = Handler.__new__(Handler)
            body = json.dumps(payload).encode()
            handler.path = "/run"
            handler.headers = {"Content-Length": str(len(body))}
            if cookie:
                handler.headers["Cookie"] = cookie
            handler.rfile = io.BytesIO(body)
            handler.wfile = io.BytesIO()
            headers = {}
            handler.send_response = lambda code: None
            handler.send_header = lambda key, value: headers.__setitem__(key, value)
            handler.end_headers = lambda: None
            handler.do_POST()
            result = json.loads(handler.wfile.getvalue())
            return result, headers.get("Set-Cookie", "").split(";", 1)[0]

        first, cookie_a = request({"source": "x := 7"})
        self.assertIsNone(first["error"])
        second, cookie_b = request({"source": "मुद्रय(x)"})
        self.assertIn("Unknown name", second["error"])
        self.assertNotEqual(cookie_a, cookie_b)
        self.assertEqual(request({"source": "मुद्रय(x)"}, cookie_a)[0]["output"], "7\n")
        request({"reset": True}, cookie_a)
        self.assertIn("Unknown name", request({"source": "मुद्रय(x)"}, cookie_a)[0]["error"])


if __name__ == "__main__":
    unittest.main()
