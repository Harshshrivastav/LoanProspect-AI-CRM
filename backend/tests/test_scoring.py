"""Tests for the deterministic scoring engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from app.tools.scoring_tools import ProspectScore, _score_customer


class MockCustomer:
    customer_id = "CUST001"
    full_name = "Test User"
    age = 35
    employment_type = "salaried"
    annual_income = 1_200_000
    credit_score_proxy = 750
    account_tenure_months = 48
    consent_marketing = True
    risk_segment = "low"
    dependents = 1
    kyc_status = "verified"



class MockAccount:
    current_balance = 500_000
    avg_monthly_balance = 300_000
    monthly_inflow = 100_000
    monthly_outflow = 70_000


class MockTransaction:
    def __init__(
        self, category: str, txn_type: str, amount: float, date_offset: int = 10
    ):
        self.category = category
        self.txn_type = txn_type
        self.amount = amount
        self.txn_date = date.today() - timedelta(days=date_offset)
        self.balance_after = 500_000


class MockProduct:
    product_type = "savings_account"
    product_status = "active"
    outstanding_amount = 0
    emi_amount = 0


# ── Helper ────────────────────────────────────────────────────────────────────


def _patch_db(mock_ctx, customer, accounts, products, transactions):
    """Wires up the DB context + repo mocks used by _score_customer."""
    mock_db = MagicMock()
    mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_db)
    mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
    return mock_db


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_score_returns_prospect_score():
    with patch("app.tools.scoring_tools.get_db_context") as mock_ctx:
        _patch_db(mock_ctx, MockCustomer(), [MockAccount()], [MockProduct()], [])

        with (
            patch("app.tools.scoring_tools.customer_repo") as mock_cr,
            patch("app.tools.scoring_tools.transaction_repo") as mock_tr,
        ):
            mock_cr.get_customer_by_id.return_value = MockCustomer()
            mock_cr.get_customer_accounts.return_value = [MockAccount()]
            mock_cr.get_product_holdings.return_value = [MockProduct()]

            salary_txns = [
                MockTransaction("salary", "credit", 100_000, i * 30) for i in range(6)
            ]
            medical_txn = [MockTransaction("medical", "debit", 150_000, 30)]
            mock_tr.get_transactions_by_customer.return_value = (
                salary_txns + medical_txn
            )
            mock_tr.get_transaction_summary.return_value = {
                "salary_months": 3,
                "by_category": {"medical": {"total": 150000}}
            }

            score = _score_customer("CUST001")

            assert isinstance(score, ProspectScore)
            assert 0 <= score.readiness_score <= 100
            assert score.conversion_band in ("high", "medium", "low")
            assert 0.0 <= score.confidence <= 1.0
            assert isinstance(score.positive_signals, list)
            assert any("salary" in s.lower() for s in score.positive_signals)
            assert any("medical" in s.lower() for s in score.positive_signals)


def test_high_score_band():
    """Customer with all positive signals should land in the 'high' band."""
    with patch("app.tools.scoring_tools.get_db_context") as mock_ctx:
        _patch_db(mock_ctx, MockCustomer(), [MockAccount()], [MockProduct()], [])

        with (
            patch("app.tools.scoring_tools.customer_repo") as mock_cr,
            patch("app.tools.scoring_tools.transaction_repo") as mock_tr,
        ):
            mock_cr.get_customer_by_id.return_value = MockCustomer()
            mock_cr.get_customer_accounts.return_value = [MockAccount()]
            mock_cr.get_product_holdings.return_value = [
                MockProduct()
            ]  # no personal loan

            txns = (
                [MockTransaction("salary", "credit", 100_000, i * 30) for i in range(6)]
                + [MockTransaction("medical", "debit", 200_000, 20)]
                + [MockTransaction("home_renovation", "debit", 200_000, 40)]
            )
            mock_tr.get_transactions_by_customer.return_value = txns
            mock_tr.get_transaction_summary.return_value = {
                "salary_months": 3,
                "by_category": {
                    "medical": {"total": 200000},
                    "home_renovation": {"total": 200000}
                }
            }

            score = _score_customer("CUST001")

            assert score.conversion_band == "high"
            assert score.readiness_score >= 70


def test_no_consent_adds_risk_flag():
    """Customers without marketing consent must receive the no_marketing_consent flag."""
    with patch("app.tools.scoring_tools.get_db_context") as mock_ctx:
        _patch_db(mock_ctx, MockCustomer(), [MockAccount()], [MockProduct()], [])

        with (
            patch("app.tools.scoring_tools.customer_repo") as mock_cr,
            patch("app.tools.scoring_tools.transaction_repo") as mock_tr,
        ):
            customer = MockCustomer()
            customer.consent_marketing = False
            mock_cr.get_customer_by_id.return_value = customer
            mock_cr.get_customer_accounts.return_value = [MockAccount()]
            mock_cr.get_product_holdings.return_value = [MockProduct()]
            mock_tr.get_transactions_by_customer.return_value = []
            mock_tr.get_transaction_summary.return_value = {
                "salary_months": 0,
                "by_category": {}
            }

            score = _score_customer("CUST001")

            assert any("no marketing consent" in f.lower() for f in score.risk_flags)
