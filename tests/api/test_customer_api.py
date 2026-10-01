import pytest
from utils.data_generator import TestDataGenerator

@pytest.mark.api
@pytest.mark.regression
class TestCustomerAPI:
    """Automated REST API tests for Customer endpoints."""

    def test_create_customer_api_success(self, api_client):
        """Test POST /customers: Creates a new customer successfully (201 Created)."""
        data = TestDataGenerator.generate_customer_data()
        response = api_client.post("/customers", json=data)
        assert response.status_code == 201

        resp_body = response.json()
        assert resp_body["customer_id"] > 0
        assert resp_body["first_name"] == data["first_name"]
        assert resp_body["last_name"] == data["last_name"]
        assert resp_body["email"] == data["email"]
        assert resp_body["status"] == data["status"]

    def test_get_customer_by_id_api(self, api_client, test_customer):
        """Test GET /customers/{id}: Retrieves customer by valid ID (200 OK)."""
        cust_id = test_customer["customer_id"]
        response = api_client.get(f"/customers/{cust_id}")
        assert response.status_code == 200

        resp_body = response.json()
        assert resp_body["customer_id"] == cust_id
        assert resp_body["email"] == test_customer["email"]

    def test_create_customer_duplicate_email_conflict(self, api_client, test_customer):
        """Negative Test: Creating customer with existing email returns 409 Conflict."""
        data = TestDataGenerator.generate_customer_data()
        data["email"] = test_customer["email"]  # Force duplicate

        response = api_client.post("/customers", json=data)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_get_non_existent_customer_returns_404(self, api_client):
        """Negative Test: GET /customers/{id} for non-existent ID returns 404 Not Found."""
        invalid_id = 9999999
        response = api_client.get(f"/customers/{invalid_id}")
        assert response.status_code == 404

    def test_update_customer_api(self, api_client, test_customer):
        """Test PUT /customers/{id}: Updates customer fields successfully."""
        cust_id = test_customer["customer_id"]
        updates = {"first_name": "UpdatedViaAPI", "status": "suspended"}
        response = api_client.put(f"/customers/{cust_id}", json=updates)
        assert response.status_code == 200

        updated = response.json()
        assert updated["first_name"] == "UpdatedViaAPI"
        assert updated["status"] == "suspended"

