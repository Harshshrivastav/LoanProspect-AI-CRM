from typing import List

from pydantic import BaseModel


class ProspectScoreResponse(BaseModel):
    customer_id: str
    full_name: str
    readiness_score: int
    conversion_band: str
    confidence: float
    positive_signals: List[str]
    risk_flags: List[str]
    recommendation_reason: str
    next_best_action: str
    suggested_product: str
    recommended_channel: str
    loan_fit_factors: List[str]
    score_breakdown: dict


class ScoreRequest(BaseModel):
    customer_id: str


class ProspectsListResponse(BaseModel):
    prospects: List[ProspectScoreResponse]
    total: int


class DynamicDecisionRequest(BaseModel):
    campaign_focus: str
    risk_appetite: str

