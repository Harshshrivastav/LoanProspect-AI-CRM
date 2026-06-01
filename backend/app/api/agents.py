import os

from app.config import settings
from app.utils.logger import get_logger
from fastapi import APIRouter

router = APIRouter(prefix="/agent", tags=["agents"])
logger = get_logger(__name__)


@router.get("/status")
def agent_status():
    """Returns the current status and configuration of all CrewAI agents and crews."""
    return {
        "status": "ready",
        "framework": "CrewAI",
        "llm": f"gemini/{settings.gemini_model}",
        "api_key_set": bool(settings.gemini_api_key),
        "agents": [
            {
                "name": "ProspectDiscoveryAgent",
                "status": "ready",
                "tools": [
                    "list_customers_brief",
                    "rank_personal_loan_prospects",
                    "fetch_customer_profile",
                ],
            },
            {
                "name": "EvidenceAggregationAgent",
                "status": "ready",
                "tools": [
                    "fetch_customer_profile",
                    "fetch_transaction_summary",
                    "detect_life_event_spends",
                    "calculate_cashflow_trend",
                ],
            },
            {
                "name": "LoanReadinessAgent",
                "status": "ready",
                "tools": ["compute_loan_readiness_score", "get_prospect_explanation"],
            },
            {
                "name": "OutreachWriterAgent",
                "status": "ready",
                "tools": ["generate_whatsapp_message", "generate_bulk_messages"],
            },
            {
                "name": "ComplianceAgent",
                "status": "ready",
                "tools": ["validate_compliance", "get_compliance_summary"],
            },
            {
                "name": "CampaignCoordinatorAgent",
                "status": "ready",
                "tools": [
                    "get_top_prospect_ids_for_campaign",
                    "create_campaign_payload",
                    "rank_personal_loan_prospects",
                ],
            },
        ],
        "crews": [
            {"name": "ProspectAnalysisCrew", "agents": 4, "process": "sequential"},
            {"name": "BulkOutreachCrew", "agents": 3, "process": "sequential"},
            {
                "name": "ConversationCrew",
                "agents": 3,
                "process": "sequential",
                "streaming": True,
            },
        ],
    }


from pydantic import BaseModel

class AgentConfigUpdate(BaseModel):
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"

@router.post("/config")
def update_config(req: AgentConfigUpdate):
    """Update LLM configuration at runtime."""
    os.environ["GEMINI_API_KEY"] = req.gemini_api_key
    os.environ["GEMINI_MODEL"] = req.gemini_model
    settings.gemini_api_key = req.gemini_api_key
    settings.gemini_model = req.gemini_model
    return {"status": "updated", "model": f"gemini/{req.gemini_model}", "api_key_set": True}

