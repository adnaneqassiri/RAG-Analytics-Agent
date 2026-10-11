from langchain_core.tools import tool

DB_SCHEMA = """
DATABASE: PostgreSQL e-commerce database

TABLE customers
- customer_id INTEGER PRIMARY KEY
- name VARCHAR
- region VARCHAR
- created_at TIMESTAMP

TABLE products
- product_id INTEGER PRIMARY KEY
- name VARCHAR
- category VARCHAR
- price NUMERIC

TABLE orders
- order_id INTEGER PRIMARY KEY
- customer_id INTEGER FOREIGN KEY REFERENCES customers(customer_id)
- order_date TIMESTAMP
- status VARCHAR (Possible values: 'completed', 'cancelled', 'pending')

TABLE order_items
- order_item_id INTEGER PRIMARY KEY
- order_id INTEGER FOREIGN KEY REFERENCES orders(order_id)
- product_id INTEGER FOREIGN KEY REFERENCES products(product_id)
- quantity INTEGER
- unit_price NUMERIC

TABLE payments
- payment_id INTEGER PRIMARY KEY
- order_id INTEGER FOREIGN KEY REFERENCES orders(order_id)
- amount NUMERIC
- payment_method VARCHAR
- payment_date TIMESTAMP

RELATIONSHIPS
- customers.customer_id = orders.customer_id
- orders.order_id = order_items.order_id
- products.product_id = order_items.product_id
- orders.order_id = payments.order_id

CRITICAL SQL RULES & GUARDRAILS:
1. COLUMN OWNERSHIP: 'order_date' exists ONLY on the 'orders' table. NEVER select or filter 'order_items.order_date'. You MUST join 'orders' on 'order_items.order_id = orders.order_id'.
2. SALES CALCULATION: Total sales = SUM(order_items.quantity * order_items.unit_price).
3. ORDER STATUS: Unless specified otherwise, exclude cancelled orders from sales analysis using `orders.status != 'cancelled'` or `orders.status = 'completed'`.
4. POSTGRESQL DATES: For month/year filtering, use explicit ranges (e.g., `o.order_date >= '2026-06-01' AND o.order_date < '2026-07-01'`) or `DATE_TRUNC('month', o.order_date)` instead of non-standard date functions.
5. PREFER SINGLE QUERIES: Always try to answer comparison queries (e.g., June vs July) in a single unified SQL query using conditional aggregation or CTEs.
"""


def create_rag_tool():
    @tool
    def get_db_context():
        """Function to retrieve the db context, db schema, KPIs, database structure"""
        return DB_SCHEMA
    return get_db_context