"""Pydantic data models for extracted school events."""

from datetime import datetime
from enum import Enum
from typing import Optional

from dateparser import parse as parse_date
from pydantic import BaseModel, Field, validator


class EventType(str, Enum):
    """Types of school events."""

    ASSIGNMENT = "assignment"
    EXAM = "exam"
    CLASS = "class"
    MEETING = "meeting"
    OTHER = "other"


class SchoolEvent(BaseModel):
    """Model for extracted school-related event information."""

    title: str = Field(..., description="Event title")
    event_type: EventType = Field(..., description="Type of event")
    date: Optional[datetime] = Field(None, description="Event date and time")
    due_date: Optional[datetime] = Field(
        None, description="Due date for assignments"
    )
    description: Optional[str] = Field(
        None, description="Event description or notes"
    )
    location: Optional[str] = Field(None, description="Event location")
    confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Extraction confidence score"
    )
    source_text: str = Field(..., description="Original message text")

    @validator("date", "due_date", pre=True)
    def parse_date(cls, v):
        """Parse date string to datetime if needed."""
        if isinstance(v, str):
            parsed = parse_date(v)
            if parsed:
                return parsed
        return v

    @validator("event_type", pre=True)
    def normalize_event_type(cls, v):
        """Normalize event type string."""
        if isinstance(v, str):
            v = v.lower().strip()
            for event_type in EventType:
                if event_type.value == v:
                    return event_type
        return v

    class Config:
        """Pydantic config."""

        use_enum_values = True

