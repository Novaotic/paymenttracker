"""Tests for recurrence service."""

import os
import tempfile
import pytest
from datetime import date, timedelta, datetime

from src.models.database import Database
from src.models.transaction import Transaction, TransactionType, RecurrencePattern
from src.services.transaction_service import TransactionService
from src.services.recurrence_service import RecurrenceService


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


@pytest.fixture
def recurrence_service(transaction_service):
    """Create a recurrence service instance."""
    return RecurrenceService(transaction_service)


class TestWeeklyRecurrence:
    """Test weekly recurrence generation."""
    
    def test_generate_weekly_instances(self, recurrence_service, transaction_service):
        """Test generating weekly recurring instances."""
        template = Transaction(
            date=date(2024, 1, 1),  # Monday
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Weekly deposit",
            is_template=True,
            recurrence_pattern=RecurrencePattern.WEEKLY
        )
        saved_template = transaction_service.create_transaction(template)
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        instances = recurrence_service.generate_instances(
            saved_template, start_date, end_date
        )
        
        # Should generate instances for Jan 1, 8, 15, 22, 29 (5 instances)
        assert len(instances) == 5
        assert instances[0].date == date(2024, 1, 1)
        assert instances[1].date == date(2024, 1, 8)
        assert instances[2].date == date(2024, 1, 15)
        assert all(inst.recurring_template_id == saved_template.id for inst in instances)
        assert all(not inst.is_template for inst in instances)
    
    def test_weekly_recurrence_saves_instances(self, recurrence_service, transaction_service):
        """Test that generated weekly instances can be saved."""
        template = Transaction(
            date=date(2024, 1, 1),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Weekly deposit",
            is_template=True,
            recurrence_pattern=RecurrencePattern.WEEKLY
        )
        saved_template = transaction_service.create_transaction(template)
        
        instances = recurrence_service.generate_instances(
            saved_template, date(2024, 1, 1), date(2024, 1, 31)
        )
        
        # Save instances
        for instance in instances:
            transaction_service.create_transaction(instance)
        
        # Verify instances were saved
        saved_instances = transaction_service.get_transaction_instances(saved_template.id)
        assert len(saved_instances) == 5


class TestBiweeklyRecurrence:
    """Test biweekly recurrence generation."""
    
    def test_generate_biweekly_instances(self, recurrence_service, transaction_service):
        """Test generating biweekly recurring instances."""
        template = Transaction(
            date=date(2024, 1, 1),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Biweekly deposit",
            is_template=True,
            recurrence_pattern=RecurrencePattern.BIWEEKLY
        )
        saved_template = transaction_service.create_transaction(template)
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 2, 29)
        
        instances = recurrence_service.generate_instances(
            saved_template, start_date, end_date
        )
        
        # Should generate instances every 2 weeks
        assert len(instances) >= 4
        assert instances[0].date == date(2024, 1, 1)
        assert instances[1].date == date(2024, 1, 15)
        assert instances[2].date == date(2024, 1, 29)
        # Verify spacing is 14 days
        for i in range(1, len(instances)):
            days_diff = (instances[i].date - instances[i-1].date).days
            assert days_diff == 14


class TestMonthlyRecurrence:
    """Test monthly recurrence generation."""
    
    def test_generate_monthly_instances(self, recurrence_service, transaction_service):
        """Test generating monthly recurring instances."""
        template = Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Monthly deposit",
            is_template=True,
            recurrence_pattern=RecurrencePattern.MONTHLY
        )
        saved_template = transaction_service.create_transaction(template)
        
        start_date = date(2024, 1, 15)
        end_date = date(2024, 6, 15)
        
        instances = recurrence_service.generate_instances(
            saved_template, start_date, end_date
        )
        
        # Should generate instances for Jan, Feb, Mar, Apr, May, Jun (6 instances)
        assert len(instances) == 6
        assert instances[0].date == date(2024, 1, 15)
        assert instances[1].date == date(2024, 2, 15)
        assert instances[2].date == date(2024, 3, 15)
    
    def test_monthly_recurrence_end_of_month_edge_case(self, recurrence_service, transaction_service):
        """Test monthly recurrence with end-of-month dates."""
        # Test with Jan 31 -> Feb should use Feb 29 (leap year) or Feb 28
        template = Transaction(
            date=date(2024, 1, 31),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Monthly end-of-month",
            is_template=True,
            recurrence_pattern=RecurrencePattern.MONTHLY
        )
        saved_template = transaction_service.create_transaction(template)
        
        instances = recurrence_service.generate_instances(
            saved_template, date(2024, 1, 31), date(2024, 4, 30)
        )
        
        # Should handle month boundaries correctly
        assert len(instances) >= 3
        # February in 2024 is a leap year, so should use Feb 29
        assert instances[1].date == date(2024, 2, 29)
        # March should use Mar 31
        assert instances[2].date == date(2024, 3, 31)
    
    def test_monthly_recurrence_february_leap_year(self, recurrence_service, transaction_service):
        """Test monthly recurrence with February in leap year."""
        template = Transaction(
            date=date(2024, 2, 29),  # Leap year
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Leap year date",
            is_template=True,
            recurrence_pattern=RecurrencePattern.MONTHLY
        )
        saved_template = transaction_service.create_transaction(template)
        
        instances = recurrence_service.generate_instances(
            saved_template, date(2024, 2, 29), date(2024, 5, 31)
        )
        
        # Should handle leap year correctly
        assert len(instances) >= 3
        # March should use last day (31)
        assert instances[1].date == date(2024, 3, 31)


