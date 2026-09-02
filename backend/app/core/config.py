"""Konfigurasi aplikasi, dibaca dari environment variables (.env)."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@localhost:3306/sysend")

    # Mistral (generator utama - cloud API free tier, ringan buat hardware development)
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

    # Qdrant Cloud (vector store, cloud - free tier, tidak perlu Docker)
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")

    # RAG behavior
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.55"))
    TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", "3"))
    # Batas bawah skor similarity buat dianggap "nyambung" sama pertanyaan.
    # Chunk di bawah ini dibuang sebelum masuk prompt - ini rem utama anti-halusinasi.
    # Kalau SEMUA chunk di bawah ini, LLM tidak dipanggil sama sekali.
    MIN_RELEVANCE_SCORE: float = float(os.getenv("MIN_RELEVANCE_SCORE", "0.40"))
    # Di bawah skor ini pertanyaan dianggap di luar topik aspripay sama sekali
    # -> ditolak sopan TANPA eskalasi (agent jangan dibebani pertanyaan random).
    # Antara OUT_OF_SCOPE_SCORE dan MIN_RELEVANCE_SCORE = zona abu-abu: masih
    # nyerempet aspripay tapi KB belum punya jawabannya -> baru dieskalasi.
    OUT_OF_SCOPE_SCORE: float = float(os.getenv("OUT_OF_SCOPE_SCORE", "0.25"))

    # Cognee Cloud API (knowledge graph memory layer)
    COGNEE_API_KEY: str = os.getenv("COGNEE_API_KEY", "")
    COGNEE_BASE_URL: str = os.getenv("COGNEE_BASE_URL", "")
    # Cognee GRAPH_COMPLETION itu LLM juga, jadi bisa ngarang kalau graph-nya tidak
    # punya konteks. Dia cuma dipanggil buat pertanyaan yang sudah dipastikan masih
    # soal aspripay (AnswerKind.NO_ANSWER) - lihat app/api/chat.py.


settings = Settings()