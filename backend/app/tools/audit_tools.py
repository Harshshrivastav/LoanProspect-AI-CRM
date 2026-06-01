"""
Audit trail tools — log agent/RM actions and retrieve structured audit history.
"""

from app.db.database import get_db_context
from app.db.repositories import audit_repo
from app.utils.logger import get_logger
from crewai.tools import tool

logger = get_logger(__name__)


@tool("log_audit_event")
def log_audit_event(
    actor_type: str,
    actor_name: str,
    action_type: str,
    entity_type: str,
    entity_id: str = "",
    tool_name: str = "",
) -> str:
    """
    Logs an agent or user action to the structured audit trail.
    Call this after every significant agent decision or tool use.
    Input: actor_type (agent|user|system), actor_name, action_type,
           entity_type (customer|campaign|outreach), entity_id (optional),
           tool_name (optional — the tool that triggered this event)
    """
    try:
        with get_db_context() as db:
            entry = audit_repo.log_event(
                db,
                actor_type=actor_type,
                actor_name=actor_name,
                action_type=action_type,
                entity_type=entity_type,
                entity_id=entity_id.strip() or None,
                tool_name=tool_name.strip() or None,
            )
            audit_id = entry.audit_id

        result = (
            f"Audit event logged.\n"
            f"  Audit ID    : {audit_id}\n"
            f"  Actor       : {actor_name} ({actor_type})\n"
            f"  Action      : {action_type}\n"
            f"  Entity      : {entity_type} {entity_id or '(global)'}\n"
            f"  Tool        : {tool_name or 'N/A'}"
        )
        logger.info(
            f"log_audit_event: {audit_id} — {actor_type}/{actor_name} → {action_type}"
        )
        return result
    except Exception as e:
        logger.error(f"log_audit_event error: {e}")
        return f"Error logging audit event: {str(e)}"


@tool("get_audit_trail")
def get_audit_trail(entity_id: str = "", limit: int = 50) -> str:
    """
    Returns the formatted audit trail for a specific entity or all recent events.
    Input: entity_id (optional — e.g. 'CUST001' to filter by customer),
           limit (default 50)
    """
    try:
        eid_filter = entity_id.strip() or None

        with get_db_context() as db:
            logs = audit_repo.get_audit_logs(db, limit=limit, entity_id=eid_filter)
            # Snapshot to plain dicts inside session
            log_dicts = [
                {
                    "audit_id": entry.audit_id[:8],
                    "actor_type": entry.actor_type,
                    "actor_name": entry.actor_name,
                    "action_type": entry.action_type,
                    "entity_type": entry.entity_type,
                    "entity_id": entry.entity_id or "",
                    "tool_name": entry.tool_name or "",
                    "created_at": (
                        entry.created_at.strftime("%Y-%m-%d %H:%M")
                        if entry.created_at
                        else "N/A"
                    ),
                }
                for entry in logs
            ]

        if not log_dicts:
            scope = f" for entity '{eid_filter}'" if eid_filter else ""
            return f"No audit logs found{scope}."

        scope_label = f" — filtered by: {eid_filter}" if eid_filter else ""
        lines = [
            f"AUDIT TRAIL ({len(log_dicts)} events{scope_label})",
            "=" * 70,
            f"  {'Time':<17} | {'Actor':<28} | {'Action':<22} | Entity",
            "  " + "-" * 85,
        ]
        for log in log_dicts:
            actor = f"{log['actor_name'][:22]} ({log['actor_type']})"
            entity = f"{log['entity_type']} {log['entity_id']}".strip()
            lines.append(
                f"  {log['created_at']:<17} | {actor:<28} | "
                f"{log['action_type']:<22} | {entity}"
            )
            if log["tool_name"]:
                lines.append(f"  {'':17}   └── Tool: {log['tool_name']}")

        logger.info(f"get_audit_trail: returned {len(log_dicts)} entries")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"get_audit_trail error: {e}")
        return f"Error fetching audit trail: {str(e)}"
