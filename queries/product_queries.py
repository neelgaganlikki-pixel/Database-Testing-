"""SQL Queries for Products Table Operations."""

INSERT_PRODUCT = """
    INSERT INTO products (category_id, product_name, description, price, stock_quantity, status)
    VALUES (%s, %s, %s, %s, %s, %s);
"""

SELECT_PRODUCT_BY_ID = """
    SELECT product_id, category_id, product_name, description, price, stock_quantity, status, created_at, updated_at
    FROM products
    WHERE product_id = %s;
"""

SELECT_ALL_PRODUCTS = """
    SELECT product_id, category_id, product_name, description, price, stock_quantity, status, created_at, updated_at
    FROM products
    ORDER BY product_id DESC
    LIMIT %s OFFSET %s;
"""

UPDATE_PRODUCT = """
    UPDATE products
    SET product_name = %s, description = %s, price = %s, stock_quantity = %s, status = %s
    WHERE product_id = %s;
"""

UPDATE_PRODUCT_STOCK = """
    UPDATE products
    SET stock_quantity = stock_quantity - %s
    WHERE product_id = %s AND stock_quantity >= %s;
"""

DELETE_PRODUCT = """
    DELETE FROM products
    WHERE product_id = %s;
"""

SELECT_PRODUCTS_BY_CATEGORY = """
    SELECT p.product_id, p.product_name, p.price, p.stock_quantity, c.category_name
    FROM products p
    JOIN categories c ON p.category_id = c.category_id
    WHERE p.category_id = %s;
"""

AGGREGATE_PRODUCT_METRICS = """
    SELECT 
        COUNT(*) as total_products,
        SUM(stock_quantity) as total_stock,
        AVG(price) as avg_price,
        MIN(price) as min_price,
        MAX(price) as max_price
    FROM products;
"""

AGGREGATE_PRODUCTS_BY_CATEGORY = """
    SELECT 
        c.category_name,
        COUNT(p.product_id) as product_count,
        AVG(p.price) as avg_price,
        SUM(p.stock_quantity) as total_stock
    FROM categories c
    LEFT JOIN products p ON c.category_id = p.category_id
    GROUP BY c.category_id, c.category_name
    HAVING product_count > 0;
"""
