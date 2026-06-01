"""
Customer service — assembles rich customer detail dicts for the API layer.
All ORM attribute access happens inside the DB session; only plain Python
types are returned.
"""

from app.db.database import get_db_context
from app.db.repositories import customer_repo, transaction_repo
from app.utils.helpers import days_ago, fmt_inr
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_customer_detail(customer_id: str) -> dict:
    """
    Returns a comprehensive customer detail dict for the client portal.
    Includes: profile, accounts, products, loan signals, notes,
              outreach history, recent transactions, and tx summary.
    Returns {} if the customer is not found.
    """
    with get_db_context() as db:
        customer = customer_repo.get_customer_by_id(db, customer_id)
        if not customer:
            return {}

        accounts = customer_repo.get_customer_accounts(db, customer_id)
        products = customer_repo.get_product_holdings(db, customer_id)
        signals = customer_repo.get_loan_signals(db, customer_id)
        notes = customer_repo.get_rm_notes(db, customer_id)
        outreach = customer_repo.get_outreach_history(db, customer_id)
        txns = transaction_repo.get_transactions_by_customer(db, customer_id, days=180)
        tx_summary = transaction_repo.get_transaction_summary(db, customer_id, days=90)

        # Build the full response dict inside the session while ORM objects are live
        result = {
            "customer": {
                "customer_id": customer.customer_id,
                "full_name": customer.full_name,
                "age": customer.age,
                "gender": customer.gender,
                "city": customer.city,
                "occupation": customer.occupation,
                "employment_type": customer.employment_type,
                "annual_income": customer.annual_income,
                "annual_income_fmt": fmt_inr(customer.annual_income),
                "credit_score_proxy": customer.credit_score_proxy,
                "account_tenure_months": customer.account_tenure_months,
                "consent_marketing": customer.consent_marketing,
                "risk_segment": customer.risk_segment,
                "rm_assigned": customer.rm_assigned,
                "phone": customer.phone,
                "email": customer.email,
                "kyc_status": customer.kyc_status,
                "dependents": customer.dependents,
                "last_contact_date": (
                    customer.last_contact_date.isoformat()
                    if customer.last_contact_date
                    else None
                ),
                "days_since_contact": (
                    days_ago(customer.last_contact_date)
                    if customer.last_contact_date
                    else None
                ),
            },
            "accounts": [
                {
                    "account_id": a.account_id,
                    "account_type": a.account_type,
                    "current_balance": a.current_balance,
                    "current_balance_fmt": fmt_inr(a.current_balance),
                    "avg_monthly_balance": a.avg_monthly_balance,
                    "avg_monthly_balance_fmt": fmt_inr(a.avg_monthly_balance),
                    "monthly_inflow": a.monthly_inflow,
                    "monthly_inflow_fmt": fmt_inr(a.monthly_inflow),
                    "monthly_outflow": a.monthly_outflow,
                    "monthly_outflow_fmt": fmt_inr(a.monthly_outflow),
                    "status": a.status,
                    "opening_date": (
                        a.opening_date.isoformat() if a.opening_date else None
                    ),
                }
                for a in accounts
            ],
            "products": [
                {
                    "holding_id": p.holding_id,
                    "product_type": p.product_type,
                    "product_status": p.product_status,
                    "outstanding_amount": p.outstanding_amount,
                    "outstanding_amount_fmt": fmt_inr(p.outstanding_amount),
                    "limit_amount": p.limit_amount,
                    "limit_amount_fmt": fmt_inr(p.limit_amount),
                    "emi_amount": p.emi_amount,
                    "emi_amount_fmt": fmt_inr(p.emi_amount),
                    "start_date": (p.start_date.isoformat() if p.start_date else None),
                }
                for p in products
            ],
            "loan_signals": [
                {
                    "signal_id": s.signal_id,
                    "signal_type": s.signal_type,
                    "signal_value": s.signal_value,
                    "signal_source": s.signal_source,
                    "confidence_score": s.confidence_score,
                    "detected_at": (
                        s.detected_at.isoformat() if s.detected_at else None
                    ),
                }
                for s in signals
            ],
            "rm_notes": [
                {
                    "note_id": n.note_id,
                    "rm_id": n.rm_id,
                    "note_text": n.note_text,
                    "created_at": (n.created_at.isoformat() if n.created_at else None),
                }
                for n in notes
            ],
            "outreach_history": [
                {
                    "outreach_id": o.outreach_id,
                    "channel": o.channel,
                    "message_text": o.message_text,
                    "sent_status": o.sent_status,
                    "approved_by_rm": o.approved_by_rm,
                    "campaign_id": o.campaign_id,
                    "created_at": (o.created_at.isoformat() if o.created_at else None),
                }
                for o in outreach
            ],
            "recent_transactions": [
                {
                    "transaction_id": t.transaction_id,
                    "txn_date": t.txn_date.isoformat() if t.txn_date else None,
                    "txn_type": t.txn_type,
                    "category": t.category,
                    "amount": t.amount,
                    "amount_fmt": fmt_inr(t.amount),
                    "balance_after": t.balance_after,
                    "channel": t.channel,
                    "merchant_name": t.merchant_name,
                    "description": t.description,
                    "is_recurring": t.is_recurring,
                }
                for t in txns[:50]  # cap at 50 most recent
            ],
            "transaction_summary": tx_summary,  # plain dict — already safe
        }

    logger.info(f"get_customer_detail: assembled detail for {customer_id}")
    return result


def get_customers_list(page: int = 1, per_page: int = 20) -> dict:
    """
    Returns a paginated list of customers with key attributes.
    """
    skip = (page - 1) * per_page
    with get_db_context() as db:
        customers = customer_repo.get_all_customers(db, skip=skip, limit=per_page)
        customer_list = [_customer_to_dict(c) for c in customers]

    return {
        "customers": customer_list,
        "page": page,
        "per_page": per_page,
        "count": len(customer_list),
    }


def search_customers(query: str) -> list[dict]:
    """Searches customers by name, city, occupation, email, or phone."""
    with get_db_context() as db:
        customers = customer_repo.search_customers(db, query)
        return [_customer_to_dict(c) for c in customers]


def _customer_to_dict(c) -> dict:
    """Converts a Customer ORM instance to a plain dict (must be called inside session)."""
    return {
        "customer_id": c.customer_id,
        "full_name": c.full_name,
        "age": c.age,
        "gender": c.gender,
        "city": c.city,
        "occupation": c.occupation,
        "employment_type": c.employment_type,
        "annual_income": c.annual_income,
        "annual_income_fmt": fmt_inr(c.annual_income),
        "risk_segment": c.risk_segment,
        "credit_score_proxy": c.credit_score_proxy,
        "consent_marketing": c.consent_marketing,
        "kyc_status": c.kyc_status,
        "account_tenure_months": c.account_tenure_months,
        "rm_assigned": c.rm_assigned,
    }
