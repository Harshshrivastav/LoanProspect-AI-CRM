"""Tests for compliance validation tool."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock, patch

import pytest


def test_compliance_blocks_no_consent():
    """Customer without marketing consent must receive a BLOCK."""
    with patch("app.tools.compliance_tools.get_db_context") as mock_ctx:
        mock_db = MagicMock()
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        with patch("app.tools.compliance_tools.customer_repo") as mock_cr:
            c = MagicMock()
            c.full_name = "Test User"
            c.consent_marketing = False
            c.kyc_status = "verified"
            c.risk_segment = "low"
            mock_cr.get_customer_by_id.return_value = c

            from app.tools.compliance_tools import validate_compliance

            result = validate_compliance.run(
                customer_id="CUST001", message_text=""
            )
            assert "BLOCK" in result
            assert "NON-COMPLIANT" in result


def test_compliance_passes_verified_consent():
    """Customer with consent + verified KYC in low-risk segment must be COMPLIANT."""
    with patch("app.tools.compliance_tools.get_db_context") as mock_ctx:
        mock_db = MagicMock()
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        with patch("app.tools.compliance_tools.customer_repo") as mock_cr:
            c = MagicMock()
            c.full_name = "Good User"
            c.consent_marketing = True
            c.kyc_status = "verified"
            c.risk_segment = "low"
            mock_cr.get_customer_by_id.return_value = c

            from app.tools.compliance_tools import validate_compliance

            result = validate_compliance.run(
                customer_id="CUST001", message_text=""
            )
            assert "COMPLIANT" in result
            assert "BLOCK" not in result


def test_prohibited_term_detected():
    """Messages containing prohibited terms must be blocked even for compliant customers."""
    with patch("app.tools.compliance_tools.get_db_context") as mock_ctx:
        mock_db = MagicMock()
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        with patch("app.tools.compliance_tools.customer_repo") as mock_cr:
            c = MagicMock()
            c.full_name = "Good User"
            c.consent_marketing = True
            c.kyc_status = "verified"
            c.risk_segment = "low"
            mock_cr.get_customer_by_id.return_value = c

            from app.tools.compliance_tools import validate_compliance

            result = validate_compliance.run(
                customer_id="CUST001",
                message_text="guaranteed approval no credit check",
            )
            assert "BLOCK" in result
