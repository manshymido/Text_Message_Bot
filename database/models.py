"""Database models for storing processed messages and events."""

from datetime import datetime
from typing import Optional


class ProcessedMessage:
    """Model for a processed Telegram message."""

    def __init__(
        self,
        message_id: int,
        chat_id: int,
        user_id: Optional[int],
        message_text: str,
        processed_at: datetime,
        event_id: Optional[str] = None,
        task_id: Optional[str] = None,
        extraction_success: bool = False,
    ):
        self.message_id = message_id
        self.chat_id = chat_id
        self.user_id = user_id
        self.message_text = message_text
        self.processed_at = processed_at
        self.event_id = event_id
        self.task_id = task_id
        self.extraction_success = extraction_success


class EventRecord:
    """Model for a created calendar event or task."""

    def __init__(
        self,
        event_id: str,
        event_type: str,  # 'calendar' or 'task'
        title: str,
        source_message_id: int,
        source_chat_id: int,
        created_at: datetime,
        google_event_id: Optional[str] = None,
        google_task_id: Optional[str] = None,
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.title = title
        self.source_message_id = source_message_id
        self.source_chat_id = source_chat_id
        self.created_at = created_at
        self.google_event_id = google_event_id
        self.google_task_id = google_task_id

