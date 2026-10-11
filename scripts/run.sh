#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

if [ -x .venv/bin/python ]; then
    repl_python=.venv/bin/python
elif command -v python3 >/dev/null 2>&1; then
    repl_python=python3
else
    echo "Python 3 is needed to run the Sanskrit Interpreter." >&2
    exit 1
fi

if [ "$#" -eq 0 ]; then
    set -- --web
fi

exec "$repl_python" -m sanskrit_interpreter "$@"
