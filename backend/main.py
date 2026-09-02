from fastapi import FastAPI

app = FastAPI(title="Sysend - AI CS Chatbot Aspripay")


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
