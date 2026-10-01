import time
import pytest
import mysql.connector
from database.connection import execute_select, fetch_one, execute_insert, execute_delete
from queries.customer_queries import INSERT_CUSTOMER, SELECT_CUSTOMER_BY_EMAIL, DELETE_CUSTOMER
from utils.data_generator import TestDataGenerator

@pytest.mark.database
@pytest.mark.regression
class TestDataIntegrity:
    """Tests for database integrity, orphan records, NULL values, and security."""

    def test_no_orphan_orders(self):
        """Verify no orphan orders exist without an associated customer."""
        orphan_query = """
            SELECT o.order_id, o.customer_id
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.customer_id
            WHERE c.customer_id IS NULL;
        """
        orphans = execute_select(orphan_query)
        assert len(orphans) == 0, f"Found orphan orders without customers: {orphans}"

    def test_no_orphan_order_items(self):
        """Verify no orphan order_items exist without a corresponding valid order or product."""
        orphan_items_query = """
            SELECT oi.order_item_id
            FROM order_items oi
            LEFT JOIN orders o ON oi.order_id = o.order_id
            LEFT JOIN products p ON oi.product_id = p.product_id
            WHERE o.order_id IS NULL OR p.product_id IS NULL;
        """
        orphans = execute_select(orphan_items_query)
        assert len(orphans) == 0, f"Found orphan order items: {orphans}"

    def test_no_orphan_payments(self):
        """Verify no orphan payments exist without an associated order."""
        orphan_payments_query = """
            SELECT p.payment_id
            FROM payments p
            LEFT JOIN orders o ON p.order_id = o.order_id
            WHERE o.order_id IS NULL;
        """
        orphans = execute_select(orphan_payments_query)
        assert len(orphans) == 0, f"Found orphan payments: {orphans}"

    def test_not_null_mandatory_columns(self):
        """Verify NOT NULL constraints are enforced on required columns."""
        with pytest.raises(mysql.connector.Error) as exc_info:
            execute_insert(
                "INSERT INTO customers (first_name, last_name, email, password) VALUES (NULL, 'Doe', 'test@null.com', 'pass');"
            )
        assert "cannot be null" in str(exc_info.value).lower() or "not null" in str(exc_info.value).lower()

    def test_sql_injection_resistance(self):
        """Verify parameterized queries prevent SQL injection payloads like ' OR '1'='1."""
        injection_email = "' OR '1'='1"
        # Querying with parameterized SQL must safely treat the injection as literal string
        result = fetch_one(SELECT_CUSTOMER_BY_EMAIL, (injection_email,))
        assert result is None, "Injected SQL must not match any rows"

    def test_query_performance_baseline(self):
        """Measure execution performance of customer lookup and complex joins."""
        start_time = time.perf_counter()
        rows = execute_select("""
            SELECT o.order_id, c.first_name, c.email, COUNT(oi.order_item_id) as total_items, SUM(oi.subtotal) as calc_sum
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            GROUP BY o.order_id, c.first_name, c.email;
        """)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        # Normal local database query should comfortably execute in under 100ms
        assert elapsed_ms < 500, f"Join query took too long: {elapsed_ms:.2f}ms"
