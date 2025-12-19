"""Tests for transaction filtering functionality."""

import os
import tempfile
import pytest
from datetime import date

from src.models.database import Database
from src.models.transaction import Transaction, TransactionType
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
def sample_transactions():
    """Create sample transactions for testing."""
    return [
        Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Salary",
            category="Income",
            payee="Employer"
        ),
        Transaction(
            date=date(2024, 1, 20),
            amount=50.0,
            type=TransactionType.WITHDRAWAL,
            description="Grocery shopping",
            category="Food",
            payee="Supermarket"
        ),
        Transaction(
            date=date(2024, 2, 5),
            amount=200.0,
            type=TransactionType.DEPOSIT,
            description="Freelance work",
            category="Income",
            payee="Client ABC"
        ),
        Transaction(
            date=date(2024, 2, 10),
            amount=75.0,
            type=TransactionType.WITHDRAWAL,
            description="Restaurant",
            category="Food",
            payee="Restaurant XYZ"
        ),
        Transaction(
            date=date(2024, 2, 15),
            amount=150.0,
            type=TransactionType.DEPOSIT,
            description="Salary",
            category="Income",
            payee="Employer"
        ),
        Transaction(
            date=date(2024, 3, 1),
            amount=30.0,
            type=TransactionType.WITHDRAWAL,
            description="Coffee",
            category="Food",
            payee="Coffee Shop"
        ),
    ]


