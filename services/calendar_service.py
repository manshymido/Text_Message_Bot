"""Google Calendar API integration."""

from datetime import datetime, timedelta
from typing import List, Optional

from googleapiclient.errors import HttpError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from extractor.models import EventType, SchoolEvent
from utils.auth import get_calendar_service
from utils.config import settings
from utils.logger import logger

# Event colors based on type
EVENT_COLORS = {
    EventType.ASSIGNMENT: "5",  # Yellow
    EventType.EXAM: "11",  # Red
    EventType.CLASS: "9",  # Blue
    EventType.MEETING: "10",  # Green
    EventType.OTHER: "1",  # Lavender
}


class CalendarService:
    """Service for managing Google Calendar events."""

    def __init__(self):
        """Initialize calendar service."""
        self.service = get_calendar_service()
        if not self.service:
            logger.warning("Calendar service not available")

    def create_event(self, event: SchoolEvent) -> Optional[str]:
        """
        Create a calendar event from extracted school event.

        Args:
            event: SchoolEvent to create calendar event for

        Returns:
            Event ID if successful, None otherwise
        """
        if not self.service:
            logger.error("Calendar service not initialized")
            return None

        # Determine date/time for event
        event_date = event.due_date if event.due_date else event.date
        if not event_date:
            logger.warning(f"No date found for event: {event.title}")
            return None

        try:
            # Build event body
            event_body = self._build_event_body(event, event_date)

            # Check for duplicates
            if self._is_duplicate(event, event_date):
                logger.info(f"Duplicate event detected, skipping: {event.title}")
                return None

            # Create event
            created_event = self._create_event_with_retry(event_body)

            if created_event:
                event_id = created_event.get("id")
                logger.info(
                    f"Created calendar event: {event.title} (ID: {event_id})"
                )
                return event_id
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            return None

    def _build_event_body(self, event: SchoolEvent, event_date: datetime) -> dict:
        """Build Google Calendar event body."""
        # Format date/time for Google Calendar API
        start_datetime = event_date.isoformat()
        end_datetime = (event_date + timedelta(hours=1)).isoformat()

        # If no time specified, make it an all-day event
        if not event_date.time() or event_date.time() == datetime.min.time():
            start_date = event_date.strftime("%Y-%m-%d")
            end_date = (event_date + timedelta(days=1)).strftime("%Y-%m-%d")
            start = {"date": start_date}
            end = {"date": end_date}
        else:
            start = {"dateTime": start_datetime, "timeZone": settings.default_timezone}
            end = {"dateTime": end_datetime, "timeZone": settings.default_timezone}

        # Build description
        description_parts = []
        if event.description:
            description_parts.append(event.description)
        description_parts.append(f"\n\nSource: {event.source_text[:200]}")
        description = "\n".join(description_parts)

        event_body = {
            "summary": event.title,
            "description": description,
            "start": start,
            "end": end,
            "colorId": EVENT_COLORS.get(event.event_type, "1"),
        }

        if event.location:
            event_body["location"] = event.location

        # Add reminders
        event_body["reminders"] = {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},  # 1 day before
                {"method": "popup", "minutes": 60},  # 1 hour before
            ],
        }

        return event_body

    def _is_duplicate(self, event: SchoolEvent, event_date: datetime) -> bool:
        """Check if event already exists (simple duplicate detection)."""
        try:
            # Search for events on the same day with similar title
            time_min = event_date.replace(hour=0, minute=0, second=0).isoformat() + "Z"
            time_max = (event_date.replace(hour=23, minute=59, second=59)).isoformat() + "Z"

            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=10,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            event_title_lower = event.title.lower()

            for existing_event in events:
                existing_title = existing_event.get("summary", "").lower()
                # Simple similarity check
                if event_title_lower in existing_title or existing_title in event_title_lower:
                    return True

            return False

        except Exception as e:
            logger.warning(f"Duplicate check failed: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((HttpError, ConnectionError)),
    )
    def _create_event_with_retry(self, event_body: dict) -> Optional[dict]:
        """Create event with retry logic."""
        try:
            created_event = (
                self.service.events()
                .insert(calendarId="primary", body=event_body)
                .execute()
            )
            return created_event
        except HttpError as e:
            logger.error(f"HTTP error creating event: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating event: {e}")
            raise

    def list_upcoming_events(self, max_results: int = 10) -> List[dict]:
        """
        List upcoming calendar events.

        Args:
            max_results: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        if not self.service:
            return []

        try:
            now = datetime.utcnow().isoformat() + "Z"
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            return events_result.get("items", [])

        except Exception as e:
            logger.error(f"Failed to list events: {e}")
            return []

