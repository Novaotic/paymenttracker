"""Tests for transaction service."""

import os
import tempfile
import pytest
from datetime import date, timedelta

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


class TestTransactionServiceCRUD:
    """Test CRUD operations."""
    
    def test_create_transaction(self, transaction_service):
        """Test creating a transaction."""
        transaction = Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Test deposit",
            category="Income",
            payee="Employer"
        )
        
        created = transaction_service.create_transaction(transaction)
        assert created.id is not None
        assert created.date == date(2024, 1, 15)
        assert created.amount == 100.0
        assert created.type == TransactionType.DEPOSIT
    
    def test_get_transaction(self, transaction_service):
        """Test retrieving a transaction."""
        transaction = Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Test deposit"
        )
        created = transaction_service.create_transaction(transaction)
        
        retrieved = transaction_service.get_transaction(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.amount == created.amount
        assert retrieved.description == created.description
    
    def test_get_nonexistent_transaction(self, transaction_service):
        """Test retrieving a non-existent transaction."""
        result = transaction_service.get_transaction(99999)
        assert result is None
    
    def test_update_transaction(self, transaction_service):
        """Test updating a transaction."""
        transaction = Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Original"
        )
        created = transaction_service.create_transaction(transaction)
        
        created.description = "Updated"
        created.amount = 200.0
        updated = transaction_service.update_transaction(created)
        
        retrieved = transaction_service.get_transaction(created.id)
        assert retrieved.description == "Updated"
        assert retrieved.amount == 200.0
    
    def test_delete_transaction(self, transaction_service):
        """Test deleting a transaction."""
        transaction = Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="To delete"
        )
        created = transaction_service.create_transaction(transaction)
        
        deleted = transaction_service.delete_transaction(created.id)
        assert deleted is True
        
        retrieved = transaction_service.get_transaction(created.id)
        assert retrieved is None
    
    def test_delete_nonexistent_transaction(self, transaction_service):
        """Test deleting a non-existent transaction."""
        result = transaction_service.delete_transaction(99999)
        assert result is False


class TestTransactionServiceQueries:
    """Test query operations."""
    
    def test_get_transactions_by_date_range(self, transaction_service):
        """Test querying transactions by date range."""
        # Create transactions on different dates
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 10),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Early"
        ))
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 15),
            amount=200.0,
            type=TransactionType.DEPOSIT,
            description="Middle"
        ))
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 20),
            amount=300.0,
            type=TransactionType.DEPOSIT,
            description="Late"
        ))
        transaction_service.create_transaction(Transaction(
            date=date(2024, 2, 1),
            amount=400.0,
            type=TransactionType.DEPOSIT,
            description="Outside range"
        ))
        
        transactions = transaction_service.get_transactions_by_date_range(
            date(2024, 1, 12),
            date(2024, 1, 18)
        )
        
        assert len(transactions) == 1
        assert transactions[0].description == "Middle"
    
    def test_get_transactions_for_month(self, transaction_service):
        """Test getting transactions for a specific month."""
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="January"
        ))
        transaction_service.create_transaction(Transaction(
            date=date(2024, 2, 15),
            amount=200.0,
            type=TransactionType.DEPOSIT,
            description="February"
        ))
        
        jan_transactions = transaction_service.get_transactions_for_month(2024, 1)
        assert len(jan_transactions) == 1
        assert jan_transactions[0].description == "January"
        
        feb_transactions = transaction_service.get_transactions_for_month(2024, 2)
        assert len(feb_transactions) == 1
        assert feb_transactions[0].description == "February"
    
    def test_filter_by_type(self, transaction_service):
        """Test filtering transactions by type."""
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Deposit"
        ))
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 16),
            amount=50.0,
            type=TransactionType.WITHDRAWAL,
            description="Withdrawal"
        ))
        
        deposits = transaction_service.get_transactions_by_date_range(
            date(2024, 1, 1),
            date(2024, 1, 31),
            transaction_type=TransactionType.DEPOSIT
        )
        assert len(deposits) == 1
        assert deposits[0].type == TransactionType.DEPOSIT
        
        withdrawals = transaction_service.get_transactions_by_date_range(
            date(2024, 1, 1),
            date(2024, 1, 31),
            transaction_type=TransactionType.WITHDRAWAL
        )
        assert len(withdrawals) == 1
        assert withdrawals[0].type == TransactionType.WITHDRAWAL


