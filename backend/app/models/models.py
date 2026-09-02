"""
SQLAlchemy models - hasil terjemahan dari ERD (docs/erd_chatbot_aspripay_v2.mermaid).

Semua PK pakai UUID (string 36 char) sesuai ERD.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.db.session import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


# Junction table CONTACT <-> TAG (many-to-many)
contact_tag = Table(
    "contact_tag",
    Base.metadata,
    Column("contact_id", String(36), ForeignKey("contact.id"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("tag.id"), primary_key=True),
)


class Contact(Base):
    __tablename__ = "contact"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="contact")
    tags = relationship("Tag", secondary=contact_tag, back_populates="contacts")


class Tag(Base):
    __tablename__ = "tag"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    label = Column(String(100), nullable=False)

    contacts = relationship("Contact", secondary=contact_tag, back_populates="tags")


class Agent(Base):
    __tablename__ = "agent"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    role = Column(String(50), nullable=False, default="agent")

    conversations = relationship("Conversation", back_populates="agent")


class Conversation(Base):
    __tablename__ = "conversation"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    contact_id = Column(String(36), ForeignKey("contact.id"), nullable=False)
    agent_id = Column(String(36), ForeignKey("agent.id"), nullable=True)
    status = Column(String(50), default="ai-handling")
    # status: ai-handling | escalated | agent-handling | resolved (sesuai state machine di PRD)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    contact = relationship("Contact", back_populates="conversations")
    agent = relationship("Agent", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "message"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    conversation_id = Column(String(36), ForeignKey("conversation.id"), nullable=False)
    sender_type = Column(String(20), nullable=False)  # visitor | ai | agent
    content = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
    kb_chunk_refs = relationship("MessageKbChunkRef", back_populates="message")


class KnowledgeBaseDocument(Base):
    __tablename__ = "knowledge_base_document"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=True)  # txt | md | scraped, dst
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("KbChunk", back_populates="document")


class KbChunk(Base):
    __tablename__ = "kb_chunk"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    document_id = Column(String(36), ForeignKey("knowledge_base_document.id"), nullable=False)
    content = Column(Text, nullable=False)
    # NOTE: vector embedding-nya sendiri disimpan di Qdrant, bukan di sini.
    # Kolom ini cuma nyimpen teks aslinya buat referensi/audit.

    document = relationship("KnowledgeBaseDocument", back_populates="chunks")
    message_refs = relationship("MessageKbChunkRef", back_populates="kb_chunk")


class MessageKbChunkRef(Base):
    """Junction table MESSAGE <-> KB_CHUNK (many-to-many, nyimpen relevance_score)."""

    __tablename__ = "message_kb_chunk_ref"

    message_id = Column(String(36), ForeignKey("message.id"), primary_key=True)
    kb_chunk_id = Column(String(36), ForeignKey("kb_chunk.id"), primary_key=True)
    relevance_score = Column(Float, nullable=True)

    message = relationship("Message", back_populates="kb_chunk_refs")
    kb_chunk = relationship("KbChunk", back_populates="message_refs")


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    system_prompt = Column(Text, nullable=True)
    business_hours = Column(String(255), nullable=True)
    fallback_message = Column(Text, nullable=True)