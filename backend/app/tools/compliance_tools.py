"""
Compliance validation tools — check marketing consent, KYC status, and
message content for prohibited terms before any outreach is sent.
"""

from datetime import datetime

from app.db.database import get_db_context
from app.db.repositories import customer_repo
from app.utils.logger import get_logger
from crewai.tools import tool

logger = get_logger(__name__)

# Phrases that must never appear in any customer-facing outreach
PROHIBITED_TERMS = [
    "guaranteed approval",
    "no credit check",
    "instant cash",
    "100% approval",
    "zero interest",
    "free loan",
    "no documentation",
]


@tool("validate_compliance")
def validate_compliance(customer_id: str, message_text: str = "") -> str:
    """
    Validates compliance for outreach to a customer.
    Checks: marketing consent, KYC status, message content safety, risk segment.
    Input: customer_id, message_text (optional — pass the draft message to check its content)
    Returns: compliance status with any warnings and blockers.
    """
    try:
        with get_db_context() as db:
            customer = customer_repo.get_customer_by_id(db, customer_id)
            if not customer:
                return f"COMPLIANCE CHECK FAILED: Customer {customer_id} not found."

            # Snapshot attributes before session closes
            full_name = customer.full_name
            consent_ok = customer.consent_marketing
            kyc_status = customer.kyc_status
            risk_segment = customer.risk_segment

        blocks: list[str] = []
        warnings: list[str] = []

        # ── Hard blocks ──────────────────────────────────────────────────────
        if not consent_ok:
            blocks.append(
                "🚫 BLOCK: No marketing consent — outreach not permitted under RBI guidelines"
            )
        if kyc_status != "verified":
            blocks.append(f"🚫 BLOCK: KYC not verified (current status: {kyc_status})")

        # ── Soft warnings ─────────────────────────────────────────────────────
        if risk_segment == "high":
            warnings.append(
                "⚠️ WARNING: High risk segment — requires senior RM review before sending"
            )
        elif risk_segment == "medium":
            warnings.append(
                "ℹ️ INFO: Medium risk segment — proceed with standard approval workflow"
            )

        # ── Message content check ─────────────────────────────────────────────
        if message_text:
            msg_lower = message_text.lower()
            for term in PROHIBITED_TERMS:
                if term.lower() in msg_lower:
                    blocks.append(f"🚫 BLOCK: Prohibited term detected: '{term}'")

        compliant = len(blocks) == 0
        status = "✅ COMPLIANT" if compliant else "❌ NON-COMPLIANT"

        blocks_list = "\n".join(f"- 🔴 **BLOCKER:** {b.replace('🚫 BLOCK: ', '')}" for b in blocks) if blocks else "- ✅ *No active blockers*"
        warnings_list = "\n".join(f"- ⚠️ **WARNING:** {w.replace('⚠️ WARNING: ', '').replace('ℹ️ INFO: ', '')}" for w in warnings) if warnings else "- ✅ *No policy warnings*"

        lines = [
            f"### 🛡️ Compliance Audit: **{full_name}** (`{customer_id}`)",
            "",
            "| Audit Parameter | Verification Status |",
            "|:---|:---|",
            f"| **Overall Compliance State** | **{status}** |",
            f"| **Audit Execution Time** | `{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}` |",
            "",
            "#### 🚫 Policy Blocker Items",
            blocks_list,
            "",
            "#### ⚠️ Policy Warnings & Flags",
            warnings_list,
            "",
        ]
        if compliant:
            lines.append("> 🟢 **Audit Sign-off:** All regulatory and internal compliance checks passed. This customer is fully approved for outreach messaging.")
        else:
            lines.append("> 🔴 **Audit Suspension:** Hard blockers detected. Outreach campaign dispatch is strictly suspended until these issues are resolved in the core CRM.")

        clean_status = "COMPLIANT" if compliant else "NON-COMPLIANT"
        logger.info(f"validate_compliance: {customer_id} -> {clean_status}")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"validate_compliance error: {e}")
        return f"Compliance check error for {customer_id}: {str(e)}"



@tool("get_compliance_summary")
def get_compliance_summary(customer_id: str) -> str:
    """
    Returns a brief compliance status for a customer (no message content check).
    Input: customer_id
    """
    try:
        return validate_compliance(customer_id=customer_id, message_text="")
    except Exception as e:
        return f"Error getting compliance summary: {str(e)}"
