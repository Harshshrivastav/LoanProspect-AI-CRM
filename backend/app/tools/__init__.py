# Tool registry — export all tool functions used by CrewAI agents.
from app.tools.audit_tools import get_audit_trail, log_audit_event
from app.tools.campaign_tools import (
    create_campaign_payload,
    get_campaign_status_summary,
    get_top_prospect_ids_for_campaign,
)
from app.tools.compliance_tools import get_compliance_summary, validate_compliance
from app.tools.conversation_tools import (
    create_chat_session,
    list_chat_sessions,
    save_chat_message,
)
from app.tools.customer_tools import (
    fetch_customer_profile,
    get_customer_risk_summary,
    list_customers_brief,
)
from app.tools.outreach_tools import generate_bulk_messages, generate_whatsapp_message
from app.tools.scoring_tools import (
    compute_loan_readiness_score,
    get_prospect_explanation,
    rank_personal_loan_prospects,
)
from app.tools.transaction_tools import (
    calculate_cashflow_trend,
    detect_life_event_spends,
    fetch_transaction_summary,
)

__all__ = [
    # customer
    "fetch_customer_profile",
    "list_customers_brief",
    "get_customer_risk_summary",
    # transaction
    "fetch_transaction_summary",
    "detect_life_event_spends",
    "calculate_cashflow_trend",
    # scoring
    "compute_loan_readiness_score",
    "rank_personal_loan_prospects",
    "get_prospect_explanation",
    # outreach
    "generate_whatsapp_message",
    "generate_bulk_messages",
    # compliance
    "validate_compliance",
    "get_compliance_summary",
    # campaign
    "create_campaign_payload",
    "get_campaign_status_summary",
    "get_top_prospect_ids_for_campaign",
    # audit
    "log_audit_event",
    "get_audit_trail",
    # conversation
    "list_chat_sessions",
    "create_chat_session",
    "save_chat_message",
]
