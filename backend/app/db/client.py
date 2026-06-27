import sqlite3
import os
import json
from contextlib import contextmanager
from app.core.logger import logger

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "database"))
DB_PATH = os.path.join(DB_DIR, "fincon.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")

@contextmanager
def get_db_conn():
    """Context manager for SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Initializes the database using schema.sql and seeds default data."""
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        if not os.path.exists(SCHEMA_PATH):
            logger.error(f"schema.sql not found at {SCHEMA_PATH}")
            return
            
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
            
        with get_db_conn() as conn:
            conn.executescript(schema_sql)
            logger.info("SQLite database tables initialized successfully.")
            
            # Seed default user if not exists
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE id = ?", ("default_user",))
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO users (id, username, email, password_hash) VALUES (?, ?, ?, ?)",
                    ("default_user", "fincon_user", "user@fincon.com", "pbkdf2:sha256:default_hash")
                )
                logger.info("Seeded default user 'default_user' in SQLite.")
                
            # Seed a default portfolio if none exist
            cur.execute("SELECT id FROM portfolios WHERE user_id = ?", ("default_user",))
            if not cur.fetchone():
                p_id = "default_portfolio"
                cur.execute(
                    "INSERT INTO portfolios (id, user_id, name) VALUES (?, ?, ?)",
                    (p_id, "default_user", "Growth Portfolio")
                )
                # Seed default holdings: NVDA - 10 Shares, AAPL - 5 Shares, MSFT - 8 Shares
                cur.execute(
                    "INSERT INTO holdings (id, portfolio_id, ticker, shares, cost_basis) VALUES (?, ?, ?, ?, ?)",
                    ("holding_1", p_id, "NVDA", 10.0, 120.0)
                )
                cur.execute(
                    "INSERT INTO holdings (id, portfolio_id, ticker, shares, cost_basis) VALUES (?, ?, ?, ?, ?)",
                    ("holding_2", p_id, "AAPL", 5.0, 180.0)
                )
                cur.execute(
                    "INSERT INTO holdings (id, portfolio_id, ticker, shares, cost_basis) VALUES (?, ?, ?, ?, ?)",
                    ("holding_3", p_id, "MSFT", 8.0, 420.0)
                )
                logger.info("Seeded default portfolio with tech holdings in SQLite.")
    except Exception as e:
        logger.error(f"Failed to initialize SQLite database: {e}")

class SQLiteClient:
    """Helper client to perform standard database queries."""
    
    @staticmethod
    def execute(query: str, params: tuple = ()) -> list:
        """Executes a SELECT query and returns a list of dictionaries."""
        with get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
            
    @staticmethod
    def execute_write(query: str, params: tuple = ()) -> int:
        """Executes an INSERT, UPDATE, or DELETE query and returns the number of affected rows."""
        with get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            return cur.rowcount

# Initialize DB on import/start
init_db()
