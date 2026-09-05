"""API key auth - biar chatbot bisa dipasang di banyak website tanpa saling bocor."""
import os
from dotenv import load_dotenv
from fastapi import Header, HTTPException, status

load_dotenv()  # baca file .env ke os.environ

# Sementara dari .env, nanti bisa dipindah ke tabel `clients` di MySQL
# biar tiap partner web punya key + quota sendiri.
_VALID_API_KEYS = set(
    k.strip() for k in os.getenv("ASPRIPAY_API_KEYS", "").split(",") if k.strip()
)
print("DEBUG loaded keys:", _VALID_API_KEYS)


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    if x_api_key not in _VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_api_key