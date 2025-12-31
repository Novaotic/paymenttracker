"""CSV import dialog for bulk transaction import."""

import csv
import io
from datetime import date
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QMessageBox,
    QFileDialog, QHeaderView, QWidget
)
from PyQt6.QtCore import Qt

from src.models.transaction import Transaction, TransactionType, RecurrencePattern


class CSVImportDialog(QDialog):
    """Dialog for importing transactions from CSV file."""
    
    # Column mapping options
    COLUMN_OPTIONS = [
        "Ignore",
        "Date",
        "Amount",
        "Type",
        "Description",
        "Category",
        "Payee",
        "Recurrence Pattern"
    ]
    
    def __init__(self, parent=None):
        """Initialize CSV import dialog."""
        super().__init__(parent)
        self.setWindowTitle("Import Transactions from CSV")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        
        self.csv_data: List[Dict[str, str]] = []
        self.csv_headers: List[str] = []
        self.column_mapping: Dict[str, str] = {}
        self.transactions: List[Transaction] = []
        self.validation_errors: List[str] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # File selection section
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("CSV File:"))
        self.file_path_label = QLabel("No file selected")
        file_layout.addWidget(self.file_path_label)
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._on_browse_file)
        file_layout.addWidget(browse_button)
        layout.addLayout(file_layout)
        
        # Column mapping section
        mapping_label = QLabel("Column Mapping:")
        layout.addWidget(mapping_label)
        
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setHorizontalHeaderLabels(["CSV Column", "Map To"])
        self.mapping_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.mapping_table)
        
        # Preview section
        preview_label = QLabel("Preview (first 20 rows):")
        layout.addWidget(preview_label)
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(7)
        self.preview_table.setHorizontalHeaderLabels([
            "Date", "Amount", "Type", "Description", "Category", "Payee", "Recurrence"
        ])
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.preview_table)
        
        # Validation errors
        self.errors_label = QLabel()
        self.errors_label.setWordWrap(True)
        self.errors_label.setStyleSheet("color: red;")
        layout.addWidget(self.errors_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.import_button = QPushButton("Import")
        self.import_button.setEnabled(False)
        self.import_button.clicked.connect(self._on_import)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
    
    def _on_browse_file(self):
        """Handle browse file button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.file_path_label.setText(Path(file_path).name)
            self._load_csv(file_path)
    
    def _load_csv(self, file_path: str):
        """Load and parse CSV file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.csv_headers = reader.fieldnames or []
                self.csv_data = list(reader)
            
            if not self.csv_data:
                QMessageBox.warning(self, "Empty File", "The CSV file is empty.")
                return
            
            self._setup_column_mapping()
            self._update_preview()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV file: {str(e)}")
    
    def _setup_column_mapping(self):
        """Set up column mapping UI."""
        self.mapping_table.setRowCount(len(self.csv_headers))
        
        # Auto-detect column mappings
        column_mapping = {}
        for header in self.csv_headers:
            header_lower = header.lower().strip()
            if any(x in header_lower for x in ['date', 'day', 'when']):
                column_mapping[header] = "Date"
            elif any(x in header_lower for x in ['amount', 'amt', 'value', 'money', 'cost', 'price']):
                column_mapping[header] = "Amount"
            elif any(x in header_lower for x in ['type', 'transaction type', 'kind']):
                column_mapping[header] = "Type"
            elif any(x in header_lower for x in ['description', 'desc', 'note', 'memo', 'details']):
                column_mapping[header] = "Description"
            elif any(x in header_lower for x in ['category', 'cat', 'cat.', 'categories']):
                column_mapping[header] = "Category"
            elif any(x in header_lower for x in ['payee', 'payer', 'from', 'to', 'recipient']):
                column_mapping[header] = "Payee"
            elif any(x in header_lower for x in ['recurrence', 'recurring', 'repeat', 'pattern']):
                column_mapping[header] = "Recurrence Pattern"
            else:
                column_mapping[header] = "Ignore"
        
        self.column_mapping = column_mapping
        
        # Populate mapping table
        for row, header in enumerate(self.csv_headers):
            # CSV column name
            header_item = QTableWidgetItem(header)
            header_item.setFlags(header_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.mapping_table.setItem(row, 0, header_item)
            
            # Map to combo box
            combo = QComboBox()
            combo.addItems(self.COLUMN_OPTIONS)
            current_mapping = column_mapping.get(header, "Ignore")
            index = combo.findText(current_mapping)
            if index >= 0:
                combo.setCurrentIndex(index)
            combo.currentTextChanged.connect(self._on_mapping_changed)
            self.mapping_table.setCellWidget(row, 1, combo)
    
    def _on_mapping_changed(self):
        """Handle column mapping change."""
        # Update column mapping dict
        for row in range(self.mapping_table.rowCount()):
            header = self.mapping_table.item(row, 0).text()
            combo = self.mapping_table.cellWidget(row, 1)
            if combo:
                self.column_mapping[header] = combo.currentText()
        
        self._update_preview()
    
    def _update_preview(self):
        """Update preview table with parsed data."""
        # Clear previous data
        self.preview_table.setRowCount(0)
        self.transactions = []
        self.validation_errors = []
        
        if not self.csv_data:
            return
        
        # Get mapped columns
        date_col = self._get_mapped_column("Date")
        amount_col = self._get_mapped_column("Amount")
        type_col = self._get_mapped_column("Type")
        desc_col = self._get_mapped_column("Description")
        cat_col = self._get_mapped_column("Category")
        payee_col = self._get_mapped_column("Payee")
        recur_col = self._get_mapped_column("Recurrence Pattern")
        
        # Validate required columns
        if not date_col or not amount_col or not type_col:
            self.errors_label.setText("Error: Date, Amount, and Type columns are required.")
            self.import_button.setEnabled(False)
            return
        
        # Parse and validate data
        preview_rows = min(20, len(self.csv_data))
        for row_idx, row_data in enumerate(self.csv_data[:preview_rows]):
            try:
                transaction = self._parse_row(
                    row_data, row_idx,
                    date_col, amount_col, type_col,
                    desc_col, cat_col, payee_col, recur_col
                )
                
                if transaction:
                    self.transactions.append(transaction)
                    
                    # Add to preview table
                    self.preview_table.insertRow(self.preview_table.rowCount())
                    self.preview_table.setItem(self.preview_table.rowCount() - 1, 0,
                                               QTableWidgetItem(str(transaction.date)))
                    self.preview_table.setItem(self.preview_table.rowCount() - 1, 1,
                                               QTableWidgetItem(f"${transaction.amount:.2f}"))
                    self.preview_table.setItem(self.preview_table.rowCount() - 1, 2,
                                               QTableWidgetItem(transaction.type.value))
                    self.preview_table.setItem(self.preview_table.rowCount() - 1, 3,
                                               QTableWidgetItem(transaction.description))
                    self.preview_table.setItem(self.preview_table.rowCount() - 1, 4,
                                               QTableWidgetItem(transaction.category))
                    self.preview_table.setItem(self.preview_table.rowCount() - 1, 5,
                                               QTableWidgetItem(transaction.payee))
                    recur_text = transaction.recurrence_pattern.value if transaction.recurrence_pattern else "One-time"
                    self.preview_table.setItem(self.preview_table.rowCount() - 1, 6,
                                               QTableWidgetItem(recur_text))
            except Exception as e:
                self.validation_errors.append(f"Row {row_idx + 2}: {str(e)}")  # +2 because of header and 0-index
        
        # Parse all remaining rows
        for row_idx, row_data in enumerate(self.csv_data[preview_rows:], start=preview_rows):
            try:
                transaction = self._parse_row(
                    row_data, row_idx,
                    date_col, amount_col, type_col,
                    desc_col, cat_col, payee_col, recur_col
                )
                if transaction:
                    self.transactions.append(transaction)
            except Exception as e:
                self.validation_errors.append(f"Row {row_idx + 2}: {str(e)}")
        
        # Update error display
        if self.validation_errors:
            error_text = f"Validation errors ({len(self.validation_errors)}):\n" + "\n".join(self.validation_errors[:10])
            if len(self.validation_errors) > 10:
                error_text += f"\n... and {len(self.validation_errors) - 10} more errors"
            self.errors_label.setText(error_text)
        else:
            self.errors_label.setText(f"Ready to import {len(self.transactions)} transactions.")
        
        # Enable import button if we have valid transactions
        self.import_button.setEnabled(len(self.transactions) > 0)
    
    def _get_mapped_column(self, target: str) -> Optional[str]:
        """Get CSV column name mapped to target field."""
        for header, mapped in self.column_mapping.items():
            if mapped == target:
                return header
        return None
    
    def _parse_row(
        self,
        row_data: Dict[str, str],
        row_idx: int,
        date_col: str,
        amount_col: str,
        type_col: str,
        desc_col: Optional[str],
        cat_col: Optional[str],
        payee_col: Optional[str],
        recur_col: Optional[str]
    ) -> Optional[Transaction]:
        """Parse a CSV row into a Transaction."""
        # Parse date
        date_str = row_data.get(date_col, "").strip()
        if not date_str:
            raise ValueError("Date is required")
        transaction_date = self._parse_date(date_str)
        
        # Parse amount
        amount_str = row_data.get(amount_col, "").strip()
        if not amount_str:
            raise ValueError("Amount is required")
        amount = self._parse_amount(amount_str)
        
        # Parse type
        type_str = row_data.get(type_col, "").strip().lower()
        if not type_str:
            raise ValueError("Type is required")
        transaction_type = self._parse_type(type_str)
        
        # Parse optional fields
        description = row_data.get(desc_col, "").strip() if desc_col else ""
        category = row_data.get(cat_col, "").strip() if cat_col else ""
        payee = row_data.get(payee_col, "").strip() if payee_col else ""
        
        # Parse recurrence pattern
        recurrence_pattern = None
        if recur_col:
            recur_str = row_data.get(recur_col, "").strip().lower()
            recurrence_pattern = self._parse_recurrence(recur_str)
        
        is_template = recurrence_pattern is not None
        
        # Create transaction
        return Transaction(
            date=transaction_date,
            amount=amount,
            type=transaction_type,
            description=description,
            category=category,
            payee=payee,
            recurrence_pattern=recurrence_pattern,
            is_template=is_template
        )
    
    def _parse_date(self, date_str: str) -> date:
        """Parse date string into date object."""
        # Try common date formats
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%m-%d-%Y",
            "%d-%m-%Y",
        ]
        
        for fmt in formats:
            try:
                from datetime import datetime
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        # Try ISO format
        try:
            return date.fromisoformat(date_str)
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}")
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string into float."""
        # Remove currency symbols and whitespace
        amount_clean = amount_str.replace("$", "").replace(",", "").strip()
        try:
            amount = float(amount_clean)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            return amount
        except ValueError:
            raise ValueError(f"Invalid amount: {amount_str}")
    
    def _parse_type(self, type_str: str) -> TransactionType:
        """Parse type string into TransactionType."""
        type_lower = type_str.lower()
        if type_lower in ['deposit', 'income', 'credit', 'in', '+']:
            return TransactionType.DEPOSIT
        elif type_lower in ['withdrawal', 'expense', 'debit', 'out', '-']:
            return TransactionType.WITHDRAWAL
        else:
            raise ValueError(f"Invalid type: {type_str} (expected deposit/withdrawal)")
    
    def _parse_recurrence(self, recur_str: str) -> Optional[RecurrencePattern]:
        """Parse recurrence string into RecurrencePattern."""
        if not recur_str:
            return None
        
        recur_lower = recur_str.lower()
        if recur_lower in ['weekly', 'week', 'w']:
            return RecurrencePattern.WEEKLY
        elif recur_lower in ['biweekly', 'bi-weekly', 'bi weekly', '2 weeks', '2w']:
            return RecurrencePattern.BIWEEKLY
        elif recur_lower in ['monthly', 'month', 'm']:
            return RecurrencePattern.MONTHLY
        else:
            return None
    
    def _on_import(self):
        """Handle import button click."""
        if not self.transactions:
            QMessageBox.warning(self, "No Transactions", "No valid transactions to import.")
            return
        
        self.accept()
    
    def get_transactions(self) -> List[Transaction]:
        """Get parsed transactions."""
        return self.transactions

