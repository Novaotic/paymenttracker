"""Widget for filtering transactions."""

from datetime import date
from typing import Optional, Tuple
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QComboBox, QDoubleSpinBox,
    QDateEdit, QPushButton, QLabel
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from src.models.transaction import TransactionType


class TransactionFilterWidget(QWidget):
    """Widget for filtering transactions by various criteria."""
    
    filter_changed = pyqtSignal()  # Emitted when filters change (for real-time filtering)
    
    def __init__(self, parent=None):
        """Initialize filter widget."""
        super().__init__(parent)
        self._date_filter_active = False  # Track if user has actively set date filter
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the filter UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Text search
        layout.addWidget(QLabel("Search:"))
        self.text_search = QLineEdit()
        self.text_search.setPlaceholderText("Description, category, payee...")
        self.text_search.setMaximumWidth(200)
        layout.addWidget(self.text_search)
        
        # Transaction type
        layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("All", None)
        self.type_combo.addItem("Deposit", TransactionType.DEPOSIT)
        self.type_combo.addItem("Withdrawal", TransactionType.WITHDRAWAL)
        layout.addWidget(self.type_combo)
        
        # Amount range
        layout.addWidget(QLabel("Amount:"))
        self.min_amount = QDoubleSpinBox()
        self.min_amount.setMinimum(0.0)
        self.min_amount.setMaximum(999999.99)
        self.min_amount.setDecimals(2)
        self.min_amount.setPrefix("$ ")
        self.min_amount.setSpecialValueText("Min")
        self.min_amount.setValue(0.0)
        layout.addWidget(self.min_amount)
        
        layout.addWidget(QLabel("to"))
        self.max_amount = QDoubleSpinBox()
        self.max_amount.setMinimum(0.0)
        self.max_amount.setMaximum(999999.99)
        self.max_amount.setDecimals(2)
        self.max_amount.setPrefix("$ ")
        self.max_amount.setSpecialValueText("Max")
        self.max_amount.setValue(0.0)
        layout.addWidget(self.max_amount)
        
        # Date range (initially not active)
        layout.addWidget(QLabel("Date:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setMinimumDate(QDate(1900, 1, 1))
        layout.addWidget(self.start_date)
        
        layout.addWidget(QLabel("to"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setMinimumDate(QDate(1900, 1, 1))
        layout.addWidget(self.end_date)
        
        # Buttons
        self.apply_button = QPushButton("Apply")
        layout.addWidget(self.apply_button)
        
        self.clear_button = QPushButton("Clear")
        layout.addWidget(self.clear_button)
        
        layout.addStretch()
    
    def _connect_signals(self):
        """Connect signals for real-time filtering."""
        # Text search and type filter are real-time
        self.text_search.textChanged.connect(self._on_realtime_filter_changed)
        self.type_combo.currentIndexChanged.connect(self._on_realtime_filter_changed)
        
        # Amount and date ranges use Apply button
        self.apply_button.clicked.connect(self._on_apply_clicked)
        self.clear_button.clicked.connect(self._on_clear_clicked)
    
    def _on_realtime_filter_changed(self):
        """Handle real-time filter changes (text search, type)."""
        self.filter_changed.emit()
    
    def _on_apply_clicked(self):
        """Handle Apply button click - activate date/amount filters."""
        self._date_filter_active = True
        self.filter_changed.emit()
    
    def _on_clear_clicked(self):
        """Handle Clear button click - reset all filters."""
        self.text_search.clear()
        self.type_combo.setCurrentIndex(0)  # "All"
        self.min_amount.setValue(0.0)
        self.max_amount.setValue(0.0)
        # Reset date filter to inactive
        self._date_filter_active = False
        from datetime import date as date_type
        today = date_type.today()
        self.start_date.setDate(QDate(today.year, today.month, today.day))
        self.end_date.setDate(QDate(today.year, today.month, today.day))
        self.filter_changed.emit()
    
    def get_text_search(self) -> str:
        """Get text search string."""
        return self.text_search.text().strip()
    
    def get_transaction_type(self) -> Optional[TransactionType]:
        """Get selected transaction type (None for 'All')."""
        return self.type_combo.currentData()
    
    def get_amount_range(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Get amount range.
        
        Returns:
            Tuple of (min_amount, max_amount). Either can be None if not set.
        """
        min_val = self.min_amount.value()
        max_val = self.max_amount.value()
        
        min_amount = min_val if min_val > 0.0 else None
        max_amount = max_val if max_val > 0.0 else None
        
        return (min_amount, max_amount)
    
    def get_date_range(self) -> Tuple[Optional[date], Optional[date]]:
        """
        Get date range.
        
        Returns:
            Tuple of (start_date, end_date). Returns (None, None) if date filter is not active.
            Returns date objects if user has clicked Apply to activate date filtering.
        """
        if not self._date_filter_active:
            return (None, None)
        
        start_qdate = self.start_date.date()
        end_qdate = self.end_date.date()
        
        start_date_obj = date(start_qdate.year(), start_qdate.month(), start_qdate.day())
        end_date_obj = date(end_qdate.year(), end_qdate.month(), end_qdate.day())
        
        return (start_date_obj, end_date_obj)

