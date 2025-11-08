"""Tests for bot handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Message, Chat, User
from telegram.ext import ContextTypes

from bot.handlers import BotMessageHandler
from extractor.models import SchoolEvent, EventType
from datetime import datetime


@pytest.fixture
def mock_update():
    """Create a mock Telegram update."""
    user = User(id=123, first_name="Test", is_bot=False, username="testuser")
    chat = Chat(id=456, type="group")
    message = Message(
        message_id=789,
        date=datetime.now(),
        chat=chat,
        from_user=user,
        text="Math assignment due Monday",
    )
    update = Update(update_id=1, message=message)
    return update


@pytest.fixture
def mock_context():
    """Create a mock context."""
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)


@pytest.fixture
def handler():
    """Create a handler instance with mocked dependencies."""
    with patch("bot.handlers.CalendarService"), patch("bot.handlers.TaskService"):
        handler = BotMessageHandler()
        # Mock services
        handler.calendar_service.create_event = MagicMock(return_value="event_123")
        handler.task_service.create_task = MagicMock(return_value="task_456")
        return handler


class TestBotMessageHandler:
    """Test cases for BotMessageHandler."""

    @pytest.mark.asyncio
    async def test_handle_message_success(self, handler, mock_update, mock_context):
        """Test successful message handling."""
        # Mock extraction
        mock_event = SchoolEvent(
            title="Math Assignment",
            event_type=EventType.ASSIGNMENT,
            date=datetime.now(),
            due_date=datetime.now(),
            confidence=0.8,
            source_text="Math assignment due Monday",
        )

        with patch.object(handler, "_extract_event", return_value=mock_event):
            await handler.handle_message(mock_update, mock_context)

        # Verify calendar event was created
        handler.calendar_service.create_event.assert_called_once()
        # Verify task was created (for assignments)
        handler.task_service.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_message_no_extraction(self, handler, mock_update, mock_context):
        """Test message handling when extraction fails."""
        with patch.object(handler, "_extract_event", return_value=None):
            await handler.handle_message(mock_update, mock_context)

        # Should not create events
        handler.calendar_service.create_event.assert_not_called()
        handler.task_service.create_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_message_filtered(self, handler, mock_update, mock_context):
        """Test that filtered messages are not processed."""
        # Set message text to non-school content
        mock_update.message.text = "Hello, how are you?"

        with patch.object(handler.message_filter, "should_process", return_value=False):
            await handler.handle_message(mock_update, mock_context)

        # Should not extract or create events
        handler.calendar_service.create_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_start(self, handler, mock_update, mock_context):
        """Test /start command handler."""
        mock_update.message.reply_text = AsyncMock()
        await handler.handle_start(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        assert "Hello" in mock_update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_status(self, handler, mock_update, mock_context):
        """Test /status command handler."""
        mock_update.message.reply_text = AsyncMock()
        handler.calendar_service.service = MagicMock()
        handler.task_service.service = MagicMock()

        await handler.handle_status(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        status_text = mock_update.message.reply_text.call_args[0][0]
        assert "Bot Status" in status_text

