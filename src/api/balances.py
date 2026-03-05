"""Balance calculation API routes."""

from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query

from src.models.database import Database, get_db
from src.schemas.transaction import BalanceResponse, WeeklyBalanceResponse
from src.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/balances", tags=["balances"])


def _service(db: Database = Depends(get_db)) -> TransactionService:
    return TransactionService(db)


@router.get("/current", response_model=BalanceResponse)
def get_current_balance(
    as_of: date = Query(default=None, description="Balance up to this date (inclusive); defaults to today"),
    svc: TransactionService = Depends(_service),
):
    target = as_of or date.today()
    balance = svc.calculate_balance_up_to_date(target)
    return BalanceResponse(date=target, balance=balance)


@router.get("/weekly", response_model=List[WeeklyBalanceResponse])
def get_weekly_balances(
    year: int = Query(default=None),
    month: int = Query(default=None),
    svc: TransactionService = Depends(_service),
):
    today = date.today()
    y = year or today.year
    m = month or today.month
    weekly = svc.calculate_weekly_balances(y, m)
    return [
        WeeklyBalanceResponse(
            week_start=w.week_start,
            week_end=w.week_end,
            starting_balance=w.starting_balance,
            ending_balance=w.ending_balance,
            net_change=w.net_change,
        )
        for w in weekly
    ]
