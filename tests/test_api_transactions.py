"""API tests for the /api/transactions endpoints."""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from src.models.database import Database, get_db
from src.app import app


@pytest.fixture()
def client():
    """TestClient backed by an in-memory temp database."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    test_db = Database(db_path)
    test_db.connect()

    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()
    test_db.close()
    os.unlink(db_path)


# ---- Helpers ----

def make_tx(client, **kwargs):
    payload = {"date": "2024-03-15", "amount": 50.0, "type": "withdrawal", **kwargs}
    res = client.post("/api/transactions", json=payload)
    assert res.status_code == 201
    return res.json()


# ---- Tests ----

def test_create_and_get(client):
    tx = make_tx(client, description="Coffee", amount=4.5)
    assert tx["id"] is not None
    assert tx["amount"] == 4.5
    assert tx["type"] == "withdrawal"
    assert tx["description"] == "Coffee"

    fetched = client.get(f"/api/transactions/{tx['id']}").json()
    assert fetched["id"] == tx["id"]


def test_list_for_month(client):
    make_tx(client, date="2024-03-01", amount=100.0, type="deposit")
    make_tx(client, date="2024-03-15", amount=20.0)
    make_tx(client, date="2024-04-01", amount=10.0)

    res = client.get("/api/transactions?year=2024&month=3")
    txs = res.json()
    assert len(txs) == 2


def test_update(client):
    tx = make_tx(client, amount=10.0, description="Old")
    res = client.put(f"/api/transactions/{tx['id']}", json={"amount": 99.99, "description": "New"})
    assert res.status_code == 200
    updated = res.json()
    assert updated["amount"] == 99.99
    assert updated["description"] == "New"


def test_delete(client):
    tx = make_tx(client)
    res = client.delete(f"/api/transactions/{tx['id']}")
    assert res.status_code == 204

    res2 = client.get(f"/api/transactions/{tx['id']}")
    assert res2.status_code == 404


def test_batch_create(client):
    payload = {
        "transactions": [
            {"date": "2024-05-01", "amount": 1000.0, "type": "deposit"},
            {"date": "2024-05-02", "amount": 50.0, "type": "withdrawal"},
        ]
    }
    res = client.post("/api/transactions/batch", json=payload)
    assert res.status_code == 201
    assert len(res.json()) == 2


def test_list_templates(client):
    make_tx(client, is_template=True, recurrence_pattern="monthly", description="Rent")
    res = client.get("/api/transactions/templates")
    templates = res.json()
    assert len(templates) == 1
    assert templates[0]["is_template"] is True


def test_get_nonexistent_returns_404(client):
    res = client.get("/api/transactions/99999")
    assert res.status_code == 404


def test_filter_by_type(client):
    make_tx(client, type="deposit", amount=200.0)
    make_tx(client, type="withdrawal", amount=50.0)

    deposits = client.get("/api/transactions?year=2024&month=3&type=deposit").json()
    assert all(t["type"] == "deposit" for t in deposits)

    withdrawals = client.get("/api/transactions?year=2024&month=3&type=withdrawal").json()
    assert all(t["type"] == "withdrawal" for t in withdrawals)
