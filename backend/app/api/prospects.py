from app.agents.crews import run_prospect_analysis_crew
from app.schemas.prospect import ScoreRequest, DynamicDecisionRequest
from app.services.scoring_service import get_all_prospects, score_single_customer, get_active_factors, recalculate_scores
from app.utils.logger import get_logger
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/prospects", tags=["prospects"])
logger = get_logger(__name__)


@router.get("")
def list_prospects(limit: int = 20):
    """Returns all customers ranked by personal loan readiness score."""
    return {"prospects": get_all_prospects(limit=limit)}


@router.get("/factors")
def read_dynamic_factors():
    """Returns the current active dynamic scoring factors."""
    return get_active_factors()


@router.post("/recalculate")
def trigger_recalculate(req: DynamicDecisionRequest):
    """Triggers a dynamic rescoring job across the portfolio."""
    logger.info(f"Recalculating scores for focus: {req.campaign_focus}, risk: {req.risk_appetite}")
    recalculated = recalculate_scores(focus=req.campaign_focus, risk=req.risk_appetite)
    return {
        "status": "success",
        "message": f"Scores recalculated for focus: {req.campaign_focus}, risk: {req.risk_appetite}",
        "prospects": recalculated[:20]
    }



@router.get("/{customer_id}")
def get_prospect(customer_id: str):
    """Returns detailed prospect scoring for one customer."""
    return score_single_customer(customer_id.upper())


@router.post("/score")
def score_customer(req: ScoreRequest):
    """Scores a specific customer for loan readiness."""
    return score_single_customer(req.customer_id.upper())


@router.post("/analyze/{customer_id}")
def analyze_customer_with_crew(customer_id: str):
    """Runs the full 4-agent ProspectAnalysisCrew for a customer. May take 30-60s."""
    return run_prospect_analysis_crew(customer_id.upper())
