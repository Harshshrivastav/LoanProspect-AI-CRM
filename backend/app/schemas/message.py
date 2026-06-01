from typing import Optional

from pydantic import BaseModel


class GenerateMessageRequest(BaseModel):
    customer_id: str
    product_type: str = "personal_loan"
    tone: str = "friendly"
    channel: str = "whatsapp"


class BulkMessageRequest(BaseModel):
    customer_ids: list[str]
    product_type: str = "personal_loan"
    tone: str = "friendly"


class ApproveMessageRequest(BaseModel):
    outreach_id: str


class MessageResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    outreach_id: Optional[str] = None
    compliance: Optional[str] = None
    error: Optional[str] = None
