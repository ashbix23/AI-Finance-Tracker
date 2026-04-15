from fastapi import APIRouter, HTTPException
from api.models import InsightRequest, InsightResponse
from api.database import get_connection
from agent.finance_agent import generate_insights
from agent.memory import load_habits

router = APIRouter()


@router.post("/", response_model=InsightResponse)
def get_insights(request: InsightRequest = InsightRequest()):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM transactions
            WHERE date >= date('now', ? || ' days')
            ORDER BY date DESC
            """,
            (f"-{request.period_days}",),
        ).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No transactions found in the last {request.period_days} days.",
        )

    transactions = [dict(row) for row in rows]

    total_spent = round(sum(t["amount"] for t in transactions), 2)

    breakdown = {}
    for t in transactions:
        cat = t["category"] or "other"
        breakdown[cat] = round(breakdown.get(cat, 0) + t["amount"], 2)

    habits = load_habits()

    insight = generate_insights(
        transactions=transactions,
        breakdown=breakdown,
        total_spent=total_spent,
        period_days=request.period_days,
        focus=request.focus,
        habits=habits,
    )

    return InsightResponse(
        period_days=request.period_days,
        total_spent=total_spent,
        transaction_count=len(transactions),
        breakdown=breakdown,
        insight=insight,
        habits=habits,
    )


@router.get("/summary")
def get_quick_summary(days: int = 7):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                category,
                COUNT(*) as count,
                ROUND(SUM(amount), 2) as total
            FROM transactions
            WHERE date >= date('now', ? || ' days')
            GROUP BY category
            ORDER BY total DESC
            """,
            (f"-{days}",),
        ).fetchall()

    if not rows:
        return {"period_days": days, "message": "No transactions found.", "breakdown": {}}

    breakdown = {row["category"]: {"count": row["count"], "total": row["total"]} for row in rows}
    grand_total = round(sum(row["total"] for row in rows), 2)

    return {
        "period_days": days,
        "grand_total": grand_total,
        "breakdown": breakdown,
    }
