"""
A minimal Flask web interface for CollectionManager.

Endpoints:
- GET  /files
- GET  /files/<filename>
- POST /files            (JSON {"filename": "a.txt"})
- POST /files/<filename>/lines  (JSON {"lines": ["a", "b"]})
- DELETE /files/<filename>
- DELETE /files/<filename>/lines/<int:line_no>
- GET /find?q=term
"""
from __future__ import annotations

from flask import Flask, jsonify, request, abort
from .manager import CollectionManager

def create_app(data_dir: str | None = None) -> Flask:
    app = Flask(__name__)
    manager = CollectionManager(data_dir) if data_dir else CollectionManager()

    @app.get("/files")
    def list_files():
        metas = manager.list_files()
        return jsonify([m.__dict__ for m in metas])

    @app.get("/files/<path:filename>")
    def show_file(filename):
        try:
            lines = manager.show_file(filename)
        except FileNotFoundError:
            abort(404)
        return jsonify({"filename": filename, "lines": lines})

    @app.post("/files")
    def create_file():
        body = request.get_json(force=True)
        filename = body.get("filename")
        if not filename:
            abort(400, description="filename required")
        try:
            manager.create_file(filename)
        except Exception as e:
            abort(400, description=str(e))
        return jsonify({"created": filename})

    @app.post("/files/<path:filename>/lines")
    def post_lines(filename):
        body = request.get_json(force=True)
        lines = body.get("lines")
        if not isinstance(lines, list):
            abort(400, description="lines must be a list")
        try:
            manager.add_lines(filename, lines)
        except FileNotFoundError:
            abort(404)
        return jsonify({"appended": len(lines)})

    @app.delete("/files/<path:filename>")
    def delete_file(filename):
        try:
            manager.remove_file(filename)
        except FileNotFoundError:
            abort(404)
        return jsonify({"deleted": filename})

    @app.delete("/files/<path:filename>/lines/<int:line_no>")
    def delete_line(filename, line_no):
        try:
            removed = manager.remove_line(filename, line_no)
        except FileNotFoundError:
            abort(404)
        except IndexError:
            abort(400, description="line number out of range")
        return jsonify({"removed": removed})

    @app.get("/find")
    def find():
        q = request.args.get("q", "")
        if not q:
            return jsonify([])
        cs = request.args.get("case", "false").lower() == "true"
        matches = manager.find_text(q, ignore_case=not cs)
        return jsonify([{"file": f, "line_no": n, "line": l} for f, n, l in matches])

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)