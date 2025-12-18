# Payment Tracker

A Python application for tracking payments, deposits, and withdrawals with a calendar-based interface.

## Features

- **Calendar UI**: Visual calendar interface showing transactions by date
- **Transaction Management**: Add, edit, and delete transactions
- **Transaction Types**: Support for deposits and withdrawals (autopays)
- **Recurring Transactions**: Set up weekly, biweekly, or monthly recurring transactions
- **Editable Recurring Instances**: Each instance of a recurring transaction can be edited independently
- **Color Coding**: Calendar days are color-coded (green for deposits, red for withdrawals)
- **Weekly Balances**: View weekly balance summaries for the current month
- **Balance Carryover**: Balances carry over between months automatically

## Requirements

- Python 3.8 or higher
- PyQt6
- pytest (for testing)

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python src/main.py
   ```

## Running Tests

```bash
pytest
```

## Project Structure

```
paymenttracker/
├── src/
│   ├── models/          # Data models and database
│   ├── services/        # Business logic services
│   ├── ui/              # UI components
│   └── main.py          # Application entry point
├── tests/               # Test suite
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Usage

1. Click on any day in the calendar to add a transaction
2. Fill in the transaction details (amount, type, description, etc.)
3. Optionally set up recurring transactions (weekly, biweekly, monthly)
4. View weekly balances in the balance section
5. View all transactions for the selected month in the transactions list

## License

Personal project - use as you wish.

