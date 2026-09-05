import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sysend - AI CS Chatbot Aspripay")

allowed_origins = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],  # fallback "*" cuma buat dev lokal
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["X-API-Key", "Content-Type"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "sysend-backend"}


from app.api import chat
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])