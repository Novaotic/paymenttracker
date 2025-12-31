"""Tests for bulk entry dialog."""

import pytest
from datetime import date
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDate

from src.ui.bulk_entry_dialog import (
    BulkEntryDialog, DateEditItem, AmountEditItem,
    TypeComboItem, RecurrenceComboItem
)
from src.models.transaction import Transaction, TransactionType, RecurrencePattern


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestBulkEntryDialogWidgets:
    """Test bulk entry dialog widget components."""
    
    def test_date_edit_item(self, qapp):
        """Test DateEditItem widget."""
        widget = DateEditItem()
        test_date = date(2024, 1, 15)
        widget.setDate(QDate(test_date.year, test_date.month, test_date.day))
        assert widget.get_date() == test_date
        widget.close()
    
    def test_amount_edit_item(self, qapp):
        """Test AmountEditItem widget."""
        widget = AmountEditItem()
        widget.setValue(100.50)
        assert abs(widget.value() - 100.50) < 0.01
        widget.close()
    
    def test_type_combo_item(self, qapp):
        """Test TypeComboItem widget."""
        widget = TypeComboItem()
        assert widget.get_type() == TransactionType.DEPOSIT  # Default first item
        widget.setCurrentIndex(1)
        assert widget.get_type() == TransactionType.WITHDRAWAL
        widget.close()
    
    def test_recurrence_combo_item(self, qapp):
        """Test RecurrenceComboItem widget."""
        widget = RecurrenceComboItem()
        assert widget.get_pattern() is None  # Default is "One-time"
        widget.setCurrentIndex(1)
        assert widget.get_pattern() == RecurrencePattern.WEEKLY
        widget.setCurrentIndex(2)
        assert widget.get_pattern() == RecurrencePattern.BIWEEKLY
        widget.setCurrentIndex(3)
        assert widget.get_pattern() == RecurrencePattern.MONTHLY
        widget.close()


class TestBulkEntryDialog:
    """Test bulk entry dialog."""
    
    def test_dialog_initialization(self, qapp):
        """Test dialog initializes correctly."""
        dialog = BulkEntryDialog()
        assert dialog.windowTitle() == "Bulk Entry"
        assert dialog.table.rowCount() == 1  # Initial row
        assert dialog.table.columnCount() == 7
        dialog.close()
    
    def test_add_row(self, qapp):
        """Test adding rows to table."""
        dialog = BulkEntryDialog()
        initial_rows = dialog.table.rowCount()
        
        dialog._on_add_row()
        assert dialog.table.rowCount() == initial_rows + 1
        
        # Check that widgets are set in new row
        row = dialog.table.rowCount() - 1
        assert dialog.table.cellWidget(row, dialog.COL_DATE) is not None
        assert dialog.table.cellWidget(row, dialog.COL_AMOUNT) is not None
        assert dialog.table.cellWidget(row, dialog.COL_TYPE) is not None
        assert dialog.table.cellWidget(row, dialog.COL_RECURRENCE) is not None
        
        dialog.close()
    
    def test_remove_rows(self, qapp):
        """Test removing rows from table."""
        dialog = BulkEntryDialog()
        dialog._on_add_row()
        dialog._on_add_row()
        initial_rows = dialog.table.rowCount()
        
        # Select first row
        dialog.table.selectRow(0)
        dialog._on_remove_rows()
        
        assert dialog.table.rowCount() == initial_rows - 1
        dialog.close()
    
    def test_parse_transactions_empty(self, qapp):
        """Test parsing transactions from empty table."""
        dialog = BulkEntryDialog()
        # Clear the initial row by removing it
        dialog.table.removeRow(0)
        transactions = dialog._parse_transactions()
        assert len(transactions) == 0
        dialog.close()
    
    def test_parse_transactions_valid(self, qapp):
        """Test parsing valid transactions."""
        dialog = BulkEntryDialog()
        
        # Fill in the first row
        date_widget = dialog.table.cellWidget(0, dialog.COL_DATE)
        date_widget.setDate(QDate(2024, 1, 15))
        
        amount_widget = dialog.table.cellWidget(0, dialog.COL_AMOUNT)
        amount_widget.setValue(100.0)
        
        type_widget = dialog.table.cellWidget(0, dialog.COL_TYPE)
        type_widget.setCurrentIndex(0)  # Deposit
        
        # Get or create description item
        from PyQt6.QtWidgets import QTableWidgetItem
        desc_item = dialog.table.item(0, dialog.COL_DESCRIPTION)
        if desc_item is None:
            desc_item = QTableWidgetItem("Test description")
            dialog.table.setItem(0, dialog.COL_DESCRIPTION, desc_item)
        else:
            desc_item.setText("Test description")
        
        transactions = dialog._parse_transactions()
        
        assert len(transactions) == 1
        assert transactions[0].date == date(2024, 1, 15)
        assert transactions[0].amount == 100.0
        assert transactions[0].type == TransactionType.DEPOSIT
        assert transactions[0].description == "Test description"
        dialog.close()
    
    def test_parse_transactions_with_recurrence(self, qapp):
        """Test parsing transactions with recurrence pattern."""
        dialog = BulkEntryDialog()
        
        # Fill in the first row with recurrence
        date_widget = dialog.table.cellWidget(0, dialog.COL_DATE)
        date_widget.setDate(QDate(2024, 1, 1))
        
        amount_widget = dialog.table.cellWidget(0, dialog.COL_AMOUNT)
        amount_widget.setValue(1000.0)
        
        type_widget = dialog.table.cellWidget(0, dialog.COL_TYPE)
        type_widget.setCurrentIndex(0)  # Deposit
        
        recur_widget = dialog.table.cellWidget(0, dialog.COL_RECURRENCE)
        recur_widget.setCurrentIndex(3)  # Monthly
        
        # Get or create description item
        from PyQt6.QtWidgets import QTableWidgetItem
        desc_item = dialog.table.item(0, dialog.COL_DESCRIPTION)
        if desc_item is None:
            desc_item = QTableWidgetItem("Salary")
            dialog.table.setItem(0, dialog.COL_DESCRIPTION, desc_item)
        else:
            desc_item.setText("Salary")
        
        transactions = dialog._parse_transactions()
        
        assert len(transactions) == 1
        assert transactions[0].is_template is True
        assert transactions[0].recurrence_pattern == RecurrencePattern.MONTHLY
        dialog.close()
    
    def test_get_transactions(self, qapp):
        """Test get_transactions method."""
        dialog = BulkEntryDialog()
        transactions = dialog.get_transactions()
        # Should return list (may be empty if default row has invalid data)
        assert isinstance(transactions, list)
        dialog.close()

