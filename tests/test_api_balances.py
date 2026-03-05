"""API tests for the /api/balances endpoints."""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from src.models.database import Database, get_db
from src.app import app


@pytest.fixture()
def client():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    test_db = Database(db_path)
    test_db.connect()

    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=True) as c:
        # Seed some transactions
        c.post("/api/transactions", json={"date": "2024-03-01", "amount": 1000.0, "type": "deposit"})
        c.post("/api/transactions", json={"date": "2024-03-10", "amount": 200.0,  "type": "withdrawal"})
        c.post("/api/transactions", json={"date": "2024-03-20", "amount": 50.0,   "type": "withdrawal"})
        yield c

    app.dependency_overrides.clear()
    test_db.close()
    os.unlink(db_path)


def test_current_balance(client):
    res = client.get("/api/balances/current?as_of=2024-03-20")
    assert res.status_code == 200
    data = res.json()
    assert data["balance"] == pytest.approx(750.0)
    assert data["date"] == "2024-03-20"


def test_balance_partial_date(client):
    res = client.get("/api/balances/current?as_of=2024-03-01")
    assert res.json()["balance"] == pytest.approx(1000.0)


def test_weekly_balances_structure(client):
    res = client.get("/api/balances/weekly?year=2024&month=3")
    assert res.status_code == 200
    weeks = res.json()
    assert len(weeks) > 0
    for w in weeks:
        assert "week_start" in w
        assert "week_end" in w
        assert "starting_balance" in w
        assert "ending_balance" in w
        assert "net_change" in w


def test_weekly_balances_net_math(client):
    res = client.get("/api/balances/weekly?year=2024&month=3")
    weeks = res.json()
    for w in weeks:
        expected_end = round(w["starting_balance"] + w["net_change"], 6)
        assert round(w["ending_balance"], 6) == pytest.approx(expected_end)
