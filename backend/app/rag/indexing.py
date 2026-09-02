"""
Indexing pipeline: dokumen KB aspripay -> chunk -> embedding -> simpan ke Qdrant Cloud.

Jalanin script ini setiap kali ada dokumen KB baru/update.
Prasyarat: cluster Qdrant Cloud sudah dibuat, QDRANT_URL & QDRANT_API_KEY sudah diisi di .env

Cara pakai:
    python -m app.rag.indexing --source ./docs/kb_aspripay
"""

import argparse
from pathlib import Path

from haystack import Pipeline
from haystack.utils import Secret
from haystack.components.converters import TextFileToDocument
from haystack.components.preprocessors import DocumentSplitter
from haystack_integrations.components.embedders.sentence_transformers import (
    SentenceTransformersDocumentEmbedder,
)
from haystack.components.writers import DocumentWriter
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from app.core.config import settings


def build_indexing_pipeline(document_store: QdrantDocumentStore) -> Pipeline:
    """Bangun pipeline: baca file -> split jadi chunk -> embed -> simpan ke Qdrant."""
    pipeline = Pipeline()

    pipeline.add_component("converter", TextFileToDocument())
    pipeline.add_component(
        "splitter",
        DocumentSplitter(split_by="sentence", split_length=5, split_overlap=1),
    )
    # Model embedding multilingual, penting karena KB aspripay berbahasa Indonesia
    pipeline.add_component(
        "embedder",
        SentenceTransformersDocumentEmbedder(
            model="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        ),
    )
    pipeline.add_component("writer", DocumentWriter(document_store=document_store))

    pipeline.connect("converter", "splitter")
    pipeline.connect("splitter", "embedder")
    pipeline.connect("embedder", "writer")

    return pipeline


def get_document_store() -> QdrantDocumentStore:
    return QdrantDocumentStore(
        url=settings.QDRANT_URL,
        api_key=Secret.from_token(settings.QDRANT_API_KEY),
        index="aspripay_kb",
        embedding_dim=768,  # sesuai output dim model embedder di atas
        recreate_index=False,
    )


def run_indexing(source_dir: str):
    document_store = get_document_store()
    pipeline = build_indexing_pipeline(document_store)

    files = list(Path(source_dir).glob("**/*.txt")) + list(Path(source_dir).glob("**/*.md"))
    if not files:
        print(f"Tidak ada file .txt/.md ditemukan di {source_dir}")
        return

    print(f"Mengindeks {len(files)} dokumen dari {source_dir} ...")
    pipeline.run({"converter": {"sources": files}})
    print("Selesai. Dokumen sudah masuk ke Qdrant Cloud collection 'aspripay_kb'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index dokumen KB aspripay ke Qdrant Cloud")
    parser.add_argument(
        "--source", type=str, required=True, help="Folder berisi dokumen KB (.txt/.md)"
    )
    args = parser.parse_args()
    run_indexing(args.source)