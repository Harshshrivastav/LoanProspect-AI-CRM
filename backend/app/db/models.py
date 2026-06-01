"""
SQLAlchemy ORM models — single source of truth for the DB schema.
All tables live here so Base.metadata.create_all() creates everything.
"""

import uuid
from datetime import date, datetime

from app.db.database import Base
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


def _uid() -> str:
    return str(uuid.uuid4())


# ── customers ─────────────────────────────────────────────────────────────────
class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(10), default="M")
    city: Mapped[str] = mapped_column(String(60))
    occupation: Mapped[str] = mapped_column(String(80))
    employment_type: Mapped[str] = mapped_column(
        String(20)
    )  # salaried / self-employed / business
    annual_income: Mapped[float] = mapped_column(Float, default=0.0)
    credit_score_proxy: Mapped[int] = mapped_column(Integer, default=700)
    account_tenure_months: Mapped[int] = mapped_column(Integer, default=12)
    consent_marketing: Mapped[bool] = mapped_column(Boolean, default=True)
    last_contact_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    risk_segment: Mapped[str] = mapped_column(
        String(20), default="medium"
    )  # low/medium/high
    rm_assigned: Mapped[str] = mapped_column(String(20), default="RM-001")
    phone: Mapped[str] = mapped_column(String(15))
    email: Mapped[str] = mapped_column(String(120))
    kyc_status: Mapped[str] = mapped_column(String(20), default="verified")
    dependents: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # relationships
    accounts: Mapped[list["CustomerAccount"]] = relationship(back_populates="customer")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="customer")
    product_holdings: Mapped[list["ProductHolding"]] = relationship(
        back_populates="customer"
    )
    loan_signals: Mapped[list["LoanSignal"]] = relationship(back_populates="customer")
    outreach_history: Mapped[list["OutreachHistory"]] = relationship(
        back_populates="customer"
    )
    rm_notes: Mapped[list["RMNote"]] = relationship(back_populates="customer")


# ── customer_accounts ─────────────────────────────────────────────────────────
class CustomerAccount(Base):
    __tablename__ = "customer_accounts"

    account_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"))
    account_type: Mapped[str] = mapped_column(String(30))  # savings / current / salary
    opening_date: Mapped[date] = mapped_column(Date)
    current_balance: Mapped[float] = mapped_column(Float, default=0.0)
    avg_monthly_balance: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_inflow: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_outflow: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="active")

    customer: Mapped["Customer"] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")


# ── transactions ──────────────────────────────────────────────────────────────
class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(
        String(40), primary_key=True, default=_uid
    )
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"))
    account_id: Mapped[str] = mapped_column(ForeignKey("customer_accounts.account_id"))
    txn_date: Mapped[date] = mapped_column(Date)
    txn_type: Mapped[str] = mapped_column(String(10))  # credit / debit
    category: Mapped[str] = mapped_column(String(40))
    amount: Mapped[float] = mapped_column(Float)
    balance_after: Mapped[float] = mapped_column(Float)
    channel: Mapped[str] = mapped_column(String(30), default="upi")
    merchant_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)

    customer: Mapped["Customer"] = relationship(back_populates="transactions")
    account: Mapped["CustomerAccount"] = relationship(back_populates="transactions")


# ── product_holdings ──────────────────────────────────────────────────────────
class ProductHolding(Base):
    __tablename__ = "product_holdings"

    holding_id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uid)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"))
    product_type: Mapped[str] = mapped_column(String(40))
    product_status: Mapped[str] = mapped_column(String(20), default="active")
    outstanding_amount: Mapped[float] = mapped_column(Float, default=0.0)
    limit_amount: Mapped[float] = mapped_column(Float, default=0.0)
    emi_amount: Mapped[float] = mapped_column(Float, default=0.0)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="product_holdings")


