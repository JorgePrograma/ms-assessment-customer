"""Integration tests: HTTP -> controller -> service -> repository -> database.

Each test references the acceptance criterion it covers in specs/customers.spec.md.
"""

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient


def assert_error(response, status_code: int, code: str) -> dict:
    assert response.status_code == status_code, response.text
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == code
    return body["error"]


class TestCreateCustomer:
    def test_creates_customer_with_pending_status(self, client: TestClient) -> None:  # AC-01
        response = client.post("/customers", json={"name": "Juan Pérez", "email": "juan@example.com"})

        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        customer = body["data"]
        assert customer["name"] == "Juan Pérez"
        assert customer["email"] == "juan@example.com"
        assert customer["status"] == "PENDING"
        assert UUID(customer["id"])
        assert customer["created_at"]

    def test_rejects_duplicated_email(self, client: TestClient, create_customer) -> None:  # AC-02
        create_customer(email="juan@example.com")

        response = client.post("/customers", json={"name": "Otro Juan", "email": "JUAN@example.com"})

        error = assert_error(response, 409, "EMAIL_ALREADY_EXISTS")
        assert error["message"] == "A customer with email 'juan@example.com' already exists"

    @pytest.mark.parametrize("email", ["not-an-email", "juan@", "@example.com", ""])
    def test_rejects_invalid_email(self, client: TestClient, email: str) -> None:  # AC-03
        response = client.post("/customers", json={"name": "Juan", "email": email})

        error = assert_error(response, 422, "VALIDATION_ERROR")
        assert [detail["field"] for detail in error["details"]] == ["email"]

    @pytest.mark.parametrize("payload", [{"email": "juan@example.com"}, {"name": "   ", "email": "juan@example.com"}])
    def test_rejects_missing_or_blank_name(self, client: TestClient, payload: dict) -> None:  # AC-04
        response = client.post("/customers", json=payload)

        error = assert_error(response, 422, "VALIDATION_ERROR")
        assert [detail["field"] for detail in error["details"]] == ["name"]

    def test_rejects_client_provided_status(self, client: TestClient) -> None:  # AC-05
        response = client.post("/customers", json={"name": "Juan", "email": "juan@example.com", "status": "ACTIVE"})

        assert_error(response, 422, "VALIDATION_ERROR")


class TestListCustomers:
    def test_lists_customers_newest_first(self, client: TestClient, create_customer) -> None:  # AC-06
        first = create_customer(name="Ana", email="ana@example.com")
        second = create_customer(name="Luis", email="luis@example.com")

        response = client.get("/customers")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert [customer["id"] for customer in body["data"]] == [second["id"], first["id"]]
        assert body["meta"] == {"page": 1, "size": 20, "total": 2, "pages": 1}

    def test_filters_by_status(self, client: TestClient, create_customer) -> None:  # AC-07
        active = create_customer(name="Ana", email="ana@example.com")
        create_customer(name="Luis", email="luis@example.com")
        client.patch(f"/customers/{active['id']}/status", json={"status": "ACTIVE"})

        response = client.get("/customers", params={"status": "ACTIVE"})

        assert response.status_code == 200
        body = response.json()
        assert [customer["id"] for customer in body["data"]] == [active["id"]]
        assert body["data"][0]["status"] == "ACTIVE"
        assert body["meta"]["total"] == 1

    def test_rejects_unknown_status_filter(self, client: TestClient) -> None:  # AC-08
        response = client.get("/customers", params={"status": "DELETED"})

        error = assert_error(response, 422, "VALIDATION_ERROR")
        assert error["details"][0]["field"] == "status"

    def test_paginates_results(self, client: TestClient, create_customer) -> None:  # AC-16
        created = [create_customer(name=f"Customer {i}", email=f"customer{i}@example.com") for i in range(5)]
        newest_first = [customer["id"] for customer in reversed(created)]

        first_page = client.get("/customers", params={"page": 1, "size": 2}).json()
        last_page = client.get("/customers", params={"page": 3, "size": 2}).json()

        assert [customer["id"] for customer in first_page["data"]] == newest_first[:2]
        assert first_page["meta"] == {"page": 1, "size": 2, "total": 5, "pages": 3}
        assert [customer["id"] for customer in last_page["data"]] == newest_first[4:]
        assert last_page["meta"] == {"page": 3, "size": 2, "total": 5, "pages": 3}

    def test_page_beyond_last_returns_empty_list(self, client: TestClient, create_customer) -> None:  # AC-17
        create_customer()

        body = client.get("/customers", params={"page": 5, "size": 10}).json()

        assert body["data"] == []
        assert body["meta"] == {"page": 5, "size": 10, "total": 1, "pages": 1}

    @pytest.mark.parametrize("params", [{"page": 0}, {"size": 0}, {"size": 101}])
    def test_rejects_invalid_pagination(self, client: TestClient, params: dict) -> None:  # AC-18
        response = client.get("/customers", params=params)

        assert_error(response, 422, "VALIDATION_ERROR")

    def test_searches_by_name_or_email(self, client: TestClient, create_customer) -> None:  # AC-22
        ana = create_customer(name="Ana López", email="ana@example.com")
        luis = create_customer(name="Luis Pérez", email="lperez@corp.com")
        create_customer(name="Marta Ruiz", email="marta@example.com")
        client.patch(f"/customers/{luis['id']}/status", json={"status": "ACTIVE"})

        by_name = client.get("/customers", params={"search": "ANA"}).json()
        by_email = client.get("/customers", params={"search": "corp.com"}).json()
        combined = client.get("/customers", params={"search": "example", "status": "ACTIVE"}).json()

        assert [customer["id"] for customer in by_name["data"]] == [ana["id"]]
        assert [customer["id"] for customer in by_email["data"]] == [luis["id"]]
        assert combined["data"] == []
        assert combined["meta"]["total"] == 0

    def test_search_treats_wildcards_literally(self, client: TestClient, create_customer) -> None:  # AC-23
        create_customer(name="Ana", email="ana@example.com")
        underscored = create_customer(name="Ana_Admin", email="admin@example.com")

        assert client.get("/customers", params={"search": "%"}).json()["data"] == []
        assert [customer["id"] for customer in client.get("/customers", params={"search": "_"}).json()["data"]] == [
            underscored["id"]
        ]


