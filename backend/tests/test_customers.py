"""Tests for customer API endpoints."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import patch

import pytest


def test_health_endpoint():
    with patch("app.db.database.init_db"), patch("app.seed.seed_data.run_seed"):
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["framework"] == "CrewAI"


def test_customers_list():
    with patch("app.db.database.init_db"), patch("app.seed.seed_data.run_seed"):
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        with patch("app.services.customer_service.get_customers_list") as mock_list:
            mock_list.return_value = {"customers": [], "page": 1, "per_page": 20}
            response = client.get("/api/customers")
            assert response.status_code == 200


def test_customer_not_found():
    with patch("app.db.database.init_db"), patch("app.seed.seed_data.run_seed"):
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        with patch("app.services.customer_service.get_customer_detail") as mock_detail:
            mock_detail.return_value = {}
            response = client.get("/api/customers/CUST999")
            assert response.status_code == 404
