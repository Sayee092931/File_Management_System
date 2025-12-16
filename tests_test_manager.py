```python
import os
from pathlib import Path
import pytest
from collection_manager.manager import CollectionManager

def test_create_add_find_remove(tmp_path: Path):
    mgr = CollectionManager(tmp_path)
    fname = "a.txt"

    # Create
    mgr.create_file(fname)
    assert (tmp_path / fname).exists()
    metas = mgr.list_files()
    assert any(m.filename == fname for m in metas)

    # Add lines
    mgr.add_lines(fname, ["line one", "another line", "final"])
    lines = mgr.show_file(fname)
    assert lines[0] == "line one"
    assert len(lines) == 3

    # Find
    matches = mgr.find_text("another")
    assert len(matches) == 1
    assert matches[0][0] == fname
    assert matches[0][1] == 2

    # Remove line
    removed = mgr.remove_line(fname, 2)
    assert removed == "another line"
    lines2 = mgr.show_file(fname)
    assert len(lines2) == 2
    assert "another" not in "\n".join(lines2)

    # Remove file
    mgr.remove_file(fname)
    assert not (tmp_path / fname).exists()
    metas_after = mgr.list_files()
    assert all(m.filename != fname for m in metas_after)

def test_tags(tmp_path: Path):
    mgr = CollectionManager(tmp_path)
    fname = "b.txt"
    mgr.create_file(fname)
    mgr.add_tag(fname, "important")
    meta = mgr.get_meta(fname)
    assert "important" in meta.tags
    mgr.remove_tag(fname, "important")
    meta2 = mgr.get_meta(fname)
    assert "important" not in meta2.tags
```