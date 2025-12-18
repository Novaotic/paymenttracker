"""Custom calendar widget with transaction indicators and color coding."""

from datetime import date, datetime
from typing import Dict, List, Optional
from PyQt6.QtWidgets import QCalendarWidget, QWidget, QLabel
from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPalette

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
    
    def paintCell(self, painter: QPainter, rect, date: QDate):
        """
        Paint a calendar cell with color coding for transactions.
        
        Args:
            painter: QPainter instance
            rect: Cell rectangle
            date: Date for the cell
        """
        # First, call parent paint to draw the date
        super().paintCell(painter, rect, date)
        
        # Convert QDate to Python date
        cell_date = date.toPyDate()
        
        # Check if there are transactions for this date
        if cell_date in self.transactions_by_date:
            transactions = self.transactions_by_date[cell_date]
            
            # Calculate net amount for the day
            net_amount = 0.0
            for transaction in transactions:
                net_amount += transaction.get_signed_amount()
            
            # Color code based on net amount
            if net_amount > 0:
                # Green for positive (more deposits than withdrawals)
                color = QColor(200, 255, 200, 150)  # Light green with transparency
            elif net_amount < 0:
                # Red for negative (more withdrawals than deposits)
                color = QColor(255, 200, 200, 150)  # Light red with transparency
            else:
                # Neutral for zero
                color = QColor(240, 240, 240, 100)  # Light gray with transparency
            
            # Draw background color
            painter.fillRect(rect, color)
            
            # Redraw the date text on top
            painter.setPen(self.palette().color(QPalette.ColorRole.Text))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(date.day()))
            
            # Draw indicator dot if there are transactions
            if transactions:
                dot_rect = rect.adjusted(rect.width() - 8, 2, -2, rect.height() - 6)
                painter.setBrush(QColor(0, 0, 0, 180))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(dot_rect)

