"""Pydantic schemas for request validation and response serialization."""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from src.models.transaction import TransactionType, RecurrencePattern


# ---------------------------------------------------------------------------
# Shared base
# ---------------------------------------------------------------------------

class TransactionBase(BaseModel):
    date: date
    amount: float = Field(..., gt=0, description="Must be positive")
    type: TransactionType
    description: str = ""
    category: str = ""
    payee: str = ""


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class TransactionCreate(TransactionBase):
    is_template: bool = False
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurring_template_id: Optional[int] = None


class TransactionUpdate(BaseModel):
    date: Optional[date] = None
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[TransactionType] = None
    description: Optional[str] = None
    category: Optional[str] = None
    payee: Optional[str] = None
    recurrence_pattern: Optional[RecurrencePattern] = None


class TransactionBatchCreate(BaseModel):
    transactions: List[TransactionCreate]


# ---------------------------------------------------------------------------
# Response bodies
# ---------------------------------------------------------------------------

class TransactionResponse(TransactionBase):
    id: int
    is_template: bool
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurring_template_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WeeklyBalanceResponse(BaseModel):
    week_start: date
    week_end: date
    starting_balance: float
    ending_balance: float
    net_change: float


class BalanceResponse(BaseModel):
    date: date
    balance: float


class ImportResultResponse(BaseModel):
    imported: int
    skipped: int
    errors: List[str] = []
