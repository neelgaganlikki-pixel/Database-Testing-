"""SQL Queries for Orders and Order Items Operations."""

INSERT_ORDER = """
    INSERT INTO orders (customer_id, order_number, total_amount, status)
    VALUES (%s, %s, %s, %s);
"""

SELECT_ORDER_BY_ID = """
    SELECT order_id, customer_id, order_number, total_amount, status, created_at, updated_at
    FROM orders
    WHERE order_id = %s;
"""

SELECT_ORDER_BY_NUMBER = """
    SELECT order_id, customer_id, order_number, total_amount, status, created_at, updated_at
    FROM orders
    WHERE order_number = %s;
"""

SELECT_ORDERS_BY_CUSTOMER = """
    SELECT order_id, customer_id, order_number, total_amount, status, created_at, updated_at
    FROM orders
    WHERE customer_id = %s
    ORDER BY order_id DESC;
"""

UPDATE_ORDER_STATUS = """
    UPDATE orders
    SET status = %s
    WHERE order_id = %s;
"""

DELETE_ORDER = """
    DELETE FROM orders
    WHERE order_id = %s;
"""

INSERT_ORDER_ITEM = """
    INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
    VALUES (%s, %s, %s, %s, %s);
"""

SELECT_ORDER_ITEMS_BY_ORDER_ID = """
    SELECT oi.order_item_id, oi.order_id, oi.product_id, oi.quantity, oi.unit_price, oi.subtotal,
           p.product_name
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    WHERE oi.order_id = %s;
"""

SELECT_ORDER_WITH_CUSTOMER_AND_ITEMS = """
    SELECT 
        o.order_id, o.order_number, o.total_amount, o.status, o.created_at,
        c.customer_id, c.first_name, c.last_name, c.email,
        oi.order_item_id, oi.product_id, oi.quantity, oi.unit_price, oi.subtotal,
        p.product_name
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    LEFT JOIN products p ON oi.product_id = p.product_id
    WHERE o.order_id = %s;
"""

CALCULATE_ORDER_SUM_SUBTOTAL = """
    SELECT COALESCE(SUM(subtotal), 0.00) as calculated_total
    FROM order_items
    WHERE order_id = %s;
"""
