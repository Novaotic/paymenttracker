"""Transaction data model."""

from datetime import date, datetime
from typing import Optional, Dict, Any
from enum import Enum


class TransactionType(str, Enum):
    """Transaction type enumeration."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class RecurrencePattern(str, Enum):
    """Recurrence pattern enumeration."""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class Transaction:
    """Represents a transaction (either a template or an instance)."""
    
    def __init__(
        self,
        date: date,
        amount: float,
        type: TransactionType,
        description: str = "",
        category: str = "",
        payee: str = "",
        recurring_template_id: Optional[int] = None,
        is_template: bool = False,
        recurrence_pattern: Optional[RecurrencePattern] = None,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None
    ):
        """
        Initialize a Transaction.
        
        Args:
            date: Transaction date
            amount: Transaction amount (must be positive)
            type: Transaction type (deposit or withdrawal)
            description: Transaction description
            category: Transaction category
            payee: Payee/payer name
            recurring_template_id: ID of the template if this is an instance
            is_template: True if this is a recurring transaction template
            recurrence_pattern: Recurrence pattern if this is a template
            id: Database ID (None for new transactions)
            created_at: Creation timestamp (None for new transactions)
        """
        self.id = id
        self.date = date
        self.amount = abs(amount)  # Ensure amount is always positive
        self.type = TransactionType(type) if isinstance(type, str) else type
        self.description = description or ""
        self.category = category or ""
        self.payee = payee or ""
        self.recurring_template_id = recurring_template_id
        self.is_template = is_template
        self.recurrence_pattern = (
            RecurrencePattern(recurrence_pattern) 
            if recurrence_pattern and isinstance(recurrence_pattern, str)
            else recurrence_pattern
        )
        self.created_at = created_at or datetime.now()
        
        self._validate()
    
    def _validate(self):
        """Validate transaction data."""
        if self.amount <= 0:
            raise ValueError("Transaction amount must be positive")
        
        if self.is_template:
            if self.recurring_template_id is not None:
                raise ValueError("Template transactions cannot have a recurring_template_id")
            if self.recurrence_pattern is None:
                raise ValueError("Template transactions must have a recurrence_pattern")
        else:
            if self.recurring_template_id is not None and self.recurrence_pattern is not None:
                raise ValueError("Instance transactions cannot have a recurrence_pattern")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary for database storage."""
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "amount": self.amount,
            "type": self.type.value,
            "description": self.description,
            "category": self.category,
            "payee": self.payee,
            "recurring_template_id": self.recurring_template_id,
            "is_template": 1 if self.is_template else 0,
            "recurrence_pattern": self.recurrence_pattern.value if self.recurrence_pattern else None,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        """Create Transaction from dictionary (e.g., from database row)."""
        # Handle date conversion
        if isinstance(data.get("date"), str):
            date_obj = date.fromisoformat(data["date"])
        else:
            date_obj = data.get("date")
        
        # Handle created_at conversion
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = datetime.now()
        elif created_at is None:
            created_at = datetime.now()
        
        return cls(
            id=data.get("id"),
            date=date_obj,
            amount=data["amount"],
            type=data["type"],
            description=data.get("description", ""),
            category=data.get("category", ""),
            payee=data.get("payee", ""),
            recurring_template_id=data.get("recurring_template_id"),
            is_template=bool(data.get("is_template", 0)),
            recurrence_pattern=data.get("recurrence_pattern"),
            created_at=created_at,
        )
    
    @classmethod
    def from_row(cls, row) -> "Transaction":
        """Create Transaction from database row (sqlite3.Row)."""
        data = dict(row)
        return cls.from_dict(data)
    
    def get_signed_amount(self) -> float:
        """Get amount with sign: positive for deposits, negative for withdrawals."""
        return self.amount if self.type == TransactionType.DEPOSIT else -self.amount
    
    def __repr__(self) -> str:
        """String representation of transaction."""
        template_info = ""
        if self.is_template:
            template_info = f", template (pattern: {self.recurrence_pattern.value})"
        elif self.recurring_template_id:
            template_info = f", instance of template {self.recurring_template_id}"
        
        return (
            f"Transaction(id={self.id}, date={self.date}, "
            f"amount={self.amount}, type={self.type.value}, "
            f"description='{self.description}'{template_info})"
        )
    
    def __eq__(self, other) -> bool:
        """Compare transactions for equality."""
        if not isinstance(other, Transaction):
            return False
        return self.id == other.id and self.id is not None

