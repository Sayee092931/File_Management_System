"""
CLI wrapper for the CollectionManager (argparse-based).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from .manager import CollectionManager


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collection Manager CLI")
    parser.add_argument("--dir", "-d", type=Path, default=Path.cwd() / "collection_data", help="data directory")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list files")

    p_show = sub.add_parser("show", help="show file with line numbers")
    p_show.add_argument("file", help="filename to show")

    p_create = sub.add_parser("create", help="create file")
    p_create.add_argument("file", help="filename to create")
    p_create.add_argument("--overwrite", action="store_true", help="overwrite existing")

    p_add = sub.add_parser("add-lines", help="append lines")
    p_add.add_argument("file", help="filename")
    p_add.add_argument("--text", "-t", action="append", help="line to append (can repeat)")
    p_add.add_argument("--interactive", "-i", action="store_true", help="enter lines interactively; finish with a single '.'")

    p_remove_file = sub.add_parser("remove-file", help="remove file")
    p_remove_file.add_argument("file", help="filename")
    p_remove_file.add_argument("--yes", "-y", action="store_true")

    p_remove_line = sub.add_parser("remove-line", help="remove specific line")
    p_remove_line.add_argument("file", help="filename")
    p_remove_line.add_argument("line_number", type=int, help="1-based line number to remove")

    p_find = sub.add_parser("find", help="find text")
    p_find.add_argument("text", help="text to find")
    p_find.add_argument("--case-sensitive", action="store_true")

    return parser.parse_args(argv)


def interactive_lines() -> List[str]:
    print("Enter lines. Enter a single '.' on a line to finish.")
    lines: List[str] = []
    while True:
        try:
            ln = input()
        except EOFError:
            break
        if ln == ".":
            break
        lines.append(ln)
    return lines


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    manager = CollectionManager(args.dir)

    try:
        if args.cmd == "list":
            for meta in manager.list_files():
                print(f"- {meta.filename} (size={meta.size}, tags={meta.tags})")

        elif args.cmd == "show":
            lines = manager.show_file(args.file)
            for i, ln in enumerate(lines, start=1):
                print(f"{i:4d}: {ln}")

        elif args.cmd == "create":
            manager.create_file(args.file, overwrite=args.overwrite)
            print("Created", args.file)

        elif args.cmd == "add-lines":
            to_add: List[str] = []
            if args.text:
                to_add.extend(args.text)
            if args.interactive:
                to_add.extend(interactive_lines())
            if not to_add:
                print("No lines provided")
                return 2
            manager.add_lines(args.file, to_add)
            print(f"Appended {len(to_add)} line(s) to {args.file}")

        elif args.cmd == "remove-file":
            if not args.yes:
                confirm = input(f"Delete file '{args.file}'? [y/N]: ").strip().lower()
                if confirm != "y":
                    print("Aborted.")
                    return 0
            manager.remove_file(args.file)
            print("Deleted", args.file)

        elif args.cmd == "remove-line":
            removed = manager.remove_line(args.file, args.line_number)
            print("Removed:", removed)

        elif args.cmd == "find":
            matches = manager.find_text(args.text, ignore_case=not args.case_sensitive)
            if not matches:
                print("No matches.")
                return 0
            for fname, lineno, line in matches:
                print(f"{fname}:{lineno}: {line}")

        else:
            print("Unknown command")
            return 2

    except Exception as e:
        print("Error:", e)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())