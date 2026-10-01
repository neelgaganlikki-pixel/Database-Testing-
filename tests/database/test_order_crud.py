import pytest
from database.connection import execute_insert, fetch_one, execute_update, execute_delete
from queries.order_queries import (
    INSERT_ORDER, SELECT_ORDER_BY_ID, UPDATE_ORDER_STATUS, DELETE_ORDER,
    INSERT_ORDER_ITEM, SELECT_ORDER_ITEMS_BY_ORDER_ID
)
from utils.data_generator import TestDataGenerator

@pytest.mark.database
@pytest.mark.regression
class TestOrderCRUD:
    """Automated CRUD tests for Orders & Order Items in MySQL."""

    def test_create_order_with_items(self, test_customer, test_product):
        """Test CREATE: Insert order and associated order items."""
        order_num = TestDataGenerator.generate_order_number()
        total_amount = round(float(test_product["price"]) * 2, 2)

        order_id = execute_insert(
            INSERT_ORDER,
            (test_customer["customer_id"], order_num, total_amount, "pending")
        )
        assert order_id > 0

        item_id = execute_insert(
            INSERT_ORDER_ITEM,
            (order_id, test_product["product_id"], 2, float(test_product["price"]), total_amount)
        )
        assert item_id > 0

        # Read order
        order = fetch_one(SELECT_ORDER_BY_ID, (order_id,))
        assert order["order_number"] == order_num
        assert float(order["total_amount"]) == total_amount

        # Cleanup
        execute_delete(DELETE_ORDER, (order_id,))

    def test_update_order_status(self, test_order):
        """Test UPDATE: Modify order status from pending to delivered."""
        order_id = test_order["order_id"]
        affected = execute_update(UPDATE_ORDER_STATUS, ("delivered", order_id))
        assert affected == 1

        updated = fetch_one(SELECT_ORDER_BY_ID, (order_id,))
        assert updated["status"] == "delivered"

    def test_delete_order_cascade(self, test_customer, test_product):
        """Test DELETE: Removing order cascades to delete order items."""
        order_num = TestDataGenerator.generate_order_number()
        order_id = execute_insert(
            INSERT_ORDER,
            (test_customer["customer_id"], order_num, 100.00, "pending")
        )
        execute_insert(
            INSERT_ORDER_ITEM,
            (order_id, test_product["product_id"], 1, 100.00, 100.00)
        )

        # Delete order
        execute_delete(DELETE_ORDER, (order_id,))

        # Verify order and items are gone
        assert fetch_one(SELECT_ORDER_BY_ID, (order_id,)) is None
        items = fetch_one("SELECT COUNT(*) as count FROM order_items WHERE order_id = %s;", (order_id,))
        assert items["count"] == 0, "Order items should be cascade deleted"
