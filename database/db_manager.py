"""Database manager for SQLite operations."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from database.models import EventRecord, ProcessedMessage
from utils.logger import logger


class DatabaseManager:
    """Manages SQLite database operations for the bot."""

    def __init__(self, db_path: str = "data/bot.db"):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Table for processed messages
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_messages (
                    message_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER,
                    message_text TEXT NOT NULL,
                    processed_at TIMESTAMP NOT NULL,
                    event_id TEXT,
                    task_id TEXT,
                    extraction_success BOOLEAN NOT NULL DEFAULT 0,
                    PRIMARY KEY (message_id, chat_id)
                )
            """
            )

            # Table for created events
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source_message_id INTEGER NOT NULL,
                    source_chat_id INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    google_event_id TEXT,
                    google_task_id TEXT
                )
            """
            )

            # Table for statistics
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value INTEGER NOT NULL,
                    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes for better performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_processed_messages_chat ON processed_messages(chat_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_processed_messages_time ON processed_messages(processed_at)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_chat ON events(source_chat_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_time ON events(created_at)"
            )

            conn.commit()
            logger.info("Database initialized successfully")

    def is_message_processed(self, message_id: int, chat_id: int) -> bool:
        """
        Check if a message has already been processed.

        Args:
            message_id: Telegram message ID
            chat_id: Telegram chat ID

        Returns:
            True if message was already processed
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM processed_messages WHERE message_id = ? AND chat_id = ?",
                (message_id, chat_id),
            )
            return cursor.fetchone() is not None

    def record_processed_message(
        self,
        message_id: int,
        chat_id: int,
        user_id: Optional[int],
        message_text: str,
        extraction_success: bool = False,
        event_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> None:
        """
        Record a processed message.

        Args:
            message_id: Telegram message ID
            chat_id: Telegram chat ID
            user_id: Telegram user ID
            message_text: Original message text
            extraction_success: Whether extraction was successful
            event_id: Created calendar event ID
            task_id: Created task ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO processed_messages
                (message_id, chat_id, user_id, message_text, processed_at,
                 event_id, task_id, extraction_success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    message_id,
                    chat_id,
                    user_id,
                    message_text,
                    datetime.utcnow(),
                    event_id,
                    task_id,
                    extraction_success,
                ),
            )
            conn.commit()

    def record_event(
        self,
        event_id: str,
        event_type: str,
        title: str,
        source_message_id: int,
        source_chat_id: int,
        google_event_id: Optional[str] = None,
        google_task_id: Optional[str] = None,
    ) -> None:
        """
        Record a created event.

        Args:
            event_id: Internal event ID
            event_type: Type of event ('calendar' or 'task')
            title: Event title
            source_message_id: Source Telegram message ID
            source_chat_id: Source Telegram chat ID
            google_event_id: Google Calendar event ID
            google_task_id: Google Task ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO events
                (event_id, event_type, title, source_message_id, source_chat_id,
                 created_at, google_event_id, google_task_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    event_id,
                    event_type,
                    title,
                    source_message_id,
                    source_chat_id,
                    datetime.utcnow(),
                    google_event_id,
                    google_task_id,
                ),
            )
            conn.commit()

    def get_recent_messages(
        self, chat_id: Optional[int] = None, limit: int = 10
    ) -> List[ProcessedMessage]:
        """
        Get recently processed messages.

        Args:
            chat_id: Optional chat ID to filter by
            limit: Maximum number of messages to return

        Returns:
            List of ProcessedMessage objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if chat_id:
                cursor.execute(
                    """
                    SELECT * FROM processed_messages
                    WHERE chat_id = ?
                    ORDER BY processed_at DESC
                    LIMIT ?
                """,
                    (chat_id, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM processed_messages
                    ORDER BY processed_at DESC
                    LIMIT ?
                """,
                    (limit,),
                )

            rows = cursor.fetchall()
            return [
                ProcessedMessage(
                    message_id=row["message_id"],
                    chat_id=row["chat_id"],
                    user_id=row["user_id"],
                    message_text=row["message_text"],
                    processed_at=datetime.fromisoformat(row["processed_at"]),
                    event_id=row["event_id"],
                    task_id=row["task_id"],
                    extraction_success=bool(row["extraction_success"]),
                )
                for row in rows
            ]

    def get_statistics(self) -> dict:
        """
        Get usage statistics.

        Returns:
            Dictionary with statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Total processed messages
            cursor.execute("SELECT COUNT(*) as count FROM processed_messages")
            stats["total_messages"] = cursor.fetchone()["count"]

            # Successful extractions
            cursor.execute(
                "SELECT COUNT(*) as count FROM processed_messages WHERE extraction_success = 1"
            )
            stats["successful_extractions"] = cursor.fetchone()["count"]

            # Total events created
            cursor.execute("SELECT COUNT(*) as count FROM events")
            stats["total_events"] = cursor.fetchone()["count"]

            # Events by type
            cursor.execute(
                "SELECT event_type, COUNT(*) as count FROM events GROUP BY event_type"
            )
            stats["events_by_type"] = {
                row["event_type"]: row["count"] for row in cursor.fetchall()
            }

            # Messages by chat
            cursor.execute(
                "SELECT chat_id, COUNT(*) as count FROM processed_messages GROUP BY chat_id"
            )
            stats["messages_by_chat"] = {
                row["chat_id"]: row["count"] for row in cursor.fetchall()
            }

            return stats

