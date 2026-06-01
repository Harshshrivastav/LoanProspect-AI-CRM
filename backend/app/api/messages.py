from app.schemas.message import (
    ApproveMessageRequest,
    BulkMessageRequest,
    GenerateMessageRequest,
)
from app.services.message_service import approve_message, generate_message
from app.utils.logger import get_logger
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/message", tags=["messages"])
logger = get_logger(__name__)


@router.post("/generate")
def generate(req: GenerateMessageRequest):
    """Generates a personalized outreach message for a single customer."""
    return generate_message(req.customer_id, req.product_type, req.tone, req.channel)


@router.post("/bulk")
def bulk_generate(req: BulkMessageRequest):
    """Generates personalized outreach messages for up to 5 customers."""
    results = []
    for cid in req.customer_ids[:5]:
        result = generate_message(cid, req.product_type, req.tone, "whatsapp")
        results.append({"customer_id": cid, **result})
    return {"messages": results, "count": len(results)}


@router.post("/approve")
def approve(req: ApproveMessageRequest):
    """Marks an outreach record as RM-approved."""
    result = approve_message(req.outreach_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Outreach record not found")
    return result
