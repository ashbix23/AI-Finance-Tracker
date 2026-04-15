import os
import json
import anthropic
from dotenv import load_dotenv
from agent.tools import get_tools, run_tool
from agent.memory import load_habits, update_habits
from prompts.loader import load_prompt

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = os.getenv("FINANCE_MODEL", "claude-sonnet-4-5")


def categorize_transaction(description: str, amount: float) -> str:
    prompt = load_prompt("categorize").format(
        description=description,
        amount=amount,
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=64,
        messages=[{"role": "user", "content": prompt}],
    )

    category = response.content[0].text.strip().lower()

    valid = [
        "food", "transport", "subscriptions",
        "utilities", "shopping", "health", "entertainment", "other"
    ]

    return category if category in valid else "other"


def generate_insights(
    transactions: list,
    breakdown: dict,
    total_spent: float,
    period_days: int,
    focus: str = None,
    habits: dict = None,
) -> str:
    prompt = load_prompt("insights").format(
        period_days=period_days,
        total_spent=total_spent,
        transaction_count=len(transactions),
        breakdown=json.dumps(breakdown, indent=2),
        transactions=json.dumps(transactions[:50], indent=2),
        habits=json.dumps(habits or {}, indent=2),
        focus=focus or "general spending patterns",
    )

    messages = [{"role": "user", "content": prompt}]
    tools = get_tools()

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    update_habits(transactions, breakdown)
                    return block.text
            return "No insight generated."

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = run_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})

        else:
            break

    return "Insight generation stopped unexpectedly."


def run_agent(user_message: str) -> str:
    habits = load_habits()
    tools = get_tools()

    system = (
        "You are a personal finance assistant. You have access to the user's transaction "
        "database through tools. Use them to answer questions accurately with real numbers. "
        "Be concise, specific, and actionable. Always cite amounts and dates when relevant.\n\n"
        f"Known spending habits: {json.dumps(habits)}"
    )

    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "No response generated."

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = run_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})

        else:
            break

    return "Agent stopped unexpectedly."
