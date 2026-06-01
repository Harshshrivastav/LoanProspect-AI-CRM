"""
Audit repository — structured event logging for agent/user/system actions.
"""

import json
import uuid
from typing import Any, Optional

from app.db.models import AuditLog
from sqlalchemy import select
from sqlalchemy.orm import Session


def log_event(
    db: Session,
    actor_type: str,
    actor_name: str,
    action_type: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    request_payload: Optional[dict[str, Any]] = None,
    response_payload: Optional[dict[str, Any]] = None,
    tool_name: Optional[str] = None,
) -> AuditLog:
    entry = AuditLog(
        audit_id=str(uuid.uuid4()),
        actor_type=actor_type,
        actor_name=actor_name,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        request_payload=json.dumps(request_payload) if request_payload else None,
        response_payload=json.dumps(response_payload) if response_payload else None,
        tool_name=tool_name,
    )
    db.add(entry)
    db.flush()
    return entry


def get_audit_logs(
    db: Session,
    limit: int = 100,
    entity_id: Optional[str] = None,
) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())
