from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    audit_id: str
    actor_type: str
    actor_name: str
    action_type: str
    entity_type: str
    entity_id: Optional[str]
    tool_name: Optional[str]
    created_at: str
    request_payload: Optional[str]
    response_payload: Optional[str]
