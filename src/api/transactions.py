"""Transaction CRUD API routes."""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.models.database import Database, get_db
from src.models.transaction import Transaction, TransactionType
from src.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionBatchCreate,
)
from src.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def _service(db: Database = Depends(get_db)) -> TransactionService:
    return TransactionService(db)


def _to_response(t: Transaction) -> TransactionResponse:
    return TransactionResponse(
        id=t.id,
        date=t.date,
        amount=t.amount,
        type=t.type,
        description=t.description,
        category=t.category,
        payee=t.payee,
        is_template=t.is_template,
        recurrence_pattern=t.recurrence_pattern,
        recurring_template_id=t.recurring_template_id,
        created_at=t.created_at,
    )


# ---------------------------------------------------------------------------
# Templates (must be defined before /{id} to avoid path-param clash)
# ---------------------------------------------------------------------------

@router.get("/templates", response_model=List[TransactionResponse])
def list_templates(svc: TransactionService = Depends(_service)):
    return [_to_response(t) for t in svc.get_template_transactions()]


@router.get("/templates/{template_id}/instances", response_model=List[TransactionResponse])
def list_template_instances(
    template_id: int,
    svc: TransactionService = Depends(_service),
):
    template = svc.get_transaction(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return [_to_response(t) for t in svc.get_transaction_instances(template_id)]


# ---------------------------------------------------------------------------
# Standard CRUD
# ---------------------------------------------------------------------------

@router.get("", response_model=List[TransactionResponse])
def list_transactions(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    type: Optional[TransactionType] = Query(None),
    search: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    svc: TransactionService = Depends(_service),
):
    if year and month:
        transactions = svc.get_transactions_for_month(year, month, transaction_type=type)
    elif start_date and end_date:
        transactions = svc.get_transactions_by_date_range(
            start_date, end_date, transaction_type=type
        )
    else:
        today = date.today()
        transactions = svc.get_transactions_for_month(
            today.year, today.month, transaction_type=type
        )

    transactions = TransactionService.filter_transactions(
        transactions,
        text_search=search or "",
        transaction_type=type,
        min_amount=min_amount,
        max_amount=max_amount,
    )
    return [_to_response(t) for t in transactions]


@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(
    body: TransactionCreate,
    svc: TransactionService = Depends(_service),
):
    t = Transaction(
        date=body.date,
        amount=body.amount,
        type=body.type,
        description=body.description,
        category=body.category,
        payee=body.payee,
        is_template=body.is_template,
        recurrence_pattern=body.recurrence_pattern,
        recurring_template_id=body.recurring_template_id,
    )
    return _to_response(svc.create_transaction(t))


@router.post("/batch", response_model=List[TransactionResponse], status_code=201)
def create_transactions_batch(
    body: TransactionBatchCreate,
    svc: TransactionService = Depends(_service),
):
    transactions = [
        Transaction(
            date=item.date,
            amount=item.amount,
            type=item.type,
            description=item.description,
            category=item.category,
            payee=item.payee,
            is_template=item.is_template,
            recurrence_pattern=item.recurrence_pattern,
            recurring_template_id=item.recurring_template_id,
        )
        for item in body.transactions
    ]
    created = svc.create_transactions_batch(transactions)
    return [_to_response(t) for t in created]


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    svc: TransactionService = Depends(_service),
):
    t = svc.get_transaction(transaction_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return _to_response(t)


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    body: TransactionUpdate,
    svc: TransactionService = Depends(_service),
):
    t = svc.get_transaction(transaction_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if body.date is not None:
        t.date = body.date
    if body.amount is not None:
        t.amount = body.amount
    if body.type is not None:
        t.type = body.type
    if body.description is not None:
        t.description = body.description
    if body.category is not None:
        t.category = body.category
    if body.payee is not None:
        t.payee = body.payee
    if body.recurrence_pattern is not None:
        t.recurrence_pattern = body.recurrence_pattern

    return _to_response(svc.update_transaction(t))


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: int,
    svc: TransactionService = Depends(_service),
):
    deleted = svc.delete_transaction(transaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found")
