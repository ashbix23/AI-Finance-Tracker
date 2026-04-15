import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.database import init_db, get_connection

TRANSACTIONS = [
    ("Starbucks", "food", 5.75),
    ("Chipotle", "food", 12.50),
    ("Whole Foods", "food", 87.32),
    ("DoorDash", "food", 34.20),
    ("Trader Joes", "food", 62.15),
    ("McDonalds", "food", 8.90),
    ("Sweetgreen", "food", 16.45),
    ("Uber", "transport", 18.50),
    ("Lyft", "transport", 22.30),
    ("Shell Gas Station", "transport", 54.00),
    ("Metro Card", "transport", 33.00),
    ("Parking Meter", "transport", 6.00),
    ("Netflix", "subscriptions", 15.99),
    ("Spotify", "subscriptions", 9.99),
    ("AWS", "subscriptions", 120.00),
    ("GitHub", "subscriptions", 4.00),
    ("ChatGPT Plus", "subscriptions", 20.00),
    ("Adobe Creative Cloud", "subscriptions", 54.99),
    ("PG&E", "utilities", 110.00),
    ("Comcast Internet", "utilities", 79.99),
    ("AT&T", "utilities", 65.00),
    ("Amazon", "shopping", 43.99),
    ("Target", "shopping", 67.23),
    ("Nike", "shopping", 89.00),
    ("Apple Store", "shopping", 129.00),
    ("CVS Pharmacy", "health", 22.40),
    ("Gym Membership", "health", 45.00),
    ("Walgreens", "health", 14.75),
    ("AMC Theaters", "entertainment", 16.00),
    ("Steam", "entertainment", 29.99),
    ("Ticketmaster", "entertainment", 85.00),
]


def random_date(days_ago_start: int, days_ago_end: int) -> str:
    delta = random.randint(days_ago_end, days_ago_start)
    date = datetime.now(datetime.UTC) - timedelta(days=delta)
    return date.strftime("%Y-%m-%d")


def seed(months: int = 3):
    init_db()

    with get_connection() as conn:
        existing = conn.execute("SELECT COUNT(*) as count FROM transactions").fetchone()
        if existing["count"] > 0:
            print(f"Database already has {existing['count']} transactions. Skipping seed.")
            print("To reseed, delete data/finance.db and run again.")
            return

    total_days = months * 30
    records = []

    for description, category, base_amount in TRANSACTIONS:
        occurrences = random.randint(2, 5) if "subscriptions" not in category else months
        for _ in range(occurrences):
            variance = random.uniform(-0.15, 0.15)
            amount = round(base_amount * (1 + variance), 2)
            date = random_date(total_days, 0)
            records.append((amount, description, category, date))

    random.shuffle(records)

    with get_connection() as conn:
        conn.executemany(
            "INSERT INTO transactions (amount, description, category, date) VALUES (?, ?, ?, ?)",
            records,
        )
        conn.commit()

    print(f"Seeded {len(records)} transactions across {months} months.")
    print("Run `uvicorn api.main:app --reload` to start the API.")


if __name__ == "__main__":
    months = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    seed(months)
