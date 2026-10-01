"""SQL Queries for Payments Table Operations."""

INSERT_PAYMENT = """
    INSERT INTO payments (order_id, payment_reference, amount, payment_method, payment_status)
    VALUES (%s, %s, %s, %s, %s);
"""

SELECT_PAYMENT_BY_ID = """
    SELECT payment_id, order_id, payment_reference, amount, payment_method, payment_status, created_at
    FROM payments
    WHERE payment_id = %s;
"""

SELECT_PAYMENT_BY_ORDER_ID = """
    SELECT payment_id, order_id, payment_reference, amount, payment_method, payment_status, created_at
    FROM payments
    WHERE order_id = %s;
"""

SELECT_PAYMENT_BY_REFERENCE = """
    SELECT payment_id, order_id, payment_reference, amount, payment_method, payment_status, created_at
    FROM payments
    WHERE payment_reference = %s;
"""

UPDATE_PAYMENT_STATUS = """
    UPDATE payments
    SET payment_status = %s
    WHERE payment_id = %s;
"""

DELETE_PAYMENT = """
    DELETE FROM payments
    WHERE payment_id = %s;
"""

SELECT_PAYMENT_WITH_ORDER_DETAILS = """
    SELECT 
        p.payment_id, p.payment_reference, p.amount as payment_amount, p.payment_method, p.payment_status,
        o.order_id, o.order_number, o.total_amount as order_total, o.status as order_status,
        c.customer_id, c.first_name, c.last_name, c.email
    FROM payments p
    JOIN orders o ON p.order_id = o.order_id
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE p.payment_id = %s;
"""