# ── loan_signals ──────────────────────────────────────────────────────────────
class LoanSignal(Base):
    __tablename__ = "loan_signals"

    signal_id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uid)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"))
    signal_type: Mapped[str] = mapped_column(String(60))
    signal_value: Mapped[float] = mapped_column(Float, default=0.0)
    signal_source: Mapped[str] = mapped_column(String(40))
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    customer: Mapped["Customer"] = relationship(back_populates="loan_signals")


# ── outreach_history ──────────────────────────────────────────────────────────
class OutreachHistory(Base):
    __tablename__ = "outreach_history"

    outreach_id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uid)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"))
    campaign_id: Mapped[str | None] = mapped_column(
        ForeignKey("campaigns.campaign_id"), nullable=True
    )
    channel: Mapped[str] = mapped_column(String(20), default="whatsapp")
    message_text: Mapped[str] = mapped_column(Text)
    generated_by_agent: Mapped[str] = mapped_column(
        String(60), default="OutreachWriterAgent"
    )
    sent_status: Mapped[str] = mapped_column(String(20), default="draft")
    approved_by_rm: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    customer: Mapped["Customer"] = relationship(back_populates="outreach_history")
    campaign: Mapped["Campaign | None"] = relationship(
        back_populates="outreach_history"
    )


# ── campaigns ─────────────────────────────────────────────────────────────────
class Campaign(Base):
    __tablename__ = "campaigns"

    campaign_id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uid)
    campaign_name: Mapped[str] = mapped_column(String(120))
    product_type: Mapped[str] = mapped_column(String(40), default="personal_loan")
    segment_name: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    approved_by_rm: Mapped[bool] = mapped_column(Boolean, default=False)
    target_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    meta_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    outreach_history: Mapped[list["OutreachHistory"]] = relationship(
        back_populates="campaign"
    )


# ── rm_notes ──────────────────────────────────────────────────────────────────
class RMNote(Base):
    __tablename__ = "rm_notes"

    note_id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uid)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"))
    rm_id: Mapped[str] = mapped_column(String(20), default="RM-001")
    note_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    customer: Mapped["Customer"] = relationship(back_populates="rm_notes")


# ── audit_logs ────────────────────────────────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uid)
    actor_type: Mapped[str] = mapped_column(String(20))  # agent / user / system
    actor_name: Mapped[str] = mapped_column(String(80))
    action_type: Mapped[str] = mapped_column(String(40))
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    request_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


# ── chat_sessions ─────────────────────────────────────────────────────────────
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uid)
    title: Mapped[str] = mapped_column(String(200), default="New Conversation")
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    customer_context: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session")


# ── chat_messages ─────────────────────────────────────────────────────────────
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uid)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.session_id"))
    role: Mapped[str] = mapped_column(String(20))  # user / assistant
    content: Mapped[str] = mapped_column(Text)
    agent_steps: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    session: Mapped["ChatSession"] = relationship(back_populates="messages")


# ── app_settings ──────────────────────────────────────────────────────────────
class AppSetting(Base):
    __tablename__ = "app_settings"

    setting_key: Mapped[str] = mapped_column(String(80), primary_key=True)
    setting_value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


# ── plans ─────────────────────────────────────────────────────────────────────
class Plan(Base):
    __tablename__ = "plans"

    plan_id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uid)
    session_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    original_query: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="planning")  # planning / running / paused_hitl / completed / failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    steps: Mapped[list["ExecutionStep"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", order_by="ExecutionStep.step_number"
    )


# ── execution_steps ───────────────────────────────────────────────────────────
class ExecutionStep(Base):
    __tablename__ = "execution_steps"

    step_id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uid)
    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.plan_id"))
    step_number: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text)  # Change-of-Thought
    tool_name: Mapped[str] = mapped_column(String(80))
    tool_args: Mapped[str] = mapped_column(Text)  # JSON string
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending / running / success / failed / retrying
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    tool_result: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string or error
    hitl_required: Mapped[bool] = mapped_column(Boolean, default=False)
    hitl_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    hitl_payload_draft: Mapped[str | None] = mapped_column(Text, nullable=True)

    plan: Mapped["Plan"] = relationship(back_populates="steps")

