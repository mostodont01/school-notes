"""Command line entry point.

    school-notes format lesson.txt    # LLM -> lesson.json + lesson.tex + lesson.pdf
    school-notes render lesson.json   # JSON -> lesson.tex + lesson.pdf (no LLM)
    school-notes schema               # print the JSON schema the LLM must follow
"""

import argparse
import sys
from pathlib import Path

from .pipeline import build_pdf, format_file, load_document


def main() -> int:
    parser = argparse.ArgumentParser(prog="school-notes")
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("render", help="build .tex and .pdf from a .json document")
    render.add_argument("json", type=Path)
    fmt = sub.add_parser("format", help="structure a .txt with the LLM, then build .json/.tex/.pdf")
    fmt.add_argument("txt", type=Path)
    sub.add_parser("schema", help="print the document JSON schema")
    args = parser.parse_args()

    if args.command == "schema":
        import json

        from .llm import document_schema
        print(json.dumps(document_schema(), ensure_ascii=False, indent=2))
        return 0

    if args.command in ("render", "format"):
        if args.command == "render":
            result = build_pdf(load_document(args.json), args.json.with_suffix(""))
        else:
            from .llm import LLMError
            try:
                result = format_file(args.txt)
            except LLMError as e:
                print(e, file=sys.stderr)
                return 1
        if not result.ok:
            print("\n".join(result.errors), file=sys.stderr)
            return 1
        print(result.pdf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
