# Payment Tracker

A personal finance web application for tracking deposits, withdrawals, and recurring transactions.
Accessible from any device on your local network — including mobile.

---

## Features

- **Calendar view** — month grid with green/coral dots indicating days with deposits or withdrawals
- **Transaction list** — searchable, filterable by type, amount, and month
- **Add / Edit / Delete** transactions with an inline modal
- **Recurring transactions** — weekly, biweekly, or monthly templates; instances auto-generated on startup
- **Bulk entry** — enter multiple transactions at once in a table
- **CSV import** — upload a CSV and map columns to fields
- **Weekly balance summary** — per-week starting/ending balance with net change
- **Running balance** — always visible in the top bar

---

## Tech Stack

| Layer    | Technology |
|----------|------------|
| Backend  | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| Database | SQLite (via Python stdlib `sqlite3`) |
| Frontend | Vanilla HTML / CSS / JavaScript (no build step) |

---

## Setup

### Requirements

- Python 3.8+

### Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Run

```bash
python main.py
```

The server starts on `http://0.0.0.0:8000` with hot-reload enabled.

**From your PC:** open [http://localhost:8000](http://localhost:8000)

**From your phone or any LAN device:** open `http://<your-pc-ip>:8000`


---

## Project Structure

```
paymenttracker/
├── src/
│   ├── app.py                      # FastAPI app, routing, startup hook
│   ├── models/
│   │   ├── database.py             # SQLite connection + get_db() dependency
│   │   └── transaction.py          # Transaction model + enums
│   ├── schemas/
│   │   └── transaction.py          # Pydantic request/response schemas
│   ├── services/
│   │   ├── transaction_service.py  # CRUD, balance calculations, filtering
│   │   └── recurrence_service.py   # Recurring instance generation
│   └── api/
│       ├── transactions.py         # /api/transactions endpoints
│       ├── balances.py             # /api/balances endpoints
│       └── import_export.py        # /api/import/csv endpoint
├── static/
│   ├── css/style.css               # Dark navy theme (Simple Bank inspired)
│   └── js/
│       ├── api.js                  # fetch() wrappers
│       ├── calendar.js             # Calendar view + day drawer
│       ├── transactions.js         # Transaction list, modals, bulk/CSV
│       └── app.js                  # Bootstrap, view routing, balance bar
├── templates/
│   └── index.html                  # Single-page HTML shell
├── tests/
│   ├── test_api_transactions.py    # API integration tests
│   ├── test_api_balances.py        # Balance API tests
│   ├── test_database.py
│   ├── test_transaction_service.py
│   ├── test_transaction_service_batch.py
│   ├── test_recurrence_service.py
│   └── test_transaction_filter.py
├── main.py                         # Entry point
└── requirements.txt
```

---

## API Reference

The interactive docs are available at [http://localhost:8000/docs](http://localhost:8000/docs) while the server is running.

### Transactions

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/transactions` | List (params: `year`, `month`, `type`, `search`, `min_amount`, `max_amount`) |
| `POST` | `/api/transactions` | Create one |
| `GET`  | `/api/transactions/{id}` | Get one |
| `PUT`  | `/api/transactions/{id}` | Update |
| `DELETE` | `/api/transactions/{id}` | Delete |
| `POST` | `/api/transactions/batch` | Bulk create |
| `GET`  | `/api/transactions/templates` | List recurring templates |
| `GET`  | `/api/transactions/templates/{id}/instances` | List instances of a template |

### Balances

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/balances/current` | Balance up to `as_of` date (defaults to today) |
| `GET`  | `/api/balances/weekly` | Weekly breakdown for `year` + `month` |

### Import

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/import/csv` | Upload CSV file with column mapping form fields |

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Database

The SQLite database is stored at `paymenttracker.db` in the project root. It is created automatically on first run.
The schema uses a single `transactions` table; recurring templates and their generated instances both live in this table,
linked by `recurring_template_id`.
