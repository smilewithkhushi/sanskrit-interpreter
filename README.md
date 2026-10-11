# Sanskrit Interpreter

> Built by [@smilewithkhushi](https://github.com/smilewithkhushi) (Khushi) and [@delta456](https://github.com/delta456) (Swastik).

[![Tests](https://github.com/smilewithkhushi/sanskrit-interpreter/actions/workflows/tests.yml/badge.svg)](https://github.com/smilewithkhushi/sanskrit-interpreter/actions/workflows/tests.yml)
&nbsp;[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
&nbsp;[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

A small Sanskrit-inspired programming language with a terminal REPL and a browser interface. It supports **Devanagari and English keywords**, Python-style indentation, and familiar collections and functions.

**[▶ Try the live demo](https://sanskrit-interpreter-misty-night-4163.fly.dev/)**

## ✨ What we built

This is more than an interpreter — it's a full toolchain for writing and running Sanskrit code:

- 🧠 **The language & interpreter** — a safe, bilingual (Devanagari + English) language with variables, conditionals, loops, functions, and collections.
- 🖥️ **A testable browser frontend** — a live playground where you write code and **run it right in the browser**, with an example library to learn from.
- 🎨 **A VS Code syntax highlighter + language server** — syntax colors, completions, hover help, and real-time diagnostics for `.skt` files.
- 🔁 **An English → Sanskrit converter** — turn English keyword spellings into Devanagari, from the CLI or inside VS Code.
- 🎙️ **Browser dictation** — speak a draft and have it transcribed into code where speech recognition is available.
- 🚀 **Ready to deploy** — containerized with Docker and shipped live on Fly.io.

```text
नाम := "आर्य"
मुद्रय("नमस्ते", नाम)

कार्य वर्ग(x):
    प्रत्यावर्तय x * x

प्रत्येक x मध्ये परास(1, 4):
    मुद्रय(वर्ग(x))
```

## Requirements

Python 3.10 or newer. The core interpreter has no runtime dependencies.

## Quick start

From the project root:

```sh
./scripts/run.sh                     # browser interface
./scripts/run.sh examples/demo.skt   # run a source file
python3 -m sanskrit_interpreter      # terminal REPL
```

Open [http://127.0.0.1:8765/](http://127.0.0.1:8765/) for the browser interface. Use `./scripts/run.sh --web --port 9000` to choose another port.

To install the `sanskrit-interpreter` command system-wide:

```sh
python3 -m pip install .
sanskrit-interpreter examples/demo.skt
```

## Language

The language supports variables, conditionals, loops, functions, and collections. See the [language rules](docs/language.md) and [examples](examples/README.md) for full syntax and behavior. This is a limited interpreter; it does not execute arbitrary Python code.

## Other tools

- **Convert English keywords to Sanskrit:**
  ```sh
  python3 -m sanskrit_interpreter --to-sanskrit examples/english_syntax.skt
  ```
  Add `--output converted.skt` to save the result.
- **Optional local speech transcription** (browser dictation does not require it):
  ```sh
  python3 -m pip install -r requirements/speech.txt
  ```
- **Build a single-file executable** archive:
  ```sh
  python3 scripts/build.py          # produces dist/sanskrit-interpreter.pyz
  ```

## Project structure

```text
sanskrit-interpreter/
├── sanskrit_interpreter/        # the language: interpreter, converter, web + speech, browser UI
├── vscode-sanskrit-interpreter/ # VS Code extension (highlighting, LSP, conversion)
├── docs/                        # language reference
├── examples/                    # sample .skt programs and conversion pairs
├── tests/                       # unit tests
├── scripts/                     # run.sh, build.py, macOS launcher
├── requirements/                # optional extra dependencies (speech)
├── pyproject.toml               # packaging
├── Dockerfile, fly.toml         # deployment
└── README.md, LICENSE
```

## Development

```sh
python3 -m unittest discover -s tests
```

Deployment configuration lives in `Dockerfile` and `fly.toml`.

## License

Licensed under the [MIT License](LICENSE). © 2026 Khushi ([@smilewithkhushi](https://github.com/smilewithkhushi)) and Swastik ([@delta456](https://github.com/delta456)).
