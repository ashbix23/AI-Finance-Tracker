import json
from api.database import get_connection


def get_tools():
    return [
        {
            "name": "query_transactions",
            "description": "Query transactions from the database with optional filters. Use this to retrieve spending data before generating insights or categorizing patterns.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of past days to query. Defaults to 30.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category name. Leave empty for all categories.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of transactions to return. Defaults to 100.",
                    },
                },
                "required": [],
            },
        },
        {
            "name": "get_category_breakdown",
            "description": "Get total spending per category for a given time period. Returns a ranked breakdown with counts and totals.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of past days to include in the breakdown.",
                    },
                },
                "required": [],
            },
        },
        {
            "name": "get_spending_trend",
            "description": "Compare spending in two consecutive periods to detect increases or decreases. Use this to identify trends.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category to compare. Leave empty to compare total spending.",
                    },
                    "period_days": {
                        "type": "integer",
                        "description": "Length of each period in days. Compares current period vs previous period.",
                    },
                },
                "required": [],
            },
        },
        {
            "name": "categorize",
            "description": "Determine the most appropriate spending category for a transaction based on its description and amount.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Transaction description to categorize.",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Transaction amount in dollars.",
                    },
                },
                "required": ["description", "amount"],
            },
        },
    ]


def run_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "query_transactions":
        return _query_transactions(**tool_input)
    elif tool_name == "get_category_breakdown":
        return _get_category_breakdown(**tool_input)
    elif tool_name == "get_spending_trend":
        return _get_spending_trend(**tool_input)
    elif tool_name == "categorize":
        return _categorize(**tool_input)
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


def _query_transactions(days: int = 30, category: str = None, limit: int = 100) -> str:
    query = """
        SELECT id, amount, description, category, date
        FROM transactions
        WHERE date >= date('now', ? || ' days')
    """
    params = [f"-{days}"]

    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY date DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return json.dumps([dict(row) for row in rows])


def _get_category_breakdown(days: int = 30) -> str:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                category,
                COUNT(*) as count,
                ROUND(SUM(amount), 2) as total,
                ROUND(AVG(amount), 2) as avg
            FROM transactions
            WHERE date >= date('now', ? || ' days')
            GROUP BY category
            ORDER BY total DESC
            """,
            (f"-{days}",),
        ).fetchall()

    return json.dumps([dict(row) for row in rows])


def _get_spending_trend(category: str = None, period_days: int = 30) -> str:
    with get_connection() as conn:
        if category:
            current = conn.execute(
                """
                SELECT ROUND(SUM(amount), 2) as total
                FROM transactions
                WHERE category = ?
                AND date >= date('now', ? || ' days')
                """,
                (category, f"-{period_days}"),
            ).fetchone()

            previous = conn.execute(
                """
                SELECT ROUND(SUM(amount), 2) as total
                FROM transactions
                WHERE category = ?
                AND date >= date('now', ? || ' days')
                AND date < date('now', ? || ' days')
                """,
                (category, f"-{period_days * 2}", f"-{period_days}"),
            ).fetchone()
        else:
            current = conn.execute(
                """
                SELECT ROUND(SUM(amount), 2) as total
                FROM transactions
                WHERE date >= date('now', ? || ' days')
                """,
                (f"-{period_days}",),
            ).fetchone()

            previous = conn.execute(
                """
                SELECT ROUND(SUM(amount), 2) as total
                FROM transactions
                WHERE date >= date('now', ? || ' days')
                AND date < date('now', ? || ' days')
                """,
                (f"-{period_days * 2}", f"-{period_days}"),
            ).fetchone()

    current_total = current["total"] or 0.0
    previous_total = previous["total"] or 0.0

    if previous_total > 0:
        change_pct = round(((current_total - previous_total) / previous_total) * 100, 1)
    else:
        change_pct = None

    return json.dumps({
        "category": category or "all",
        "period_days": period_days,
        "current_period": current_total,
        "previous_period": previous_total,
        "change_pct": change_pct,
        "direction": "up" if change_pct and change_pct > 0 else "down" if change_pct and change_pct < 0 else "flat",
    })


def _categorize(description: str, amount: float) -> str:
    categories = [
        "food", "transport", "subscriptions",
        "utilities", "shopping", "health", "entertainment", "other"
    ]
    return json.dumps({
        "description": description,
        "amount": amount,
        "available_categories": categories,
    })
