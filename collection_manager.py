#!/usr/bin/env python3
"""
collection_manager.py

A CLI tool to manage up to 100 text files in a collection directory.

Features:
- list: show all file names in the collection
- show: display a file with numbered lines
- create: add a new (empty) file
- add-lines: append one or more lines to a file (interactive or via argument)
- remove-file: delete a file from the collection
- remove-line: remove a specific line (by 1-based index) from a file
- find: search for a text across all files and report file + line numbers

Usage examples:
  python collection_manager.py list
  python collection_manager.py create notes.txt
  python collection_manager.py add-lines notes.txt --text "First line" --text "Second line"
  python collection_manager.py add-lines notes.txt --interactive
  python collection_manager.py show notes.txt
  python collection_manager.py find "error occurred"
  python collection_manager.py remove-line notes.txt 3
  python collection_manager.py remove-file notes.txt

Author: Copilot-style example for professional project
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

# Configuration
DEFAULT_DATA_DIR = Path.cwd() / "collection_data"
MAX_FILES = 100
FILENAME_RE = re.compile(r"^[\w\-. ]+$")  # allow letters, numbers, underscore, dash, dot, space

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("collection_manager")


# Utility functions
def ensure_data_dir(path: Path = DEFAULT_DATA_DIR) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_filename(name: str) -> str:
    """
    Validate and normalize filename to avoid path traversal.
    Only allow basename matching FILENAME_RE.
    """
    base = os.path.basename(name)
    if not base:
        raise ValueError("Invalid filename")
    if not FILENAME_RE.match(base):
        raise ValueError(
            "Filename contains invalid characters. Allowed: letters, numbers, underscore, dash, dot, space."
        )
    return base


def collection_files(data_dir: Path = DEFAULT_DATA_DIR) -> List[Path]:
    ensure_data_dir(data_dir)
    files = sorted([p for p in data_dir.iterdir() if p.is_file()])
    return files


def count_files(data_dir: Path = DEFAULT_DATA_DIR) -> int:
    return len(collection_files(data_dir))


def file_path_for(name: str, data_dir: Path = DEFAULT_DATA_DIR) -> Path:
    sanitized = sanitize_filename(name)
    return ensure_data_dir(data_dir) / sanitized


# Core operations
def list_files(data_dir: Path = DEFAULT_DATA_DIR) -> None:
    files = collection_files(data_dir)
    if not files:
        print("No files in the collection.")
        return
    print(f"Files in collection ({len(files)}/{MAX_FILES}):")
    for p in files:
        try:
            size = p.stat().st_size
        except Exception:
            size = 0
        print(f"- {p.name} (size: {size} bytes)")


def show_file(name: str, data_dir: Path = DEFAULT_DATA_DIR) -> None:
    p = file_path_for(name, data_dir)
    if not p.exists():
        logger.error("File '%s' not found in collection.", p.name)
        return
    with p.open("r", encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, start=1):
            print(f"{i:4d}: {line.rstrip()}")


def create_file(name: str, data_dir: Path = DEFAULT_DATA_DIR, overwrite: bool = False) -> None:
    files_count = count_files(data_dir)
    if files_count >= MAX_FILES:
        logger.error("Cannot create file: collection already has maximum (%d) files.", MAX_FILES)
        return
    p = file_path_for(name, data_dir)
    if p.exists() and not overwrite:
        logger.error("File '%s' already exists. Use --overwrite to replace.", p.name)
        return
    # Create empty file
    p.write_text("", encoding="utf-8")
    logger.info("Created file '%s'.", p.name)


def add_lines(name: str, lines: Iterable[str], data_dir: Path = DEFAULT_DATA_DIR) -> None:
    p = file_path_for(name, data_dir)
    if not p.exists():
        logger.error("File '%s' does not exist. Create it first.", p.name)
        return
    # Append lines (ensure each ends with newline)
    with p.open("a", encoding="utf-8") as fh:
        for line in lines:
            fh.write(line.rstrip("\n") + "\n")
    logger.info("Appended %d line(s) to '%s'.", sum(1 for _ in lines), p.name)


def remove_file(name: str, data_dir: Path = DEFAULT_DATA_DIR, confirm: bool = True) -> None:
    p = file_path_for(name, data_dir)
    if not p.exists():
        logger.error("File '%s' not found.", p.name)
        return
    if confirm:
        ans = input(f"Delete file '{p.name}'? [y/N]: ").strip().lower()
        if ans != "y":
            print("Aborted.")
            return
    p.unlink()
    logger.info("Deleted file '%s'.", p.name)


def remove_line(name: str, line_number: int, data_dir: Path = DEFAULT_DATA_DIR) -> None:
    if line_number < 1:
        logger.error("line_number must be >= 1")
        return
    p = file_path_for(name, data_dir)
    if not p.exists():
        logger.error("File '%s' not found.", p.name)
        return
    with p.open("r", encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    if line_number > len(lines):
        logger.error("File '%s' has only %d line(s).", p.name, len(lines))
        return
    removed = lines.pop(line_number - 1)
    with p.open("w", encoding="utf-8") as fh:
        fh.writelines(lines)
    logger.info("Removed line %d from '%s': %s", line_number, p.name, removed.rstrip())


def find_text_across_files(text: str, data_dir: Path = DEFAULT_DATA_DIR, ignore_case: bool = True) -> List[Tuple[Path, int, str]]:
    matches: List[Tuple[Path, int, str]] = []
    if ignore_case:
        needle = text.lower()
    else:
        needle = text
    for p in collection_files(data_dir):
        try:
            with p.open("r", encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh, start=1):
                    hay = line.lower() if ignore_case else line
                    if needle in hay:
                        matches.append((p, i, line.rstrip("\n")))
        except Exception as e:
            logger.warning("Could not read file '%s': %s", p.name, e)
    return matches


# CLI
def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage a collection of up to 100 text files. Files are stored in ./collection_data by default."
    )
    parser.add_argument("--dir", "-d", type=Path, default=DEFAULT_DATA_DIR, help="directory to store collection files")

    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List all files in the collection")

    p_show = sub.add_parser("show", help="Show a file with line numbers")
    p_show.add_argument("file", help="file name to show")

    p_create = sub.add_parser("create", help="Create a new empty file")
    p_create.add_argument("file", help="file name to create")
    p_create.add_argument("--overwrite", action="store_true", help="overwrite if exists")

    p_add = sub.add_parser("add-lines", help="Append lines to an existing file")
    p_add.add_argument("file", help="file name to append to")
    p_add.add_argument("--text", "-t", action="append", help="line to append (multiple OK)")
    p_add.add_argument("--interactive", "-i", action="store_true", help="enter lines interactively (end with a single '.' on a line)")

    p_remove_file = sub.add_parser("remove-file", help="Remove a file from collection")
    p_remove_file.add_argument("file", help="file name to remove")
    p_remove_file.add_argument("--yes", "-y", action="store_true", help="do not prompt for confirmation")

    p_remove_line = sub.add_parser("remove-line", help="Remove a specific line number from a file")
    p_remove_line.add_argument("file", help="file name")
    p_remove_line.add_argument("line_number", type=int, help="1-based line number to remove")

    p_find = sub.add_parser("find", help="Find text across all files; reports file and line number(s)")
    p_find.add_argument("text", help="text to find (substring match)")
    p_find.add_argument("--case-sensitive", action="store_true", help="do case-sensitive search")

    return parser.parse_args(argv)


def interactive_lines_input(prompt: str = "Enter lines (single '.' on a line to finish):") -> List[str]:
    print(prompt)
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
    data_dir: Path = args.dir
    ensure_data_dir(data_dir)

    try:
        if args.cmd == "list":
            list_files(data_dir)

        elif args.cmd == "show":
            show_file(args.file, data_dir)

        elif args.cmd == "create":
            create_file(args.file, data_dir, overwrite=args.overwrite)

        elif args.cmd == "add-lines":
            if args.text is None and not args.interactive:
                logger.error("Provide --text lines or --interactive")
                return 2
            to_add: List[str] = []
            if args.text:
                to_add.extend(args.text)
            if args.interactive:
                to_add.extend(interactive_lines_input())
            if not to_add:
                print("No lines to add.")
                return 0
            add_lines(args.file, to_add, data_dir)

        elif args.cmd == "remove-file":
            remove_file(args.file, data_dir, confirm=not args.yes)

        elif args.cmd == "remove-line":
            remove_line(args.file, args.line_number, data_dir)

        elif args.cmd == "find":
            matches = find_text_across_files(args.text, data_dir, ignore_case=not args.case_sensitive)
            if not matches:
                print("No matches found.")
                return 0
            # Group by file for nicer output
            current_file: Path | None = None
            for p, lineno, line in matches:
                print(f"{p.name}:{lineno}: {line}")
        else:
            logger.error("Unknown command")
            return 2

    except ValueError as ve:
        logger.error("Invalid input: %s", ve)
        return 2
    except Exception as exc:
        logger.exception("Unhandled error: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())