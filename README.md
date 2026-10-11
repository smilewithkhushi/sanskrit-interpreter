# Sanskrit REPL

A small Sanskrit-inspired interpreter with three ways to use it: a terminal REPL, a browser text REPL, and browser speech input. It uses Devanagari keywords, Python-style indentation and collections, and Go-inspired short declarations (`:=`), `func`, `make`, `append`, `cap`, and `copy`. The runtime executes its own limited language tree; it does not run arbitrary Python code.

## Start

The core interpreter requires Python 3.10+ and no packages. Local audio transcription is optional and has a separate dependency.

For a shell command available from your Python environment, run `python3 -m pip install .` from the project root, then `sanskrit-repl examples/demo.skt` or `sanskrit-repl --web`.

For a single runnable file, use `python3 build.py`. It creates `dist/sanskrit-repl.pyz`. A Python 3 installation is still required; this is a packaged interpreter, not a native machine-code binary.

### Web interface

From the project root, start the local web server:

```sh
./script.sh
```

The script uses `.venv/bin/python` when available and falls back to `python3`. You can also start the server directly with `python3 -m sanskrit_repl --web`.

Open `http://127.0.0.1:8765/` in your browser. Type code and click **Run code**, or click **Dictate** to add speech input. Click **Reset state** to clear saved variables. Stop the server with `Ctrl+C` in the terminal.

To use a different port, run:

```sh
./script.sh --web --port 9000
```

Then open `http://127.0.0.1:9000/`.

To run the packaged version, build it once and start its web server:

```sh
python3 build.py
python3 dist/sanskrit-repl.pyz --web
```

On macOS, you can also double-click `Start Sanskrit REPL.command` after building. It starts the packaged server and opens the browser page. Do not open `sanskrit_repl/index.html` as a `file://` page; the interface needs the local server.

The source editor highlights Sanskrit and English keywords, built-ins, function names, strings, numbers, comments, and operators as you type. **Browser dictate** uses your browser's speech recognition. The transcript stays editable before execution.

To enable the optional local audio-to-text library, install `faster-whisper` and start the server with the same Python environment. On macOS, for example:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-speech.txt
.venv/bin/python -m sanskrit_repl --web
```

The macOS launcher uses `.venv/bin/python` when that environment exists. Open `http://127.0.0.1:8765/`, choose Sanskrit, Hindi, or English, then click **Record locally** and **Stop recording**, or click **Transcribe audio file**. The model defaults to multilingual `base` and downloads on first use. Set `SANSKRIT_STT_MODEL=small` before starting the server to use a larger model. Audio is processed on your computer and the temporary upload is deleted after transcription. Review the transcript in the syntax editor before running it. Speech recognition quality, especially for Sanskrit and code punctuation, varies by recording and model. [faster-whisper documents its Python installation and PyAV audio decoding](https://github.com/SYSTRAN/faster-whisper); [Whisper lists Sanskrit (`sa`) among its language codes](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py).

### Terminal and source files

```sh
python3 -m sanskrit_repl
python3 -m sanskrit_repl examples/demo.skt
./script.sh examples/demo.skt
```

See [examples/README.md](examples/README.md) for small runnable programs covering conditions, functions, collections, English aliases, and spoken-style commands.

To convert English spellings of this language into Sanskrit spellings, run `python3 -m sanskrit_repl --to-sanskrit examples/english_syntax.skt`. The converted source is printed to the terminal. Add `--output converted.skt` to save it as a new file. Strings, comments, formatting, and user-defined names are preserved. The VS Code extension also has **Sanskrit REPL: Convert English Syntax to Sanskrit**, which opens a preview beside the source.

For realistic conversion pairs, see [examples/conversion/README.md](examples/conversion/README.md).

## Syntax

```text
नाम := "आर्य"                  # short declaration / assignment
स्थापय आयु = 20               # declaration word is optional
मुद्रय("नमस्ते", नाम)

यदि आयु >= 18:
    मुद्रय("वयस्क")
अन्यथा:
    मुद्रय("बालक")

कार्य वर्ग(x):
    प्रत्यावर्तय x * x

प्रत्येक x मध्ये परास(1, 4):
    मुद्रय(वर्ग(x))

गणक := 0
यावत् गणक < 3:
    गणक += 1
```
Control words: `यदि`/`if`, `अन्ययदि`/`elif`, `अन्यथा`/`else`, `यावत्`/`while`, `प्रत्येक`/`for`, `मध्ये`/`in`, `कार्य`/`func`/`def`, `प्रत्यावर्तय`/`return`, `विराम`/`break`, `अग्रे`/`continue`, `च`/`and`, `वा`/`or`, `न`/`not`, `सत्यम्`/`true`, `असत्यम्`/`false`, `शून्यम्`/`nil`. English Python spellings also work.

Built-ins include `मुद्रय`/`print`, `लम्बाई`/`len`, `परास`/`range`, `योग`/`sum`, `न्यूनतम`/`min`, `अधिकतम`/`max`, `क्रम`/`sorted`, `उलट`/`reversed`, `सूची`/`list`, `कोश`/`dict`, `समुच्चय`/`set`, `गणना`/`enumerate`, `युग्म`/`zip`, `पूर्णांक`/`int`, `दशमलव`/`float`, `अक्षर`/`str`, `बूल`/`bool`, `निरपेक्ष`/`abs`, `सर्व`/`all`, `कोई`/`any`, `वर्गमूल`/`sqrt`, `बनाओ`/`make`, `जोड़ो`/`append`, `क्षमता`/`cap`, and `प्रतिलिपि`/`copy`.

For a spoken-style calculation, enter `गणय दो जोड़ तीन` or `calculate 2 plus 3`. `दर्शय x` and `show x` print a value. These are limited, explicit intent commands; general natural-language requests are not compiled automatically.

Lists, dictionaries, sets, tuples, indexing, slices, arithmetic, comparisons, functions, loops, and conditionals are supported. The terminal REPL keeps variables between entries; use `:reset` to clear them. Enter a blank line after an indented block. The browser REPL also keeps state until Reset.

See [language rules](docs/language.md) for assignment and function scope, collection behavior, built-in return values, and error reporting.

## Scope

This is a small interpreted language rather than a complete Sanskrit grammar or a Python/Go compiler. Voice recognition is transcription; review its text before running. Imports, object attributes, classes, file I/O, concurrency, and Python/Go modules are outside this version.

Run the test suite with `python3 -m unittest discover -s tests -v`. The project is released under the [MIT license](LICENSE).
