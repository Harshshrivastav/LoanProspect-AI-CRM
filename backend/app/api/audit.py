from app.db.database import get_db_context
from app.db.repositories import audit_repo
from app.utils.logger import get_logger
from fastapi import APIRouter, Query

router = APIRouter(prefix="/audit", tags=["audit"])
logger = get_logger(__name__)


@router.get("")
def get_audit_logs(limit: int = Query(100, le=500), entity_id: str = Query(None)):
    """Returns audit log entries, optionally filtered by entity_id."""
    with get_db_context() as db:
        logs = audit_repo.get_audit_logs(db, limit=limit, entity_id=entity_id)
        return {
            "logs": [
                {
                    "audit_id": l.audit_id,
                    "actor_type": l.actor_type,
                    "actor_name": l.actor_name,
                    "action_type": l.action_type,
                    "entity_type": l.entity_type,
                    "entity_id": l.entity_id,
                    "tool_name": l.tool_name,
                    "created_at": str(l.created_at),
                }
                for l in logs
            ],
            "total": len(logs),
        }
