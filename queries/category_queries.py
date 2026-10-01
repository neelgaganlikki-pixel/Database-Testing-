"""SQL Queries for Categories Table Operations."""

INSERT_CATEGORY = """
    INSERT INTO categories (category_name, description, status)
    VALUES (%s, %s, %s);
"""

SELECT_CATEGORY_BY_ID = """
    SELECT category_id, category_name, description, status, created_at
    FROM categories
    WHERE category_id = %s;
"""

SELECT_CATEGORY_BY_NAME = """
    SELECT category_id, category_name, description, status, created_at
    FROM categories
    WHERE category_name = %s;
"""

SELECT_ALL_CATEGORIES = """
    SELECT category_id, category_name, description, status, created_at
    FROM categories
    ORDER BY category_id ASC;
"""

UPDATE_CATEGORY = """
    UPDATE categories
    SET category_name = %s, description = %s, status = %s
    WHERE category_id = %s;
"""

DELETE_CATEGORY = """
    DELETE FROM categories
    WHERE category_id = %s;
"""
