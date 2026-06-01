from app.agents.crews import run_bulk_outreach_crew
from app.schemas.campaign import (
    ApproveCampaignRequest,
    BulkOutreachRequest,
    CreateCampaignRequest,
)
from app.services.campaign_service import (
    approve_campaign,
    create_campaign,
    get_all_campaigns,
    get_campaign_detail,
)
from app.utils.logger import get_logger
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/campaigns", tags=["campaigns"])
logger = get_logger(__name__)


@router.get("")
def list_campaigns():
    """Returns all campaigns."""
    return {"campaigns": get_all_campaigns()}


@router.get("/{campaign_id}")
def get_campaign(campaign_id: str):
    """Returns detail for a single campaign."""
    detail = get_campaign_detail(campaign_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return detail


@router.post("")
def create_new_campaign(req: CreateCampaignRequest):
    """Creates a new campaign with a pre-selected list of target customers."""
    return create_campaign(
        name=req.campaign_name,
        product=req.product_type,
        segment=req.segment_name,
        target_ids=req.target_customer_ids,
    )


@router.post("/approve")
def approve(req: ApproveCampaignRequest):
    """Approves a campaign for execution."""
    result = approve_campaign(req.campaign_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Campaign not found")
    return result


@router.post("/run-bulk-outreach")
def run_bulk(req: BulkOutreachRequest):
    """Runs the BulkOutreachCrew to discover prospects, validate compliance, and generate messages."""
    return run_bulk_outreach_crew(req.campaign_name, req.product_type, req.target_count)
