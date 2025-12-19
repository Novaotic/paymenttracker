# Payment Tracker

A Python application for tracking payments, deposits, and withdrawals with a calendar-based interface.

## Features

- **Calendar UI**: Visual calendar interface showing transactions by date
- **Transaction Indicators**: Dot indicators show deposits (green, top-right) and withdrawals (red, bottom-right) on calendar days
- **Transaction Management**: Add, edit, and delete transactions
- **Multiple Transactions per Day**: Support for multiple deposits and withdrawals on the same day
- **Transaction Types**: Support for deposits and withdrawals (autopays)
- **Recurring Transactions**: Set up weekly, biweekly, or monthly recurring transactions
- **Editable Recurring Instances**: Each instance of a recurring transaction can be edited independently
- **Weekly Balances**: View weekly balance summaries for the current month
- **Balance Carryover**: Balances carry over between months automatically
- **Search and Filter**: Filter transactions by text (description, category, payee), type, amount range, and date range

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

1. Click on any day in the calendar to add a transaction (you can add multiple transactions to the same day)
2. Fill in the transaction details (amount, type, description, category, payee)
3. Optionally set up recurring transactions (weekly, biweekly, monthly)
4. View weekly balances in the balance section
5. View all transactions for the selected month in the transactions list
6. Use the filter panel above the transactions list to:
   - Search by text (searches description, category, and payee) - updates in real-time
   - Filter by transaction type (Deposit/Withdrawal/All) - updates in real-time
   - Filter by amount range - click "Apply" to filter
   - Filter by date range - click "Apply" to filter
   - Click "Clear" to reset all filters

## License

MIT License - see [LICENSE](LICENSE) file for details.

