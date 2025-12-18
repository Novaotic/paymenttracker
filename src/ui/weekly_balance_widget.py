"""Widget for displaying weekly balances."""

from typing import List
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from src.services.transaction_service import WeeklyBalance


class WeeklyBalanceWidget(QWidget):
    """Widget displaying weekly balances for a month."""
    
    def __init__(self, parent=None):
        """Initialize weekly balance widget."""
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Weekly Balances")
        title.setStyleSheet("font-weight: bold; font-size: 14pt;")
        layout.addWidget(title)
        
        # Table for weekly balances
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Week", "Starting Balance", "Ending Balance", "Net Change"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        layout.addWidget(self.table)
    
    def update_balances(self, weekly_balances: List[WeeklyBalance]):
        """
        Update the display with weekly balances.
        
        Args:
            weekly_balances: List of WeeklyBalance objects
        """
        self.table.setRowCount(len(weekly_balances))
        
        for row, weekly_balance in enumerate(weekly_balances):
            # Week range
            week_str = f"{weekly_balance.week_start.strftime('%b %d')} - {weekly_balance.week_end.strftime('%b %d')}"
            week_item = QTableWidgetItem(week_str)
            self.table.setItem(row, 0, week_item)
            
            # Starting balance
            start_balance = weekly_balance.starting_balance
            start_item = QTableWidgetItem(f"${start_balance:,.2f}")
            start_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if start_balance < 0:
                start_item.setForeground(QColor(200, 0, 0))
            elif start_balance > 0:
                start_item.setForeground(QColor(0, 150, 0))
            self.table.setItem(row, 1, start_item)
            
            # Ending balance
            end_balance = weekly_balance.ending_balance
            end_item = QTableWidgetItem(f"${end_balance:,.2f}")
            end_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if end_balance < 0:
                end_item.setForeground(QColor(200, 0, 0))
            elif end_balance > 0:
                end_item.setForeground(QColor(0, 150, 0))
            self.table.setItem(row, 2, end_item)
            
            # Net change
            net_change = weekly_balance.net_change
            net_item = QTableWidgetItem(f"${net_change:+,.2f}")
            net_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if net_change < 0:
                net_item.setForeground(QColor(200, 0, 0))
            elif net_change > 0:
                net_item.setForeground(QColor(0, 150, 0))
            self.table.setItem(row, 3, net_item)
        
        # Resize columns to fit content
        self.table.resizeColumnsToContents()

