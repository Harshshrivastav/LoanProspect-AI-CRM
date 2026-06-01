"""
Scoring service — thin adapter between the scoring engine and the API layer.
Returns plain dicts so the API layer can serialize them however it needs.
"""

import dataclasses

from app.db.database import get_db_context
from app.db.repositories import customer_repo
from app.tools.scoring_tools import ProspectScore, _score_customer, set_dynamic_factors
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Global in-memory score cache and active dynamic decision state
_SCORES_CACHE: list[dict] = []
_ACTIVE_FACTORS = {
    "campaign_focus": "general",
    "risk_appetite": "moderate"
}

def get_active_factors() -> dict:
    return _ACTIVE_FACTORS

def recalculate_scores(focus: str = "general", risk: str = "moderate") -> list[dict]:
    """
    Recalculates prospect scores dynamically under the chosen campaign focus and risk appetite appetite.
    Caches the results so that future requests are lightning-fast.
    """
    global _SCORES_CACHE, _ACTIVE_FACTORS
    _ACTIVE_FACTORS["campaign_focus"] = focus
    _ACTIVE_FACTORS["risk_appetite"] = risk

    # Set parameters inside the underwriting engine
    set_dynamic_factors(focus, risk)

    with get_db_context() as db:
        # Pull up to 200 customers to rank
        customers = customer_repo.get_all_customers(db, skip=0, limit=200)
        customer_ids = [c.customer_id for c in customers]

    prospects: list[dict] = []
    for cid in customer_ids:
        try:
            score: ProspectScore = _score_customer(cid)
            prospects.append(dataclasses.asdict(score))
        except Exception as e:
            logger.warning(f"recalculate_scores: skipping {cid} — {e}")

    prospects.sort(key=lambda x: x["readiness_score"], reverse=True)
    _SCORES_CACHE = prospects
    return _SCORES_CACHE

def get_all_prospects(limit: int = 50) -> list[dict]:
    """
    Returns ranked prospects instantly from the dynamic cache.
    If the cache is empty, triggers a default recalculation job first.
    """
    global _SCORES_CACHE
    if not _SCORES_CACHE:
        recalculate_scores(_ACTIVE_FACTORS["campaign_focus"], _ACTIVE_FACTORS["risk_appetite"])
    return _SCORES_CACHE[:limit]



def score_single_customer(customer_id: str) -> dict:
    """
    Scores one customer and returns the result as a plain dict.
    Raises ValueError if the customer does not exist.
    """
    score = _score_customer(customer_id)
    if score.full_name == "Unknown":
        raise ValueError(f"Customer {customer_id} not found.")
    return dataclasses.asdict(score)


def get_high_intent_prospects(limit: int = 20) -> list[dict]:
    """Returns only 'high' conversion-band prospects, ranked by score."""
    all_prospects = get_all_prospects(limit=500)
    high = [p for p in all_prospects if p["conversion_band"] == "high"]
    return high[:limit]


def get_portfolio_summary() -> dict:
    """
    Returns a portfolio-level summary of prospect distribution across bands.
    """
    all_prospects = get_all_prospects(limit=500)
    high = [p for p in all_prospects if p["conversion_band"] == "high"]
    medium = [p for p in all_prospects if p["conversion_band"] == "medium"]
    low = [p for p in all_prospects if p["conversion_band"] == "low"]

    avg_score = (
        sum(p["readiness_score"] for p in all_prospects) / len(all_prospects)
        if all_prospects
        else 0
    )

    return {
        "total_scored": len(all_prospects),
        "high_intent_count": len(high),
        "medium_intent_count": len(medium),
        "low_intent_count": len(low),
        "avg_readiness_score": round(avg_score, 1),
        "top_5_prospects": [
            {
                "customer_id": p["customer_id"],
                "full_name": p["full_name"],
                "readiness_score": p["readiness_score"],
                "conversion_band": p["conversion_band"],
            }
            for p in all_prospects[:5]
        ],
    }
