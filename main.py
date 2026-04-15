import sys
import os
from dotenv import load_dotenv

load_dotenv()

from agent.finance_agent import run_agent
from agent.memory import get_habit_summary
from api.database import init_db


def print_habits():
    summary = get_habit_summary()
    if "message" in summary:
        print(summary["message"])
        return

    print(f"Last updated: {summary.get('last_updated', 'unknown')}")
    print(f"Transactions tracked: {summary.get('total_transactions_tracked', 0)}")

    top = summary.get("top_categories", {})
    if top:
        print("\nTop categories:")
        for cat, score in list(top.items())[:5]:
            print(f"  {cat}: {score}")

    patterns = summary.get("active_patterns", {})
    if patterns:
        print("\nActive patterns:")
        for cat, data in patterns.items():
            print(f"  {cat}: {data['trend']} ({data['change_pct']:+.1f}%)")


def main():
    init_db()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "habits":
            print_habits()
            return

        if command == "ask":
            if len(sys.argv) < 3:
                print("Usage: python main.py ask \"your question here\"")
                sys.exit(1)
            question = " ".join(sys.argv[2:])
            print(f"\nQuestion: {question}")
            print("\nThinking...\n")
            response = run_agent(question)
            print(response)
            return

        print(f"Unknown command: {command}")
        print("Commands: habits, ask")
        sys.exit(1)

    print("AI Finance Tracker CLI")
    print("Commands: habits, ask")
    print()
    print("Examples:")
    print("  python main.py habits")
    print("  python main.py ask \"how much did I spend on food last month?\"")
    print("  python main.py ask \"what are my biggest expenses this week?\"")
    print()
    print("To start the API server:")
    print("  uvicorn api.main:app --reload")


if __name__ == "__main__":
    main()
