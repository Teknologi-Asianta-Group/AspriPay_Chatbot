"""
Script sekali-pakai buat kosongin/reset index Qdrant.
HATI-HATI: ini hapus SEMUA data lama di collection aspripay_kb.

Cara pakai: python clear_qdrant.py
"""

from haystack.utils import Secret
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from app.core.config import settings

print("Menghapus & recreate index 'aspripay_kb' di Qdrant...")

store = QdrantDocumentStore(
    url=settings.QDRANT_URL,
    api_key=Secret.from_token(settings.QDRANT_API_KEY),
    index="aspripay_kb",
    embedding_dim=768,
    recreate_index=True,  # <-- ini yang hapus & bikin ulang kosongan
)

print("Selesai. Index 'aspripay_kb' sekarang kosong.")  