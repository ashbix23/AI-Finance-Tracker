from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from api.models import TransactionCreate, TransactionResponse
from api.database import get_connection
from agent.finance_agent import categorize_transaction

router = APIRouter()


@router.post("/", response_model=TransactionResponse)
def create_transaction(transaction: TransactionCreate):
    category = transaction.category

    if not category:
        category = categorize_transaction(
            transaction.description, transaction.amount
        )

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO transactions (amount, description, category, date)
            VALUES (?, ?, ?, ?)
            """,
            (transaction.amount, transaction.description, category, transaction.date),
        )
        conn.commit()
        transaction_id = cursor.lastrowid

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (transaction_id,)
        ).fetchone()

    return dict(row)


@router.get("/", response_model=list[TransactionResponse])
def get_transactions(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    category: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
):
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (transaction_id,)
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return dict(row)


@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (transaction_id,)
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Transaction not found")

        conn.execute(
            "DELETE FROM transactions WHERE id = ?", (transaction_id,)
        )
        conn.commit()

    return {"deleted": transaction_id}
