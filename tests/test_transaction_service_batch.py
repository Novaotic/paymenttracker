"""Tests for batch transaction creation."""

import os
import tempfile
import pytest
from datetime import date

from src.models.database import Database
from src.models.transaction import Transaction, TransactionType, RecurrencePattern
from src.services.transaction_service import TransactionService


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    db = Database(db_path)
    db.connect()
    yield db
    db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def transaction_service(temp_db):
    """Create a transaction service instance."""
    return TransactionService(temp_db)


class TestTransactionServiceBatch:
    """Test batch transaction creation."""
    
    def test_create_transactions_batch_success(self, transaction_service):
        """Test successful batch creation."""
        transactions = [
            Transaction(
                date=date(2024, 1, 15),
                amount=100.0,
                type=TransactionType.DEPOSIT,
                description="Deposit 1"
            ),
            Transaction(
                date=date(2024, 1, 16),
                amount=50.0,
                type=TransactionType.WITHDRAWAL,
                description="Withdrawal 1"
            ),
            Transaction(
                date=date(2024, 1, 17),
                amount=200.0,
                type=TransactionType.DEPOSIT,
                description="Deposit 2"
            ),
        ]
        
        created = transaction_service.create_transactions_batch(transactions)
        
        assert len(created) == 3
        assert all(t.id is not None for t in created)
        assert created[0].description == "Deposit 1"
        assert created[1].description == "Withdrawal 1"
        assert created[2].description == "Deposit 2"
        
        # Verify all transactions are in database
        all_transactions = transaction_service.get_transactions_by_date_range(
            date(2024, 1, 1), date(2024, 1, 31)
        )
        assert len(all_transactions) == 3
    
    def test_create_transactions_batch_with_templates(self, transaction_service):
        """Test batch creation including templates."""
        transactions = [
            Transaction(
                date=date(2024, 1, 1),
                amount=1000.0,
                type=TransactionType.DEPOSIT,
                description="Salary",
                is_template=True,
                recurrence_pattern=RecurrencePattern.MONTHLY
            ),
            Transaction(
                date=date(2024, 1, 15),
                amount=50.0,
                type=TransactionType.WITHDRAWAL,
                description="One-time expense"
            ),
        ]
        
        created = transaction_service.create_transactions_batch(transactions)
        
        assert len(created) == 2
        templates = [t for t in created if t.is_template]
        assert len(templates) == 1
        assert templates[0].recurrence_pattern == RecurrencePattern.MONTHLY
    
    def test_create_transactions_batch_empty(self, transaction_service):
        """Test batch creation with empty list."""
        created = transaction_service.create_transactions_batch([])
        assert len(created) == 0
    
    def test_create_transactions_batch_large(self, transaction_service):
        """Test batch creation with many transactions."""
        transactions = []
        for i in range(100):
            transactions.append(Transaction(
                date=date(2024, 1, (i % 28) + 1),
                amount=10.0 + i,
                type=TransactionType.DEPOSIT if i % 2 == 0 else TransactionType.WITHDRAWAL,
                description=f"Transaction {i}"
            ))
        
        created = transaction_service.create_transactions_batch(transactions)
        assert len(created) == 100
        assert all(t.id is not None for t in created)

