-- ============================================================
-- E-Commerce Seed Data
-- ============================================================

USE ecommerce_test;

SET FOREIGN_KEY_CHECKS = 0;

-- Clean existing data
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

-- 1. Insert Categories
INSERT INTO categories (category_id, category_name, description, status) VALUES
(1, 'Electronics', 'Smartphones, laptops, accessories, and gadgets', 'active'),
(2, 'Clothing & Apparel', 'Men and women casual and formal clothing', 'active'),
(3, 'Home & Kitchen', 'Home appliances, cookware, and furniture', 'active'),
(4, 'Books & Media', 'Physical books, eBooks, and media', 'active'),
(5, 'Sports & Fitness', 'Sporting goods, fitness equipment, and sportswear', 'active');

-- 2. Insert Products
INSERT INTO products (product_id, category_id, product_name, description, price, stock_quantity, status) VALUES
(1, 1, 'Pro Wireless Headphones', 'Noise-cancelling over-ear Bluetooth headphones', 149.99, 50, 'active'),
(2, 1, 'Ultra Slim Laptop 15-inch', '16GB RAM, 512GB NVMe SSD, Intel Core i7', 999.00, 20, 'active'),
(3, 1, 'Smart Watch Series 5', 'Waterproof fitness smartwatch with heart rate monitor', 199.50, 45, 'active'),
(4, 2, 'Classic Cotton Crew T-Shirt', '100% organic cotton breathable t-shirt', 24.99, 150, 'active'),
(5, 2, 'Slim Fit Denim Jeans', 'Stretchable comfortable blue denim jeans', 59.90, 80, 'active'),
(6, 3, 'Stainless Steel Coffee Maker', '12-cup programmable drip coffee machine', 79.99, 30, 'active'),
(7, 3, 'Non-Stick Cookware 10-Piece Set', 'Durable non-stick frying pans and pots', 129.00, 25, 'active'),
(8, 4, 'Clean Code: Handbook of Agile Software', 'Software engineering craftmanship book', 44.95, 60, 'active'),
(9, 5, 'Yoga Mat Non-Slip Extra Thick', 'Eco-friendly high-density workout mat', 29.99, 90, 'active'),
(10, 5, 'Adjustable Dumbbell Set 50lbs', 'Quick-adjust steel dumbbell pair', 249.99, 15, 'active');

-- 3. Insert Customers
INSERT INTO customers (customer_id, first_name, last_name, email, phone, password, status) VALUES
(1, 'Alex', 'Morgan', 'alex.morgan@example.com', '+1-555-0101', 'hashed_pass_123', 'active'),
(2, 'Jordan', 'Lee', 'jordan.lee@example.com', '+1-555-0102', 'hashed_pass_456', 'active'),
(3, 'Taylor', 'Swift', 'taylor.swift@example.com', '+1-555-0103', 'hashed_pass_789', 'active'),
(4, 'Casey', 'Neistat', 'casey.n@example.com', '+1-555-0104', 'hashed_pass_abc', 'active'),
(5, 'Sam', 'Wilson', 'sam.wilson@example.com', '+1-555-0105', 'hashed_pass_def', 'inactive');

-- 4. Insert Addresses
INSERT INTO addresses (address_id, customer_id, address_line, city, state, postal_code, country, is_default) VALUES
(1, 1, '123 Market Street, Apt 4B', 'San Francisco', 'California', '94105', 'USA', TRUE),
(2, 1, '456 Business Blvd, Suite 200', 'San Francisco', 'California', '94107', 'USA', FALSE),
(3, 2, '789 Pine Avenue', 'Seattle', 'Washington', '98101', 'USA', TRUE),
(4, 3, '321 Elm Court', 'Austin', 'Texas', '78701', 'USA', TRUE),
(5, 4, '654 Broadway', 'New York', 'New York', '10012', 'USA', TRUE);

-- 5. Insert Cart
INSERT INTO cart (cart_id, customer_id, status) VALUES
(1, 1, 'active'),
(2, 2, 'active'),
(3, 3, 'converted'),
(4, 4, 'abandoned');

-- 6. Insert Cart Items
INSERT INTO cart_items (cart_item_id, cart_id, product_id, quantity, price) VALUES
(1, 1, 1, 1, 149.99),
(2, 1, 4, 2, 24.99),
(3, 2, 2, 1, 999.00),
(4, 4, 9, 1, 29.99);

-- 7. Insert Orders
INSERT INTO orders (order_id, customer_id, order_number, total_amount, status) VALUES
(1, 1, 'ORD-2026-0001', 199.97, 'delivered'),
(2, 2, 'ORD-2026-0002', 1043.95, 'processing'),
(3, 3, 'ORD-2026-0003', 149.99, 'confirmed'),
(4, 4, 'ORD-2026-0004', 79.99, 'pending');

-- 8. Insert Order Items
INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price, subtotal) VALUES
(1, 1, 1, 1, 149.99, 149.99),
(2, 1, 4, 2, 24.99, 49.98),
(3, 2, 2, 1, 999.00, 999.00),
(4, 2, 8, 1, 44.95, 44.95),
(5, 3, 1, 1, 149.99, 149.99),
(6, 4, 6, 1, 79.99, 79.99);

-- 9. Insert Payments
INSERT INTO payments (payment_id, order_id, payment_reference, amount, payment_method, payment_status) VALUES
(1, 1, 'PAY-REF-9901A', 199.97, 'credit_card', 'completed'),
(2, 2, 'PAY-REF-9902B', 1043.95, 'paypal', 'completed'),
(3, 3, 'PAY-REF-9903C', 149.99, 'debit_card', 'completed'),
(4, 4, 'PAY-REF-9904D', 79.99, 'credit_card', 'pending');
