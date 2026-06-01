"""
Customer repository — all DB queries related to customers and their sub-entities.
Includes Levenshtein-based fuzzy name matching for typo-tolerant search.
"""

import uuid
from typing import Optional

from app.db.models import (
    Customer,
    CustomerAccount,
    LoanSignal,
    OutreachHistory,
    ProductHolding,
    RMNote,
)
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

# ── Levenshtein distance (pure Python, no external deps) ─────────────────────


def _levenshtein(a: str, b: str) -> int:
    """Computes the Levenshtein edit distance between two strings."""
    if len(a) < len(b):
        return _levenshtein(b, a)
    if len(b) == 0:
        return len(a)
    prev_row = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr_row = [i + 1]
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr_row.append(min(
                curr_row[j] + 1,       # insert
                prev_row[j + 1] + 1,   # delete
                prev_row[j] + cost     # replace
            ))
        prev_row = curr_row
    return prev_row[-1]


def _similarity_score(query: str, full_name: str) -> float:
    """
    Computes a 0.0–1.0 similarity score between a query string and a customer's
    full name. Checks both the full name and individual name tokens (first, last)
    and returns the best (highest) score found.
    """
    q = query.lower().strip()
    name = full_name.lower().strip()

    # Score against full name
    max_len = max(len(q), len(name), 1)
    full_score = 1.0 - (_levenshtein(q, name) / max_len)

    # Score against individual tokens (first name, last name, etc.)
    best_token_score = 0.0
    for token in name.split():
        token_max = max(len(q), len(token), 1)
        token_score = 1.0 - (_levenshtein(q, token) / token_max)
        best_token_score = max(best_token_score, token_score)

    return max(full_score, best_token_score)


# ── Customer lookups ──────────────────────────────────────────────────────────


def get_customer_by_id(db: Session, customer_id: str) -> Optional[Customer]:
    return db.get(Customer, customer_id)


def get_all_customers(db: Session, skip: int = 0, limit: int = 100) -> list[Customer]:
    stmt = select(Customer).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def search_customers(db: Session, query: str) -> list[Customer]:
    pattern = f"%{query}%"
    stmt = (
        select(Customer)
        .where(
            or_(
                Customer.full_name.ilike(pattern),
                Customer.city.ilike(pattern),
                Customer.occupation.ilike(pattern),
                Customer.email.ilike(pattern),
                Customer.phone.ilike(pattern),
            )
        )
        .limit(50)
    )
    return list(db.execute(stmt).scalars().all())


def fuzzy_search_customers(
    db: Session, query: str, min_score: float = 0.45, top_n: int = 5
) -> list[tuple[Customer, float]]:
    """
    Fuzzy-matches a query (possibly a misspelled name like 'Vitram') against
    ALL customer full names using Levenshtein edit distance.
    Returns a list of (Customer, similarity_score) tuples sorted best-first.
    Only includes matches with score >= min_score.
    """
    all_customers = list(db.execute(select(Customer)).scalars().all())
    scored: list[tuple[Customer, float]] = []
    for c in all_customers:
        score = _similarity_score(query, c.full_name)
        if score >= min_score:
            scored.append((c, round(score, 3)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]


def get_customers_by_city(db: Session, city: str) -> list[Customer]:
    stmt = select(Customer).where(Customer.city.ilike(city))
    return list(db.execute(stmt).scalars().all())


# ── Customer sub-entity lookups ───────────────────────────────────────────────


def get_customer_accounts(db: Session, customer_id: str) -> list[CustomerAccount]:
    stmt = select(CustomerAccount).where(CustomerAccount.customer_id == customer_id)
    return list(db.execute(stmt).scalars().all())


def get_product_holdings(db: Session, customer_id: str) -> list[ProductHolding]:
    stmt = select(ProductHolding).where(ProductHolding.customer_id == customer_id)
    return list(db.execute(stmt).scalars().all())


def get_loan_signals(db: Session, customer_id: str) -> list[LoanSignal]:
    stmt = (
        select(LoanSignal)
        .where(LoanSignal.customer_id == customer_id)
        .order_by(LoanSignal.detected_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_rm_notes(db: Session, customer_id: str) -> list[RMNote]:
    stmt = (
        select(RMNote)
        .where(RMNote.customer_id == customer_id)
        .order_by(RMNote.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_outreach_history(db: Session, customer_id: str) -> list[OutreachHistory]:
    stmt = (
        select(OutreachHistory)
        .where(OutreachHistory.customer_id == customer_id)
        .order_by(OutreachHistory.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


# ── Mutations ─────────────────────────────────────────────────────────────────


def upsert_loan_signal(db: Session, signal: LoanSignal) -> LoanSignal:
    """
    Insert a new LoanSignal, or update the existing one that matches
    (customer_id, signal_type) — whichever exists first.
    """
    stmt = select(LoanSignal).where(
        LoanSignal.customer_id == signal.customer_id,
        LoanSignal.signal_type == signal.signal_type,
    )
    existing = db.execute(stmt).scalars().first()
    if existing:
        existing.signal_value = signal.signal_value
        existing.signal_source = signal.signal_source
        existing.confidence_score = signal.confidence_score
        existing.detected_at = signal.detected_at
        db.flush()
        return existing
    db.add(signal)
    db.flush()
    return signal


def create_rm_note(
    db: Session,
    customer_id: str,
    rm_id: str,
    note_text: str,
) -> RMNote:
    note = RMNote(
        note_id=str(uuid.uuid4()),
        customer_id=customer_id,
        rm_id=rm_id,
        note_text=note_text,
    )
    db.add(note)
    db.flush()
    return note
