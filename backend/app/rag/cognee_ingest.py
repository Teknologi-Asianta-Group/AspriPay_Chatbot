"""
Proses dokumen KB aspripay lewat Cognee -> bikin knowledge graph
(entitas & relasi antar topik/produk), sebagai lapisan memory tambahan
di luar pencarian vector biasa (Qdrant).

Cara pakai:
    python -m app.rag.cognee_ingest --source ./docs/kb_aspripay
"""

import argparse
import asyncio
from pathlib import Path

import cognee


async def run_cognify(source_dir: str):
    files = list(Path(source_dir).glob("**/*.txt")) + list(Path(source_dir).glob("**/*.md"))
    if not files:
        print(f"Tidak ada file .txt/.md ditemukan di {source_dir}")
        return

    print(f"Menambahkan {len(files)} dokumen ke Cognee...")
    for f in files:
        content = f.read_text(encoding="utf-8")
        await cognee.add(content, dataset_name="aspripay_kb")

    print("Membangun knowledge graph (cognify)... ini bisa makan waktu, manggil LLM buat tiap chunk.")
    await cognee.cognify(datasets=["aspripay_kb"])

    print("Selesai. Knowledge graph aspripay_kb sudah terbentuk.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bangun knowledge graph Cognee dari dokumen KB aspripay")
    parser.add_argument("--source", type=str, required=True, help="Folder berisi dokumen KB (.txt/.md)")
    args = parser.parse_args()
    asyncio.run(run_cognify(args.source))