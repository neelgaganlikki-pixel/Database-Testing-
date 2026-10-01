import pytest

@pytest.mark.api
@pytest.mark.regression
class TestPaymentAPI:
    """Automated REST API tests for Payment processing endpoints."""

    def test_create_payment_api_success(self, api_client, test_order):
        """Test POST /payments: Processes payment for an order and returns 201 Created."""
        payload = {
            "order_id": test_order["order_id"],
            "payment_method": "credit_card",
            "amount": float(test_order["total_amount"])
        }
        response = api_client.post("/payments", json=payload)
        assert response.status_code == 201

        payment = response.json()
        assert payment["payment_id"] > 0
        assert payment["order_id"] == test_order["order_id"]
        assert payment["payment_status"] == "completed"
        assert len(payment["payment_reference"]) > 5

    def test_get_payment_by_id_api(self, api_client, test_order):
        """Test GET /payments/{id}: Retrieves payment record."""
        # Create payment first
        payload = {
            "order_id": test_order["order_id"],
            "payment_method": "paypal",
            "amount": float(test_order["total_amount"])
        }
        create_resp = api_client.post("/payments", json=payload)
        pay_id = create_resp.json()["payment_id"]

        get_resp = api_client.get(f"/payments/{pay_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["payment_id"] == pay_id

    def test_create_payment_invalid_order_fails(self, api_client):
        """Negative Test: Processing payment for non-existent order returns 404."""
        payload = {
            "order_id": 9999999,
            "payment_method": "credit_card",
            "amount": 99.99
        }
        response = api_client.post("/payments", json=payload)
        assert response.status_code == 404

    def test_create_payment_negative_amount_fails(self, api_client, test_order):
        """Boundary/Negative Test: Reject negative payment amount with 422."""
        payload = {
            "order_id": test_order["order_id"],
            "payment_method": "credit_card",
            "amount": -50.00
        }
        response = api_client.post("/payments", json=payload)
        assert response.status_code == 422

