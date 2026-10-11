CREATE EXTENSION IF NOT EXISTS vector;


-- =========================================
-- CUSTOMERS
-- =========================================

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    region VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================
-- PRODUCTS
-- =========================================

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(100),
    price NUMERIC(10, 2)
);


-- =========================================
-- ORDERS
-- =========================================

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    order_date TIMESTAMP,
    status VARCHAR(50)
);


-- =========================================
-- ORDER ITEMS
-- =========================================

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    product_id INT REFERENCES products(product_id),
    quantity INT,
    unit_price NUMERIC(10, 2)
);


-- =========================================
-- PAYMENTS
-- =========================================

CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    amount NUMERIC(10, 2),
    payment_method VARCHAR(50),
    payment_date TIMESTAMP
);


-- =========================================
-- Pgvector documents table
-- =========================================


CREATE TABLE knowledge_chunks (
    id BIGSERIAL PRIMARY KEY,

    source_type VARCHAR(100),
    source_name VARCHAR(255),

    content TEXT NOT NULL,

    embedding VECTOR(384),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);