class TestRecurrenceEdgeCases:
    """Test edge cases for recurrence generation."""
    
    def test_regenerate_existing_instances(self, recurrence_service, transaction_service):
        """Test regenerating instances that already exist."""
        template = Transaction(
            date=date(2024, 1, 1),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Weekly deposit",
            is_template=True,
            recurrence_pattern=RecurrencePattern.WEEKLY
        )
        saved_template = transaction_service.create_transaction(template)
        
        # Generate and save instances
        instances = recurrence_service.generate_instances(
            saved_template, date(2024, 1, 1), date(2024, 1, 31)
        )
        for instance in instances:
            transaction_service.create_transaction(instance)
        
        # Generate again without regenerate flag
        new_instances = recurrence_service.generate_instances(
            saved_template, date(2024, 1, 1), date(2024, 1, 31), regenerate_existing=False
        )
        # Should not generate duplicates
        assert len(new_instances) == 0
        
        # Generate with regenerate flag
        regenerated = recurrence_service.generate_instances(
            saved_template, date(2024, 1, 1), date(2024, 1, 31), regenerate_existing=True
        )
        # Should generate all instances again
        assert len(regenerated) == 5
    
    def test_generate_all_instances_up_to_date(self, recurrence_service, transaction_service):
        """Test generating all recurring instances up to a future date."""
        # Create multiple templates
        template1 = Transaction(
            date=date(2024, 1, 1),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Weekly",
            is_template=True,
            recurrence_pattern=RecurrencePattern.WEEKLY
        )
        template2 = Transaction(
            date=date(2024, 1, 1),
            amount=200.0,
            type=TransactionType.DEPOSIT,
            description="Monthly",
            is_template=True,
            recurrence_pattern=RecurrencePattern.MONTHLY
        )
        
        transaction_service.create_transaction(template1)
        transaction_service.create_transaction(template2)
        
        end_date = date(2024, 2, 29)
        all_instances = recurrence_service.generate_all_instances_up_to(end_date, regenerate_existing=False)
        
        # Should generate instances for both templates
        assert len(all_instances) > 0


class TestRecurrenceValidation:
    """Test recurrence service validation."""
    
    def test_generate_instances_requires_template(self, recurrence_service, transaction_service):
        """Test that generate_instances requires a template."""
        non_template = Transaction(
            date=date(2024, 1, 1),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Not a template",
            is_template=False
        )
        saved = transaction_service.create_transaction(non_template)
        
        with pytest.raises(ValueError, match="is_template=True"):
            recurrence_service.generate_instances(saved, date(2024, 1, 1), date(2024, 1, 31))
    
    def test_generate_instances_requires_pattern(self, recurrence_service, transaction_service):
        """Test that generate_instances requires a recurrence pattern."""
        # Transaction validation prevents creating a template without pattern
        # So we'll test by creating a transaction object directly and bypassing validation
        # by manually creating an invalid template object
        
        # Create transaction object without validation (bypass __init__ validation)
        template_no_pattern = object.__new__(Transaction)
        template_no_pattern.id = None
        template_no_pattern.date = date(2024, 1, 1)
        template_no_pattern.amount = 100.0
        template_no_pattern.type = TransactionType.DEPOSIT
        template_no_pattern.description = "Template without pattern"
        template_no_pattern.category = ""
        template_no_pattern.payee = ""
        template_no_pattern.recurring_template_id = None
        template_no_pattern.is_template = True
        template_no_pattern.recurrence_pattern = None
        template_no_pattern.created_at = datetime.now()
        
        # Now test that generate_instances raises an error
        with pytest.raises(ValueError, match="recurrence_pattern"):
            recurrence_service.generate_instances(template_no_pattern, date(2024, 1, 1), date(2024, 1, 31))

