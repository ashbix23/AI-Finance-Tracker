from fastapi import APIRouter, HTTPException
from api.models import CategoryResponse
from api.database import get_connection

router = APIRouter()


@router.get("/", response_model=list[CategoryResponse])
def get_categories():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM categories ORDER BY name ASC"
        ).fetchall()

    return [dict(row) for row in rows]


@router.get("/{name}", response_model=CategoryResponse)
def get_category(name: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM categories WHERE name = ?", (name.lower(),)
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Category '{name}' not found")

    return dict(row)


@router.get("/{name}/summary")
def get_category_summary(name: str, days: int = 30):
    with get_connection() as conn:
        category_row = conn.execute(
            "SELECT * FROM categories WHERE name = ?", (name.lower(),)
        ).fetchone()

        if not category_row:
            raise HTTPException(status_code=404, detail=f"Category '{name}' not found")

        rows = conn.execute(
            """
            SELECT
                COUNT(*) as transaction_count,
                ROUND(SUM(amount), 2) as total_spent,
                ROUND(AVG(amount), 2) as avg_transaction,
                MIN(amount) as min_transaction,
                MAX(amount) as max_transaction,
                MIN(date) as earliest,
                MAX(date) as latest
            FROM transactions
            WHERE category = ?
            AND date >= date('now', ? || ' days')
            """,
            (name.lower(), f"-{days}"),
        ).fetchone()

    return {
        "category": name.lower(),
        "period_days": days,
        "transaction_count": rows["transaction_count"] or 0,
        "total_spent": rows["total_spent"] or 0.0,
        "avg_transaction": rows["avg_transaction"] or 0.0,
        "min_transaction": rows["min_transaction"] or 0.0,
        "max_transaction": rows["max_transaction"] or 0.0,
        "earliest": rows["earliest"],
        "latest": rows["latest"],
    }
