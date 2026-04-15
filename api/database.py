import sqlite3
import os
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/finance.db")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                description TEXT NOT NULL,
                category TEXT,
                date TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            );

            INSERT OR IGNORE INTO categories (name, description) VALUES
                ('food', 'Groceries, restaurants, coffee, delivery'),
                ('transport', 'Uber, gas, parking, public transit'),
                ('subscriptions', 'Netflix, Spotify, SaaS, recurring bills'),
                ('utilities', 'Electricity, internet, phone, water'),
                ('shopping', 'Clothing, electronics, Amazon, retail'),
                ('health', 'Pharmacy, gym, doctor, insurance'),
                ('entertainment', 'Movies, events, games, hobbies'),
                ('other', 'Anything that does not fit above');
        """)
        conn.commit()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
