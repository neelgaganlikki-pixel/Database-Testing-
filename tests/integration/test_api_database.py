import pytest
from database.connection import fetch_one
from queries.customer_queries import SELECT_CUSTOMER_BY_ID, DELETE_CUSTOMER
from queries.product_queries import SELECT_PRODUCT_BY_ID, DELETE_PRODUCT
from queries.payment_queries import SELECT_PAYMENT_BY_ID, DELETE_PAYMENT
from queries.order_queries import SELECT_ORDER_BY_ID
from utils.data_generator import TestDataGenerator

@pytest.mark.integration
@pytest.mark.regression
class TestAPIToDatabaseValidation:
    """Integration tests validating data consistency between REST API responses and MySQL database records."""

    def test_customer_api_to_db_validation(self, api_client):
        """API -> DB: Verify customer created via API is identical to DB record."""
        cust_payload = TestDataGenerator.generate_customer_data()
        response = api_client.post("/customers", json=cust_payload)
        assert response.status_code == 201
        api_data = response.json()
        cust_id = api_data["customer_id"]

        # Directly query MySQL Database
        db_record = fetch_one(SELECT_CUSTOMER_BY_ID, (cust_id,))
        assert db_record is not None, f"Customer {cust_id} not found in database!"

        # Field-by-field verification
        assert db_record["customer_id"] == api_data["customer_id"]
        assert db_record["first_name"] == api_data["first_name"]
        assert db_record["last_name"] == api_data["last_name"]
        assert db_record["email"] == api_data["email"]
        assert db_record["status"] == api_data["status"]

    def test_product_api_to_db_validation(self, api_client):
        """API -> DB: Verify product created via API matches database row exactly."""
        prod_payload = TestDataGenerator.generate_product_data(category_id=1)
        response = api_client.post("/products", json=prod_payload)
        assert response.status_code == 201
        api_prod = response.json()
        prod_id = api_prod["product_id"]

        # Directly query MySQL Database
        db_prod = fetch_one(SELECT_PRODUCT_BY_ID, (prod_id,))
        assert db_prod is not None

        assert db_prod["product_id"] == api_prod["product_id"]
        assert db_prod["product_name"] == api_prod["product_name"]
        assert float(db_prod["price"]) == float(api_prod["price"])
        assert db_prod["stock_quantity"] == api_prod["stock_quantity"]
        assert db_prod["category_id"] == api_prod["category_id"]

    def test_payment_api_to_db_validation(self, api_client, test_order):
        """API -> DB: Verify payment API updates payment table and orders status in DB."""
        order_id = test_order["order_id"]
        amount = float(test_order["total_amount"])
        pay_payload = {
            "order_id": order_id,
            "payment_method": "credit_card",
            "amount": amount
        }

        response = api_client.post("/payments", json=pay_payload)
        assert response.status_code == 201
        api_pay = response.json()
        payment_id = api_pay["payment_id"]

        # Verify payment in DB
        db_pay = fetch_one(SELECT_PAYMENT_BY_ID, (payment_id,))
        assert db_pay is not None
        assert db_pay["payment_reference"] == api_pay["payment_reference"]
        assert float(db_pay["amount"]) == amount
        assert db_pay["payment_status"] == "completed"

        # Verify order status in DB was updated to 'confirmed'
        db_order = fetch_one(SELECT_ORDER_BY_ID, (order_id,))
        assert db_order["status"] == "confirmed"

