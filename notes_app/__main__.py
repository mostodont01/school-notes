"""Command line entry point.

    school-notes render lesson.json   # JSON -> lesson.tex + lesson.pdf (no LLM)
"""

import argparse
import sys
from pathlib import Path

from .pipeline import build_pdf, load_document


def main() -> int:
    parser = argparse.ArgumentParser(prog="school-notes")
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("render", help="build .tex and .pdf from a .json document")
    render.add_argument("json", type=Path)
    args = parser.parse_args()

    if args.command == "render":
        result = build_pdf(load_document(args.json), args.json.with_suffix(""))
        if not result.ok:
            print("\n".join(result.errors), file=sys.stderr)
            return 1
        print(result.pdf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
