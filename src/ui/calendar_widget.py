"""Custom calendar widget with transaction indicators and color coding."""

from datetime import date, datetime
from typing import Dict, List, Optional
from PyQt6.QtWidgets import QCalendarWidget, QWidget, QLabel
from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPalette, QFont

from src.models.transaction import Transaction, TransactionType


class CalendarWidget(QCalendarWidget):
    """Calendar widget with transaction color coding."""
    
    date_clicked = pyqtSignal(date)  # Signal emitted when a date is clicked
    
    def __init__(self, parent=None):
        """Initialize calendar widget."""
        super().__init__(parent)
        self.transactions_by_date: Dict[date, List[Transaction]] = {}
        self.setGridVisible(True)
        
        # Connect selection changed signal
        self.selectionChanged.connect(self._on_selection_changed)
        # Connect clicked signal to handle clicks even when date is already selected
        self.clicked.connect(self._on_date_clicked)
    
    def set_transactions(self, transactions: List[Transaction]):
        """
        Set transactions to display on calendar.
        
        Args:
            transactions: List of transactions to display
        """
        self.transactions_by_date = {}
        for transaction in transactions:
            transaction_date = transaction.date
            if transaction_date not in self.transactions_by_date:
                self.transactions_by_date[transaction_date] = []
            self.transactions_by_date[transaction_date].append(transaction)
        
        # Force repaint
        self.updateCells()
    
    def _on_selection_changed(self):
        """Handle calendar date selection."""
        selected_date = self.selectedDate()
        transaction_date = date(
            selected_date.year(),
            selected_date.month(),
            selected_date.day()
        )
        self.date_clicked.emit(transaction_date)
    
    def _on_date_clicked(self, clicked_date: QDate):
        """Handle date click - always fires even if already selected."""
        transaction_date = date(
            clicked_date.year(),
            clicked_date.month(),
            clicked_date.day()
        )
        self.date_clicked.emit(transaction_date)
    
    def paintCell(self, painter: QPainter, rect, date: QDate):
        """
        Paint a calendar cell with +/- indicators for deposits and withdrawals.
        
        Args:
            painter: QPainter instance
            rect: Cell rectangle
            date: Date for the cell
        """
        # First, call parent paint to draw the date (no background fill)
        super().paintCell(painter, rect, date)
        
        # Convert QDate to Python date
        cell_date = date.toPyDate()
        
        # Check if there are transactions for this date
        if cell_date in self.transactions_by_date:
            transactions = self.transactions_by_date[cell_date]
            
            # Count deposits and withdrawals separately
            deposit_count = sum(1 for t in transactions if t.type == TransactionType.DEPOSIT)
            withdrawal_count = sum(1 for t in transactions if t.type == TransactionType.WITHDRAWAL)
            
            # Set up font for indicators (slightly bold and larger)
            font = painter.font()
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            painter.setFont(font)
            
            # Draw "+" indicator for deposits in top-right
            if deposit_count > 0:
                painter.setPen(QColor(0, 150, 0))  # Green
                plus_rect = rect.adjusted(rect.width() - 15, 2, -2, rect.height() // 2)
                painter.drawText(plus_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, "+")
            
            # Draw "-" indicator for withdrawals in bottom-right
            if withdrawal_count > 0:
                painter.setPen(QColor(200, 0, 0))  # Red
                minus_rect = rect.adjusted(rect.width() - 15, rect.height() // 2, -2, rect.height() - 2)
                painter.drawText(minus_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom, "-")

