"""
Chat service — full CRUD for chat sessions and message persistence.
All ORM attribute access happens inside the DB session.
"""

import json
import uuid

from app.db.database import get_db_context
from app.db.models import ChatMessage, ChatSession
from app.utils.logger import get_logger
from sqlalchemy import select

logger = get_logger(__name__)


# ── Session management ────────────────────────────────────────────────────────


def get_all_sessions() -> list[dict]:
    """Returns all non-archived sessions, newest-updated first."""
    with get_db_context() as db:
        stmt = (
            select(ChatSession)
            .where(ChatSession.is_archived == False)  # noqa: E712
            .order_by(ChatSession.updated_at.desc())
        )
        sessions = list(db.execute(stmt).scalars().all())
        return [_session_to_dict(s) for s in sessions]


def create_session(
    title: str = "New Conversation",
    customer_context: str | None = None,
) -> dict:
    """Creates a new chat session and returns its dict."""
    with get_db_context() as db:
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            title=title,
            customer_context=customer_context,
        )
        db.add(session)
        db.flush()
        result = _session_to_dict(session)
    logger.info(f"create_session: {result['session_id']}")
    return result


def get_session_messages(session_id: str) -> list[dict]:
    """Returns all messages in a session in chronological order."""
    with get_db_context() as db:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = list(db.execute(stmt).scalars().all())
        return [_message_to_dict(m) for m in messages]


def rename_session(session_id: str, title: str) -> dict:
    """Renames a session. Returns the updated session dict, or {} if not found."""
    with get_db_context() as db:
        session = db.get(ChatSession, session_id)
        if not session:
            return {}
        session.title = title
        db.flush()
        result = _session_to_dict(session)
    logger.info(f"rename_session: {session_id} → '{title}'")
    return result


def archive_session(session_id: str) -> dict:
    """Archives a session (soft delete). Returns updated session dict."""
    with get_db_context() as db:
        session = db.get(ChatSession, session_id)
        if not session:
            return {}
        session.is_archived = True
        db.flush()
        result = _session_to_dict(session)
    logger.info(f"archive_session: {session_id}")
    return result


def pin_session(session_id: str, pinned: bool) -> dict:
    """Pins or unpins a session. Returns updated session dict."""
    with get_db_context() as db:
        session = db.get(ChatSession, session_id)
        if not session:
            return {}
        session.is_pinned = pinned
        db.flush()
        result = _session_to_dict(session)
    logger.info(f"pin_session: {session_id} → pinned={pinned}")
    return result


def delete_session(session_id: str) -> bool:
    """
    Permanently deletes a session and all its messages.
    Returns True on success, False if the session was not found.
    """
    with get_db_context() as db:
        session = db.get(ChatSession, session_id)
        if not session:
            return False
        # Delete child messages first to respect FK constraint
        msg_stmt = select(ChatMessage).where(ChatMessage.session_id == session_id)
        messages = list(db.execute(msg_stmt).scalars().all())
        for msg in messages:
            db.delete(msg)
        db.delete(session)
        db.flush()
    logger.info(f"delete_session: {session_id} (deleted {len(messages)} messages)")
    return True


def save_message(
    session_id: str,
    role: str,
    content: str,
    agent_steps: list | None = None,
) -> dict:
    """
    Saves a message to a session. Returns the saved message dict.
    Returns {} if the session does not exist.
    """
    with get_db_context() as db:
        session = db.get(ChatSession, session_id)
        if not session:
            return {}
        message = ChatMessage(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            agent_steps=json.dumps(agent_steps) if agent_steps else None,
        )
        db.add(message)
        db.flush()
        result = _message_to_dict(message)
    logger.info(
        f"save_message: {result['message_id']} in session {session_id} (role={role})"
    )
    return result


def get_session_with_messages(session_id: str) -> dict:
    """
    Returns a single session dict with its messages embedded.
    Returns {} if the session does not exist.
    """
    with get_db_context() as db:
        session = db.get(ChatSession, session_id)
        if not session:
            return {}
        session_dict = _session_to_dict(session)

        msg_stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = list(db.execute(msg_stmt).scalars().all())
        session_dict["messages"] = [_message_to_dict(m) for m in messages]

    return session_dict


# ── Serializers ───────────────────────────────────────────────────────────────


def _session_to_dict(s: ChatSession) -> dict:
    """Converts a ChatSession ORM instance to a plain dict (call inside session)."""
    return {
        "session_id": s.session_id,
        "title": s.title,
        "is_pinned": s.is_pinned,
        "is_archived": s.is_archived,
        "customer_context": s.customer_context,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _message_to_dict(m: ChatMessage) -> dict:
    """Converts a ChatMessage ORM instance to a plain dict (call inside session)."""
    agent_steps: list = []
    if m.agent_steps:
        try:
            agent_steps = json.loads(m.agent_steps)
        except (json.JSONDecodeError, TypeError):
            agent_steps = []

    return {
        "message_id": m.message_id,
        "session_id": m.session_id,
        "role": m.role,
        "content": m.content,
        "agent_steps": agent_steps,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }
