import pytest
from database.connection import execute_select, fetch_one

@pytest.mark.database
@pytest.mark.regression
class TestSQLJoinsAndAggregations:
    """Automated tests for SQL JOINs, multi-table relationships, and aggregations."""

    def test_customer_orders_join(self):
        """Test JOIN: Customers + Orders relationship."""
        query = """
            SELECT c.customer_id, c.first_name, c.email, o.order_id, o.order_number, o.total_amount
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            WHERE o.order_id = 1;
        """
        result = fetch_one(query)
        assert result is not None
        assert result["customer_id"] == 1
        assert "ORD-2026-0001" in result["order_number"]
        assert float(result["total_amount"]) > 0

    def test_order_items_products_join(self):
        """Test JOIN: Orders + Order Items + Products."""
        query = """
            SELECT o.order_number, oi.quantity, oi.unit_price, oi.subtotal, p.product_name
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE o.order_id = 1;
        """
        rows = execute_select(query)
        assert len(rows) >= 1
        for row in rows:
            assert row["quantity"] > 0
            assert float(row["unit_price"]) > 0
            assert round(row["quantity"] * float(row["unit_price"]), 2) == round(float(row["subtotal"]), 2)

    def test_products_categories_join(self):
        """Test JOIN: Products + Categories relationship."""
        query = """
            SELECT p.product_id, p.product_name, p.price, c.category_name
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE c.category_id = 1;
        """
        rows = execute_select(query)
        assert len(rows) > 0
        for row in rows:
            assert row["category_name"] == "Electronics"

    def test_orders_payments_join(self):
        """Test JOIN: Orders + Payments."""
        query = """
            SELECT o.order_id, o.order_number, o.total_amount, p.payment_reference, p.amount, p.payment_status
            FROM orders o
            JOIN payments p ON o.order_id = p.order_id
            WHERE o.order_id = 1;
        """
        result = fetch_one(query)
        assert result is not None
        assert float(result["total_amount"]) == float(result["amount"])
        assert result["payment_status"] == "completed"

    def test_customer_addresses_join(self):
        """Test JOIN: Customers + Addresses."""
        query = """
            SELECT c.customer_id, c.first_name, a.city, a.state, a.postal_code, a.country
            FROM customers c
            JOIN addresses a ON c.customer_id = a.customer_id
            WHERE c.customer_id = 1;
        """
        addresses = execute_select(query)
        assert len(addresses) >= 1
        assert addresses[0]["city"] == "San Francisco"

    def test_cart_items_products_join(self):
        """Test JOIN: Cart + Cart Items + Products."""
        query = """
            SELECT c.cart_id, c.customer_id, ci.quantity, p.product_name, p.price
            FROM cart c
            JOIN cart_items ci ON c.cart_id = ci.cart_id
            JOIN products p ON ci.product_id = p.product_id
            WHERE c.cart_id = 1;
        """
        items = execute_select(query)
        assert len(items) >= 1
        for it in items:
            assert it["quantity"] > 0
            assert float(it["price"]) > 0

    def test_aggregation_order_total_equals_sum_subtotal(self):
        """Test Aggregation: Verify that order total equals SUM(order_items.subtotal)."""
        query = """
            SELECT 
                o.order_id,
                o.total_amount,
                SUM(oi.subtotal) as sum_items_subtotal,
                COUNT(oi.order_item_id) as total_items_count
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.order_id = 1
            GROUP BY o.order_id, o.total_amount;
        """
        res = fetch_one(query)
        assert res is not None
        order_total = round(float(res["total_amount"]), 2)
        calc_subtotal = round(float(res["sum_items_subtotal"]), 2)
        assert order_total == calc_subtotal, f"Order total {order_total} != calculated items sum {calc_subtotal}"

    def test_aggregation_metrics_group_by_having(self):
        """Test Aggregation: COUNT(), SUM(), AVG(), MIN(), MAX(), GROUP BY, HAVING."""
        query = """
            SELECT 
                c.category_name,
                COUNT(p.product_id) as prod_count,
                SUM(p.stock_quantity) as total_stock,
                AVG(p.price) as avg_price,
                MIN(p.price) as min_price,
                MAX(p.price) as max_price
            FROM categories c
            JOIN products p ON c.category_id = p.category_id
            GROUP BY c.category_id, c.category_name
            HAVING prod_count > 0;
        """
        rows = execute_select(query)
        assert len(rows) > 0
        for r in rows:
            assert r["prod_count"] > 0
            assert float(r["min_price"]) <= float(r["max_price"])
            assert float(r["avg_price"]) >= float(r["min_price"])
