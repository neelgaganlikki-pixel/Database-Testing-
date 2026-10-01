import pytest
import mysql.connector
from database.connection import DatabaseManager, execute_insert
from queries.customer_queries import INSERT_CUSTOMER
from queries.product_queries import INSERT_PRODUCT
from queries.order_queries import INSERT_ORDER
from utils.data_generator import TestDataGenerator

@pytest.mark.database
@pytest.mark.regression
class TestDatabaseConstraints:
    """Automated tests validating database schema constraints and integrity enforcement."""

    def test_unique_customer_email_constraint(self, test_customer):
        """Verify UNIQUE constraint: Inserting duplicate customer email raises integrity error."""
        duplicate_data = TestDataGenerator.generate_customer_data()
        duplicate_data["email"] = test_customer["email"]

        with pytest.raises(mysql.connector.IntegrityError) as exc_info:
            with DatabaseManager() as db:
                db.execute_insert(
                    INSERT_CUSTOMER,
                    (duplicate_data["first_name"], duplicate_data["last_name"], duplicate_data["email"],
                     duplicate_data["phone"], duplicate_data["password"], duplicate_data["status"])
                )
        assert "Duplicate entry" in str(exc_info.value) or "UNIQUE" in str(exc_info.value).upper()

    def test_negative_product_price_constraint(self):
        """Verify CHECK constraint: Negative product price is rejected."""
        with pytest.raises(mysql.connector.Error) as exc_info:
            with DatabaseManager() as db:
                db.execute_insert(
                    INSERT_PRODUCT,
                    (1, "Invalid Price Item", "Test", -19.99, 10, "active")
                )
        error_msg = str(exc_info.value).lower()
        assert "chk_product_price" in error_msg or "check constraint" in error_msg or "failed" in error_msg

    def test_negative_stock_quantity_constraint(self):
        """Verify CHECK constraint: Negative stock quantity is rejected."""
        with pytest.raises(mysql.connector.Error) as exc_info:
            with DatabaseManager() as db:
                db.execute_insert(
                    INSERT_PRODUCT,
                    (1, "Invalid Stock Item", "Test", 29.99, -5, "active")
                )
        error_msg = str(exc_info.value).lower()
        assert "chk_product_stock" in error_msg or "check constraint" in error_msg or "failed" in error_msg

    def test_foreign_key_invalid_category_constraint(self):
        """Verify FOREIGN KEY constraint: Non-existent category ID is rejected."""
        invalid_cat_id = 999999
        with pytest.raises(mysql.connector.IntegrityError) as exc_info:
            with DatabaseManager() as db:
                db.execute_insert(
                    INSERT_PRODUCT,
                    (invalid_cat_id, "Orphan Product", "Test", 49.99, 10, "active")
                )
        assert "foreign key constraint fails" in str(exc_info.value).lower()

    def test_foreign_key_invalid_customer_order_constraint(self):
        """Verify FOREIGN KEY constraint: Order referencing non-existent customer fails."""
        invalid_cust_id = 888888
        order_num = TestDataGenerator.generate_order_number()

        with pytest.raises(mysql.connector.IntegrityError) as exc_info:
            with DatabaseManager() as db:
                db.execute_insert(
                    INSERT_ORDER,
                    (invalid_cust_id, order_num, 99.99, "pending")
                )
        assert "foreign key constraint fails" in str(exc_info.value).lower()
