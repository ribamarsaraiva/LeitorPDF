import os
import sqlite3
import json
import tempfile

from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pypdf import PdfReader

PDF_ROOT = os.environ.get("PDF_ROOT", "./pdfs")
DB_PATH = "./progress.db"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            path TEXT PRIMARY KEY,
            current_page INTEGER DEFAULT 1,
            total_pages INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    return conn


def get_pdf_pages(filepath: str) -> int:
    try:
        return len(PdfReader(filepath).pages)
    except Exception:
        return 1


def build_tree(root: str) -> list:
    result = []
    root_path = Path(root).resolve()

    for entry in sorted(Path(root).iterdir()):
        if entry.is_dir():
            children = build_tree(str(entry))
            if children:
                result.append({"type": "folder", "name": entry.name, "children": children})
        elif entry.suffix.lower() == ".pdf" and ":" not in entry.name:
            rel = str(entry.resolve().relative_to(root_path))
            result.append({"type": "pdf", "name": entry.name, "path": rel})

    return result


@app.get("/api/tree")
def get_tree():
    if not Path(PDF_ROOT).exists():
        return []
    return build_tree(PDF_ROOT)


@app.get("/api/progress/{path:path}")
def get_progress(path: str):
    conn = get_db()
    row = conn.execute("SELECT current_page, total_pages FROM progress WHERE path = ?", (path,)).fetchone()
    conn.close()
    if row:
        return {"current_page": row[0], "total_pages": row[1]}
    total = get_pdf_pages(str(Path(PDF_ROOT) / path))
    return {"current_page": 1, "total_pages": total}


class ProgressUpdate(BaseModel):
    current_page: int
    total_pages: int


@app.post("/api/progress/{path:path}")
def save_progress(path: str, body: ProgressUpdate):
    conn = get_db()
    conn.execute("""
        INSERT INTO progress (path, current_page, total_pages)
        VALUES (?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET current_page=excluded.current_page, total_pages=excluded.total_pages
    """, (path, body.current_page, body.total_pages))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/api/progress-bulk")
def get_progress_bulk():
    conn = get_db()
    rows = conn.execute("SELECT path, current_page, total_pages FROM progress").fetchall()
    conn.close()
    return {r[0]: {"current_page": r[1], "total_pages": r[2]} for r in rows}


@app.get("/pdf/{path:path}")
def serve_pdf(path: str):
    full = Path(PDF_ROOT) / path
    if not full.exists() or full.suffix.lower() != ".pdf":
        raise HTTPException(404)
    return FileResponse(str(full), media_type="application/pdf")


@app.get("/api/export")
def export_progress():
    conn = get_db()
    rows = conn.execute("SELECT path, current_page, total_pages FROM progress").fetchall()
    conn.close()
    data = [{ "path": r[0], "current_page": r[1], "total_pages": r[2] } for r in rows]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8")
    json.dump(data, tmp, ensure_ascii=False, indent=2)
    tmp.close()
    return FileResponse(tmp.name, media_type="application/json", filename="leitor_progress.json", background=None)


@app.post("/api/import")
async def import_progress(file: UploadFile = File(...)):
    content = await file.read()
    try:
        data = json.loads(content)
    except Exception:
        raise HTTPException(400, "Arquivo JSON inválido")
    conn = get_db()
    for item in data:
        conn.execute("""
            INSERT INTO progress (path, current_page, total_pages)
            VALUES (?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                current_page = MAX(current_page, excluded.current_page),
                total_pages  = excluded.total_pages
        """, (item["path"], item["current_page"], item["total_pages"]))
    conn.commit()
    conn.close()
    return {"ok": True, "imported": len(data)}


app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
