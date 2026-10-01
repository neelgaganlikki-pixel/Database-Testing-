import pytest
from database.connection import execute_insert, fetch_one, execute_update, execute_delete
from queries.product_queries import (
    INSERT_PRODUCT, SELECT_PRODUCT_BY_ID, UPDATE_PRODUCT, DELETE_PRODUCT
)
from utils.data_generator import TestDataGenerator

@pytest.mark.database
@pytest.mark.regression
class TestProductCRUD:
    """Automated CRUD tests for Products entity in MySQL."""

    def test_create_product(self):
        """Test CREATE: Insert a new product and verify database values."""
        data = TestDataGenerator.generate_product_data(category_id=1)
        prod_id = execute_insert(
            INSERT_PRODUCT,
            (data["category_id"], data["product_name"], data["description"], data["price"], data["stock_quantity"], data["status"])
        )
        assert prod_id > 0

        created = fetch_one(SELECT_PRODUCT_BY_ID, (prod_id,))
        assert created is not None
        assert created["product_name"] == data["product_name"]
        assert float(created["price"]) == float(data["price"])
        assert created["stock_quantity"] == data["stock_quantity"]

        # Cleanup
        execute_delete(DELETE_PRODUCT, (prod_id,))

    def test_read_product(self, test_product):
        """Test READ: Query existing product by ID."""
        prod_id = test_product["product_id"]
        prod = fetch_one(SELECT_PRODUCT_BY_ID, (prod_id,))
        assert prod is not None
        assert prod["product_id"] == prod_id
        assert prod["product_name"] == test_product["product_name"]

    def test_update_product(self, test_product):
        """Test UPDATE: Modify product pricing, stock, and description."""
        prod_id = test_product["product_id"]
        new_name = "Updated " + test_product["product_name"]
        new_price = 299.99
        new_stock = 75

        affected = execute_update(
            UPDATE_PRODUCT,
            (new_name, "Updated description", new_price, new_stock, "active", prod_id)
        )
        assert affected == 1

        updated = fetch_one(SELECT_PRODUCT_BY_ID, (prod_id,))
        assert updated["product_name"] == new_name
        assert float(updated["price"]) == new_price
        assert updated["stock_quantity"] == new_stock

    def test_delete_product(self):
        """Test DELETE: Remove product from database and verify removal."""
        data = TestDataGenerator.generate_product_data(category_id=1)
        prod_id = execute_insert(
            INSERT_PRODUCT,
            (data["category_id"], data["product_name"], data["description"], data["price"], data["stock_quantity"], data["status"])
        )
        assert fetch_one(SELECT_PRODUCT_BY_ID, (prod_id,)) is not None

        affected = execute_delete(DELETE_PRODUCT, (prod_id,))
        assert affected == 1

        deleted = fetch_one(SELECT_PRODUCT_BY_ID, (prod_id,))
        assert deleted is None
