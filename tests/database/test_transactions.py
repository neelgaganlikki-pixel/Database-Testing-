import pytest
import mysql.connector
from database.connection import DatabaseManager, fetch_one
from queries.customer_queries import INSERT_CUSTOMER, SELECT_CUSTOMER_BY_ID
from queries.order_queries import INSERT_ORDER, SELECT_ORDER_BY_ID
from utils.data_generator import TestDataGenerator

@pytest.mark.database
@pytest.mark.transaction
@pytest.mark.regression
class TestDatabaseTransactions:
    """Automated tests validating database ACID transaction semantics (COMMIT and ROLLBACK)."""

    def test_transaction_commit_success(self):
        """Verify successful multi-table transaction commits all changes."""
        cust_data = TestDataGenerator.generate_customer_data()
        order_num = TestDataGenerator.generate_order_number()

        cust_id = None
        order_id = None
        with DatabaseManager() as db:
            conn = db.connect()
            cursor = conn.cursor(dictionary=True)
            try:
                # 1. Insert customer
                cursor.execute(
                    INSERT_CUSTOMER,
                    (cust_data["first_name"], cust_data["last_name"], cust_data["email"],
                     cust_data["phone"], cust_data["password"], cust_data["status"])
                )
                cust_id = cursor.lastrowid

                # 2. Insert order
                cursor.execute(INSERT_ORDER, (cust_id, order_num, 150.00, "pending"))
                order_id = cursor.lastrowid

                # Explicit commit
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()

        # Verify both records exist after commit
        assert cust_id is not None and order_id is not None
        assert fetch_one(SELECT_CUSTOMER_BY_ID, (cust_id,)) is not None
        assert fetch_one(SELECT_ORDER_BY_ID, (order_id,)) is not None

        # Cleanup
        with DatabaseManager() as db:
            db.execute_delete("DELETE FROM orders WHERE order_id = %s;", (order_id,))
            db.execute_delete("DELETE FROM customers WHERE customer_id = %s;", (cust_id,))

    def test_transaction_rollback_on_failure(self):
        """Verify transaction rollback: Error in middle of transaction leaves 0 records."""
        cust_data = TestDataGenerator.generate_customer_data()
        order_num = TestDataGenerator.generate_order_number()

        rolled_back_cust_id = None
        with DatabaseManager() as db:
            conn = db.connect()
            cursor = conn.cursor(dictionary=True)
            try:
                # 1. Insert customer
                cursor.execute(
                    INSERT_CUSTOMER,
                    (cust_data["first_name"], cust_data["last_name"], cust_data["email"],
                     cust_data["phone"], cust_data["password"], cust_data["status"])
                )
                rolled_back_cust_id = cursor.lastrowid

                # 2. Force an error: Invalid SQL syntax or constraint violation
                cursor.execute("INSERT INTO orders (non_existent_column) VALUES ('invalid');")
                conn.commit()
            except mysql.connector.Error:
                conn.rollback()
            finally:
                cursor.close()

        # Verify that customer was ROLLED BACK and does NOT exist
        assert rolled_back_cust_id is not None
        persisted = fetch_one(SELECT_CUSTOMER_BY_ID, (rolled_back_cust_id,))
        assert persisted is None, "Customer inserted before failed statement must be rolled back"

    def test_partial_failure_foreign_key_rollback(self):
        """Verify atomic rollback when a subsequent foreign key violation occurs."""
        cust_data = TestDataGenerator.generate_customer_data()
        test_cust_id = None

        with DatabaseManager() as db:
            conn = db.connect()
            cursor = conn.cursor(dictionary=True)
            try:
                # Insert customer
                cursor.execute(
                    INSERT_CUSTOMER,
                    (cust_data["first_name"], cust_data["last_name"], cust_data["email"],
                     cust_data["phone"], cust_data["password"], cust_data["status"])
                )
                test_cust_id = cursor.lastrowid

                # Attempt to insert an order item referencing a non-existent order
                invalid_order_id = 9999999
                cursor.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES (%s, 1, 1, 10.00, 10.00);",
                    (invalid_order_id,)
                )
                conn.commit()
            except mysql.connector.IntegrityError:
                conn.rollback()
            finally:
                cursor.close()

        # Ensure customer was not saved due to rollback
        assert fetch_one(SELECT_CUSTOMER_BY_ID, (test_cust_id,)) is None

