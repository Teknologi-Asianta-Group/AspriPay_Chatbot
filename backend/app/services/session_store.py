"""
Session store sederhana buat nyimpen histori percakapan per conversation_id.

NOTE: Ini masih in-memory (hilang kalau server restart) - dipakai sementara
sebelum MySQL disetup di Fase 2. Struktur data disamain sama tabel MESSAGE
di ERD, biar gampang dipindah ke database nanti.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatTurn:
    sender_type: str  # "visitor" atau "ai" atau "agent"
    content: str
    sent_at: datetime = field(default_factory=datetime.utcnow)


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, list[ChatTurn]] = {}

    def add_turn(self, conversation_id: str, sender_type: str, content: str) -> None:
        self._sessions.setdefault(conversation_id, []).append(
            ChatTurn(sender_type=sender_type, content=content)
        )

    def get_history(self, conversation_id: str, max_turns: int = 10) -> list[ChatTurn]:
        """Ambil N histori percakapan terakhir buat conversation_id ini."""
        turns = self._sessions.get(conversation_id, [])
        return turns[-max_turns:]

    def get_history_as_text(self, conversation_id: str, max_turns: int = 10) -> str:
        """Format histori jadi teks siap pakai buat prompt LLM."""
        turns = self.get_history(conversation_id, max_turns)
        if not turns:
            return ""
        lines = []
        for turn in turns:
            role = "Pengunjung" if turn.sender_type == "visitor" else "Asisten"
            lines.append(f"{role}: {turn.content}")
        return "\n".join(lines)

    def clear_session(self, conversation_id: str) -> None:
        self._sessions.pop(conversation_id, None)


# Instance singleton dipakai di seluruh app (sementara, sampai MySQL siap)
session_store = SessionStore()