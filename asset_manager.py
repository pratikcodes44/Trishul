import sqlite3
from datetime import datetime, timezone
import logging
from typing import List

logger = logging.getLogger(__name__)

class AssetManager:
    """
    AssetManager handles state management for the bug bounty reconnaissance pipeline.
    It uses a local SQLite database to store discovered assets and diff them against
    previous scans to identify newly spawned subdomains.
    """
    def __init__(self, db_path: str = "recon_state.db"):
        """
        Initialize the AssetManager with a SQLite database.
        
        Args:
            db_path (str): The path to the SQLite database file. Defaults to 'recon_state.db'.
        """
        self.db_path = db_path
        self._conn = None
        if db_path == ":memory:":
            self._conn = sqlite3.connect(":memory:")
        self._initialize_db()

    def _get_connection(self):
        """Returns the appropriate database connection."""
        if self._conn:
            return self._conn
        return sqlite3.connect(self.db_path)

    def _initialize_db(self):
        """
        Initializes the database by creating the required 'subdomains' table
        if it does not already exist.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subdomains (
                    domain TEXT PRIMARY KEY,
                    first_seen TIMESTAMP,
                    last_seen TIMESTAMP
                )
            ''')
            conn.commit()
            if not self._conn:
                conn.close()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def insert_and_diff(self, new_subdomains_list: List[str]) -> List[str]:
        """
        Compares a list of subdomains against the database, inserts new records,
        updates existing records, and returns only the newly discovered subdomains.
        
        Args:
            new_subdomains_list (List[str]): The freshly generated list of in-scope subdomains.
            
        Returns:
            List[str]: A list of new subdomains that haven't been seen in previous scans.
        """
        new_discoveries = []
        current_time = datetime.now(timezone.utc)

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for domain in new_subdomains_list:
                # Check if the domain exists in the database
                cursor.execute("SELECT domain FROM subdomains WHERE domain = ?", (domain,))
                result = cursor.fetchone()

                if result is None:
                    # Domain does NOT exist: insert it with current timestamp
                    cursor.execute(
                        "INSERT INTO subdomains (domain, first_seen, last_seen) VALUES (?, ?, ?)",
                        (domain, current_time, current_time)
                    )
                    new_discoveries.append(domain)
                else:
                    # Domain ALREADY exists: update its last_seen timestamp
                    cursor.execute(
                        "UPDATE subdomains SET last_seen = ? WHERE domain = ?",
                        (current_time, domain)
                    )
            conn.commit()
            if not self._conn:
                conn.close()
        except sqlite3.Error as e:
            logger.error(f"Database error during diffing: {e}")
            raise

        return new_discoveries
