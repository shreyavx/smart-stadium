
import sqlite3
from pathlib import Path

# Store the database in the main project folder
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_ROOT / "friend_finder.db"


def get_connection():
    """Create and return a database connection."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create Friend Finder tables if they do not exist."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Private groups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS friend_groups (
                group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT NOT NULL,
                invite_code TEXT UNIQUE NOT NULL,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Users who belong to each group
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                sharing_enabled INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (group_id)
                    REFERENCES friend_groups(group_id),

                UNIQUE(group_id, user_id)
            )
        """)

        # Latest simulated location of each member
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS friend_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                zone_id TEXT NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(group_id, user_id),

                FOREIGN KEY (group_id)
                    REFERENCES friend_groups(group_id)
            )
        """)

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
    print("Friend Finder database initialized successfully!")
