"""SQLite database connection and schema management."""

import sqlite3
import os
from pathlib import Path
from typing import Optional


class Database:
    """Manages SQLite database connection and schema."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to database file. If None, uses 'paymenttracker.db' in user's home directory.
        """
        if db_path is None:
            # Use project root directory
            project_root = Path(__file__).parent.parent.parent
            db_path = str(project_root / "paymenttracker.db")
        
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        
    def connect(self) -> sqlite3.Connection:
        """Establish database connection and initialize schema if needed."""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Return rows as dictionaries
            self._initialize_schema()
        return self.connection
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def _initialize_schema(self):
        """Create database tables if they don't exist."""
        cursor = self.connection.cursor()
        
        # Create transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('deposit', 'withdrawal')),
                description TEXT,
                category TEXT,
                payee TEXT,
                recurring_template_id INTEGER,
                is_template INTEGER NOT NULL DEFAULT 0 CHECK(is_template IN (0, 1)),
                recurrence_pattern TEXT CHECK(recurrence_pattern IN ('weekly', 'biweekly', 'monthly', NULL)),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recurring_template_id) REFERENCES transactions(id),
                CHECK((is_template = 1 AND recurring_template_id IS NULL) OR 
                      (is_template = 0))
            )
        """)
        
        # Create index on date for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)
        """)
        
        # Create index on recurring_template_id for template lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_template_id ON transactions(recurring_template_id)
        """)
        
        # Create index on is_template for template queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_is_template ON transactions(is_template)
        """)
        
        self.connection.commit()
    
    def __enter__(self):
        """Context manager entry."""
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

