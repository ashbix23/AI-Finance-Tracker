import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

MEMORY_PATH = os.getenv("MEMORY_PATH", "data/habits.json")


def load_habits() -> dict:
    if not os.path.exists(MEMORY_PATH):
        return {}

    try:
        with open(MEMORY_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_habits(habits: dict) -> None:
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, "w") as f:
        json.dump(habits, f, indent=2)


def update_habits(transactions: list, breakdown: dict) -> None:
    habits = load_habits()

    now = datetime.utcnow().isoformat()
    total_spent = round(sum(t["amount"] for t in transactions), 2)
    transaction_count = len(transactions)

    if "spending_history" not in habits:
        habits["spending_history"] = []

    habits["spending_history"].append({
        "recorded_at": now,
        "total_spent": total_spent,
        "transaction_count": transaction_count,
        "breakdown": breakdown,
    })

    habits["spending_history"] = habits["spending_history"][-12:]

    if "category_averages" not in habits:
        habits["category_averages"] = {}

    for category, amount in breakdown.items():
        history = habits["category_averages"].get(category, [])
        history.append(amount)
        history = history[-6:]
        habits["category_averages"][category] = history

    if "top_categories" not in habits:
        habits["top_categories"] = {}

    for category, amount in breakdown.items():
        existing = habits["top_categories"].get(category, 0)
        habits["top_categories"][category] = round(
            (existing * 0.7) + (amount * 0.3), 2
        )

    habits["top_categories"] = dict(
        sorted(habits["top_categories"].items(), key=lambda x: x[1], reverse=True)
    )

    if "patterns" not in habits:
        habits["patterns"] = {}

    for category, amount in breakdown.items():
        avg_history = habits["category_averages"].get(category, [amount])
        if len(avg_history) >= 2:
            avg = sum(avg_history[:-1]) / len(avg_history[:-1])
            latest = avg_history[-1]
            if avg > 0:
                change_pct = round(((latest - avg) / avg) * 100, 1)
                if abs(change_pct) >= 15:
                    habits["patterns"][category] = {
                        "trend": "increasing" if change_pct > 0 else "decreasing",
                        "change_pct": change_pct,
                        "detected_at": now,
                    }
                elif category in habits["patterns"]:
                    del habits["patterns"][category]

    habits["last_updated"] = now
    habits["total_transactions_tracked"] = habits.get(
        "total_transactions_tracked", 0
    ) + transaction_count

    save_habits(habits)


def get_habit_summary() -> dict:
    habits = load_habits()

    if not habits:
        return {"message": "No habits tracked yet."}

    summary = {
        "last_updated": habits.get("last_updated"),
        "total_transactions_tracked": habits.get("total_transactions_tracked", 0),
        "top_categories": habits.get("top_categories", {}),
        "active_patterns": habits.get("patterns", {}),
    }

    category_averages = habits.get("category_averages", {})
    if category_averages:
        summary["category_averages"] = {
            cat: round(sum(vals) / len(vals), 2)
            for cat, vals in category_averages.items()
        }

    return summary


def clear_habits() -> None:
    if os.path.exists(MEMORY_PATH):
        os.remove(MEMORY_PATH)
