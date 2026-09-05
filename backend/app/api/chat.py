"""Endpoint chat - terima pesan pengunjung, jalankan RAG pipeline, simpan ke MySQL, return jawaban."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.answer_menu import extract_menu_items, normalize_list_answer
from app.core.auth import verify_api_key
from app.db.session import get_db
from app.rag.indexing import get_document_store
from app.rag.query_pipeline import (
    AnswerKind,
    LOW_CONFIDENCE_MESSAGE,
    build_query_pipeline,
    ask,
)
from app.memory.graph_query import ask_graph
from app.services import chat_service

# Semua endpoint di router ini wajib kirim header X-API-Key yang valid
router = APIRouter(dependencies=[Depends(verify_api_key)])

# Document store & pipeline di-build sekali saat startup, bukan per-request
_document_store = get_document_store()
_engine = build_query_pipeline(_document_store)

_COGNEE_EMPTY_MARKERS = (
    "tidak tahu",
    "tidak ada informasi",
    "tidak ditemukan",
    "no information",
    "i don't know",
    "cannot answer",
    "no relevant",
)


def _is_usable_graph_answer(text: str) -> bool:
    """Jawaban Cognee dianggap kepakai kalau isinya beneran ada dan bukan pengakuan tidak tahu."""
    cleaned = (text or "").strip()
    if len(cleaned) < 15:
        return False
    lowered = cleaned.lower()
    return not any(marker in lowered for marker in _COGNEE_EMPTY_MARKERS)


_LOW_CONFIDENCE_OPTIONS = [
    {"label": "Hubungkan ke CS", "action": "contact_agent"},
    {"label": "Sudah jelas, terima kasih", "action": "dismiss"},
]


class ChatRequest(BaseModel):
    conversation_id: str
    message: str


class EscalateRequest(BaseModel):
    conversation_id: str


class FollowupOption(BaseModel):
    label: str
    action: str  # "contact_agent" | "dismiss"


class QuickReply(BaseModel):
    """Satu tombol menu. `detail` sudah berisi jawabannya, jadi tidak perlu round-trip."""

    label: str
    detail: str


class ChatResponse(BaseModel):
    answer: str
    confidence_score: float
    should_escalate: bool
    source_chunk_ids: list[str]
    # "haystack" | "cognee" | "small_talk" | "out_of_scope" | "fallback" - transparansi/debug
    answered_by: str
    # Kalau jawabannya kurang yakin: pesan + tombol pilihan buat pengunjung.
    # Kosong artinya tidak perlu ditawari apa-apa.
    followup_message: str | None = None
    followup_options: list[FollowupOption] = []
    # Jawaban berbentuk daftar dipecah jadi tombol biar tidak jadi tembok teks.
    # Kosong artinya jawabannya ditampilkan biasa.
    quick_replies: list[QuickReply] = []


@router.get("/init")
def init_conversation():
    """Dipanggil widget saat pertama kali load di web klien - generate conversation_id baru."""
    return {"conversation_id": str(uuid.uuid4())}


@router.post("/message", response_model=ChatResponse)
def send_message(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Terima pesan pengunjung -> pastikan conversation ada -> ambil histori dari MySQL
    -> jalankan RAG (Haystack+Qdrant) -> tentukan jenis jawabannya -> simpan pesan+jawaban
    ke MySQL -> update status kalau harus eskalasi -> return jawaban.

    Tiga cabang, sesuai AnswerKind:
      - GROUNDED     -> jawab dari KB.
      - OUT_OF_SCOPE -> pertanyaannya bukan soal aspripay. Tolak sopan, JANGAN dieskalasi
                        dan JANGAN dilempar ke Cognee. Bot ini bukan asisten serbaguna.
      - NO_ANSWER    -> soal aspripay tapi KB belum punya. Baru di sini Cognee dicoba
                        sebagai sumber kedua; kalau tetap nihil, eskalasi ke agent.

    PENTING soal halusinasi: Cognee GRAPH_COMPLETION itu LLM juga, jadi kalau ditanya
    di luar topik ("makan apa hari ini?") dia tetap ngarang jawaban dengan percaya diri.
    Makanya dia cuma dipanggil untuk NO_ANSWER, dan hasilnya masih divalidasi dulu lewat
    _is_usable_graph_answer sebelum dipercaya.

    Sesuai flowchart & state machine di PRD:
    ai-handling -> escalated (kalau kedua sumber tidak yakin) -> agent-handling -> resolved.
    """
    chat_service.get_or_create_conversation(db, payload.conversation_id)

    history_text = chat_service.get_history_as_text(db, payload.conversation_id)
    # Dipisah dari history_text: yang ini buat retrieval (nempel ke query embedding),
    # history_text buat prompt. Tanpa ini pertanyaan lanjutan macam "kalau ke sesama?"
    # skor retrieval-nya nol dan salah divonis di luar topik.
    context_questions = chat_service.get_recent_visitor_questions(db, payload.conversation_id)

    result = ask(
        _engine,
        question=payload.message,
        history=history_text,
        context_questions=context_questions,
    )
    final_should_escalate = result.should_escalate

    if result.kind == AnswerKind.GROUNDED:
        answered_by = "haystack"
    elif result.kind == AnswerKind.SMALL_TALK:
        answered_by = "small_talk"
    elif result.kind == AnswerKind.OUT_OF_SCOPE:
        answered_by = "out_of_scope"
    else:
        answered_by = "fallback"

    # Fallback ke Cognee HANYA buat pertanyaan yang masih soal aspripay.
    if result.kind == AnswerKind.NO_ANSWER:
        try:
            graph_answer = ask_graph(payload.message)
        except Exception:
            graph_answer = ""

        if _is_usable_graph_answer(graph_answer):
            result.answer = graph_answer
            answered_by = "cognee"
            final_should_escalate = False

    # Jawaban kurang yakin TIDAK dibuang lagi. Dulu diganti pesan eskalasi, padahal
    # datanya ada dan jawabannya benar - pengunjung jadi dilempar ke agent percuma.
    # Sekarang jawabannya tetap dikirim, ditambah tawaran menghubungi CS. Eskalasi
    # baru terjadi kalau pengunjung sendiri menekan tombolnya (endpoint /escalate).
    followup_message = None
    followup_options: list[FollowupOption] = []
    if result.low_confidence:
        followup_message = LOW_CONFIDENCE_MESSAGE
        followup_options = [FollowupOption(**opt) for opt in _LOW_CONFIDENCE_OPTIONS]

    # Jawaban berbentuk daftar diseragamkan jadi format bernomor. Perlu dilakukan di
    # sini karena Cognee punya prompt sendiri yang tidak bisa kita atur lewat aturan 9.
    # Tidak ada isi yang dibuang - cuma disusun ulang; kalau bukan daftar, dikembalikan
    # apa adanya. Tombolnya pintasan tambahan buat daftar panjang, bukan pengganti teks.
    result.answer = normalize_list_answer(result.answer)
    quick_replies = [
        QuickReply(label=i.label, detail=i.body) for i in extract_menu_items(result.answer)
    ]

    # Simpan pesan pengunjung
    chat_service.save_message(db, payload.conversation_id, "visitor", payload.message)
    chat_service.save_message(
        db, payload.conversation_id, "ai", result.answer, confidence_score=result.confidence_score
    )

    if final_should_escalate:
        chat_service.update_conversation_status(db, payload.conversation_id, "escalated")

    db.commit()

    return ChatResponse(
        answer=result.answer,
        confidence_score=result.confidence_score,
        should_escalate=final_should_escalate,
        # jawaban dari Cognee tidak bersandar ke chunk Qdrant, jadi jangan klaim sumbernya
        source_chunk_ids=result.source_chunks if answered_by == "haystack" else [],
        answered_by=answered_by,
        followup_message=followup_message,
        followup_options=followup_options,
        quick_replies=quick_replies,
    )


@router.post("/escalate")
def escalate(payload: EscalateRequest, db: Session = Depends(get_db)):
    """
    Eskalasi atas permintaan pengunjung sendiri - dipanggil waktu tombol
    "Hubungkan ke CS" ditekan.

    Dipisah dari /message supaya eskalasi jadi keputusan sadar pengunjung, bukan
    efek samping dari skor retrieval yang kebetulan rendah.
    """
    chat_service.get_or_create_conversation(db, payload.conversation_id)
    # Dicatat sebagai pesan visitor biar agent tahu konteks kenapa dia dipanggil
    chat_service.save_message(
        db, payload.conversation_id, "visitor", "[Pengunjung meminta dihubungkan ke CS]"
    )
    chat_service.update_conversation_status(db, payload.conversation_id, "escalated")
    db.commit()
    return {"status": "escalated", "conversation_id": payload.conversation_id}