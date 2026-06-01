from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class AccountSchema(BaseModel):
    account_id: str
    account_type: str
    current_balance: float
    avg_monthly_balance: float
    monthly_inflow: float
    monthly_outflow: float
    status: str

    model_config = {"from_attributes": True}


class ProductHoldingSchema(BaseModel):
    holding_id: str
    product_type: str
    product_status: str
    outstanding_amount: float
    limit_amount: float
    emi_amount: float
    start_date: Optional[date]

    model_config = {"from_attributes": True}


class LoanSignalSchema(BaseModel):
    signal_id: str
    signal_type: str
    signal_value: float
    signal_source: str
    confidence_score: float
    detected_at: datetime

    model_config = {"from_attributes": True}


class RMNoteSchema(BaseModel):
    note_id: str
    rm_id: str
    note_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OutreachHistorySchema(BaseModel):
    outreach_id: str
    channel: str
    message_text: str
    generated_by_agent: str
    sent_status: str
    approved_by_rm: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerBriefSchema(BaseModel):
    customer_id: str
    full_name: str
    age: int
    gender: str
    city: str
    occupation: str
    employment_type: str
    annual_income: float
    credit_score_proxy: int
    account_tenure_months: int
    risk_segment: str
    consent_marketing: bool
    kyc_status: str

    model_config = {"from_attributes": True}


class CustomerDetailResponse(BaseModel):
    customer: dict
    accounts: List[dict]
    products: List[dict]
    signals: List[dict]
    rm_notes: List[dict]
    outreach_history: List[dict]
    transaction_summary: dict
    recent_transactions: List[dict]
