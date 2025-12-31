"""Bulk entry dialog for manually entering multiple transactions."""

from datetime import date
from typing import List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QDateEdit,
    QDoubleSpinBox, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, QDate

from src.models.transaction import Transaction, TransactionType, RecurrencePattern


class DateEditItem(QDateEdit):
    """Custom date edit widget for table cells."""
    
    def __init__(self, parent=None):
        """Initialize date edit widget."""
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDate(QDate.currentDate())
        self.setDisplayFormat("yyyy-MM-dd")
    
    def get_date(self) -> date:
        """Get date as Python date object."""
        qt_date = self.date()
        return date(qt_date.year(), qt_date.month(), qt_date.day())


class AmountEditItem(QDoubleSpinBox):
    """Custom amount spinbox for table cells."""
    
    def __init__(self, parent=None):
        """Initialize amount spinbox."""
        super().__init__(parent)
        self.setMinimum(0.01)
        self.setMaximum(999999.99)
        self.setDecimals(2)
        self.setPrefix("$ ")
        self.setValue(0.01)


class TypeComboItem(QComboBox):
    """Custom combo box for transaction type."""
    
    def __init__(self, parent=None):
        """Initialize type combo box."""
        super().__init__(parent)
        self.addItem("Deposit", TransactionType.DEPOSIT)
        self.addItem("Withdrawal", TransactionType.WITHDRAWAL)
    
    def get_type(self) -> TransactionType:
        """Get selected transaction type."""
        return self.currentData()


class RecurrenceComboItem(QComboBox):
    """Custom combo box for recurrence pattern."""
    
    def __init__(self, parent=None):
        """Initialize recurrence combo box."""
        super().__init__(parent)
        self.addItem("One-time", None)
        self.addItem("Weekly", RecurrencePattern.WEEKLY)
        self.addItem("Biweekly", RecurrencePattern.BIWEEKLY)
        self.addItem("Monthly", RecurrencePattern.MONTHLY)
    
    def get_pattern(self) -> Optional[RecurrencePattern]:
        """Get selected recurrence pattern."""
        return self.currentData()


class BulkEntryDialog(QDialog):
    """Dialog for bulk entry of transactions."""
    
    COL_DATE = 0
    COL_AMOUNT = 1
    COL_TYPE = 2
    COL_DESCRIPTION = 3
    COL_CATEGORY = 4
    COL_PAYEE = 5
    COL_RECURRENCE = 6
    
    def __init__(self, parent=None):
        """Initialize bulk entry dialog."""
        super().__init__(parent)
        self.setWindowTitle("Bulk Entry")
        self.setModal(True)
        self.setMinimumSize(900, 600)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("Enter transactions below. Use the buttons to add or remove rows.")
        layout.addWidget(instructions)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Date", "Amount", "Type", "Description", "Category", "Payee", "Recurrence"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(True)
        layout.addWidget(self.table)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        add_row_button = QPushButton("Add Row")
        add_row_button.clicked.connect(self._on_add_row)
        button_layout.addWidget(add_row_button)
        
        remove_row_button = QPushButton("Remove Selected Rows")
        remove_row_button.clicked.connect(self._on_remove_rows)
        button_layout.addWidget(remove_row_button)
        
        button_layout.addStretch()
        
        self.import_button = QPushButton("Import")
        self.import_button.clicked.connect(self._on_import)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Add initial row
        self._on_add_row()
    
    def _on_add_row(self):
        """Add a new row to the table."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Date column
        date_edit = DateEditItem()
        self.table.setCellWidget(row, self.COL_DATE, date_edit)
        
        # Amount column
        amount_edit = AmountEditItem()
        self.table.setCellWidget(row, self.COL_AMOUNT, amount_edit)
        
        # Type column
        type_combo = TypeComboItem()
        self.table.setCellWidget(row, self.COL_TYPE, type_combo)
        
        # Description column
        desc_item = QTableWidgetItem("")
        self.table.setItem(row, self.COL_DESCRIPTION, desc_item)
        
        # Category column
        cat_item = QTableWidgetItem("")
        self.table.setItem(row, self.COL_CATEGORY, cat_item)
        
        # Payee column
        payee_item = QTableWidgetItem("")
        self.table.setItem(row, self.COL_PAYEE, payee_item)
        
        # Recurrence column
        recur_combo = RecurrenceComboItem()
        self.table.setCellWidget(row, self.COL_RECURRENCE, recur_combo)
    
    def _on_remove_rows(self):
        """Remove selected rows from the table."""
        selected_rows = sorted(set(item.row() for item in self.table.selectedItems()), reverse=True)
        
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select rows to remove.")
            return
        
        for row in selected_rows:
            self.table.removeRow(row)
    
    def _on_import(self):
        """Handle import button click."""
        transactions = self._parse_transactions()
        
        if not transactions:
            QMessageBox.warning(self, "No Transactions", "No valid transactions to import. Please add at least one transaction.")
            return
        
        # Validate transactions
        errors = []
        for idx, transaction in enumerate(transactions):
            if transaction is None:
                errors.append(f"Row {idx + 1}: Invalid transaction data")
        
        if errors:
            error_msg = "Validation errors:\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                error_msg += f"\n... and {len(errors) - 10} more errors"
            QMessageBox.warning(self, "Validation Errors", error_msg)
            return
        
        self.accept()
    
    def _parse_transactions(self) -> List[Optional[Transaction]]:
        """Parse transactions from table."""
        transactions = []
        
        for row in range(self.table.rowCount()):
            try:
                # Get widgets
                date_widget = self.table.cellWidget(row, self.COL_DATE)
                amount_widget = self.table.cellWidget(row, self.COL_AMOUNT)
                type_widget = self.table.cellWidget(row, self.COL_TYPE)
                desc_item = self.table.item(row, self.COL_DESCRIPTION)
                cat_item = self.table.item(row, self.COL_CATEGORY)
                payee_item = self.table.item(row, self.COL_PAYEE)
                recur_widget = self.table.cellWidget(row, self.COL_RECURRENCE)
                
                if not all([date_widget, amount_widget, type_widget, recur_widget]):
                    continue
                
                # Get values
                transaction_date = date_widget.get_date()
                amount = amount_widget.value()
                transaction_type = type_widget.get_type()
                description = desc_item.text().strip() if desc_item else ""
                category = cat_item.text().strip() if cat_item else ""
                payee = payee_item.text().strip() if payee_item else ""
                recurrence_pattern = recur_widget.get_pattern()
                
                # Skip if amount is zero or default
                if amount <= 0:
                    continue
                
                is_template = recurrence_pattern is not None
                
                # Create transaction (validation happens in __init__)
                transaction = Transaction(
                    date=transaction_date,
                    amount=amount,
                    type=transaction_type,
                    description=description,
                    category=category,
                    payee=payee,
                    recurrence_pattern=recurrence_pattern,
                    is_template=is_template
                )
                
                transactions.append(transaction)
            except Exception as e:
                # Skip invalid rows
                transactions.append(None)
        
        # Filter out None values
        return [t for t in transactions if t is not None]
    
    def get_transactions(self) -> List[Transaction]:
        """Get parsed transactions."""
        return self._parse_transactions()

