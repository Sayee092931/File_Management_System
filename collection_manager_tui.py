"""
Simple TUI (terminal menu) for the collection manager.

This is intentionally simple and dependency-free (no curses). It provides
a prompt-driven menu loop that you can run in a terminal.
"""
from __future__ import annotations

from typing import List
from .manager import CollectionManager


def menu(manager: CollectionManager) -> None:
    prompt = """
Collection Manager (TUI)
Commands:
  ls                     - list files
  show <file>            - show file with numbers
  create <file>          - create a new file
  add <file>             - add lines interactively to file (finish with single '.')
  rm <file>              - remove file
  rml <file> <line_no>   - remove specific line
  find <text>            - find text across files
  tags <file>            - show tags
  addtag <file> <tag>    - add tag
  rmtag <file> <tag>     - remove tag
  quit                   - exit
"""
    print(prompt)
    while True:
        try:
            raw = input(">> ").strip()
        except EOFError:
            break
        if not raw:
            continue
        parts = raw.split()
        cmd = parts[0].lower()
        try:
            if cmd in ("quit", "exit"):
                break
            elif cmd == "ls":
                metas = manager.list_files()
                for m in metas:
                    print(f"- {m.filename} (size={m.size}, tags={m.tags})")
            elif cmd == "show" and len(parts) >= 2:
                for i, ln in enumerate(manager.show_file(parts[1]), start=1):
                    print(f"{i:4d}: {ln}")
            elif cmd == "create" and len(parts) >= 2:
                manager.create_file(parts[1])
                print("Created", parts[1])
            elif cmd == "add" and len(parts) >= 2:
                print("Enter lines. Single '.' to finish.")
                lines: List[str] = []
                while True:
                    ln = input()
                    if ln == ".":
                        break
                    lines.append(ln)
                manager.add_lines(parts[1], lines)
                print(f"Appended {len(lines)} lines.")
            elif cmd == "rm" and len(parts) >= 2:
                confirm = input(f"Delete '{parts[1]}'? [y/N]: ").strip().lower()
                if confirm == "y":
                    manager.remove_file(parts[1])
                    print("Deleted.")
            elif cmd == "rml" and len(parts) >= 3:
                ln = int(parts[2])
                removed = manager.remove_line(parts[1], ln)
                print("Removed:", removed)
            elif cmd == "find" and len(parts) >= 2:
                text = " ".join(parts[1:])
                matches = manager.find_text(text)
                for fname, lineno, line in matches:
                    print(f"{fname}:{lineno}: {line}")
            elif cmd == "tags" and len(parts) >= 2:
                meta = manager.get_meta(parts[1])
                print("Tags:", meta.tags if meta else "file not found")
            elif cmd == "addtag" and len(parts) >= 3:
                manager.add_tag(parts[1], parts[2])
                print("Tag added.")
            elif cmd == "rmtag" and len(parts) >= 3:
                manager.remove_tag(parts[1], parts[2])
                print("Tag removed.")
            else:
                print("Unknown or malformed command.")
        except Exception as e:
            print("Error:", e)


def run(data_dir: str | None = None) -> None:
    manager = CollectionManager(data_dir) if data_dir else CollectionManager()
    menu(manager)


if __name__ == "__main__":
    run()