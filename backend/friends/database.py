
import sqlite3
from pathlib import Path

# Store the database in the main project folder
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_ROOT / "friend_finder.db"


def get_connection():
    """Create and return a database connection."""
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Create application tables without replacing existing data."""

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_users (
                user_id TEXT PRIMARY KEY,
                phone_number TEXT UNIQUE,
                role TEXT NOT NULL
                    CHECK (role IN ('USER', 'CONTROLLER', 'ADMIN')),
                password_hash TEXT,
                phone_verified_at INTEGER,
                must_change_password INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at INTEGER NOT NULL,
                CHECK (
                    (role = 'USER'
                        AND phone_number IS NOT NULL
                        AND password_hash IS NULL)
                    OR
                    (role IN ('CONTROLLER', 'ADMIN')
                        AND phone_number IS NULL
                        AND password_hash IS NOT NULL)
                )
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_otp_challenges (
                challenge_id TEXT PRIMARY KEY,
                phone_number TEXT NOT NULL,
                purpose TEXT NOT NULL CHECK (purpose IN ('signup', 'login')),
                code_hash TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                consumed_at INTEGER
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_auth_otp_phone_purpose_created
            ON auth_otp_challenges (phone_number, purpose, created_at)
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                revoked_at INTEGER,
                FOREIGN KEY (user_id) REFERENCES auth_users(user_id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_expiry
            ON auth_sessions (user_id, expires_at)
        """)

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
    print("Friend Finder database initialized successfully!")
