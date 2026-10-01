"""SQL Queries for Cart and Cart Items Operations."""

INSERT_OR_GET_CART = """
    INSERT INTO cart (customer_id, status)
    VALUES (%s, 'active')
    ON DUPLICATE KEY UPDATE status = 'active', updated_at = CURRENT_TIMESTAMP;
"""

SELECT_CART_BY_CUSTOMER = """
    SELECT cart_id, customer_id, status, created_at, updated_at
    FROM cart
    WHERE customer_id = %s;
"""

INSERT_CART_ITEM = """
    INSERT INTO cart_items (cart_id, product_id, quantity, price)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE 
        quantity = quantity + VALUES(quantity),
        price = VALUES(price);
"""

SELECT_CART_ITEMS_BY_CART_ID = """
    SELECT ci.cart_item_id, ci.cart_id, ci.product_id, ci.quantity, ci.price,
           p.product_name, (ci.quantity * ci.price) as item_total
    FROM cart_items ci
    JOIN products p ON ci.product_id = p.product_id
    WHERE ci.cart_id = %s;
"""

SELECT_CART_WITH_ITEMS_BY_CUSTOMER = """
    SELECT c.cart_id, c.customer_id, c.status as cart_status,
           ci.cart_item_id, ci.product_id, p.product_name, ci.quantity, ci.price,
           (ci.quantity * ci.price) as item_total
    FROM cart c
    LEFT JOIN cart_items ci ON c.cart_id = ci.cart_id
    LEFT JOIN products p ON ci.product_id = p.product_id
    WHERE c.customer_id = %s;
"""

DELETE_CART_ITEMS_BY_CART = """
    DELETE FROM cart_items
    WHERE cart_id = %s;
"""

DELETE_CART_ITEM = """
    DELETE FROM cart_items
    WHERE cart_item_id = %s;
"""
