from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date


class TransactionCreate(BaseModel):
    amount: float
    description: str
    date: str
    category: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("amount must be greater than 0")
        return round(v, 2)

    @field_validator("date")
    @classmethod
    def date_must_be_valid(cls, v):
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("date must be in YYYY-MM-DD format")
        return v

    @field_validator("description")
    @classmethod
    def description_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("description cannot be empty")
        return v.strip()


class TransactionResponse(BaseModel):
    id: int
    amount: float
    description: str
    category: Optional[str]
    date: str
    created_at: str


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]


class InsightRequest(BaseModel):
    period_days: Optional[int] = 30
    focus: Optional[str] = None


class InsightResponse(BaseModel):
    period_days: int
    total_spent: float
    transaction_count: int
    breakdown: dict
    insight: str
    habits: Optional[dict] = None
