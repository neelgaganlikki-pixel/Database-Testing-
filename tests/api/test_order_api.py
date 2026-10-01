import pytest

@pytest.mark.api
@pytest.mark.regression
class TestOrderAPI:
    """Automated REST API tests for Orders endpoints."""

    def test_create_order_with_items_api(self, api_client, test_customer, test_product):
        """Test POST /orders: Creates order with items and verifies structure."""
        payload = {
            "customer_id": test_customer["customer_id"],
            "items": [
                {"product_id": test_product["product_id"], "quantity": 2}
            ],
            "from_cart": False
        }
        response = api_client.post("/orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["order_id"] > 0
        assert order["customer_id"] == test_customer["customer_id"]
        assert len(order["items"]) == 1
        expected_total = round(float(test_product["price"]) * 2, 2)
        assert round(order["total_amount"], 2) == expected_total

    def test_get_order_by_id_api(self, api_client, test_order):
        """Test GET /orders/{id}: Retrieves order details."""
        order_id = test_order["order_id"]
        response = api_client.get(f"/orders/{order_id}")
        assert response.status_code == 200

        order = response.json()
        assert order["order_id"] == order_id
        assert order["order_number"] == test_order["order_number"]

    def test_update_order_status_api(self, api_client, test_order):
        """Test PUT /orders/{id}/status: Updates order status to shipped."""
        order_id = test_order["order_id"]
        response = api_client.put(f"/orders/{order_id}/status", json={"status": "shipped"})
        assert response.status_code == 200

        updated = response.json()
        assert updated["status"] == "shipped"

    def test_create_order_invalid_customer_fails(self, api_client, test_product):
        """Negative Test: Create order for non-existent customer returns 404."""
        payload = {
            "customer_id": 999999,
            "items": [{"product_id": test_product["product_id"], "quantity": 1}]
        }
        response = api_client.post("/orders", json=payload)
        assert response.status_code == 404

