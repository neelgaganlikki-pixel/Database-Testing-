-- ============================================================
-- E-Commerce Database Cleanup Script
-- Safely truncates/cleans tables in child-to-parent order
-- ============================================================

USE ecommerce_test;

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE payments;
TRUNCATE TABLE order_items;
TRUNCATE TABLE orders;
TRUNCATE TABLE cart_items;
TRUNCATE TABLE cart;
TRUNCATE TABLE addresses;
TRUNCATE TABLE products;
TRUNCATE TABLE categories;
TRUNCATE TABLE customers;

SET FOREIGN_KEY_CHECKS = 1;
