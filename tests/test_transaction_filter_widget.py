"""Tests for transaction filter widget UI."""

import pytest
from datetime import date
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDate, Qt

from src.ui.transaction_filter_widget import TransactionFilterWidget
from src.models.transaction import TransactionType


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for tests."""
    if not QApplication.instance():
        app = QApplication([])
        yield app
        app.quit()
    else:
        yield QApplication.instance()


class TestTransactionFilterWidget:
    """Test transaction filter widget."""
    
    def test_widget_initialization(self, qapp):
        """Test filter widget initializes correctly."""
        widget = TransactionFilterWidget()
        assert widget is not None
        assert widget.text_search is not None
        assert widget.type_combo is not None
        assert widget.min_amount is not None
        assert widget.max_amount is not None
        assert widget.start_date is not None
        assert widget.end_date is not None
        assert widget.apply_button is not None
        assert widget.clear_button is not None
        widget.close()
    
    def test_text_search_getter(self, qapp):
        """Test getting text search value."""
        widget = TransactionFilterWidget()
        widget.text_search.setText("test search")
        assert widget.get_text_search() == "test search"
        widget.close()
    
    def test_text_search_trimmed(self, qapp):
        """Test that text search is trimmed."""
        widget = TransactionFilterWidget()
        widget.text_search.setText("  test search  ")
        assert widget.get_text_search() == "test search"
        widget.close()
    
    def test_transaction_type_getter_all(self, qapp):
        """Test getting transaction type - All selected."""
        widget = TransactionFilterWidget()
        widget.type_combo.setCurrentIndex(0)  # "All"
        assert widget.get_transaction_type() is None
        widget.close()
    
    def test_transaction_type_getter_deposit(self, qapp):
        """Test getting transaction type - Deposit selected."""
        widget = TransactionFilterWidget()
        widget.type_combo.setCurrentIndex(1)  # "Deposit"
        assert widget.get_transaction_type() == TransactionType.DEPOSIT
        widget.close()
    
    def test_transaction_type_getter_withdrawal(self, qapp):
        """Test getting transaction type - Withdrawal selected."""
        widget = TransactionFilterWidget()
        widget.type_combo.setCurrentIndex(2)  # "Withdrawal"
        assert widget.get_transaction_type() == TransactionType.WITHDRAWAL
        widget.close()
    
    def test_amount_range_getter_no_values(self, qapp):
        """Test getting amount range when values are at zero."""
        widget = TransactionFilterWidget()
        widget.min_amount.setValue(0.0)
        widget.max_amount.setValue(0.0)
        min_amount, max_amount = widget.get_amount_range()
        assert min_amount is None
        assert max_amount is None
        widget.close()
    
    def test_amount_range_getter_with_values(self, qapp):
        """Test getting amount range with actual values."""
        widget = TransactionFilterWidget()
        widget.min_amount.setValue(50.0)
        widget.max_amount.setValue(200.0)
        min_amount, max_amount = widget.get_amount_range()
        assert min_amount == 50.0
        assert max_amount == 200.0
        widget.close()
    
    def test_amount_range_getter_min_only(self, qapp):
        """Test getting amount range with only min value."""
        widget = TransactionFilterWidget()
        widget.min_amount.setValue(100.0)
        widget.max_amount.setValue(0.0)
        min_amount, max_amount = widget.get_amount_range()
        assert min_amount == 100.0
        assert max_amount is None
        widget.close()
    
    def test_amount_range_getter_max_only(self, qapp):
        """Test getting amount range with only max value."""
        widget = TransactionFilterWidget()
        widget.min_amount.setValue(0.0)
        widget.max_amount.setValue(500.0)
        min_amount, max_amount = widget.get_amount_range()
        assert min_amount is None
        assert max_amount == 500.0
        widget.close()
    
    def test_date_range_getter_inactive(self, qapp):
        """Test getting date range when filter is not active."""
        widget = TransactionFilterWidget()
        # Date filter should be inactive by default
        start_date, end_date = widget.get_date_range()
        assert start_date is None
        assert end_date is None
        widget.close()
    
    def test_date_range_getter_active(self, qapp):
        """Test getting date range when filter is active."""
        widget = TransactionFilterWidget()
        widget.start_date.setDate(QDate(2024, 1, 1))
        widget.end_date.setDate(QDate(2024, 12, 31))
        # Click apply to activate date filter
        widget._on_apply_clicked()
        start_date, end_date = widget.get_date_range()
        assert start_date == date(2024, 1, 1)
        assert end_date == date(2024, 12, 31)
        widget.close()
    
    def test_clear_filters(self, qapp):
        """Test clearing all filters."""
        widget = TransactionFilterWidget()
        # Set some values
        widget.text_search.setText("test")
        widget.type_combo.setCurrentIndex(1)  # Deposit
        widget.min_amount.setValue(100.0)
        widget.max_amount.setValue(200.0)
        widget._on_apply_clicked()  # Activate date filter
        
        # Clear filters
        widget._on_clear_clicked()
        
        assert widget.get_text_search() == ""
        assert widget.get_transaction_type() is None  # "All"
        min_amount, max_amount = widget.get_amount_range()
        assert min_amount is None
        assert max_amount is None
        start_date, end_date = widget.get_date_range()
        assert start_date is None
        assert end_date is None
        widget.close()
    
    def test_filter_changed_signal(self, qapp, qtbot):
        """Test that filter_changed signal is emitted."""
        widget = TransactionFilterWidget()
        signal_emitted = []
        
        def on_filter_changed():
            signal_emitted.append(True)
        
        widget.filter_changed.connect(on_filter_changed)
        
        # Change text search (real-time)
        widget.text_search.setText("test")
        qtbot.wait(100)
        assert len(signal_emitted) > 0
        
        # Change type (real-time)
        signal_emitted.clear()
        widget.type_combo.setCurrentIndex(1)
        qtbot.wait(100)
        assert len(signal_emitted) > 0
        
        # Click apply
        signal_emitted.clear()
        widget.apply_button.click()
        qtbot.wait(100)
        assert len(signal_emitted) > 0
        
        widget.close()

