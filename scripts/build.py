"""Package the interpreter as one executable Python zip application."""

from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import zipapp


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "dist" / "sanskrit-interpreter.pyz"


def main():
    OUTPUT.parent.mkdir(exist_ok=True)
    with TemporaryDirectory() as temporary:
        staging = Path(temporary)
        shutil.copytree(ROOT / "sanskrit_interpreter", staging / "sanskrit_interpreter", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (staging / "__main__.py").write_text("from sanskrit_interpreter.__main__ import main\nmain()\n", encoding="utf-8")
        zipapp.create_archive(staging, OUTPUT, interpreter="/usr/bin/env python3", compressed=True)
    OUTPUT.chmod(0o755)
    print(OUTPUT)


if __name__ == "__main__":
    main()
