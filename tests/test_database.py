"""Tests for database layer."""

import os
import tempfile
import pytest
import sqlite3

from src.models.database import Database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    db = Database(db_path)
    yield db
    db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestDatabase:
    """Test database initialization and schema."""
    
    def test_database_initialization(self, temp_db):
        """Test database connection initialization."""
        conn = temp_db.connect()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
    
    def test_database_schema_creation(self, temp_db):
        """Test that database schema is created correctly."""
        conn = temp_db.connect()
        cursor = conn.cursor()
        
        # Check that transactions table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='transactions'
        """)
        result = cursor.fetchone()
        assert result is not None
        
        # Check table structure
        cursor.execute("PRAGMA table_info(transactions)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        expected_columns = {
            'id', 'date', 'amount', 'type', 'description', 'category',
            'payee', 'recurring_template_id', 'is_template', 'recurrence_pattern', 'created_at'
        }
        assert set(columns.keys()) == expected_columns
        
        # Verify id is INTEGER PRIMARY KEY
        cursor.execute("PRAGMA table_info(transactions)")
        column_info = cursor.fetchall()
        id_column = next((col for col in column_info if col[1] == 'id'), None)
        assert id_column is not None
        assert id_column[2].upper() == 'INTEGER'
    
    def test_database_indexes(self, temp_db):
        """Test that indexes are created."""
        conn = temp_db.connect()
        cursor = conn.cursor()
        
        # Check indexes exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_transactions%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        expected_indexes = [
            'idx_transactions_date',
            'idx_transactions_template_id',
            'idx_transactions_is_template'
        ]
        for index_name in expected_indexes:
            assert index_name in indexes
    
    def test_database_context_manager(self, temp_db):
        """Test database context manager usage."""
        with temp_db as conn:
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)
        
        # Connection should be closed after context exit
        assert temp_db.connection is None
    
    def test_database_close(self, temp_db):
        """Test database connection closing."""
        conn = temp_db.connect()
        assert conn is not None
        temp_db.close()
        assert temp_db.connection is None

