"""
collection_manager.manager

Core manager for file collection with persistent JSON metadata index.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

FILENAME_RE = re.compile(r"^[\w\-. ]+$")
MAX_FILES = 100
INDEX_FILENAME = "index.json"


@dataclass
class FileMeta:
    filename: str
    created_at: str
    last_modified: str
    size: int
    tags: List[str]


class CollectionManager:
    def __init__(self, data_dir: Path | str = Path.cwd() / "collection_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.data_dir / INDEX_FILENAME
        self._index: Dict[str, FileMeta] = {}
        self._load_index()

    # ----- Index persistence -----
    def _load_index(self) -> None:
        if self.index_path.exists():
            try:
                with self.index_path.open("r", encoding="utf-8") as fh:
                    raw = json.load(fh)
                for fname, meta in raw.items():
                    self._index[fname] = FileMeta(**meta)
            except Exception:
                # If corrupt, rebuild from actual files
                self._rebuild_index()
        else:
            self._rebuild_index()

    def _write_index(self) -> None:
        tmp = self.index_path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump({k: asdict(v) for k, v in self._index.items()}, fh, indent=2)
        tmp.replace(self.index_path)

    def _rebuild_index(self) -> None:
        self._index = {}
        for p in sorted(self.data_dir.iterdir()):
            if p.is_file() and p.name != INDEX_FILENAME:
                stat = p.stat()
                meta = FileMeta(
                    filename=p.name,
                    created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    size=stat.st_size,
                    tags=[],
                )
                self._index[p.name] = meta
        self._write_index()

    # ----- Utilities -----
    def _sanitize_filename(self, name: str) -> str:
        base = os.path.basename(name)
        if not base or not FILENAME_RE.match(base):
            raise ValueError("Invalid filename. Allowed: letters, numbers, underscore, dash, dot, space.")
        if base == INDEX_FILENAME:
            raise ValueError("Filename reserved")
        return base

    def _file_path(self, name: str) -> Path:
        fname = self._sanitize_filename(name)
        return self.data_dir / fname

    def _update_meta_for(self, path: Path) -> None:
        stat = path.stat()
        meta = self._index.get(path.name)
        now = datetime.utcnow().isoformat()
        if not meta:
            meta = FileMeta(filename=path.name, created_at=now, last_modified=now, size=stat.st_size, tags=[])
        else:
            meta.last_modified = now
            meta.size = stat.st_size
        self._index[path.name] = meta
        self._write_index()

    # ----- Public API -----
    def list_files(self) -> List[FileMeta]:
        # Ensure index matches the disk
        self._rebuild_index()
        return list(self._index.values())

    def create_file(self, name: str, overwrite: bool = False) -> None:
        files_count = len([p for p in self.data_dir.iterdir() if p.is_file() and p.name != INDEX_FILENAME])
        if files_count >= MAX_FILES:
            raise RuntimeError(f"Cannot create file: maximum of {MAX_FILES} files reached.")
        path = self._file_path(name)
        if path.exists() and not overwrite:
            raise FileExistsError(f"File '{path.name}' already exists")
        path.write_text("", encoding="utf-8")
        self._update_meta_for(path)

    def show_file(self, name: str) -> List[str]:
        path = self._file_path(name)
        if not path.exists():
            raise FileNotFoundError(name)
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            return [line.rstrip("\n") for line in fh]

    def add_lines(self, name: str, lines: List[str]) -> None:
        path = self._file_path(name)
        if not path.exists():
            raise FileNotFoundError(name)
        with path.open("a", encoding="utf-8") as fh:
            for line in lines:
                fh.write(line.rstrip("\n") + "\n")
        self._update_meta_for(path)

    def remove_file(self, name: str) -> None:
        path = self._file_path(name)
        if not path.exists():
            raise FileNotFoundError(name)
        path.unlink()
        if name in self._index:
            del self._index[name]
            self._write_index()

    def remove_line(self, name: str, line_no: int) -> str:
        if line_no < 1:
            raise ValueError("line_no must be >= 1")
        path = self._file_path(name)
        if not path.exists():
            raise FileNotFoundError(name)
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
        if line_no > len(lines):
            raise IndexError("line number out of range")
        removed = lines.pop(line_no - 1)
        with path.open("w", encoding="utf-8") as fh:
            fh.writelines(lines)
        self._update_meta_for(path)
        return removed.rstrip("\n")

    def find_text(self, text: str, ignore_case: bool = True) -> List[Tuple[str, int, str]]:
        results: List[Tuple[str, int, str]] = []
        needle = text.lower() if ignore_case else text
        for p in sorted(self.data_dir.iterdir()):
            if not p.is_file() or p.name == INDEX_FILENAME:
                continue
            with p.open("r", encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh, start=1):
                    hay = line.lower() if ignore_case else line
                    if needle in hay:
                        results.append((p.name, i, line.rstrip("\n")))
        return results

    def get_meta(self, name: str) -> Optional[FileMeta]:
        name = self._sanitize_filename(name)
        return self._index.get(name)

    def add_tag(self, name: str, tag: str) -> None:
        meta = self.get_meta(name)
        if not meta:
            raise FileNotFoundError(name)
        if tag not in meta.tags:
            meta.tags.append(tag)
            self._write_index()

    def remove_tag(self, name: str, tag: str) -> None:
        meta = self.get_meta(name)
        if not meta:
            raise FileNotFoundError(name)
        if tag in meta.tags:
            meta.tags.remove(tag)
            self._write_index()