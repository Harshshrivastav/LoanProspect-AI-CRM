from app.db.database import get_db_context
from app.db.repositories import transaction_repo
from app.utils.logger import get_logger
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/transactions", tags=["transactions"])
logger = get_logger(__name__)


@router.get("/{customer_id}")
def get_transactions(customer_id: str, days: int = 90):
    """Returns transaction history for a customer."""
    with get_db_context() as db:
        txns = transaction_repo.get_transactions_by_customer(
            db, customer_id.upper(), days=days
        )
        summary = transaction_repo.get_transaction_summary(
            db, customer_id.upper(), days=days
        )

    return {
        "customer_id": customer_id.upper(),
        "days": days,
        "summary": summary,
        "transactions": [
            {
                "transaction_id": t.transaction_id,
                "txn_date": str(t.txn_date),
                "txn_type": t.txn_type,
                "category": t.category,
                "amount": t.amount,
                "balance_after": t.balance_after,
                "merchant_name": t.merchant_name,
                "description": t.description,
                "channel": t.channel,
                "is_recurring": t.is_recurring,
            }
            for t in txns
        ],
    }
