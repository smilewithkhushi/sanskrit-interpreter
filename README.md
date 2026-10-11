# Sanskrit REPL

A small Sanskrit-inspired programming language with a terminal REPL and browser interface. It supports Devanagari and English keywords, Python-style indentation, and familiar collections and functions.

[Try the live demo](https://sanskrit-interpreter-misty-night-4163.fly.dev/)

## Requirements

Python 3.10 or newer. The core interpreter has no runtime dependencies.

## Run locally

From the project root:

```sh
./script.sh                     # browser interface
./script.sh examples/demo.skt   # run a source file
python3 -m sanskrit_repl        # terminal REPL
```

Open [http://127.0.0.1:8765/](http://127.0.0.1:8765/) for the browser interface. Use `./script.sh --web --port 9000` to choose another port. The browser supports code editing and dictation where speech recognition is available.

To install the `sanskrit-repl` command, run `python3 -m pip install .`.

## Language example

```text
नाम := "आर्य"
मुद्रय("नमस्ते", नाम)

कार्य वर्ग(x):
    प्रत्यावर्तय x * x

प्रत्येक x मध्ये परास(1, 4):
    मुद्रय(वर्ग(x))
```

The language supports variables, conditionals, loops, functions, and collections. See [language rules](docs/language.md) and [examples](examples/README.md) for syntax and behavior. This is a limited interpreter; it does not execute arbitrary Python code.

## Other tools

- Convert English keyword spellings to Sanskrit: `python3 -m sanskrit_repl --to-sanskrit examples/english_syntax.skt`. Add `--output converted.skt` to save the result.
- Install the optional local speech transcription dependency with `python3 -m pip install -r requirements-speech.txt`. Browser dictation does not require it.
- Build a single-file Python archive with `python3 build.py`; the result is `dist/sanskrit-repl.pyz`.

Deployment configuration is provided in `Dockerfile` and `fly.toml`. Run tests with `python3 -m unittest discover -s tests`. Licensed under [MIT](LICENSE).
