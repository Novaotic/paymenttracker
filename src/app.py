"""FastAPI application factory."""

from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.models.database import get_database
from src.services.recurrence_service import RecurrenceService
from src.services.transaction_service import TransactionService
from src.api.transactions import router as transactions_router
from src.api.balances import router as balances_router
from src.api.import_export import router as import_router

BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_database()
    db.connect()
    svc = TransactionService(db)
    rec = RecurrenceService(svc)
    one_year_out = date(date.today().year + 1, date.today().month, date.today().day)
    rec.generate_all_instances_up_to(one_year_out)
    yield


app = FastAPI(title="Payment Tracker", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(transactions_router)
app.include_router(balances_router)
app.include_router(import_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
