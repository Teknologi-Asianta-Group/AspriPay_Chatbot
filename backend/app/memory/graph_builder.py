"""
Bangun knowledge graph aspripay pakai Cognee Cloud API (bukan pip install cognee lokal).
Alur: add (kirim dokumen) -> cognify (proses jadi graph).

PENTING: endpoint /api/v1/add butuh multipart/form-data (upload file),
BUKAN JSON body -- makanya requests.post() di sini pakai `files=` dan `data=`,
bukan `json=`.

Cara pakai:
    python -m app.memory.graph_builder --source ../docs/kb_aspripay
"""

import argparse
from pathlib import Path

import requests

from app.core.config import settings

DATASET_NAME = "aspripay_kb"


def _headers():
    # Jangan set Content-Type manual di sini -- biarin `requests` yang nentuin
    # boundary multipart-nya sendiri pas kita pakai `files=`.
    return {
        "X-Api-Key": settings.COGNEE_API_KEY,
    }


def add_documents_from_text(content: str, filename: str = "document.txt"):
    resp = requests.post(
        f"{settings.COGNEE_BASE_URL}/api/v1/add",
        files={"data": (filename, content.encode("utf-8"), "text/plain")},
        data={"datasetName": DATASET_NAME},
        headers=_headers(),
    )
    if not resp.ok:
        print(f"  [ERROR {resp.status_code}] {resp.text}")
    resp.raise_for_status()
    return resp.json()


def add_documents(source_dir: str):
    files = list(Path(source_dir).glob("**/*.txt")) + list(Path(source_dir).glob("**/*.md"))
    if not files:
        print(f"Tidak ada file .txt/.md ditemukan di {source_dir}")
        return 0

    for f in files:
        content = f.read_text(encoding="utf-8")
        add_documents_from_text(content, filename=f.name)
        print(f"  + {f.name} ditambahkan")

    return len(files)


def cognify():
    print("Membangun knowledge graph (cognify)... bisa makan waktu.")
    resp = requests.post(
        f"{settings.COGNEE_BASE_URL}/api/v1/cognify",
        json={"datasets": [DATASET_NAME]},
        headers={**_headers(), "Content-Type": "application/json"},
    )
    if not resp.ok:
        print(f"  [ERROR {resp.status_code}] {resp.text}")
    resp.raise_for_status()
    return resp.json()


def build_graph(source_dir: str):
    print(f"Menambahkan dokumen dari {source_dir} ke Cognee...")
    count = add_documents(source_dir)
    if count == 0:
        return

    result = cognify()
    print("Selesai. Knowledge graph aspripay_kb sudah terbentuk.")
    print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bangun knowledge graph Cognee dari KB aspripay")
    parser.add_argument("--source", type=str, required=True, help="Folder berisi dokumen KB (.txt/.md)")
    args = parser.parse_args()
    build_graph(args.source)