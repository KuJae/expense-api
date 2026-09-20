from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


class TransactionCreate(BaseModel):
    amount: float = Field(gt=0)
    type: TransactionType
    category: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)
    occurred_on: date


class TransactionOut(BaseModel):
    id: int
    amount: float
    type: TransactionType
    category: str
    description: str | None
    occurred_on: date
    created_at: datetime
