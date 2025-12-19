"""Custom calendar widget with transaction indicators."""

from datetime import date
from typing import Dict, List
from PyQt6.QtWidgets import QCalendarWidget
from PyQt6.QtCore import QDate, QPoint, Qt, pyqtSignal, QRect
from PyQt6.QtGui import QColor, QPainter

from src.models.transaction import Transaction, TransactionType


class CalendarWidget(QCalendarWidget):
    """Calendar widget with dot indicators for deposits and withdrawals."""
    
    date_clicked = pyqtSignal(date)  # Signal emitted when a date is clicked
    
    def __init__(self, parent=None):
        """Initialize calendar widget."""
        super().__init__(parent)
        self.transactions_by_date: Dict[date, List[Transaction]] = {}
        self.setGridVisible(True)
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
        Paint a calendar cell and draw transaction indicators.
        
        Args:
            painter: QPainter instance
            rect: Cell rectangle
            date: Date for the cell
        """
        super().paintCell(painter, rect, date)
        self.drawIndicators(painter, rect, date)

    def drawIndicators(self, painter: QPainter, rect: QRect, date: QDate):
        """
        Draw dot indicators for deposits and withdrawals.
        
        Args:
            painter: QPainter instance
            rect: Cell rectangle
            date: Date for the cell
        """
        cell_date = date.toPyDate()
        if cell_date not in self.transactions_by_date:
            return
        
        transactions = self.transactions_by_date[cell_date]
        has_deposit = any(t.type == TransactionType.DEPOSIT for t in transactions)
        has_withdrawal = any(t.type == TransactionType.WITHDRAWAL for t in transactions)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        radius = 3  # dot size
        margin = 3  # distance from edges

        # Anchors
        right_x = rect.right() - radius - margin
        top_y = rect.top() + radius + margin
        bottom_y = rect.bottom() - radius - margin

        # Top-right: deposit
        if has_deposit:
            painter.setBrush(QColor(0, 150, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPoint(right_x, top_y), radius, radius)

        # Bottom-right: withdrawal
        if has_withdrawal:
            painter.setBrush(QColor(200, 0, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPoint(right_x, bottom_y), radius, radius)

        painter.restore()
