"""
Service buat handle logic percakapan: bikin/lanjutin conversation,
simpan message ke MySQL, dan ambil histori buat konteks prompt LLM.

Ini gantiin session_store.py (in-memory) - sekarang histori persisten di MySQL.
"""

from sqlalchemy import case
from sqlalchemy.orm import Session

from app.models.models import Contact, Conversation, Message


def get_or_create_conversation(db: Session, conversation_id: str, contact_id: str | None = None) -> Conversation:
    """
    Ambil conversation yang sudah ada, atau bikin baru kalau belum ada.
    conversation_id di sini dianggap sebagai Conversation.id (UUID).
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        return conversation

    # Kalau belum ada contact_id yang dikirim, bikin contact anonim dulu
    if contact_id is None:
        contact = Contact(name=None, email=None)
        db.add(contact)
        db.flush()  # biar contact.id ke-generate tanpa commit dulu
        contact_id = contact.id

    conversation = Conversation(id=conversation_id, contact_id=contact_id, status="ai-handling")
    db.add(conversation)
    db.flush()
    return conversation


def save_message(
    db: Session,
    conversation_id: str,
    sender_type: str,
    content: str,
    confidence_score: float | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        sender_type=sender_type,
        content=content,
        confidence_score=confidence_score,
    )
    db.add(message)
    db.flush()
    return message


# Kolom sent_at itu DATETIME (presisi detik), sedangkan pesan visitor & ai dalam
# satu request hampir selalu tersimpan di detik yang sama -> urutannya jadi seri.
# Tiebreak eksplisit: di dalam detik yang sama, jawaban ai SELALU sesudah pesan visitor.
# Tanpa ini riwayatnya bisa terbalik dan LLM salah paham siapa bilang apa.
_AI_LAST = case((Message.sender_type == "ai", 0), else_=1)


def _recent_messages(db: Session, conversation_id: str, limit: int) -> list[Message]:
    """N pesan terakhir, sudah diurutkan dari lama ke baru."""
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.sent_at.desc(), _AI_LAST.asc())
        .limit(limit)
        .all()
    )
    messages.reverse()  # urutkan lagi dari lama ke baru
    return messages


def get_recent_visitor_questions(
    db: Session, conversation_id: str, max_questions: int = 2
) -> list[str]:
    """
    Pertanyaan-pertanyaan terakhir dari pengunjung saja.

    Dipakai buat retrieval, BUKAN buat prompt. Pertanyaan lanjutan yang elipsis
    ("kalau ke sesama?") kalau di-embed sendirian skornya jeblok dan tidak nyambung
    ke chunk mana pun - perlu ditempeli pertanyaan sebelumnya biar ketemu.
    """
    recent = _recent_messages(db, conversation_id, max_questions * 4)
    questions = [m.content for m in recent if m.sender_type == "visitor"]
    return questions[-max_questions:]


def get_history_as_text(db: Session, conversation_id: str, max_turns: int = 10) -> str:
    """Ambil N pesan terakhir dari MySQL, format jadi teks siap pakai buat prompt LLM."""
    messages = _recent_messages(db, conversation_id, max_turns)

    if not messages:
        return ""

    lines = []
    for msg in messages:
        role = "Pengunjung" if msg.sender_type == "visitor" else "Asisten"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)


def update_conversation_status(db: Session, conversation_id: str, status: str) -> None:
    """Update status conversation - dipakai buat eskalasi ke agent (state machine)."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        conversation.status = status
        db.flush()      