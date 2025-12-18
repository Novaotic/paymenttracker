"""Transaction dialog for adding/editing transactions."""

from datetime import date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDoubleSpinBox, QComboBox, QPushButton, QDateEdit, QMessageBox
)
from PyQt6.QtCore import QDate, Qt

from src.models.transaction import Transaction, TransactionType, RecurrencePattern


class TransactionDialog(QDialog):
    """Dialog for adding or editing a transaction."""
    
    def __init__(self, parent=None, transaction: Transaction = None):
        """
        Initialize transaction dialog.
        
        Args:
            parent: Parent widget
            transaction: Transaction to edit (None for new transaction)
        """
        super().__init__(parent)
        self.transaction = transaction
        self.setWindowTitle("Edit Transaction" if transaction else "Add Transaction")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self._setup_ui()
        
        if transaction:
            self._populate_fields()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Date field
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(self.date_edit)
        layout.addLayout(date_layout)
        
        # Amount field
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel("Amount:"))
        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setMinimum(0.01)
        self.amount_spinbox.setMaximum(999999.99)
        self.amount_spinbox.setDecimals(2)
        self.amount_spinbox.setPrefix("$ ")
        amount_layout.addWidget(self.amount_spinbox)
        layout.addLayout(amount_layout)
        
        # Type field
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("Deposit", TransactionType.DEPOSIT)
        self.type_combo.addItem("Withdrawal", TransactionType.WITHDRAWAL)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Description field
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.description_edit = QLineEdit()
        desc_layout.addWidget(self.description_edit)
        layout.addLayout(desc_layout)
        
        # Category field
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Category:"))
        self.category_edit = QLineEdit()
        category_layout.addWidget(self.category_edit)
        layout.addLayout(category_layout)
        
        # Payee field
        payee_layout = QHBoxLayout()
        payee_layout.addWidget(QLabel("Payee:"))
        self.payee_edit = QLineEdit()
        payee_layout.addWidget(self.payee_edit)
        layout.addLayout(payee_layout)
        
        # Recurrence pattern (only for new transactions or templates)
        recurrence_layout = QHBoxLayout()
        recurrence_layout.addWidget(QLabel("Recurrence:"))
        self.recurrence_combo = QComboBox()
        self.recurrence_combo.addItem("One-time", None)
        self.recurrence_combo.addItem("Weekly", RecurrencePattern.WEEKLY)
        self.recurrence_combo.addItem("Biweekly", RecurrencePattern.BIWEEKLY)
        self.recurrence_combo.addItem("Monthly", RecurrencePattern.MONTHLY)
        recurrence_layout.addWidget(self.recurrence_combo)
        layout.addLayout(recurrence_layout)
        
        # Disable recurrence for editing existing instances
        if self.transaction and not self.transaction.is_template:
            self.recurrence_combo.setEnabled(False)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._on_save)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
    
    def _populate_fields(self):
        """Populate fields with transaction data."""
        if not self.transaction:
            return
        
        qt_date = QDate(
            self.transaction.date.year,
            self.transaction.date.month,
            self.transaction.date.day
        )
        self.date_edit.setDate(qt_date)
        self.amount_spinbox.setValue(self.transaction.amount)
        
        # Set type
        index = self.type_combo.findData(self.transaction.type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        
        self.description_edit.setText(self.transaction.description)
        self.category_edit.setText(self.transaction.category)
        self.payee_edit.setText(self.transaction.payee)
        
        # Set recurrence pattern
        if self.transaction.recurrence_pattern:
            index = self.recurrence_combo.findData(self.transaction.recurrence_pattern)
            if index >= 0:
                self.recurrence_combo.setCurrentIndex(index)
    
    def _on_save(self):
        """Handle save button click."""
        if not self._validate():
            return
        
        self.accept()
    
    def _validate(self) -> bool:
        """Validate form data."""
        # Check if amount is valid (spinbox minimum is 0.01, so check for very small values)
        if self.amount_spinbox.value() < 0.01:
            QMessageBox.warning(self, "Validation Error", "Amount must be greater than 0")
            return False
        
        return True
    
    def get_transaction_data(self) -> dict:
        """
        Get transaction data from form fields.
        
        Returns:
            Dictionary with transaction data
        """
        qt_date = self.date_edit.date()
        transaction_date = date(qt_date.year(), qt_date.month(), qt_date.day())
        
        recurrence_pattern = self.recurrence_combo.currentData()
        
        return {
            "date": transaction_date,
            "amount": self.amount_spinbox.value(),
            "type": self.type_combo.currentData(),
            "description": self.description_edit.text().strip(),
            "category": self.category_edit.text().strip(),
            "payee": self.payee_edit.text().strip(),
            "recurrence_pattern": recurrence_pattern,
            "is_template": recurrence_pattern is not None,
        }

