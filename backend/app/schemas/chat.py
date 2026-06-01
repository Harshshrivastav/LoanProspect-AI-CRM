from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ChatSessionResponse(BaseModel):
    session_id: str
    title: str
    is_pinned: bool
    is_archived: bool
    customer_context: Optional[str]
    created_at: str
    updated_at: str
    message_count: int = 0


class ChatMessageResponse(BaseModel):
    message_id: str
    session_id: str
    role: str
    content: str
    agent_steps: Optional[list]
    created_at: str


class CreateSessionRequest(BaseModel):
    title: str = "New Conversation"
    customer_context: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    customer_context: Optional[str] = None
    mode: Optional[str] = "auto"  # auto / plan_only / direct


class ApprovePlanRequest(BaseModel):
    plan_id: str
    approved: bool
    edited_steps: Optional[list] = None


class RenameSessionRequest(BaseModel):
    title: str


class RunCrewRequest(BaseModel):
    customer_id: str

