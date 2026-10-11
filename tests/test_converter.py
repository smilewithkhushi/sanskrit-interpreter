import unittest
from pathlib import Path

from sanskrit_repl import Interpreter
from sanskrit_repl.converter import ConversionError, convert_to_sanskrit


class ConverterTests(unittest.TestCase):
    def test_keywords_builtins_and_behavior(self):
        source = "func square(n):\n    return n * n\nfor n in range(1, 4):\n    print(square(n))\n"
        result = convert_to_sanskrit(source)
        self.assertEqual(result, "कार्य square(n):\n    प्रत्यावर्तय n * n\nप्रत्येक n मध्ये परास(1, 4):\n    मुद्रय(square(n))\n")
        self.assertEqual(Interpreter().execute(source), Interpreter().execute(result))

    def test_preserves_comments_strings_and_spacing(self):
        source = 'x := "print and if"  # return print\nprint( x )\n'
        self.assertEqual(convert_to_sanskrit(source), 'x := "print and if"  # return print\nमुद्रय( x )\n')

    def test_preserves_shadowed_builtin(self):
        source = "func print(value):\n    return value * 2\nprint(3)\n"
        result = convert_to_sanskrit(source)
        self.assertIn("कार्य print(value):", result)
        self.assertIn("print(3)", result)
        self.assertEqual(Interpreter().execute(source), Interpreter().execute(result))

    def test_preserves_builtin_when_sanskrit_alias_is_shadowed(self):
        source = "मुद्रय := 7\nx := print(3)\n"
        result = convert_to_sanskrit(source)
        self.assertIn("x := print(3)", result)
        self.assertEqual(Interpreter().execute(source), Interpreter().execute(result))

    def test_mixed_sanskrit_and_english(self):
        source = 'यदि true:\n    print("हैलो")\n'
        self.assertEqual(convert_to_sanskrit(source), 'यदि सत्यम्:\n    मुद्रय("हैलो")\n')

    def test_keyword_argument_name_is_preserved(self):
        source = 'print(dict(print=2))\n'
        result = convert_to_sanskrit(source)
        self.assertEqual(result, 'मुद्रय(कोश(print=2))\n')
        self.assertEqual(Interpreter().execute(source), Interpreter().execute(result))

    def test_spoken_command(self):
        source = "calculate 2 plus 3\nshow 8 divided by 2\n"
        result = convert_to_sanskrit(source)
        self.assertEqual(result, "गणय 2 जोड़ 3\nदर्शय 8 भाग 2\n")
        self.assertEqual(Interpreter().execute(source), Interpreter().execute(result))

    def test_rejects_unsupported_code(self):
        with self.assertRaisesRegex(ConversionError, "Unsupported Import at line 1"):
            convert_to_sanskrit("import os\n")
        with self.assertRaisesRegex(ConversionError, "Syntax at line 1"):
            convert_to_sanskrit("if :\n")

    def test_existing_example(self):
        source = Path("examples/english_syntax.skt").read_text(encoding="utf-8")
        converted = convert_to_sanskrit(source)
        self.assertEqual(Interpreter().execute(source), Interpreter().execute(converted))

    def test_production_example_pairs(self):
        expected = {
            "inventory_reorder": "A-100 reorder 6\nC-300 reorder 5\nReorder lines: 2\n",
            "invoice_cents": "Invoice total (cents): 4522\n",
            "service_health": "api healthy 9980 bps\nworker alert 9700 bps\nscheduler no valid sample\n",
        }
        directory = Path("examples/conversion")
        for name, output in expected.items():
            with self.subTest(name=name):
                english = (directory / f"{name}.english.skt").read_text(encoding="utf-8")
                sanskrit = (directory / f"{name}.sanskrit.skt").read_text(encoding="utf-8")
                self.assertEqual(convert_to_sanskrit(english), sanskrit)
                self.assertEqual(Interpreter().execute(english), output)
                self.assertEqual(Interpreter().execute(sanskrit), output)


if __name__ == "__main__":
    unittest.main()
