"""Run a terminal REPL, source file, or local browser interface."""

import argparse
import codeop
from pathlib import Path

from .interpreter import Interpreter, SanskritError, normalize
from .converter import ConversionError, convert_to_sanskrit


def repl():
    engine = Interpreter()
    print("संस्कृत Interpreter — :help for examples, :quit to leave")
    lines = []
    while True:
        try:
            line = input("... " if lines else "संस्कृत> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not lines and line in (":quit", ":exit"):
            return
        if not lines and line == ":help":
            print("Examples: x := 3; मुद्रय(x) | यदि x > 2: | कार्य वर्ग(n):")
            print("Enter an empty line after an indented block. :reset clears variables.")
            continue
        if not lines and line == ":reset":
            engine = Interpreter()
            print("State cleared.")
            continue
        lines.append(line)
        source = "\n".join(lines) + "\n"
        try:
            complete = codeop.compile_command(normalize(source), symbol="exec") is not None
        except (SyntaxError, OverflowError, ValueError, SanskritError):
            complete = True
        if not complete:
            continue
        try:
            print(engine.execute(source), end="")
        except SanskritError as exc:
            print(f"त्रुटि: {exc}")
        lines.clear()


def main():
    parser = argparse.ArgumentParser(description="Sanskrit-inspired interpreter")
    parser.add_argument("file", nargs="?", type=Path, help="run a .skt source file")
    parser.add_argument("--web", action="store_true", help="start local text and voice REPL")
    parser.add_argument("--host", default="127.0.0.1", help="web server bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--to-sanskrit", action="store_true", help="convert English language spellings to Sanskrit")
    parser.add_argument("--output", type=Path, help="write converted source to this file")
    args = parser.parse_args()
    if args.to_sanskrit:
        if args.file is None or args.web:
            parser.error("--to-sanskrit needs a source file and cannot be combined with --web")
        try:
            converted = convert_to_sanskrit(args.file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ConversionError) as exc:
            parser.exit(1, f"Conversion failed: {exc}\n")
        if args.output:
            try:
                args.output.write_text(converted, encoding="utf-8")
            except OSError as exc:
                parser.exit(1, f"Could not write output: {exc}\n")
        else:
            print(converted, end="")
    elif args.output:
        parser.error("--output requires --to-sanskrit")
    elif args.web:
        from .web import serve
        serve(args.port, args.host)
    elif args.file:
        engine = Interpreter()
        try:
            print(engine.execute(args.file.read_text(encoding="utf-8")), end="")
        except SanskritError as exc:
            parser.exit(1, f"त्रुटि: {exc}\n")
    else:
        repl()


if __name__ == "__main__":
    main()
