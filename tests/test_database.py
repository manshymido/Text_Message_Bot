"""Tests for database operations."""

import pytest
from datetime import datetime

from database.db_manager import DatabaseManager


class TestDatabaseManager:
    """Test cases for DatabaseManager."""

    def test_database_initialization(self, temp_db):
        """Test database initialization."""
        assert temp_db is not None
        # Database should be created
        assert temp_db.db_path.exists()

    def test_message_processing_tracking(self, temp_db):
        """Test tracking of processed messages."""
        message_id = 123
        chat_id = 456
        user_id = 789
        message_text = "Test message"

        # Message should not be processed initially
        assert temp_db.is_message_processed(message_id, chat_id) is False

        # Record message
        temp_db.record_processed_message(
            message_id=message_id,
            chat_id=chat_id,
            user_id=user_id,
            message_text=message_text,
            extraction_success=True,
        )

        # Message should now be marked as processed
        assert temp_db.is_message_processed(message_id, chat_id) is True

    def test_duplicate_message_prevention(self, temp_db):
        """Test that duplicate messages are detected."""
        message_id = 999
        chat_id = 888

        temp_db.record_processed_message(
            message_id=message_id,
            chat_id=chat_id,
            user_id=None,
            message_text="Duplicate test",
            extraction_success=False,
        )

        # Should detect as already processed
        assert temp_db.is_message_processed(message_id, chat_id) is True

    def test_event_recording(self, temp_db):
        """Test recording of created events."""
        import uuid

        event_id = str(uuid.uuid4())
        temp_db.record_event(
            event_id=event_id,
            event_type="calendar",
            title="Test Event",
            source_message_id=123,
            source_chat_id=456,
            google_event_id="google_event_123",
        )

        # Verify event was recorded (check statistics)
        stats = temp_db.get_statistics()
        assert stats["total_events"] >= 1

    def test_statistics(self, temp_db):
        """Test statistics collection."""
        # Record some test data
        for i in range(5):
            temp_db.record_processed_message(
                message_id=i,
                chat_id=100,
                user_id=200,
                message_text=f"Test message {i}",
                extraction_success=(i % 2 == 0),
            )

        stats = temp_db.get_statistics()
        assert stats["total_messages"] == 5
        assert stats["successful_extractions"] >= 0
        assert "messages_by_chat" in stats

    def test_recent_messages(self, temp_db):
        """Test retrieving recent messages."""
        # Record multiple messages
        for i in range(10):
            temp_db.record_processed_message(
                message_id=i,
                chat_id=100,
                user_id=200,
                message_text=f"Message {i}",
                extraction_success=True,
            )

        recent = temp_db.get_recent_messages(limit=5)
        assert len(recent) == 5
        assert recent[0].message_id == 9  # Most recent first

    def test_chat_specific_messages(self, temp_db):
        """Test filtering messages by chat ID."""
        # Record messages for different chats
        temp_db.record_processed_message(
            message_id=1, chat_id=100, user_id=1, message_text="Chat 100", extraction_success=True
        )
        temp_db.record_processed_message(
            message_id=2, chat_id=200, user_id=2, message_text="Chat 200", extraction_success=True
        )

        chat_100_messages = temp_db.get_recent_messages(chat_id=100, limit=10)
        assert len(chat_100_messages) == 1
        assert chat_100_messages[0].chat_id == 100

