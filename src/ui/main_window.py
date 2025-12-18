"""Main application window."""

from datetime import date, datetime, timedelta
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMenuBar,
    QStatusBar, QMenu, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QDate

from src.models.database import Database
from src.models.transaction import Transaction, TransactionType, RecurrencePattern
from src.services.transaction_service import TransactionService
from src.services.recurrence_service import RecurrenceService
from src.ui.calendar_widget import CalendarWidget
from src.ui.weekly_balance_widget import WeeklyBalanceWidget
from src.ui.transactions_list_widget import TransactionsListWidget
from src.ui.transaction_dialog import TransactionDialog


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, database: Database):
        """
        Initialize main window.
        
        Args:
            database: Database instance
        """
        super().__init__()
        self.db = database
        self.transaction_service = TransactionService(database)
        self.recurrence_service = RecurrenceService(self.transaction_service)
        
        self.current_date = date.today()
        
        self._setup_ui()
        self._load_data()
        
        # Generate recurring transaction instances up to 1 year ahead
        self._generate_recurring_instances()
    
    def _setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("Payment Tracker")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Calendar widget
        self.calendar = CalendarWidget()
        self.calendar.setSelectedDate(QDate(
            self.current_date.year,
            self.current_date.month,
            self.current_date.day
        ))
        self.calendar.date_clicked.connect(self._on_calendar_date_clicked)
        self.calendar.currentPageChanged.connect(self._on_calendar_month_changed)
        main_layout.addWidget(self.calendar)
        
        # Weekly balance widget
        self.weekly_balance_widget = WeeklyBalanceWidget()
        main_layout.addWidget(self.weekly_balance_widget)
        
        # Transactions list widget
        self.transactions_list = TransactionsListWidget()
        self.transactions_list.edit_requested.connect(self._on_edit_transaction)
        self.transactions_list.delete_requested.connect(self._on_delete_transaction)
        main_layout.addWidget(self.transactions_list)
        
        # Menu bar
        self._setup_menu_bar()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _setup_menu_bar(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        add_transaction_action = edit_menu.addAction("Add Transaction")
        add_transaction_action.setShortcut("Ctrl+N")
        add_transaction_action.triggered.connect(self._on_add_transaction)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._on_about)
    
    def _load_data(self):
        """Load transactions for the current month view."""
        selected_date = self.calendar.selectedDate()
        year = selected_date.year()
        month = selected_date.month()
        
        # Get transactions for the month
        transactions = self.transaction_service.get_transactions_for_month(year, month)
        
        # Update calendar
        self.calendar.set_transactions(transactions)
        
        # Update transactions list
        self.transactions_list.set_transactions(transactions)
        
        # Update weekly balances
        weekly_balances = self.transaction_service.calculate_weekly_balances(year, month)
        self.weekly_balance_widget.update_balances(weekly_balances)
    
    def _generate_recurring_instances(self):
        """Generate recurring transaction instances up to 1 year ahead."""
        end_date = date.today() + timedelta(days=365)
        try:
            self.recurrence_service.generate_all_instances_up_to(end_date, regenerate_existing=False)
            self._load_data()  # Reload to show new instances
        except Exception as e:
            # Log error but don't crash
            print(f"Error generating recurring instances: {e}")
    
    def _on_calendar_date_clicked(self, clicked_date: date):
        """Handle calendar date click."""
        # Open dialog to add transaction for this date
        dialog = TransactionDialog(self)
        qt_date = QDate(clicked_date.year, clicked_date.month, clicked_date.day)
        dialog.date_edit.setDate(qt_date)
        
        if dialog.exec():
            transaction_data = dialog.get_transaction_data()
            transaction_date = transaction_data.pop("date")  # Remove date from dict to avoid duplicate
            recurrence_pattern = transaction_data.pop("recurrence_pattern")
            is_template = transaction_data.pop("is_template")
            
            # Create transaction
            if is_template:
                # Create template
                template = Transaction(
                    date=transaction_date,
                    is_template=True,
                    recurrence_pattern=recurrence_pattern,
                    **transaction_data
                )
                saved_template = self.transaction_service.create_transaction(template)
                
                # Generate instances
                end_date = date.today() + timedelta(days=365)
                instances = self.recurrence_service.generate_instances(
                    saved_template,
                    transaction_date,
                    end_date,
                    regenerate_existing=False
                )
                
                # Save instances
                for instance in instances:
                    self.transaction_service.create_transaction(instance)
            else:
                # Create one-time transaction
                transaction = Transaction(
                    date=transaction_date,
                    is_template=False,
                    recurrence_pattern=None,
                    **transaction_data
                )
                self.transaction_service.create_transaction(transaction)
            
            self._load_data()
            self.status_bar.showMessage("Transaction added successfully", 3000)
    
    def _on_calendar_month_changed(self, year: int, month: int):
        """Handle calendar month change."""
        self._load_data()
    
    def _on_add_transaction(self):
        """Handle add transaction action."""
        selected_date = self.calendar.selectedDate()
        transaction_date = date(
            selected_date.year(),
            selected_date.month(),
            selected_date.day()
        )
        
        dialog = TransactionDialog(self)
        dialog.date_edit.setDate(selected_date)
        
        if dialog.exec():
            transaction_data = dialog.get_transaction_data()
            transaction_date = transaction_data.pop("date")  # Remove date from dict to avoid duplicate
            recurrence_pattern = transaction_data.pop("recurrence_pattern")
            is_template = transaction_data.pop("is_template")
            
            # Create transaction
            if is_template:
                # Create template
                template = Transaction(
                    date=transaction_date,
                    is_template=True,
                    recurrence_pattern=recurrence_pattern,
                    **transaction_data
                )
                saved_template = self.transaction_service.create_transaction(template)
                
                # Generate instances
                end_date = date.today() + timedelta(days=365)
                instances = self.recurrence_service.generate_instances(
                    saved_template,
                    transaction_date,
                    end_date,
                    regenerate_existing=False
                )
                
                # Save instances
                for instance in instances:
                    self.transaction_service.create_transaction(instance)
            else:
                # Create one-time transaction
                transaction = Transaction(
                    date=transaction_date,
                    is_template=False,
                    recurrence_pattern=None,
                    **transaction_data
                )
                self.transaction_service.create_transaction(transaction)
            
            self._load_data()
            self.status_bar.showMessage("Transaction added successfully", 3000)
    
    def _on_edit_transaction(self, transaction: Transaction):
        """Handle edit transaction request."""
        dialog = TransactionDialog(self, transaction)
        
        if dialog.exec():
            transaction_data = dialog.get_transaction_data()
            
            # Update transaction fields
            transaction.date = transaction_data["date"]
            transaction.amount = transaction_data["amount"]
            transaction.type = transaction_data["type"]
            transaction.description = transaction_data["description"]
            transaction.category = transaction_data["category"]
            transaction.payee = transaction_data["payee"]
            
            # Update in database
            self.transaction_service.update_transaction(transaction)
            
            # If this is a template, regenerate future instances
            if transaction.is_template:
                end_date = date.today() + timedelta(days=365)
                # Delete existing future instances
                existing_instances = self.transaction_service.get_transaction_instances(transaction.id)
                for instance in existing_instances:
                    if instance.date > date.today():
                        self.transaction_service.delete_transaction(instance.id)
                
                # Regenerate future instances
                instances = self.recurrence_service.generate_instances(
                    transaction,
                    date.today() + timedelta(days=1),
                    end_date,
                    regenerate_existing=False
                )
                for instance in instances:
                    self.transaction_service.create_transaction(instance)
            
            self._load_data()
            self.status_bar.showMessage("Transaction updated successfully", 3000)
    
    def _on_delete_transaction(self, transaction: Transaction):
        """Handle delete transaction request."""
        # Delete from database
        self.transaction_service.delete_transaction(transaction.id)
        
        self._load_data()
        self.status_bar.showMessage("Transaction deleted successfully", 3000)
    
    def _on_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Payment Tracker",
            "Payment Tracker v1.0\n\n"
            "A Python application for tracking payments, deposits, and withdrawals\n"
            "with a calendar-based interface."
        )
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.db.close()
        event.accept()

