
import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Give each test its own temporary database.
    # Your real cardguard.db will not be changed.
    monkeypatch.setattr(main, "DATABASE", tmp_path / "test_cardguard.db")
    main.initialize_database()

    return TestClient(main.app)


def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "CardGuard API is running"


def test_normal_transaction(client):
    response = client.post("/transactions", json={
        "card_id": "TEST-1001",
        "amount": 35,
        "merchant": "Coffee Shop",
        "country": "US",
    })

    assert response.status_code == 201

    data = response.json()
    assert data["id"] == 1
    assert data["risk_level"] == "low"
    assert data["reasons"] == []


def test_high_amount(client):
    response = client.post("/transactions", json={
        "card_id": "TEST-1002",
        "amount": 2450,
        "merchant": "Electronics Store",
        "country": "US",
    })

    assert response.status_code == 201
    assert response.json()["risk_level"] == "review"
    assert "High transaction amount" in response.json()["reasons"]


def test_rapid_country_change(client):
    client.post("/transactions", json={
        "card_id": "TEST-1003",
        "amount": 35,
        "merchant": "Coffee Shop",
        "country": "US",
    })

    response = client.post("/transactions", json={
        "card_id": "TEST-1003",
        "amount": 120,
        "merchant": "Hotel",
        "country": "GR",
    })

    assert response.status_code == 201
    assert response.json()["risk_level"] == "review"
    assert "Rapid change in transaction country" in response.json()["reasons"]


def test_multiple_rapid_transactions(client):
    for amount in [20, 30]:
        client.post("/transactions", json={
            "card_id": "TEST-1004",
            "amount": amount,
            "merchant": "Demo Store",
            "country": "US",
        })

    response = client.post("/transactions", json={
        "card_id": "TEST-1004",
        "amount": 40,
        "merchant": "Demo Store",
        "country": "US",
    })

    assert response.status_code == 201
    assert "Multiple transactions within ten minutes" in response.json()["reasons"]


def test_transaction_history(client):
    client.post("/transactions", json={
        "card_id": "TEST-1005",
        "amount": 49.99,
        "merchant": "Bookstore",
        "country": "US",
    })

    response = client.get("/transactions")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["amount"] == 49.99


def test_invalid_amount(client):
    response = client.post("/transactions", json={
        "card_id": "TEST-1006",
        "amount": -50,
        "merchant": "Demo Store",
        "country": "US",
    })

    assert response.status_code == 422


def test_missing_transaction(client):
    response = client.get("/transactions/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"