class TestTransactionServiceTemplates:
    """Test template and instance relationships."""
    
    def test_create_template(self, transaction_service):
        """Test creating a template transaction."""
        template = Transaction(
            date=date(2024, 1, 1),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Template",
            is_template=True,
            recurrence_pattern=RecurrencePattern.WEEKLY
        )
        
        created = transaction_service.create_transaction(template)
        assert created.is_template is True
        assert created.recurrence_pattern == RecurrencePattern.WEEKLY
    
    def test_get_template_transactions(self, transaction_service):
        """Test retrieving template transactions."""
        # Create a template and an instance
        template = Transaction(
            date=date(2024, 1, 1),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Template",
            is_template=True,
            recurrence_pattern=RecurrencePattern.WEEKLY
        )
        created_template = transaction_service.create_transaction(template)
        
        instance = Transaction(
            date=date(2024, 1, 8),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Instance",
            recurring_template_id=created_template.id,
            is_template=False
        )
        transaction_service.create_transaction(instance)
        
        templates = transaction_service.get_template_transactions()
        assert len(templates) == 1
        assert templates[0].is_template is True
    
    def test_get_transaction_instances(self, transaction_service):
        """Test retrieving instances of a template."""
        template = Transaction(
            date=date(2024, 1, 1),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Template",
            is_template=True,
            recurrence_pattern=RecurrencePattern.WEEKLY
        )
        created_template = transaction_service.create_transaction(template)
        
        instance1 = Transaction(
            date=date(2024, 1, 8),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Instance 1",
            recurring_template_id=created_template.id,
            is_template=False
        )
        instance2 = Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Instance 2",
            recurring_template_id=created_template.id,
            is_template=False
        )
        transaction_service.create_transaction(instance1)
        transaction_service.create_transaction(instance2)
        
        instances = transaction_service.get_transaction_instances(created_template.id)
        assert len(instances) == 2


class TestTransactionServiceBalance:
    """Test balance calculations."""
    
    def test_calculate_balance_up_to_date(self, transaction_service):
        """Test calculating balance up to a specific date."""
        # Create transactions
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 10),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Deposit 1"
        ))
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 15),
            amount=50.0,
            type=TransactionType.WITHDRAWAL,
            description="Withdrawal 1"
        ))
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 20),
            amount=200.0,
            type=TransactionType.DEPOSIT,
            description="Deposit 2"
        ))
        
        # Balance up to Jan 15 should be 100 - 50 = 50
        balance = transaction_service.calculate_balance_up_to_date(date(2024, 1, 15))
        assert balance == 50.0
        
        # Balance up to Jan 20 should be 100 - 50 + 200 = 250
        balance = transaction_service.calculate_balance_up_to_date(date(2024, 1, 20))
        assert balance == 250.0
    
    def test_calculate_weekly_balances(self, transaction_service):
        """Test calculating weekly balances for a month."""
        # Create transactions in January 2024
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 1),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Week 1"
        ))
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 10),
            amount=50.0,
            type=TransactionType.WITHDRAWAL,
            description="Week 2"
        ))
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 20),
            amount=200.0,
            type=TransactionType.DEPOSIT,
            description="Week 3"
        ))
        
        weekly_balances = transaction_service.calculate_weekly_balances(2024, 1)
        assert len(weekly_balances) > 0
        
        # Check that balances are calculated correctly
        # Ending balance should equal starting balance + total net change
        starting_balance = weekly_balances[0].starting_balance
        total_change = sum(wb.net_change for wb in weekly_balances)
        final_balance = weekly_balances[-1].ending_balance
        expected_balance = starting_balance + total_change
        assert abs(final_balance - expected_balance) < 0.01  # Allow for floating point
        
    def test_balance_carryover_between_months(self, transaction_service):
        """Test that balance carries over between months."""
        # Create transactions in January
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="January deposit"
        ))
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 20),
            amount=30.0,
            type=TransactionType.WITHDRAWAL,
            description="January withdrawal"
        ))
        # January ending balance should be 70.0
        
        # Create transaction in February
        transaction_service.create_transaction(Transaction(
            date=date(2024, 2, 5),
            amount=50.0,
            type=TransactionType.DEPOSIT,
            description="February deposit"
        ))
        # February balance should start at 70.0 and end at 120.0
        
        jan_balances = transaction_service.calculate_weekly_balances(2024, 1)
        feb_balances = transaction_service.calculate_weekly_balances(2024, 2)
        
        # Check that February starting balance equals January ending balance
        if jan_balances and feb_balances:
            jan_ending = jan_balances[-1].ending_balance
            feb_starting = feb_balances[0].starting_balance
            assert abs(jan_ending - feb_starting) < 0.01  # Allow for floating point

