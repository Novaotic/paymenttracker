"""Tests for CSV import dialog."""

import csv
import tempfile
import os
from datetime import date

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDate

from src.ui.csv_import_dialog import CSVImportDialog
from src.models.transaction import Transaction, TransactionType, RecurrencePattern


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestCSVImportDialog:
    """Test CSV import dialog."""
    
    def test_dialog_initialization(self, qapp):
        """Test dialog initializes correctly."""
        dialog = CSVImportDialog()
        assert dialog.windowTitle() == "Import Transactions from CSV"
        assert not dialog.import_button.isEnabled()
        dialog.close()
    
    def test_csv_parsing_basic(self, qapp):
        """Test basic CSV parsing."""
        # Create temporary CSV file
        csv_data = [
            ["Date", "Amount", "Type", "Description"],
            ["2024-01-15", "100.00", "deposit", "Test deposit"],
            ["2024-01-16", "50.00", "withdrawal", "Test withdrawal"],
        ]
        
        fd, csv_path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(csv_data)
            
            dialog = CSVImportDialog()
            dialog._load_csv(csv_path)
            
            assert len(dialog.csv_data) == 2
            assert len(dialog.csv_headers) == 4
            assert "Date" in dialog.csv_headers
            assert "Amount" in dialog.csv_headers
            dialog.close()
        finally:
            if os.path.exists(csv_path):
                os.unlink(csv_path)
    
    def test_column_mapping_auto_detect(self, qapp):
        """Test automatic column mapping."""
        csv_data = [
            ["Date", "Amount", "Type", "Description", "Category", "Payee"],
            ["2024-01-15", "100.00", "deposit", "Test", "Income", "Employer"],
        ]
        
        fd, csv_path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(csv_data)
            
            dialog = CSVImportDialog()
            dialog._load_csv(csv_path)
            dialog._setup_column_mapping()
            
            assert dialog.column_mapping.get("Date") == "Date"
            assert dialog.column_mapping.get("Amount") == "Amount"
            assert dialog.column_mapping.get("Type") == "Type"
            assert dialog.column_mapping.get("Description") == "Description"
            assert dialog.column_mapping.get("Category") == "Category"
            assert dialog.column_mapping.get("Payee") == "Payee"
            dialog.close()
        finally:
            if os.path.exists(csv_path):
                os.unlink(csv_path)
    
    def test_parse_row_valid(self, qapp):
        """Test parsing a valid CSV row."""
        dialog = CSVImportDialog()
        
        row_data = {
            "Date": "2024-01-15",
            "Amount": "100.00",
            "Type": "deposit",
            "Description": "Test deposit",
            "Category": "Income",
            "Payee": "Employer"
        }
        
        transaction = dialog._parse_row(
            row_data, 0,
            "Date", "Amount", "Type",
            "Description", "Category", "Payee", None
        )
        
        assert transaction is not None
        assert transaction.date == date(2024, 1, 15)
        assert transaction.amount == 100.0
        assert transaction.type == TransactionType.DEPOSIT
        assert transaction.description == "Test deposit"
        assert transaction.category == "Income"
        assert transaction.payee == "Employer"
        dialog.close()
    
    def test_parse_row_with_recurrence(self, qapp):
        """Test parsing row with recurrence pattern."""
        dialog = CSVImportDialog()
        
        row_data = {
            "Date": "2024-01-15",
            "Amount": "1000.00",
            "Type": "deposit",
            "Description": "Salary",
            "Recurrence": "monthly"
        }
        
        transaction = dialog._parse_row(
            row_data, 0,
            "Date", "Amount", "Type",
            "Description", None, None, "Recurrence"
        )
        
        assert transaction is not None
        assert transaction.is_template is True
        assert transaction.recurrence_pattern == RecurrencePattern.MONTHLY
        dialog.close()
    
    def test_parse_date_formats(self, qapp):
        """Test parsing different date formats."""
        dialog = CSVImportDialog()
        
        formats = [
            ("2024-01-15", date(2024, 1, 15)),
            ("01/15/2024", date(2024, 1, 15)),
            ("15/01/2024", date(2024, 1, 15)),
        ]
        
        for date_str, expected_date in formats:
            parsed = dialog._parse_date(date_str)
            assert parsed == expected_date
        
        dialog.close()
    
    def test_parse_amount_formats(self, qapp):
        """Test parsing different amount formats."""
        dialog = CSVImportDialog()
        
        amounts = [
            ("100.00", 100.0),
            ("$100.00", 100.0),
            ("1,000.00", 1000.0),
            ("$1,000.00", 1000.0),
        ]
        
        for amount_str, expected_amount in amounts:
            parsed = dialog._parse_amount(amount_str)
            assert abs(parsed - expected_amount) < 0.01
        
        dialog.close()
    
    def test_parse_type_variations(self, qapp):
        """Test parsing different type strings."""
        dialog = CSVImportDialog()
        
        assert dialog._parse_type("deposit") == TransactionType.DEPOSIT
        assert dialog._parse_type("income") == TransactionType.DEPOSIT
        assert dialog._parse_type("credit") == TransactionType.DEPOSIT
        assert dialog._parse_type("withdrawal") == TransactionType.WITHDRAWAL
        assert dialog._parse_type("expense") == TransactionType.WITHDRAWAL
        assert dialog._parse_type("debit") == TransactionType.WITHDRAWAL
        
        dialog.close()
    
    def test_parse_recurrence_variations(self, qapp):
        """Test parsing different recurrence strings."""
        dialog = CSVImportDialog()
        
        assert dialog._parse_recurrence("weekly") == RecurrencePattern.WEEKLY
        assert dialog._parse_recurrence("biweekly") == RecurrencePattern.BIWEEKLY
        assert dialog._parse_recurrence("monthly") == RecurrencePattern.MONTHLY
        assert dialog._parse_recurrence("") is None
        assert dialog._parse_recurrence("invalid") is None
        
        dialog.close()
    
    def test_parse_row_invalid_date(self, qapp):
        """Test parsing row with invalid date."""
        dialog = CSVImportDialog()
        
        row_data = {
            "Date": "invalid-date",
            "Amount": "100.00",
            "Type": "deposit"
        }
        
        with pytest.raises(ValueError, match="Invalid date"):
            dialog._parse_row(row_data, 0, "Date", "Amount", "Type", None, None, None, None)
        
        dialog.close()
    
    def test_parse_row_invalid_amount(self, qapp):
        """Test parsing row with invalid amount."""
        dialog = CSVImportDialog()
        
        row_data = {
            "Date": "2024-01-15",
            "Amount": "invalid",
            "Type": "deposit"
        }
        
        with pytest.raises(ValueError, match="Invalid amount"):
            dialog._parse_row(row_data, 0, "Date", "Amount", "Type", None, None, None, None)
        
        dialog.close()
    
    def test_get_transactions_empty(self, qapp):
        """Test getting transactions when none parsed."""
        dialog = CSVImportDialog()
        assert len(dialog.get_transactions()) == 0
        dialog.close()

