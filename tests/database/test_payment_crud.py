import pytest
from database.connection import execute_insert, fetch_one, execute_update, execute_delete
from queries.payment_queries import (
    INSERT_PAYMENT, SELECT_PAYMENT_BY_ID, UPDATE_PAYMENT_STATUS, DELETE_PAYMENT
)
from utils.data_generator import TestDataGenerator

@pytest.mark.database
@pytest.mark.regression
class TestPaymentCRUD:
    """Automated CRUD tests for Payments in MySQL."""

    def test_create_payment(self, test_order):
        """Test CREATE: Insert payment record linked to order."""
        pay_ref = TestDataGenerator.generate_payment_reference()
        order_id = test_order["order_id"]
        amount = float(test_order["total_amount"])

        payment_id = execute_insert(
            INSERT_PAYMENT,
            (order_id, pay_ref, amount, "credit_card", "pending")
        )
        assert payment_id > 0

        created = fetch_one(SELECT_PAYMENT_BY_ID, (payment_id,))
        assert created["payment_reference"] == pay_ref
        assert float(created["amount"]) == amount
        assert created["payment_status"] == "pending"

        # Cleanup
        execute_delete(DELETE_PAYMENT, (payment_id,))

    def test_update_payment_status(self, test_order):
        """Test UPDATE: Update payment status to completed."""
        pay_ref = TestDataGenerator.generate_payment_reference()
        payment_id = execute_insert(
            INSERT_PAYMENT,
            (test_order["order_id"], pay_ref, 50.00, "paypal", "pending")
        )

        affected = execute_update(UPDATE_PAYMENT_STATUS, ("completed", payment_id))
        assert affected == 1

        updated = fetch_one(SELECT_PAYMENT_BY_ID, (payment_id,))
        assert updated["payment_status"] == "completed"

        # Cleanup
        execute_delete(DELETE_PAYMENT, (payment_id,))

    def test_delete_payment(self, test_order):
        """Test DELETE: Remove payment record."""
        pay_ref = TestDataGenerator.generate_payment_reference()
        payment_id = execute_insert(
            INSERT_PAYMENT,
            (test_order["order_id"], pay_ref, 75.00, "debit_card", "completed")
        )

        affected = execute_delete(DELETE_PAYMENT, (payment_id,))
        assert affected == 1
        assert fetch_one(SELECT_PAYMENT_BY_ID, (payment_id,)) is None
