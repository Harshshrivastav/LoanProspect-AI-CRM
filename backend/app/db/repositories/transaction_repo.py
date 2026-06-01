"""
Transaction repository — queries for transaction data and summaries.
"""

from datetime import date, timedelta
from typing import Any

from app.db.models import Transaction
from sqlalchemy import select
from sqlalchemy.orm import Session


def get_transactions_by_customer(
    db: Session,
    customer_id: str,
    days: int = 180,
) -> list[Transaction]:
    since = date.today() - timedelta(days=days)
    stmt = (
        select(Transaction)
        .where(
            Transaction.customer_id == customer_id,
            Transaction.txn_date >= since,
        )
        .order_by(Transaction.txn_date.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_transactions_by_category(
    db: Session,
    customer_id: str,
    category: str,
) -> list[Transaction]:
    stmt = (
        select(Transaction)
        .where(
            Transaction.customer_id == customer_id,
            Transaction.category == category,
        )
        .order_by(Transaction.txn_date.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_transaction_summary(
    db: Session,
    customer_id: str,
    days: int = 90,
) -> dict[str, Any]:
    """
    Returns:
        {
            total_credit: float,
            total_debit: float,
            by_category: {category: {count, total}},
            large_txns: [list of txn dicts with amount >= 50 000],
            salary_months: int,
        }
    """
    since = date.today() - timedelta(days=days)
    stmt = select(Transaction).where(
        Transaction.customer_id == customer_id,
        Transaction.txn_date >= since,
    )
    txns = list(db.execute(stmt).scalars().all())

    total_credit = sum(t.amount for t in txns if t.txn_type == "credit")
    total_debit = sum(t.amount for t in txns if t.txn_type == "debit")

    by_category: dict[str, dict[str, Any]] = {}
    for t in txns:
        bucket = by_category.setdefault(t.category, {"count": 0, "total": 0.0})
        bucket["count"] += 1
        bucket["total"] = round(bucket["total"] + t.amount, 2)

    large_txns = [
        {
            "transaction_id": t.transaction_id,
            "txn_date": str(t.txn_date),
            "category": t.category,
            "txn_type": t.txn_type,
            "amount": t.amount,
            "merchant_name": t.merchant_name,
            "description": t.description,
        }
        for t in txns
        if t.amount >= 50_000
    ]

    salary_months = len(
        {
            t.txn_date.month
            for t in txns
            if t.txn_type == "credit" and t.category == "salary"
        }
    )

    return {
        "total_credit": round(total_credit, 2),
        "total_debit": round(total_debit, 2),
        "by_category": by_category,
        "large_txns": large_txns,
        "salary_months": salary_months,
    }


def get_recent_large_transactions(
    db: Session,
    customer_id: str,
    min_amount: float = 50_000,
) -> list[Transaction]:
    stmt = (
        select(Transaction)
        .where(
            Transaction.customer_id == customer_id,
            Transaction.amount >= min_amount,
        )
        .order_by(Transaction.txn_date.desc())
        .limit(50)
    )
    return list(db.execute(stmt).scalars().all())