class TestGetCustomer:
    def test_returns_existing_customer(self, client: TestClient, create_customer) -> None:  # AC-09
        created = create_customer()

        response = client.get(f"/customers/{created['id']}")

        assert response.status_code == 200
        assert response.json() == {"success": True, "data": created}

    def test_returns_404_for_unknown_customer(self, client: TestClient) -> None:  # AC-10
        customer_id = uuid4()

        response = client.get(f"/customers/{customer_id}")

        assert response.json() == {
            "success": False,
            "error": {"code": "CUSTOMER_NOT_FOUND", "message": f"Customer '{customer_id}' not found", "details": None},
        }
        assert response.status_code == 404

    def test_rejects_malformed_id(self, client: TestClient) -> None:  # AC-11
        response = client.get("/customers/123")

        error = assert_error(response, 422, "VALIDATION_ERROR")
        assert error["details"][0]["field"] == "customer_id"


class TestUpdateCustomerStatus:
    def test_updates_status(self, client: TestClient, create_customer) -> None:  # AC-12
        created = create_customer()

        response = client.patch(f"/customers/{created['id']}/status", json={"status": "BLOCKED"})

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "BLOCKED"
        assert client.get(f"/customers/{created['id']}").json()["data"]["status"] == "BLOCKED"

    def test_rejects_invalid_status(self, client: TestClient, create_customer) -> None:  # AC-13
        created = create_customer()

        response = client.patch(f"/customers/{created['id']}/status", json={"status": "DELETED"})

        error = assert_error(response, 422, "VALIDATION_ERROR")
        assert error["details"][0]["field"] == "status"

    def test_returns_404_for_unknown_customer(self, client: TestClient) -> None:  # AC-14
        response = client.patch(f"/customers/{uuid4()}/status", json={"status": "ACTIVE"})

        assert_error(response, 404, "CUSTOMER_NOT_FOUND")


class TestCustomersSummary:
    def test_returns_totals_per_status_including_empty_ones(self, client: TestClient, create_customer) -> None:  # AC-25
        active = create_customer(name="Ana", email="ana@example.com")
        create_customer(name="Luis", email="luis@example.com")
        client.patch(f"/customers/{active['id']}/status", json={"status": "ACTIVE"})

        response = client.get("/customers/summary")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 2
        assert data["by_status"] == {"ACTIVE": 1, "PENDING": 1, "BLOCKED": 0}

    def test_returns_consecutive_days_ending_today(self, client: TestClient, create_customer) -> None:  # AC-26
        create_customer()

        registrations = client.get("/customers/summary", params={"days": 7}).json()["data"]["registrations"]

        days = [date.fromisoformat(item["date"]) for item in registrations]
        today = datetime.now(UTC).date()
        assert days == [today - timedelta(days=offset) for offset in range(6, -1, -1)]
        assert [item["count"] for item in registrations] == [0, 0, 0, 0, 0, 0, 1]

    @pytest.mark.parametrize("days", [6, 91])
    def test_rejects_out_of_range_days(self, client: TestClient, days: int) -> None:  # AC-27
        response = client.get("/customers/summary", params={"days": days})

        assert_error(response, 422, "VALIDATION_ERROR")
