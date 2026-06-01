"""
Message service — orchestrates compliance checking, message generation,
approval, and audit logging in one place for the API layer.
"""

from app.db.database import get_db_context
from app.db.repositories import campaign_repo
from app.tools.audit_tools import log_audit_event
from app.tools.compliance_tools import validate_compliance
from app.tools.outreach_tools import generate_whatsapp_message
from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_message(
    customer_id: str,
    product_type: str = "personal_loan",
    tone: str = "friendly",
    channel: str = "whatsapp",
) -> dict:
    """
    Generates a personalized outreach message for a customer after first
    verifying compliance.

    Returns:
        { "success": bool, "message": str, "compliance": str, "error"?: str }
    """
    # 1. Compliance gate — hard-stop if any block exists
    compliance_result = validate_compliance(customer_id=customer_id, message_text="")
    if "BLOCK" in compliance_result:
        logger.warning(f"generate_message: compliance block for {customer_id}")
        return {
            "success": False,
            "error": "Compliance check failed — see compliance field for details",
            "compliance": compliance_result,
        }

    # 2. Generate the message
    try:
        message_result = generate_whatsapp_message(
            customer_id=customer_id,
            product_type=product_type,
            tone=tone,
        )
    except Exception as e:
        logger.error(f"generate_message: generation error for {customer_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "compliance": compliance_result,
        }

    # 3. Audit trail
    try:
        log_audit_event(
            actor_type="agent",
            actor_name="OutreachWriterAgent",
            action_type="message_generated",
            entity_type="customer",
            entity_id=customer_id,
            tool_name="generate_whatsapp_message",
        )
    except Exception as e:
        logger.warning(f"generate_message: audit log failed (non-fatal): {e}")

    return {
        "success": True,
        "message": message_result,
        "compliance": compliance_result,
    }


def approve_message(outreach_id: str) -> dict:
    """
    Marks an outreach record as RM-approved and updates status to 'sent'.

    Returns:
        { "success": bool, "outreach_id": str, "status": str }  on success
        { "success": False, "error": str }                       on failure
    """
    try:
        with get_db_context() as db:
            outreach = campaign_repo.approve_outreach(db, outreach_id)
            # outreach is still live inside the session
            oid = outreach.outreach_id
            status = outreach.sent_status

        try:
            log_audit_event(
                actor_type="user",
                actor_name="RM",
                action_type="message_approved",
                entity_type="outreach",
                entity_id=oid,
                tool_name="approve_outreach",
            )
        except Exception as e:
            logger.warning(f"approve_message: audit log failed (non-fatal): {e}")

        return {"success": True, "outreach_id": oid, "status": status}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"approve_message error: {e}")
        return {"success": False, "error": str(e)}


def get_pending_outreach(customer_id: str | None = None) -> list[dict]:
    """
    Returns a list of outreach records that are in 'draft' status
    (pending RM approval), optionally filtered by customer.
    """
    from app.db.models import OutreachHistory
    from sqlalchemy import select

    with get_db_context() as db:
        stmt = select(OutreachHistory).where(
            OutreachHistory.sent_status == "draft",
            OutreachHistory.approved_by_rm == False,  # noqa: E712
        )
        if customer_id:
            stmt = stmt.where(OutreachHistory.customer_id == customer_id)
        stmt = stmt.order_by(OutreachHistory.created_at.desc())
        records = list(db.execute(stmt).scalars().all())

        return [
            {
                "outreach_id": r.outreach_id,
                "customer_id": r.customer_id,
                "channel": r.channel,
                "message_text": r.message_text,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]
