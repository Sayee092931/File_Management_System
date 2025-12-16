# Collection Manager

A professional Python project to manage a collection of text files (up to 100). The system stores files in a data directory and maintains a persistent JSON index with metadata (creation time, last modified, size, tags). It includes:

- Core manager library: collection_manager.manager
- CLI: collection_manager.cli
- TUI: collection_manager.tui (simple interactive menu)
- Web UI (Flask): collection_manager.web
- Executable script: scripts/collection_manager.py
- Unit tests: tests/test_manager.py
- Requirements: requirements.txt

Features
- List all files in the collection
- Show a file with line numbers
- Create (add) a new file (with metadata)
- Append lines to a file
- Remove a file (and its metadata)
- Remove a specific line (by 1-based index)
- Find text across all files reporting file and line number(s)
- Add/remove tags in metadata
- Up to 100 files by default (changeable via MAX_FILES)

Installation
1. Clone or copy the project files into a directory.
2. (Optional) Create and activate a virtualenv.
3. Install dependencies:

   pip install -r requirements.txt

Usage (CLI)
- List files:
  python scripts/collection_manager.py cli list

- Create a file:
  python scripts/collection_manager.py cli create notes.txt

- Append lines:
  python scripts/collection_manager.py cli add-lines notes.txt -t "First line" -t "Second line"

- Interactive append:
  python scripts/collection_manager.py cli add-lines notes.txt --interactive

- Show file:
  python scripts/collection_manager.py cli show notes.txt

- Remove a line:
  python scripts/collection_manager.py cli remove-line notes.txt 3

- Find text:
  python scripts/collection_manager.py cli find "error"

Usage (TUI)
  python scripts/collection_manager.py tui

Usage (Web)
  python scripts/collection_manager.py web
  The Flask app runs on http://127.0.0.1:5000 by default. Endpoints:
  - GET /files
  - GET /files/<filename>  (shows file with numbered lines)
  - POST /files            (JSON: {"filename": "a.txt"})
  - POST /files/<filename>/lines  (JSON: {"lines":["a","b"]})
  - DELETE /files/<filename>
  - DELETE /files/<filename>/lines/<int:line_no>
  - GET /find?q=term

Testing
Run unit tests with pytest:
  pytest

Project structure
- collection_manager/manager.py  — core manager & persistence
- collection_manager/cli.py      — CLI wrapper
- collection_manager/tui.py      — simple terminal menu
- collection_manager/web.py      — Flask web interface
- scripts/collection_manager.py  — executable entrypoint
- tests/test_manager.py          — pytest tests
- requirements.txt               — dependencies

Notes
- Files are stored in `./collection_data` by default (change with --dir).
- Filenames are sanitized and path traversal is prevented.
- Index file: `index.json` inside the data directory. It records metadata for each file.

If you want, I can:
- Add authentication to the Flask UI
- Add a richer TUI using `prompt_toolkit` or `urwid`
- Add continuous integration (GitHub Actions) and a coverage report
- Or any suggestions of you own!
 
**Developed by Sayee Krishnaa SP**

