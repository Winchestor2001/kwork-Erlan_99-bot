import sqlite3 as sql
from contextlib import contextmanager
from typing import Optional, List, Any


class DB:
    def __init__(self, db: str = "database.db"):
        self.db_path = db
        self.conn: Optional[sql.Connection] = None
        self.cursor: Optional[sql.Cursor] = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = sql.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except sql.Error as e:
            raise Exception(f"Database connection error: {e}")

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.cursor = None
        self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create_tables(self):
        """Create all necessary tables"""
        if not self.conn or not self.cursor:
            self.connect()

        try:
            self.cursor.execute(
                """CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_id BIGINT NOT NULL UNIQUE,
                    username TEXT
                )"""
            )
            self.cursor.execute(
                """CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )"""
            )
            self.cursor.execute(
                """CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_link TEXT NOT NULL UNIQUE
                )"""
            )
            self.cursor.execute(
                """CREATE TABLE IF NOT EXISTS keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_text TEXT NOT NULL UNIQUE
                )"""
            )
            self.conn.commit()
        except sql.Error as e:
            self.conn.rollback()
            raise Exception(f"Error creating tables: {e}")

    # User operations
    def add_user(self, tg_id: int, username: Optional[str] = None) -> int:
        """Add a new user and return their ID"""
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO users (tg_id, username) VALUES (?, ?)",
                (tg_id, username)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sql.Error as e:
            self.conn.rollback()
            raise Exception(f"Error adding user: {e}")

    def get_user(self, tg_id: int) -> Optional[dict]:
        """Get user by Telegram ID"""
        try:
            self.cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
            row = self.cursor.fetchone()
            if row:
                return {"id": row[0], "tg_id": row[1], "username": row[2]}
            return None
        except sql.Error as e:
            raise Exception(f"Error getting user: {e}")

    def get_all_users(self) -> List[dict]:
        """Get all users"""
        try:
            self.cursor.execute("SELECT id, tg_id, username FROM users")
            return [{"id": row[0], "tg_id": row[1], "username": row[2]} for row in self.cursor.fetchall()]
        except sql.Error as e:
            raise Exception(f"Error getting users: {e}")

    # Admin operations
    def add_admin(self, user_id: int | str) -> bool:
        """Add a new admin"""
        try:
            # First check if user exists
            self.cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not self.cursor.fetchone():
                raise Exception(f"User with ID {user_id} does not exist")

            self.cursor.execute(
                "INSERT OR IGNORE INTO admins (user_id) VALUES (?)",
                (user_id,)
            )
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sql.Error as e:
            self.conn.rollback()
            raise Exception(f"Error adding admin: {e}")

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        try:
            self.cursor.execute(
                "SELECT 1 FROM admins WHERE user_id = ?",
                (user_id,)
            )
            return self.cursor.fetchone() is not None
        except sql.Error as e:
            raise Exception(f"Error checking admin status: {e}")

    def get_all_admins(self, make_list=False) -> str | list | None:
        """Get all admins with their user information"""
        try:
            # Debug: Show all admins
            self.cursor.execute("SELECT * FROM admins")
            admins = self.cursor.fetchall()
            if admins:
                if make_list:
                    return [row[1] for row in self.cursor.fetchall()]
                return "\n".join([str(admin[1]) for admin in admins])
        except sql.Error as e:
            print(f"Database error: {str(e)}")
            raise Exception(f"Error getting admins: {e}")

    # Group operations
    def add_group(self, group_link: str) -> int:
        """Add a new group and return its ID"""
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO groups (group_link) VALUES (?)",
                (group_link,)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sql.Error as e:
            self.conn.rollback()
            raise Exception(f"Error adding group: {e}")

    def get_all_groups(self, make_list=False) -> str | list | None:
        """Get all groups with their IDs"""
        try:
            self.cursor.execute("SELECT id, group_link FROM groups")
            if make_list:
                return [row[1] for row in self.cursor.fetchall()]
            return "\n".join([row[1] for row in self.cursor.fetchall()])
        except sql.Error as e:
            raise Exception(f"Error getting groups: {e}")

    # Keyword operations
    def add_keyword(self, key_text: str) -> int:
        """Add a new keyword and return its ID"""
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO keywords (key_text) VALUES (?)",
                (key_text,)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sql.Error as e:
            self.conn.rollback()
            raise Exception(f"Error adding keyword: {e}")

    def get_all_keywords(self, make_list=False) -> str | list | None:
        """Get all keywords with their IDs"""
        try:
            self.cursor.execute("SELECT id, key_text FROM keywords")
            if make_list:
                return [row[1] for row in self.cursor.fetchall()]
            return "\n".join([row[1] for row in self.cursor.fetchall()])
        except sql.Error as e:
            raise Exception(f"Error getting keywords: {e}")

    def delete_keyword(self, key_text: str) -> bool:
        """Delete a keyword"""
        try:
            self.cursor.execute(
                "DELETE FROM keywords WHERE key_text = ?",
                (key_text,)
            )
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sql.Error as e:
            self.conn.rollback()
            raise Exception(f"Error deleting keyword: {e}")
