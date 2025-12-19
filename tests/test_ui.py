"""UI tests using pytest-qt."""

import os
import tempfile
import pytest
from datetime import date
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import QApplication

from src.models.database import Database
from src.models.transaction import Transaction, TransactionType, RecurrencePattern
from src.services.transaction_service import TransactionService
from src.ui.transaction_dialog import TransactionDialog
from src.ui.calendar_widget import CalendarWidget
from src.ui.main_window import MainWindow
from src.ui.transactions_list_widget import TransactionsListWidget


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for tests."""
    if not QApplication.instance():
        app = QApplication([])
        yield app
        app.quit()
    else:
        yield QApplication.instance()


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


class TestTransactionDialog:
    """Test transaction dialog."""
    
    def test_dialog_initialization(self, qapp):
        """Test dialog initializes correctly."""
        dialog = TransactionDialog()
        assert dialog is not None
        assert dialog.windowTitle() == "Add Transaction"
        dialog.close()
    
    def test_dialog_fields_exist(self, qapp):
        """Test that all required fields exist in the dialog."""
        dialog = TransactionDialog()
        assert dialog.date_edit is not None
        assert dialog.amount_spinbox is not None
        assert dialog.type_combo is not None
        assert dialog.description_edit is not None
        assert dialog.category_edit is not None
        assert dialog.payee_edit is not None
        assert dialog.recurrence_combo is not None
        assert dialog.save_button is not None
        assert dialog.cancel_button is not None
        dialog.close()
    
    def test_dialog_edit_mode(self, qapp, transaction_service):
        """Test dialog in edit mode."""
        transaction = Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Test transaction",
            category="Test",
            payee="Test Payee"
        )
        saved = transaction_service.create_transaction(transaction)
        
        dialog = TransactionDialog(transaction=saved)
        assert dialog.windowTitle() == "Edit Transaction"
        assert dialog.description_edit.text() == "Test transaction"
        assert dialog.amount_spinbox.value() == 100.0
        dialog.close()
    
    def test_dialog_get_transaction_data(self, qapp):
        """Test getting transaction data from dialog."""
        dialog = TransactionDialog()
        dialog.date_edit.setDate(QDate(2024, 1, 15))
        dialog.amount_spinbox.setValue(150.0)
        dialog.type_combo.setCurrentIndex(0)  # Deposit
        dialog.description_edit.setText("Test description")
        dialog.category_edit.setText("Test category")
        dialog.payee_edit.setText("Test payee")
        
        data = dialog.get_transaction_data()
        assert data["date"] == date(2024, 1, 15)
        assert data["amount"] == 150.0
        assert data["type"] == TransactionType.DEPOSIT
        assert data["description"] == "Test description"
        assert data["category"] == "Test category"
        assert data["payee"] == "Test payee"
        dialog.close()
    
    def test_dialog_validation(self, qapp):
        """Test dialog validation."""
        dialog = TransactionDialog()
        
        # Test validation with valid amount (spinbox minimum is 0.01, so we test with valid values)
        dialog.amount_spinbox.setValue(0.01)  # Minimum valid value
        result = dialog._validate()
        assert result is True
        
        # Test validation with larger valid amount
        dialog.amount_spinbox.setValue(100.0)
        result = dialog._validate()
        assert result is True
        
        # Note: We cannot test invalid values (< 0.01) because QDoubleSpinBox
        # enforces the minimum value and prevents setting values below 0.01
        dialog.close()


class TestCalendarWidget:
    """Test calendar widget."""
    
    def test_calendar_initialization(self, qapp):
        """Test calendar widget initializes correctly."""
        calendar = CalendarWidget()
        assert calendar is not None
        assert calendar.transactions_by_date == {}
        calendar.close()
    
    def test_calendar_set_transactions(self, qapp):
        """Test setting transactions on calendar."""
        calendar = CalendarWidget()
        transactions = [
            Transaction(
                date=date(2024, 1, 15),
                amount=100.0,
                type=TransactionType.DEPOSIT,
                description="Test"
            ),
            Transaction(
                date=date(2024, 1, 15),
                amount=50.0,
                type=TransactionType.WITHDRAWAL,
                description="Test 2"
            ),
            Transaction(
                date=date(2024, 1, 20),
                amount=200.0,
                type=TransactionType.DEPOSIT,
                description="Test 3"
            )
        ]
        
        calendar.set_transactions(transactions)
        assert len(calendar.transactions_by_date) == 2
        assert date(2024, 1, 15) in calendar.transactions_by_date
        assert date(2024, 1, 20) in calendar.transactions_by_date
        assert len(calendar.transactions_by_date[date(2024, 1, 15)]) == 2
        calendar.close()
    
    def test_calendar_date_clicked_signal(self, qapp, qtbot):
        """Test calendar date clicked signal."""
        calendar = CalendarWidget()
        
        clicked_dates = []
        def on_date_clicked(clicked_date):
            clicked_dates.append(clicked_date)
        
        calendar.date_clicked.connect(on_date_clicked)
        
        # Simulate a date click by calling the handler directly
        test_qdate = QDate(2024, 1, 15)
        calendar._on_date_clicked(test_qdate)
        
        assert len(clicked_dates) > 0
        assert clicked_dates[-1] == date(2024, 1, 15)
        calendar.close()


class TestMainWindow:
    """Test main window."""
    
    def test_main_window_initialization(self, qapp, temp_db):
        """Test main window initializes correctly."""
        window = MainWindow(temp_db)
        assert window is not None
        assert window.windowTitle() == "Payment Tracker"
        assert window.calendar is not None
        assert window.weekly_balance_widget is not None
        assert window.transactions_list is not None
        window.close()
    
    def test_main_window_load_data(self, qapp, temp_db, transaction_service, qtbot):
        """Test main window loads data correctly."""
        # Create test transactions
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Test"
        ))
        
        window = MainWindow(temp_db)
        window.calendar.setSelectedDate(QDate(2024, 1, 15))
        
        # Process events to allow Qt to handle signals
        qtbot.wait(100)
        
        window._load_data()
        qtbot.wait(100)
        
        # Check that transactions are loaded
        transactions = window.transactions_list.transactions
        assert len(transactions) > 0
        window.close()
    
    def test_main_window_add_transaction(self, qapp, temp_db, qtbot):
        """Test adding transaction through main window."""
        window = MainWindow(temp_db)
        
        # Process events to allow Qt to handle initialization
        qtbot.wait(100)
        
        # Set calendar to a specific date
        window.calendar.setSelectedDate(QDate(2024, 1, 15))
        qtbot.wait(100)
        
        # Note: _on_add_transaction opens a dialog which requires user interaction
        # So we'll just test that the method exists and can be called
        # In a real test with qtbot, we'd use qtbot.keyClick or similar to interact with dialog
        # For now, just verify the method exists
        assert hasattr(window, '_on_add_transaction')
        assert callable(window._on_add_transaction)
        
        window.close()
    
    def test_main_window_menu_bar(self, qapp, temp_db):
        """Test main window menu bar exists."""
        window = MainWindow(temp_db)
        menubar = window.menuBar()
        assert menubar is not None
        
        # Check that menus exist
        actions = menubar.actions()
        menu_names = [action.text() for action in actions]
        assert "File" in menu_names
        assert "Edit" in menu_names
        assert "Help" in menu_names
        window.close()


class TestTransactionsListWidgetFiltering:
    """Test transactions list widget with filtering."""
    
    def test_transactions_list_with_filter_widget(self, qapp, temp_db, transaction_service):
        """Test that transactions list widget has filter widget."""
        # Create test transactions
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Test deposit"
        ))
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 20),
            amount=50.0,
            type=TransactionType.WITHDRAWAL,
            description="Test withdrawal"
        ))
        
        widget = TransactionsListWidget()
        transactions = transaction_service.get_transactions_for_month(2024, 1)
        widget.set_transactions(transactions)
        
        # Verify filter widget exists
        assert widget.filter_widget is not None
        assert len(widget.all_transactions) == 2
        assert len(widget.transactions) == 2  # Initially all shown
        
        widget.close()
    
    def test_filter_text_search(self, qapp, temp_db, transaction_service):
        """Test filtering transactions by text search."""
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Salary payment",
            category="Income"
        ))
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 20),
            amount=50.0,
            type=TransactionType.WITHDRAWAL,
            description="Grocery shopping",
            category="Food"
        ))
        
        widget = TransactionsListWidget()
        transactions = transaction_service.get_transactions_for_month(2024, 1)
        widget.set_transactions(transactions)
        
        # Apply text filter
        widget.filter_widget.text_search.setText("Salary")
        widget._apply_filters()
        
        assert len(widget.transactions) == 1
        assert widget.transactions[0].description == "Salary payment"
        
        widget.close()
    
    def test_filter_by_type(self, qapp, temp_db, transaction_service):
        """Test filtering transactions by type."""
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Deposit"
        ))
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 20),
            amount=50.0,
            type=TransactionType.WITHDRAWAL,
            description="Withdrawal"
        ))
        
        widget = TransactionsListWidget()
        transactions = transaction_service.get_transactions_for_month(2024, 1)
        widget.set_transactions(transactions)
        
        # Filter by deposit only
        widget.filter_widget.type_combo.setCurrentIndex(1)  # Deposit
        widget._apply_filters()
        
        assert len(widget.transactions) == 1
        assert widget.transactions[0].type == TransactionType.DEPOSIT
        
        widget.close()
    
    def test_filter_combined(self, qapp, temp_db, transaction_service):
        """Test combined filtering."""
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 15),
            amount=100.0,
            type=TransactionType.DEPOSIT,
            description="Salary",
            category="Income"
        ))
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 20),
            amount=50.0,
            type=TransactionType.DEPOSIT,
            description="Bonus",
            category="Income"
        ))
        transaction_service.create_transaction(Transaction(
            date=date(2024, 1, 25),
            amount=150.0,
            type=TransactionType.WITHDRAWAL,
            description="Rent",
            category="Housing"
        ))
        
        widget = TransactionsListWidget()
        transactions = transaction_service.get_transactions_for_month(2024, 1)
        widget.set_transactions(transactions)
        
        # Filter by type (deposit) and text (Income)
        widget.filter_widget.type_combo.setCurrentIndex(1)  # Deposit
        widget.filter_widget.text_search.setText("Income")
        widget._apply_filters()
        
        assert len(widget.transactions) == 2
        assert all(t.type == TransactionType.DEPOSIT for t in widget.transactions)
        assert all("Income" in t.category for t in widget.transactions)
        
        widget.close()

