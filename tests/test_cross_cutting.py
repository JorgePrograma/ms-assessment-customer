import logging

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.database import get_db
from app.main import create_app


def test_unknown_route_uses_error_envelope(client: TestClient) -> None:  # AC-19
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "error": {"code": "NOT_FOUND", "message": "Not Found", "details": None},
    }


def test_unexpected_error_returns_500_without_leaking_details(caplog: pytest.LogCaptureFixture) -> None:  # AC-20
    def broken_db():
        raise RuntimeError("connection string with secrets")

    app = create_app()
    app.dependency_overrides[get_db] = broken_db

    with TestClient(app) as client, caplog.at_level(logging.ERROR):
        response = client.get("/customers")

    assert response.status_code == 500
    assert response.json() == {
        "success": False,
        "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred", "details": None},
    }
    assert "secrets" not in response.text
    assert any(record.exc_info for record in caplog.records if record.levelno == logging.ERROR)


def test_generates_request_id_when_missing(client: TestClient) -> None:  # AC-21
    response = client.get("/health")

    assert len(response.headers["X-Request-ID"]) == 32


def test_reuses_valid_incoming_request_id(client: TestClient) -> None:  # AC-21
    response = client.get("/health", headers={"X-Request-ID": "abc-123"})

    assert response.headers["X-Request-ID"] == "abc-123"


def test_replaces_unsafe_incoming_request_id(client: TestClient) -> None:  # AC-21
    response = client.get("/health", headers={"X-Request-ID": "bad id\nINJECTED LOG LINE"})

    assert response.headers["X-Request-ID"] != "bad id\nINJECTED LOG LINE"
    assert len(response.headers["X-Request-ID"]) == 32


def test_logs_carry_request_id_and_no_personal_data(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        response = client.post(
            "/customers", json={"name": "Juan Pérez", "email": "juan@example.com"}, headers={"X-Request-ID": "trace-1"}
        )

    assert response.status_code == 201
    request_records = [record for record in caplog.records if getattr(record, "request_id", None) == "trace-1"]
    messages = [record.getMessage() for record in request_records]
    assert any(message.startswith("Customer created") for message in messages)
    assert any(message.startswith("POST /customers -> 201") for message in messages)
    assert not any("juan" in message.lower() for message in caplog.messages)


@pytest.mark.parametrize(
    "origin", ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:4173", "http://localhost"]
)
def test_cors_allows_local_frontends_on_any_port(client: TestClient, origin: str) -> None:
    response = client.get("/customers", headers={"Origin": origin})

    assert response.headers["access-control-allow-origin"] == origin
    assert "X-Request-ID" in response.headers["access-control-expose-headers"]


@pytest.mark.parametrize(
    "origin", ["https://evil.example.com", "http://localhost.evil.com", "http://192.168.1.10:5173"]
)
def test_cors_rejects_foreign_origins(client: TestClient, origin: str) -> None:
    response = client.get("/customers", headers={"Origin": origin})

    assert "access-control-allow-origin" not in response.headers
