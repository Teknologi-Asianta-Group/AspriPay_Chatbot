from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sysend - AI CS Chatbot Aspripay")

# CORS - izinkan widget diakses dari mana saja (file://, domain aspripay, dll).
# Untuk production nanti, ganti allow_origins ke domain aspripay yang spesifik
# demi keamanan, jangan biarkan "*" di production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Basic health check endpoint - juga dipakai buat cek Ollama & Qdrant nanti."""
    return {"status": "ok", "service": "sysend-backend"}


from app.api import chat

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# Router lain nyusul setelah dibuat:
# from app.api import kb, inbox
# app.include_router(kb.router, prefix="/api/kb", tags=["knowledge-base"])
# app.include_router(inbox.router, prefix="/api/inbox", tags=["inbox"])