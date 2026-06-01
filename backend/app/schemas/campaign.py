from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class CampaignResponse(BaseModel):
    campaign_id: str
    campaign_name: str
    product_type: str
    segment_name: str
    status: str
    approved_by_rm: bool
    target_count: int
    success_count: int
    created_at: Optional[str]
    meta: dict = {}


class CreateCampaignRequest(BaseModel):
    campaign_name: str
    product_type: str = "personal_loan"
    segment_name: str = "high_intent_prospects"
    target_customer_ids: List[str]


class ApproveCampaignRequest(BaseModel):
    campaign_id: str


class BulkOutreachRequest(BaseModel):
    campaign_name: str
    product_type: str = "personal_loan"
    target_count: int = 5
