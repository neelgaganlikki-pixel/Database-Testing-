"""SQL Queries for Customers Table Operations."""

INSERT_CUSTOMER = """
    INSERT INTO customers (first_name, last_name, email, phone, password, status)
    VALUES (%s, %s, %s, %s, %s, %s);
"""

SELECT_CUSTOMER_BY_ID = """
    SELECT customer_id, first_name, last_name, email, phone, status, created_at, updated_at
    FROM customers
    WHERE customer_id = %s;
"""

SELECT_CUSTOMER_BY_EMAIL = """
    SELECT customer_id, first_name, last_name, email, phone, status, created_at, updated_at
    FROM customers
    WHERE email = %s;
"""

SELECT_ALL_CUSTOMERS = """
    SELECT customer_id, first_name, last_name, email, phone, status, created_at, updated_at
    FROM customers
    ORDER BY customer_id DESC
    LIMIT %s OFFSET %s;
"""

UPDATE_CUSTOMER = """
    UPDATE customers
    SET first_name = %s, last_name = %s, phone = %s, status = %s
    WHERE customer_id = %s;
"""

DELETE_CUSTOMER = """
    DELETE FROM customers
    WHERE customer_id = %s;
"""

COUNT_CUSTOMERS_BY_EMAIL = """
    SELECT COUNT(*) as count
    FROM customers
    WHERE email = %s;
"""

SELECT_CUSTOMER_WITH_ADDRESSES = """
    SELECT c.customer_id, c.first_name, c.last_name, c.email,
           a.address_id, a.address_line, a.city, a.state, a.postal_code, a.country, a.is_default
    FROM customers c
    LEFT JOIN addresses a ON c.customer_id = a.customer_id
    WHERE c.customer_id = %s;
"""
