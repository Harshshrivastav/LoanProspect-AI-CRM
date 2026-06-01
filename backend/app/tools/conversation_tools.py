"""
Chat session management tools — create sessions and persist messages.
Used by the orchestration layer to maintain conversation history.
"""

import uuid

from app.db.database import get_db_context
from app.db.models import ChatMessage, ChatSession
from app.utils.logger import get_logger
from crewai.tools import tool
from sqlalchemy import select

logger = get_logger(__name__)


@tool("list_chat_sessions")
def list_chat_sessions() -> str:
    """
    Returns all active (non-archived) chat sessions, newest first.
    Shows session ID, title, pinned status, and last-updated timestamp.
    """
    try:
        with get_db_context() as db:
            stmt = (
                select(ChatSession)
                .where(ChatSession.is_archived == False)  # noqa: E712
                .order_by(ChatSession.updated_at.desc())
            )
            sessions = list(db.execute(stmt).scalars().all())
            # Snapshot inside session
            session_dicts = [
                {
                    "session_id": s.session_id,
                    "title": s.title,
                    "is_pinned": s.is_pinned,
                    "context": s.customer_context or "",
                    "updated_at": (
                        s.updated_at.strftime("%Y-%m-%d %H:%M")
                        if s.updated_at
                        else "N/A"
                    ),
                }
                for s in sessions
            ]

        if not session_dicts:
            return (
                "No active chat sessions found. Use create_chat_session to start one."
            )

        lines = [f"ACTIVE CHAT SESSIONS ({len(session_dicts)})", "=" * 60]
        for s in session_dicts:
            pin_icon = "📌 " if s["is_pinned"] else "   "
            ctx_label = f" [ctx: {s['context']}]" if s["context"] else ""
            lines.append(
                f"  {pin_icon}{s['session_id'][:8]}... | "
                f"{s['title'][:40]:<40} | {s['updated_at']}{ctx_label}"
            )

        logger.info(f"list_chat_sessions: returned {len(session_dicts)} sessions")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"list_chat_sessions error: {e}")
        return f"Error listing chat sessions: {str(e)}"


@tool("create_chat_session")
def create_chat_session(
    title: str = "New Conversation",
    customer_context: str = "",
) -> str:
    """
    Creates a new chat session. Returns the session_id for use in subsequent calls.
    Input: title (default: 'New Conversation'),
           customer_context (optional — e.g. 'CUST001' to associate with a customer)
    """
    try:
        session_id = str(uuid.uuid4())

        with get_db_context() as db:
            session = ChatSession(
                session_id=session_id,
                title=title,
                customer_context=customer_context.strip() or None,
            )
            db.add(session)
            db.flush()
            created_at = session.created_at.isoformat() if session.created_at else "N/A"

        result = (
            f"Chat session created.\n"
            f"  Session ID : {session_id}\n"
            f"  Title      : {title}\n"
            f"  Context    : {customer_context or 'None'}\n"
            f"  Created At : {created_at}"
        )
        logger.info(f"create_chat_session: created {session_id}")
        return result
    except Exception as e:
        logger.error(f"create_chat_session error: {e}")
        return f"Error creating chat session: {str(e)}"


@tool("save_chat_message")
def save_chat_message(session_id: str, role: str, content: str) -> str:
    """
    Saves a message to an existing chat session.
    Input: session_id (from create_chat_session),
           role ('user' | 'assistant'),
           content (the message text)
    """
    try:
        message_id = str(uuid.uuid4())

        with get_db_context() as db:
            # Verify session exists
            session = db.get(ChatSession, session_id)
            if not session:
                return f"Chat session {session_id} not found."

            message = ChatMessage(
                message_id=message_id,
                session_id=session_id,
                role=role,
                content=content,
            )
            db.add(message)
            db.flush()
            created_at = message.created_at.isoformat() if message.created_at else "N/A"

        result = (
            f"Message saved.\n"
            f"  Message ID : {message_id}\n"
            f"  Session    : {session_id}\n"
            f"  Role       : {role}\n"
            f"  Created At : {created_at}\n"
            f"  Preview    : {content[:80]}{'...' if len(content) > 80 else ''}"
        )
        logger.info(
            f"save_chat_message: saved message {message_id} to session {session_id}"
        )
        return result
    except Exception as e:
        logger.error(f"save_chat_message error: {e}")
        return f"Error saving chat message: {str(e)}"
