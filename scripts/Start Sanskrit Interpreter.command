#!/bin/sh
cd "$(dirname "$0")/.." || exit 1
if [ -x .venv/bin/python ]; then
    repl_python=.venv/bin/python
elif command -v python3 >/dev/null 2>&1; then
    repl_python=python3
else
    echo "Python 3 is needed to run the Sanskrit Interpreter."
    echo "Press Enter to close."
    read _
    exit 1
fi
(sleep 1; open http://127.0.0.1:8765/) >/dev/null 2>&1 &
exec "$repl_python" dist/sanskrit-interpreter.pyz --web
