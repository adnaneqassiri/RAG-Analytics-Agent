import os
import random
from datetime import datetime, timedelta

import psycopg
from faker import Faker
from dotenv import load_dotenv


load_dotenv()
DB_URL = os.getenv(
    "DB_URL",
    "postgresql://analytics:analytics123@localhost:5432/analytics_db"
)

fake = Faker()
Faker.seed(42)
random.seed(42)


NUM_CUSTOMERS = 500

CATEGORIES = {
    "Electronics": (100, 1200),
    "Furniture": (80, 800),
    "Clothing": (20, 150),
    "Books": (10, 60),
    "Home Appliances": (70, 700),
    "Sports": (20, 300),
}

REGIONS = [
    "North",
    "South",
    "East",
    "West",
    "Central",
]


def create_customers(cur):
    print("Creating customers...")

    customers = []

    for _ in range(NUM_CUSTOMERS):

        created_at = datetime(2024, 1, 1) + timedelta(
            days=random.randint(0, 700)
        )

        customers.append(
            (
                fake.name(),
                random.choice(REGIONS),
                created_at,
            )
        )

    cur.executemany(
        """
        INSERT INTO customers (name, region, created_at)
        VALUES (%s, %s, %s)
        """,
        customers,
    )


def create_products(cur):
    print("Creating products...")

    products = []

    for category, (min_price, max_price) in CATEGORIES.items():

        for i in range(10):

            price = round(
                random.uniform(min_price, max_price),
                2
            )

            products.append(
                (
                    f"{category} Product {i + 1}",
                    category,
                    price,
                )
            )

    cur.executemany(
        """
        INSERT INTO products (name, category, price)
        VALUES (%s, %s, %s)
        """,
        products,
    )


def get_products(cur):

    cur.execute(
        """
        SELECT product_id, category, price
        FROM products
        """
    )

    rows = cur.fetchall()

    products_by_category = {}

    for product_id, category, price in rows:

        products_by_category.setdefault(
            category,
            []
        ).append(
            (
                product_id,
                float(price),
            )
        )

    return products_by_category


def choose_category(month):
    """
    Deliberately create a decline in Electronics
    and Furniture during Aug/Sep 2026.

    This gives our future analytics agent
    something meaningful to discover.
    """

    categories = list(CATEGORIES.keys())

    # Normal demand
    weights = [
        0.25,  # Electronics
        0.18,  # Furniture
        0.18,  # Clothing
        0.12,  # Books
        0.15,  # Home Appliances
        0.12,  # Sports
    ]

    # Recent decline
    if month in [8, 9]:

        weights = [
            0.12,  # Electronics drops heavily
            0.10,  # Furniture drops
            0.26,  # Clothing grows
            0.17,
            0.18,
            0.17,
        ]

    return random.choices(
        categories,
        weights=weights,
        k=1
    )[0]


def create_orders(cur):
    print("Creating orders...")

    products_by_category = get_products(cur)

    start_date = datetime(2025, 10, 1)

    # Monthly order volumes.
    # August and September deliberately decline.
    monthly_orders = {
        (2025, 10): 450,
        (2025, 11): 470,
        (2025, 12): 550,
        (2026, 1): 480,
        (2026, 2): 500,
        (2026, 3): 520,
        (2026, 4): 540,
        (2026, 5): 570,
        (2026, 6): 590,
        (2026, 7): 610,
        (2026, 8): 520,
        (2026, 9): 430,
    }

    order_counter = 0

    for (year, month), order_count in monthly_orders.items():

        for _ in range(order_count):

            customer_id = random.randint(
                1,
                NUM_CUSTOMERS
            )

            day = random.randint(1, 28)

            order_date = datetime(
                year,
                month,
                day,
                random.randint(8, 22),
                random.randint(0, 59),
            )

            status = random.choices(
                ["completed", "cancelled", "pending"],
                weights=[0.92, 0.05, 0.03],
                k=1,
            )[0]

            cur.execute(
                """
                INSERT INTO orders (
                    customer_id,
                    order_date,
                    status
                )
                VALUES (%s, %s, %s)
                RETURNING order_id
                """,
                (
                    customer_id,
                    order_date,
                    status,
                ),
            )

            order_id = cur.fetchone()[0]

            category = choose_category(month)

            number_items = random.randint(1, 3)

            total_amount = 0

            for _ in range(number_items):

                product_id, base_price = random.choice(
                    products_by_category[category]
                )

                quantity = random.randint(1, 3)

                # Small price variation
                actual_price = round(
                    base_price
                    * random.uniform(0.90, 1.10),
                    2,
                )

                total_amount += quantity * actual_price

                cur.execute(
                    """
                    INSERT INTO order_items (
                        order_id,
                        product_id,
                        quantity,
                        unit_price
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        order_id,
                        product_id,
                        quantity,
                        actual_price,
                    ),
                )

            if status == "completed":

                cur.execute(
                    """
                    INSERT INTO payments (
                        order_id,
                        amount,
                        payment_method,
                        payment_date
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        order_id,
                        round(total_amount, 2),
                        random.choice(
                            [
                                "card",
                                "bank_transfer",
                                "paypal",
                            ]
                        ),
                        order_date
                        + timedelta(
                            minutes=random.randint(1, 60)
                        ),
                    ),
                )

            order_counter += 1

    print(
        f"Created {order_counter} orders."
    )


def main():

    print("Connecting to PostgreSQL...")

    with psycopg.connect(DB_URL) as conn:

        with conn.cursor() as cur:

            print("Cleaning existing data...")

            cur.execute(
                """
                TRUNCATE TABLE
                    payments,
                    order_items,
                    orders,
                    products,
                    customers
                RESTART IDENTITY CASCADE;
                """
            )

            create_customers(cur)
            create_products(cur)
            create_orders(cur)

        conn.commit()

    print("Database population finished.")


if __name__ == "__main__":
    main()