class TestTransactionServiceFilter:
    """Test transaction filtering in TransactionService."""
    
    def test_filter_by_text_search_description(self, sample_transactions):
        """Test filtering by text search in description."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            text_search="Salary"
        )
        assert len(filtered) == 2
        assert all("Salary" in t.description for t in filtered)
    
    def test_filter_by_text_search_category(self, sample_transactions):
        """Test filtering by text search in category."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            text_search="Food"
        )
        assert len(filtered) == 3
        assert all("Food" in t.category for t in filtered)
    
    def test_filter_by_text_search_payee(self, sample_transactions):
        """Test filtering by text search in payee."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            text_search="Employer"
        )
        assert len(filtered) == 2
        assert all("Employer" in t.payee for t in filtered)
    
    def test_filter_by_text_search_case_insensitive(self, sample_transactions):
        """Test that text search is case-insensitive."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            text_search="salary"
        )
        assert len(filtered) == 2
    
    def test_filter_by_text_search_partial_match(self, sample_transactions):
        """Test that text search does partial matching."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            text_search="shop"
        )
        assert len(filtered) == 2  # "shopping" and "Coffee Shop"
    
    def test_filter_by_type_deposit(self, sample_transactions):
        """Test filtering by transaction type - deposits only."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            transaction_type=TransactionType.DEPOSIT
        )
        assert len(filtered) == 3
        assert all(t.type == TransactionType.DEPOSIT for t in filtered)
    
    def test_filter_by_type_withdrawal(self, sample_transactions):
        """Test filtering by transaction type - withdrawals only."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            transaction_type=TransactionType.WITHDRAWAL
        )
        assert len(filtered) == 3
        assert all(t.type == TransactionType.WITHDRAWAL for t in filtered)
    
    def test_filter_by_amount_min(self, sample_transactions):
        """Test filtering by minimum amount."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            min_amount=100.0
        )
        assert len(filtered) == 3  # 100.0, 200.0, 150.0
        assert all(t.amount >= 100.0 for t in filtered)
    
    def test_filter_by_amount_max(self, sample_transactions):
        """Test filtering by maximum amount."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            max_amount=75.0
        )
        assert len(filtered) == 3  # 50.0, 75.0, 30.0
        assert all(t.amount <= 75.0 for t in filtered)
    
    def test_filter_by_amount_range(self, sample_transactions):
        """Test filtering by amount range."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            min_amount=50.0,
            max_amount=100.0
        )
        assert len(filtered) == 3  # 50.0, 100.0, 75.0
        assert all(50.0 <= t.amount <= 100.0 for t in filtered)
    
    def test_filter_by_date_range(self, sample_transactions):
        """Test filtering by date range."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 28)
        )
        assert len(filtered) == 3
        assert all(date(2024, 2, 1) <= t.date <= date(2024, 2, 28) for t in filtered)
    
    def test_filter_by_start_date_only(self, sample_transactions):
        """Test filtering by start date only."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            start_date=date(2024, 2, 1)
        )
        assert len(filtered) == 4
        assert all(t.date >= date(2024, 2, 1) for t in filtered)
    
    def test_filter_by_end_date_only(self, sample_transactions):
        """Test filtering by end date only."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            end_date=date(2024, 1, 31)
        )
        assert len(filtered) == 2
        assert all(t.date <= date(2024, 1, 31) for t in filtered)
    
    def test_filter_combined_all_criteria(self, sample_transactions):
        """Test filtering with all criteria combined."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            text_search="Income",
            transaction_type=TransactionType.DEPOSIT,
            min_amount=100.0,
            max_amount=200.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 2, 28)
        )
        # Should match: 100.0 (Jan 15), 200.0 (Feb 5), 150.0 (Feb 15) - all deposits with "Income"
        assert len(filtered) == 3
        assert all(
            "Income" in t.category and
            t.type == TransactionType.DEPOSIT and
            100.0 <= t.amount <= 200.0 and
            date(2024, 1, 1) <= t.date <= date(2024, 2, 28)
            for t in filtered
        )
    
    def test_filter_no_results(self, sample_transactions):
        """Test filtering that returns no results."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            text_search="NonExistentTerm"
        )
        assert len(filtered) == 0
    
    def test_filter_empty_list(self):
        """Test filtering an empty transaction list."""
        filtered = TransactionService.filter_transactions([])
        assert len(filtered) == 0
    
    def test_filter_no_criteria(self, sample_transactions):
        """Test filtering with no criteria (should return all)."""
        filtered = TransactionService.filter_transactions(sample_transactions)
        assert len(filtered) == len(sample_transactions)
        assert filtered == sample_transactions


class TestTransactionFilterEdgeCases:
    """Test edge cases for transaction filtering."""
    
    def test_filter_amount_exact_boundary(self, sample_transactions):
        """Test filtering at exact amount boundaries."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            min_amount=50.0,
            max_amount=50.0
        )
        assert len(filtered) == 1
        assert filtered[0].amount == 50.0
    
    def test_filter_date_exact_boundary(self, sample_transactions):
        """Test filtering at exact date boundaries."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            start_date=date(2024, 1, 20),
            end_date=date(2024, 1, 20)
        )
        assert len(filtered) == 1
        assert filtered[0].date == date(2024, 1, 20)
    
    def test_filter_empty_text_search(self, sample_transactions):
        """Test that empty text search returns all transactions."""
        filtered = TransactionService.filter_transactions(
            sample_transactions,
            text_search=""
        )
        assert len(filtered) == len(sample_transactions)
    
    def test_filter_text_search_special_characters(self, sample_transactions):
        """Test text search with special characters."""
        # Add a transaction with special characters
        special_transaction = Transaction(
            date=date(2024, 3, 5),
            amount=25.0,
            type=TransactionType.WITHDRAWAL,
            description="Payment #123",
            category="Misc",
            payee="Vendor & Co."
        )
        transactions = sample_transactions + [special_transaction]
        
        filtered = TransactionService.filter_transactions(
            transactions,
            text_search="#123"
        )
        assert len(filtered) == 1
        assert filtered[0].description == "Payment #123"
        assert filtered[0].date == date(2024, 3, 5)
    
    def test_filter_amount_zero(self, sample_transactions):
        """Test filtering with very small amount (edge case)."""
        # Transaction validation requires amount > 0, so test with a very small amount instead
        small_transaction = Transaction(
            date=date(2024, 3, 10),
            amount=0.01,  # Minimum valid amount
            type=TransactionType.DEPOSIT,
            description="Free item",
            category="Misc",
            payee="Free Store"
        )
        transactions = sample_transactions + [small_transaction]
        
        filtered = TransactionService.filter_transactions(
            transactions,
            min_amount=0.01
        )
        # Should include the small amount transaction
        assert any(t.amount == 0.01 for t in filtered)

