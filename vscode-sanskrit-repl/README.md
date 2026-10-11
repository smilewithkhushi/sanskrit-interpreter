# Sanskrit REPL for VS Code

Syntax highlighting for the project's `.skt` and `.sanskrit` files. It colors Devanagari and English keywords, function declarations, built-ins, numbers, strings, comments, and Go-style `:=` assignments. It also configures `#` comment toggling, bracket pairs, and indentation after `:`.

The bundled Python language server adds syntax and unsupported-construct diagnostics, keyword and built-in completions, completion for functions declared in the current file, and hover help. It parses source without executing it. Python 3.10+ must be available as `python3`, or set `sanskritRepl.pythonPath` to your Python executable.

Use **Sanskrit REPL: Convert English Syntax to Sanskrit** from the Command Palette while a `.skt` or `.sanskrit` file is open. The converted code opens beside the source as an unsaved preview. Strings, comments, spacing, and user-defined names are preserved. Unsupported syntax produces a message instead of a partial conversion.

Code Spell Checker is disabled for this language so Sanskrit identifiers do not get "Unknown word" squiggles. Spell checking in other languages remains enabled.

Run a program with `python3 -m sanskrit_repl examples/demo.skt` from the project root. The language server only analyzes code while you edit.

To build an installable extension file, run `python3 build_vsix.py` in this directory. Then use VS Code's **Extensions: Install from VSIX...** command or `code --install-extension sanskrit-repl-syntax-0.3.0.vsix`.
