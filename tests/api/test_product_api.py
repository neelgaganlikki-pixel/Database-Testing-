import pytest
from utils.data_generator import TestDataGenerator

@pytest.mark.api
@pytest.mark.regression
class TestProductAPI:
    """Automated REST API tests for Product endpoints."""

    def test_create_product_api_success(self, api_client):
        """Test POST /products: Creates a new product (201 Created)."""
        data = TestDataGenerator.generate_product_data(category_id=1)
        response = api_client.post("/products", json=data)
        assert response.status_code == 201

        resp_body = response.json()
        assert resp_body["product_id"] > 0
        assert resp_body["product_name"] == data["product_name"]
        assert resp_body["price"] == data["price"]
        assert resp_body["stock_quantity"] == data["stock_quantity"]

    def test_get_product_by_id_api(self, api_client, test_product):
        """Test GET /products/{id}: Retrieves product by ID (200 OK)."""
        prod_id = test_product["product_id"]
        response = api_client.get(f"/products/{prod_id}")
        assert response.status_code == 200

        resp_body = response.json()
        assert resp_body["product_id"] == prod_id
        assert resp_body["product_name"] == test_product["product_name"]

    def test_create_product_negative_price_rejected(self, api_client):
        """Boundary/Negative Test: Reject negative price payload (422 Unprocessable Entity)."""
        data = TestDataGenerator.generate_product_data(category_id=1)
        data["price"] = -49.99
        response = api_client.post("/products", json=data)
        assert response.status_code == 422

    def test_create_product_invalid_category_fails(self, api_client):
        """Negative Test: Reject product creation when category does not exist (400 Bad Request)."""
        data = TestDataGenerator.generate_product_data(category_id=999999)
        response = api_client.post("/products", json=data)
        assert response.status_code == 400

    def test_update_product_api(self, api_client, test_product):
        """Test PUT /products/{id}: Updates product price and stock."""
        prod_id = test_product["product_id"]
        updates = {"price": 189.50, "stock_quantity": 40}
        response = api_client.put(f"/products/{prod_id}", json=updates)
        assert response.status_code == 200

        updated = response.json()
        assert updated["price"] == 189.50
        assert updated["stock_quantity"] == 40

