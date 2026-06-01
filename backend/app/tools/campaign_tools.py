"""
Campaign management tools — create campaigns, check status, and surface
the best customer IDs to target.
"""

from app.db.database import get_db_context
from app.db.repositories import campaign_repo, customer_repo
from app.tools.scoring_tools import _score_customer
from app.utils.logger import get_logger
from crewai.tools import tool

logger = get_logger(__name__)


@tool("create_campaign_payload")
def create_campaign_payload(
    campaign_name: str,
    target_customer_ids_csv: str,
    product_type: str = "personal_loan",
    segment_name: str = "high_intent_prospects",
) -> str:
    """
    Creates a new outreach campaign in the system with the specified customers.
    Input: campaign_name, target_customer_ids_csv (comma-separated),
           product_type (default: personal_loan), segment_name (default: high_intent_prospects)
    """
    try:
        ids = [x.strip() for x in target_customer_ids_csv.split(",") if x.strip()]
        if not ids:
            return "Error: No valid customer IDs provided in target_customer_ids_csv."

        with get_db_context() as db:
            campaign = campaign_repo.create_campaign(
                db,
                name=campaign_name,
                product=product_type,
                segment=segment_name,
                target_ids=ids,
            )
            campaign_id = campaign.campaign_id
            target_count = campaign.target_count
            status = campaign.status
            product_label = campaign.product_type.replace("_", " ").title()

        preview_ids = ", ".join(f"`{x}`" for x in ids[:5]) + ("..." if len(ids) > 5 else "")
        result = (
            f"### ✅ Campaign Successfully Created\n\n"
            f"| Campaign Parameter | Settings / Details |\n"
            f"|:---|:---|\n"
            f"| **Campaign ID** | `{campaign_id}` |\n"
            f"| **Campaign Name** | **{campaign_name}** |\n"
            f"| **Product Offering** | `{product_label}` |\n"
            f"| **Target Segment** | `{segment_name}` |\n"
            f"| **Target Customer Count** | **{target_count}** customer(s) |\n"
            f"| **Current Status** | 📋 **{status.upper()}** |\n"
            f"| **Target Profile IDs** | {preview_ids} |\n\n"
            f"> 📢 **Outreach Compliance Action Step:** Please request the Relationship Manager to review and approve this campaign before executing the message dispatcher.\n"
            f"> \n"
            f"> **Approval Campaign Token:** `{campaign_id}`"
        )
        logger.info(
            f"create_campaign_payload: created campaign {campaign_id} with {target_count} targets"
        )
        return result
    except Exception as e:
        logger.error(f"create_campaign_payload error: {e}")
        return f"Error creating campaign: {str(e)}"


@tool("get_campaign_status_summary")
def get_campaign_status_summary() -> str:
    """Returns a summary of all campaigns and their current status."""
    try:
        with get_db_context() as db:
            campaigns = campaign_repo.get_all_campaigns(db)
            # Build plain-dict list inside session
            camp_dicts = [
                {
                    "id": c.campaign_id[:8],
                    "name": c.campaign_name[:35],
                    "product": c.product_type,
                    "status": c.status,
                    "approved": c.approved_by_rm,
                    "targets": c.target_count,
                    "success": c.success_count,
                    "created": c.created_at.strftime("%Y-%m-%d")
                    if c.created_at
                    else "N/A",
                }
                for c in campaigns
            ]

        if not camp_dicts:
            return "No campaigns found in the system. Use `create_campaign_payload` to start one."

        lines = [
            f"### 📢 Campaign Status Summary (Total: {len(camp_dicts)})",
            "",
            "| Campaign ID | Campaign Name | Product | Status | Targets | Successes | Approval State |",
            "|---|:---|:---|:---:|:---:|:---:|:---:|",
        ]
        for c in camp_dicts:
            approved_icon = "✅ Approved" if c["approved"] else "⏳ Awaiting Review"
            lines.append(
                f"| `{c['id']}` | **{c['name']}** | `{c['product'].replace('_', ' ').title()}` | **{c['status'].upper()}** | {c['targets']} | {c['success']} | {approved_icon} |"
            )

        active = sum(1 for c in camp_dicts if c["status"] == "active")
        draft = sum(1 for c in camp_dicts if c["status"] == "draft")
        closed = sum(1 for c in camp_dicts if c["status"] not in ("active", "draft"))

        lines += [
            "",
            f"> 📊 **Status Snapshot**: 🟢 Active: **{active}** | 📝 Draft: **{draft}** | 🔒 Closed: **{closed}** | Total Campaign Entities: **{len(camp_dicts)}**",
        ]
        logger.info(
            f"get_campaign_status_summary: returned {len(camp_dicts)} campaigns"
        )
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"get_campaign_status_summary error: {e}")
        return f"Error fetching campaign summary: {str(e)}"


@tool("get_top_prospect_ids_for_campaign")
def get_top_prospect_ids_for_campaign(limit: int = 10) -> str:
    """
    Returns the top customer IDs ranked by personal loan readiness score.
    Only includes customers who have marketing consent (outreach-eligible).
    Use the returned CSV directly in create_campaign_payload.
    Input: limit (default 10)
    """
    try:
        with get_db_context() as db:
            all_customers = customer_repo.get_all_customers(db, skip=0, limit=500)
            # Only consider customers with marketing consent
            eligible_ids = [c.customer_id for c in all_customers if c.consent_marketing]

        scored = []
        for cid in eligible_ids:
            try:
                s = _score_customer(cid)
                scored.append(s)
            except Exception as err:
                logger.warning(f"Skipping {cid} in campaign ranking: {err}")

        scored.sort(key=lambda x: x.readiness_score, reverse=True)
        top = scored[:limit]

        if not top:
            return (
                "No eligible high/medium-intent prospects found. "
                "Check that customers have marketing consent enabled."
            )

        ids_csv = ", ".join(s.customer_id for s in top)

        lines = [
            f"### 🎯 Top {len(top)} Prospects for Campaign Targeting",
            "",
            "| Rank | Customer ID | Name | Readiness Score | Intent Band | Primary Behavioral Trigger |",
            "|---|:---|:---|:---:|:---:|:---|",
        ]
        for i, s in enumerate(top, 1):
            key_signal = s.positive_signals[0] if s.positive_signals else "—"
            band_emoji = "🔥 HIGH" if s.conversion_band == "high" else ("⚡ MEDIUM" if s.conversion_band == "medium" else "🔵 LOW")
            lines.append(
                f"| **{i}** | `{s.customer_id}` | **{s.full_name}** | **{s.readiness_score}/100** | {band_emoji} | {key_signal} |"
            )

        lines += [
            "",
            "#### 📝 Copy-Paste CSV Target IDs",
            "Use the following comma-separated list directly as the input target ID list in `create_campaign_payload`:",
            f"```text\n{ids_csv}\n```",
        ]
        logger.info(
            f"get_top_prospect_ids_for_campaign: found {len(top)} targets from {len(eligible_ids)} eligible"
        )
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"get_top_prospect_ids_for_campaign error: {e}")
        return f"Error fetching top prospects: {str(e)}"
