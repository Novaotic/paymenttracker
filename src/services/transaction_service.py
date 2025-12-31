"""Transaction service for business logic and database operations."""

from datetime import date, datetime
from typing import List, Optional, Tuple
from collections import namedtuple

from src.models.database import Database
from src.models.transaction import Transaction, TransactionType


WeeklyBalance = namedtuple(
    "WeeklyBalance",
    ["week_start", "week_end", "starting_balance", "ending_balance", "net_change"]
)


class TransactionService:
    """Service for managing transactions and calculating balances."""
    
    def __init__(self, database: Database):
        """
        Initialize transaction service.
        
        Args:
            database: Database instance
        """
        self.db = database
    
    def create_transaction(self, transaction: Transaction) -> Transaction:
        """
        Create a new transaction in the database.
        
        Args:
            transaction: Transaction to create
            
        Returns:
            Created transaction with ID set
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO transactions (
                date, amount, type, description, category, payee,
                recurring_template_id, is_template, recurrence_pattern, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction.date.isoformat(),
            transaction.amount,
            transaction.type.value,
            transaction.description,
            transaction.category,
            transaction.payee,
            transaction.recurring_template_id,
            1 if transaction.is_template else 0,
            transaction.recurrence_pattern.value if transaction.recurrence_pattern else None,
            transaction.created_at.isoformat(),
        ))
        
        transaction.id = cursor.lastrowid
        conn.commit()
        return transaction
    
    def create_transactions_batch(self, transactions: List[Transaction]) -> List[Transaction]:
        """
        Create multiple transactions in a batch.
        
        Args:
            transactions: List of transactions to create
            
        Returns:
            List of successfully created transactions (with IDs set)
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        
        created_transactions = []
        
        for transaction in transactions:
            try:
                cursor.execute("""
                    INSERT INTO transactions (
                        date, amount, type, description, category, payee,
                        recurring_template_id, is_template, recurrence_pattern, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction.date.isoformat(),
                    transaction.amount,
                    transaction.type.value,
                    transaction.description,
                    transaction.category,
                    transaction.payee,
                    transaction.recurring_template_id,
                    1 if transaction.is_template else 0,
                    transaction.recurrence_pattern.value if transaction.recurrence_pattern else None,
                    transaction.created_at.isoformat(),
                ))
                
                transaction.id = cursor.lastrowid
                created_transactions.append(transaction)
            except Exception as e:
                # Skip invalid transactions, continue with the rest
                # Transaction validation happens in __init__, so this is for DB errors
                print(f"Error creating transaction: {e}")
                continue
        
        conn.commit()
        return created_transactions
    
    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction if found, None otherwise
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
        row = cursor.fetchone()
        
        if row:
            return Transaction.from_row(row)
        return None
    
    def update_transaction(self, transaction: Transaction) -> Transaction:
        """
        Update an existing transaction.
        
        Args:
            transaction: Transaction with updated data (must have ID set)
            
        Returns:
            Updated transaction
        """
        if transaction.id is None:
            raise ValueError("Cannot update transaction without ID")
        
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE transactions SET
                date = ?, amount = ?, type = ?, description = ?,
                category = ?, payee = ?, recurring_template_id = ?,
                is_template = ?, recurrence_pattern = ?
            WHERE id = ?
        """, (
            transaction.date.isoformat(),
            transaction.amount,
            transaction.type.value,
            transaction.description,
            transaction.category,
            transaction.payee,
            transaction.recurring_template_id,
            1 if transaction.is_template else 0,
            transaction.recurrence_pattern.value if transaction.recurrence_pattern else None,
            transaction.id,
        ))
        
        conn.commit()
        return transaction
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """
        Delete a transaction.
        
        Args:
            transaction_id: Transaction ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        
        return deleted
    
    def get_transactions_by_date_range(
        self,
        start_date: date,
        end_date: date,
        transaction_type: Optional[TransactionType] = None,
        include_templates: bool = False
    ) -> List[Transaction]:
        """
        Get transactions within a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            transaction_type: Filter by type (None for all types)
            include_templates: Whether to include template transactions
            
        Returns:
            List of transactions sorted by date
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM transactions
            WHERE date >= ? AND date <= ?
        """
        params = [start_date.isoformat(), end_date.isoformat()]
        
        if not include_templates:
            query += " AND is_template = 0"
        
        if transaction_type:
            query += " AND type = ?"
            params.append(transaction_type.value)
        
        query += " ORDER BY date ASC, id ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [Transaction.from_row(row) for row in rows]
    
    def get_transactions_for_month(
        self,
        year: int,
        month: int,
        transaction_type: Optional[TransactionType] = None
    ) -> List[Transaction]:
        """
        Get all transactions for a specific month.
        
        Args:
            year: Year
            month: Month (1-12)
            transaction_type: Filter by type (None for all types)
            
        Returns:
            List of transactions for the month
        """
        # Calculate start and end dates for the month
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        
        start_date = date(year, month, 1)
        end_date = date(year, month, (next_month - date(year, month, 1)).days)
        
        return self.get_transactions_by_date_range(
            start_date, end_date, transaction_type, include_templates=False
        )
    
    def get_template_transactions(self) -> List[Transaction]:
        """
        Get all recurring transaction templates.
        
        Returns:
            List of template transactions
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM transactions
            WHERE is_template = 1
            ORDER BY date ASC
        """)
        
        rows = cursor.fetchall()
        return [Transaction.from_row(row) for row in rows]
    
    def get_transaction_instances(self, template_id: int) -> List[Transaction]:
        """
        Get all instances of a recurring transaction template.
        
        Args:
            template_id: Template transaction ID
            
        Returns:
            List of transaction instances
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM transactions
            WHERE recurring_template_id = ?
            ORDER BY date ASC
        """, (template_id,))
        
        rows = cursor.fetchall()
        return [Transaction.from_row(row) for row in rows]
    
    def calculate_balance_up_to_date(self, target_date: date) -> float:
        """
        Calculate balance up to and including a specific date.
        This includes ALL transactions from the beginning of time up to target_date.
        
        Args:
            target_date: Date to calculate balance up to (inclusive)
            
        Returns:
            Balance (deposits - withdrawals)
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        
        # Get all transactions up to target_date (only instances, not templates)
        cursor.execute("""
            SELECT type, amount FROM transactions
            WHERE date <= ? AND is_template = 0
            ORDER BY date ASC, id ASC
        """, (target_date.isoformat(),))
        
        rows = cursor.fetchall()
        
        balance = 0.0
        for row in rows:
            amount = row["amount"]
            if row["type"] == TransactionType.DEPOSIT.value:
                balance += amount
            else:  # withdrawal
                balance -= amount
        
        return balance
    
    def calculate_weekly_balances(
        self,
        year: int,
        month: int
    ) -> List[WeeklyBalance]:
        """
        Calculate weekly balances for a given month.
        Weeks are Monday-Sunday. The first week starts on the first day of the month
        (even if it's not Monday) and ends on the first Sunday, or end of month if earlier.
        Subsequent weeks are Monday-Sunday.
        
        Balance carries over from the previous month: the starting balance of the first week
        is the balance up to the last day of the previous month.
        
        Args:
            year: Year
            month: Month (1-12)
            
        Returns:
            List of WeeklyBalance objects
        """
        # Calculate month start and end dates
        if month == 12:
            next_month_start = date(year + 1, 1, 1)
        else:
            next_month_start = date(year, month + 1, 1)
        
        month_start = date(year, month, 1)
        # Calculate last day of month
        month_end = date(year, month, (next_month_start - month_start).days)
        
        # Calculate starting balance (balance at end of previous month)
        prev_month_end = month_start - date.resolution  # One day before month start
        starting_balance = self.calculate_balance_up_to_date(prev_month_end)
        
        weekly_balances = []
        current_balance = starting_balance
        current_date = month_start
        
        while current_date <= month_end:
            # Determine week start
            if current_date == month_start:
                # First week starts on first day of month
                week_start = month_start
            else:
                # Subsequent weeks start on Monday
                # current_date should already be a Monday, but ensure it is
                days_since_monday = current_date.weekday()  # 0 = Monday
                week_start = current_date
            
            # Determine week end (Sunday or end of month)
            days_until_sunday = (6 - week_start.weekday()) % 7
            if days_until_sunday == 0:
                # Week starts on Sunday, so week_end is the same day
                week_end = week_start
            else:
                week_end = week_start + date.resolution * days_until_sunday
            
            # Don't go past month end
            week_end = min(week_end, month_end)
            
            # Get transactions for this week
            week_transactions = self.get_transactions_by_date_range(
                week_start, week_end, include_templates=False
            )
            
            # Calculate net change for this week
            net_change = sum(t.get_signed_amount() for t in week_transactions)
            week_starting_balance = current_balance
            current_balance += net_change
            week_ending_balance = current_balance
            
            weekly_balances.append(WeeklyBalance(
                week_start=week_start,
                week_end=week_end,
                starting_balance=week_starting_balance,
                ending_balance=week_ending_balance,
                net_change=net_change
            ))
            
            # Move to next week (start of next Monday)
            if week_end < month_end:
                current_date = week_end + date.resolution  # Next day after week_end
            else:
                break
        
        return weekly_balances
    
    @staticmethod
    def filter_transactions(
        transactions: List[Transaction],
        text_search: str = "",
        transaction_type: Optional[TransactionType] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Transaction]:
        """
        Filter a list of transactions by various criteria.
        
        Args:
            transactions: List of transactions to filter
            text_search: Search text (searches in description, category, payee - case-insensitive)
            transaction_type: Filter by transaction type (None for all types)
            min_amount: Minimum amount (None for no minimum)
            max_amount: Maximum amount (None for no maximum)
            start_date: Start date for filtering (None for no start limit)
            end_date: End date for filtering (None for no end limit)
            
        Returns:
            Filtered list of transactions
        """
        filtered = transactions
        
        # Text search (description, category, payee)
        if text_search:
            text_lower = text_search.lower()
            filtered = [
                t for t in filtered
                if text_lower in t.description.lower()
                or text_lower in t.category.lower()
                or text_lower in t.payee.lower()
            ]
        
        # Transaction type filter
        if transaction_type is not None:
            filtered = [t for t in filtered if t.type == transaction_type]
        
        # Amount range filter
        if min_amount is not None:
            filtered = [t for t in filtered if t.amount >= min_amount]
        if max_amount is not None:
            filtered = [t for t in filtered if t.amount <= max_amount]
        
        # Date range filter (only apply if dates are provided)
        # Note: We always get dates from the widget, so we need to handle the case
        # where dates are set to default values but user hasn't actively filtered
        # For now, apply the filters if dates are provided
        if start_date is not None:
            filtered = [t for t in filtered if t.date >= start_date]
        if end_date is not None:
            filtered = [t for t in filtered if t.date <= end_date]
        
        return filtered

