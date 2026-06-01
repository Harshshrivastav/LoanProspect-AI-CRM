"""
Campaign repository — campaigns and outreach record management.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from app.db.models import Campaign, OutreachHistory
from sqlalchemy import select
from sqlalchemy.orm import Session

# ── Campaign queries ──────────────────────────────────────────────────────────


def get_all_campaigns(db: Session) -> list[Campaign]:
    stmt = select(Campaign).order_by(Campaign.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def get_campaign_by_id(db: Session, campaign_id: str) -> Optional[Campaign]:
    return db.get(Campaign, campaign_id)


def create_campaign(
    db: Session,
    name: str,
    product: str,
    segment: str,
    target_ids: list[str],
) -> Campaign:
    campaign = Campaign(
        campaign_id=str(uuid.uuid4()),
        campaign_name=name,
        product_type=product,
        segment_name=segment,
        status="draft",
        approved_by_rm=False,
        target_count=len(target_ids),
        success_count=0,
        meta_json=json.dumps({"target_customer_ids": target_ids}),
    )
    db.add(campaign)
    db.flush()
    return campaign


def approve_campaign(db: Session, campaign_id: str) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise ValueError(f"Campaign {campaign_id!r} not found")
    campaign.approved_by_rm = True
    campaign.status = "active"
    db.flush()
    return campaign


# ── Outreach ──────────────────────────────────────────────────────────────────


def create_outreach(
    db: Session,
    customer_id: str,
    message: str,
    campaign_id: Optional[str] = None,
    channel: str = "whatsapp",
) -> OutreachHistory:
    outreach = OutreachHistory(
        outreach_id=str(uuid.uuid4()),
        customer_id=customer_id,
        campaign_id=campaign_id,
        channel=channel,
        message_text=message,
        generated_by_agent="OutreachWriterAgent",
        sent_status="draft",
        approved_by_rm=False,
    )
    db.add(outreach)
    db.flush()
    return outreach


def approve_outreach(db: Session, outreach_id: str) -> OutreachHistory:
    outreach = db.get(OutreachHistory, outreach_id)
    if outreach is None:
        raise ValueError(f"Outreach {outreach_id!r} not found")
    outreach.approved_by_rm = True
    outreach.sent_status = "sent"
    db.flush()
    return outreach
