#!/usr/bin/env python3
"""
Entrypoint script for various interfaces.

Usage:
  python scripts/collection_manager.py cli ...     # run CLI
  python scripts/collection_manager.py tui         # run TUI
  python scripts/collection_manager.py web         # run Flask web server (development)
"""
from __future__ import annotations

import sys
from pathlib import Path

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print("Usage: scripts/collection_manager.py [cli|tui|web] ...")
        return 2
    mode = argv[0]
    if mode == "cli":
        from collection_manager.cli import main as cli_main
        return cli_main(argv[1:])
    elif mode == "tui":
        from collection_manager.tui import run as run_tui
        data_dir = None
        if len(argv) > 1:
            data_dir = argv[1]
        run_tui(data_dir)
        return 0
    elif mode == "web":
        from collection_manager.web import create_app
        app = create_app()
        # run the Flask app in development mode
        app.run()
        return 0
    else:
        print("Unknown mode:", mode)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())