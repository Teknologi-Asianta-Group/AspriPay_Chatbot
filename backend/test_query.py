"""
Script testing RAG pipeline secara interaktif dari terminal.
Pipeline & model di-load SEKALI di awal, lalu bisa tanya berkali-kali tanpa reload.

Cara pakai: python test_query.py
Ketik "q" atau "exit" buat keluar.
"""

from app.rag.indexing import get_document_store
from app.rag.query_pipeline import build_query_pipeline, ask


def main():
    print("Menyiapkan pipeline (sekali saja)...")
    document_store = get_document_store()
    engine = build_query_pipeline(document_store)
    print("Siap! Ketik pertanyaan, atau 'q' untuk keluar.\n")

    while True:
        question = input("🧑 ").strip()
        if question.lower() in ("q", "exit", "quit"):
            break
        if not question:
            continue

        result = ask(engine, question=question)

        print("=" * 50)
        print(f"🤖 {result.answer}")
        print(f"Confidence score: {result.confidence_score}")
        print(f"Should escalate ke agent: {result.should_escalate}")
        print(f"Jenis jawaban: {result.kind}")
        print(f"Source chunks: {result.source_chunks}")
        print("=" * 50)
        print()


if __name__ == "__main__":
    main()