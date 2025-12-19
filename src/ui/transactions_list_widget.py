"""Widget for displaying a list of transactions."""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from src.models.transaction import Transaction, TransactionType
from src.services.transaction_service import TransactionService
from src.ui.transaction_filter_widget import TransactionFilterWidget


class TransactionsListWidget(QWidget):
    """Widget displaying a list of transactions."""
    
    edit_requested = pyqtSignal(Transaction)  # Signal emitted when edit is requested
    delete_requested = pyqtSignal(Transaction)  # Signal emitted when delete is requested
    
    def __init__(self, parent=None):
        """Initialize transactions list widget."""
        super().__init__(parent)
        self.all_transactions: List[Transaction] = []  # Store all transactions
        self.transactions: List[Transaction] = []  # Displayed (filtered) transactions
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Transactions")
        title.setStyleSheet("font-weight: bold; font-size: 14pt;")
        layout.addWidget(title)
        
        # Filter widget
        self.filter_widget = TransactionFilterWidget()
        self.filter_widget.filter_changed.connect(self._apply_filters)
        layout.addWidget(self.filter_widget)
        
        # Table for transactions
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Date", "Type", "Amount", "Description", "Category", "Payee"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self._on_edit_clicked)
        self.edit_button.setEnabled(False)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Enable/disable buttons based on selection
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
    
    def set_transactions(self, transactions: List[Transaction]):
        """
        Set transactions to display.
        
        Args:
            transactions: List of transactions to display
        """
        # Store all transactions and apply current filters
        self.all_transactions = sorted(transactions, key=lambda t: (t.date, t.id or 0))
        self._apply_filters()
    
    def _apply_filters(self):
        """Apply current filters to the transaction list."""
        # Get filter values from filter widget
        text_search = self.filter_widget.get_text_search()
        transaction_type = self.filter_widget.get_transaction_type()
        min_amount, max_amount = self.filter_widget.get_amount_range()
        start_date, end_date = self.filter_widget.get_date_range()
        
        # Apply filters using transaction service method
        self.transactions = TransactionService.filter_transactions(
            self.all_transactions,
            text_search=text_search,
            transaction_type=transaction_type,
            min_amount=min_amount,
            max_amount=max_amount,
            start_date=start_date,
            end_date=end_date
        )
        
        # Update table display
        self._populate_table()
    
    def _populate_table(self):
        """Populate the table with transactions."""
        self.table.setRowCount(len(self.transactions))
        
        for row, transaction in enumerate(self.transactions):
            # Date
            date_item = QTableWidgetItem(transaction.date.strftime("%Y-%m-%d"))
            self.table.setItem(row, 0, date_item)
            
            # Type
            type_str = "Deposit" if transaction.type == TransactionType.DEPOSIT else "Withdrawal"
            type_item = QTableWidgetItem(type_str)
            if transaction.type == TransactionType.DEPOSIT:
                type_item.setForeground(QColor(0, 150, 0))
            else:
                type_item.setForeground(QColor(200, 0, 0))
            self.table.setItem(row, 1, type_item)
            
            # Amount
            amount_item = QTableWidgetItem(f"${transaction.amount:,.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if transaction.type == TransactionType.DEPOSIT:
                amount_item.setForeground(QColor(0, 150, 0))
            else:
                amount_item.setForeground(QColor(200, 0, 0))
            self.table.setItem(row, 2, amount_item)
            
            # Description
            desc_item = QTableWidgetItem(transaction.description)
            # Show indicator for recurring transactions
            if transaction.recurring_template_id:
                desc_item.setText(f"📅 {transaction.description}")
            self.table.setItem(row, 3, desc_item)
            
            # Category
            category_item = QTableWidgetItem(transaction.category)
            self.table.setItem(row, 4, category_item)
            
            # Payee
            payee_item = QTableWidgetItem(transaction.payee)
            self.table.setItem(row, 5, payee_item)
        
        # Resize columns to fit content
        self.table.resizeColumnsToContents()
    
    def _on_selection_changed(self):
        """Handle table selection change."""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
    
    def _on_item_double_clicked(self, item: QTableWidgetItem):
        """Handle double-click on table item."""
        self._on_edit_clicked()
    
    def _on_edit_clicked(self):
        """Handle edit button click."""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if 0 <= row < len(self.transactions):
            self.edit_requested.emit(self.transactions[row])
    
    def _on_delete_clicked(self):
        """Handle delete button click."""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if 0 <= row < len(self.transactions):
            transaction = self.transactions[row]
            
            # Confirm deletion
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete this transaction?\n\n"
                f"Date: {transaction.date}\n"
                f"Amount: ${transaction.amount:,.2f}\n"
                f"Description: {transaction.description}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.delete_requested.emit(transaction)

