"""
Campaign service — wraps campaign repository calls and adds
scoring-based targeting for the API layer.
"""

import json

from app.db.database import get_db_context
from app.db.repositories import campaign_repo, customer_repo
from app.tools.scoring_tools import _score_customer
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_all_campaigns() -> list[dict]:
    """Returns all campaigns as plain dicts, newest first."""
    with get_db_context() as db:
        campaigns = campaign_repo.get_all_campaigns(db)
        return [_campaign_to_dict(c) for c in campaigns]


def get_campaign_detail(campaign_id: str) -> dict:
    """Returns a single campaign detail dict, or {} if not found."""
    with get_db_context() as db:
        campaign = campaign_repo.get_campaign_by_id(db, campaign_id)
        if not campaign:
            return {}
        return _campaign_to_dict(campaign)


def create_campaign(
    name: str,
    product: str,
    segment: str,
    target_ids: list[str],
) -> dict:
    """Creates a new campaign and returns its dict representation."""
    with get_db_context() as db:
        campaign = campaign_repo.create_campaign(
            db,
            name=name,
            product=product,
            segment=segment,
            target_ids=target_ids,
        )
        result = _campaign_to_dict(campaign)
    logger.info(
        f"create_campaign: {result['campaign_id']} ({name}) with {len(target_ids)} targets"
    )
    return result


def approve_campaign(campaign_id: str) -> dict:
    """
    Marks a campaign as approved by RM and activates it.
    Returns { "success": True, "campaign": dict } or { "success": False, "error": str }.
    """
    try:
        with get_db_context() as db:
            campaign = campaign_repo.approve_campaign(db, campaign_id)
            result = _campaign_to_dict(campaign)
        logger.info(f"approve_campaign: {campaign_id} approved")
        return {"success": True, "campaign": result}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"approve_campaign error: {e}")
        return {"success": False, "error": str(e)}


def get_auto_target_ids(product: str = "personal_loan", limit: int = 10) -> list[str]:
    """
    Uses the scoring engine to surface the best targets for a new campaign.
    Returns a list of customer IDs with marketing consent and high/medium readiness.
    """
    with get_db_context() as db:
        customers = customer_repo.get_all_customers(db, skip=0, limit=500)
        eligible_ids = [c.customer_id for c in customers if c.consent_marketing]

    scored = []
    for cid in eligible_ids:
        try:
            s = _score_customer(cid)
            if s.conversion_band in ("high", "medium"):
                scored.append(s)
        except Exception as e:
            logger.warning(f"get_auto_target_ids: skipping {cid} — {e}")

    scored.sort(key=lambda x: x.readiness_score, reverse=True)
    return [s.customer_id for s in scored[:limit]]


def create_auto_campaign(
    name: str,
    product: str = "personal_loan",
    segment: str = "ai_selected_prospects",
    target_limit: int = 10,
) -> dict:
    """
    Convenience method: automatically picks the best targets using the scoring
    engine, then creates and returns a new campaign.
    """
    target_ids = get_auto_target_ids(product=product, limit=target_limit)
    if not target_ids:
        return {
            "success": False,
            "error": "No eligible prospects found for auto-targeting",
        }

    result = create_campaign(
        name=name,
        product=product,
        segment=segment,
        target_ids=target_ids,
    )
    return {"success": True, "campaign": result, "target_ids": target_ids}


def _campaign_to_dict(c) -> dict:
    """Converts a Campaign ORM instance to a plain dict (must be called inside session)."""
    return {
        "campaign_id": c.campaign_id,
        "campaign_name": c.campaign_name,
        "product_type": c.product_type,
        "segment_name": c.segment_name,
        "status": c.status,
        "approved_by_rm": c.approved_by_rm,
        "target_count": c.target_count,
        "success_count": c.success_count,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "meta": json.loads(c.meta_json) if c.meta_json else {},
    }
