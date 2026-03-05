"""CSV import API route."""

import csv
import io
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.models.database import Database, get_db
from src.models.transaction import Transaction, TransactionType
from src.schemas.transaction import ImportResultResponse
from src.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/import", tags=["import"])

VALID_DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y"]


def _service(db: Database = Depends(get_db)) -> TransactionService:
    return TransactionService(db)


def _parse_date(value: str) -> date:
    from datetime import datetime
    for fmt in VALID_DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {value!r}")


def _parse_type(value: str) -> TransactionType:
    v = value.strip().lower()
    if v in ("deposit", "credit", "income"):
        return TransactionType.DEPOSIT
    if v in ("withdrawal", "debit", "expense", "payment"):
        return TransactionType.WITHDRAWAL
    raise ValueError(f"Unknown transaction type: {value!r}")


@router.post("/csv", response_model=ImportResultResponse)
async def import_csv(
    file: UploadFile = File(...),
    date_col: str = Form("date"),
    amount_col: str = Form("amount"),
    type_col: str = Form("type"),
    description_col: str = Form(default=""),
    category_col: str = Form(default=""),
    payee_col: str = Form(default=""),
    svc: TransactionService = Depends(_service),
):
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")  # handle BOM if present
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise HTTPException(status_code=400, detail="CSV file appears to be empty")

    transactions: List[Transaction] = []
    errors: List[str] = []

    for row_num, row in enumerate(reader, start=2):
        try:
            row_date = _parse_date(row[date_col])
            row_amount = abs(float(row[amount_col].replace(",", "").replace("$", "")))
            row_type = _parse_type(row[type_col])
            row_desc = row.get(description_col, "").strip() if description_col else ""
            row_cat = row.get(category_col, "").strip() if category_col else ""
            row_payee = row.get(payee_col, "").strip() if payee_col else ""

            transactions.append(Transaction(
                date=row_date,
                amount=row_amount,
                type=row_type,
                description=row_desc,
                category=row_cat,
                payee=row_payee,
            ))
        except (KeyError, ValueError) as exc:
            errors.append(f"Row {row_num}: {exc}")

    created = svc.create_transactions_batch(transactions)
    skipped = len(transactions) - len(created)

    return ImportResultResponse(
        imported=len(created),
        skipped=skipped + len(errors),
        errors=errors,
    )
