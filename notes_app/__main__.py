"""Command line entry point.

    school-notes format lesson.txt    # LLM -> lesson.json + lesson.tex + lesson.pdf
    school-notes render lesson.json   # JSON -> lesson.tex + lesson.pdf (no LLM)
    school-notes schema               # print the JSON schema the LLM must follow
    school-notes install-desktop      # add the app to the app menu (--uninstall removes it)
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
    desktop = sub.add_parser("install-desktop", help="add School Notes to the app menu")
    desktop.add_argument("--uninstall", action="store_true", help="remove it again")
    args = parser.parse_args()

    if args.command == "install-desktop":
        from . import desktop as d
        if args.uninstall:
            d.uninstall()
            print("Removed School Notes from the app menu.")
        else:
            print(f"Added School Notes to the app menu ({d.install()}).")
        return 0

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
        if args.command == "format":
            from .llm.usage import current_usage, describe
            usage = current_usage()
            if usage:
                print(describe(usage))
    return 0


if __name__ == "__main__":
    sys.exit(main())
