"""Pattern matching for extracting school-related information."""

import re
from datetime import datetime, timedelta
from typing import List, Optional

from dateparser import parse as parse_date

from extractor.models import EventType, SchoolEvent
from utils.logger import logger

# Keywords for different event types
ASSIGNMENT_KEYWORDS = [
    "assignment",
    "homework",
    "hw",
    "project",
    "essay",
    "paper",
    "due",
    "submit",
    "hand in",
]

EXAM_KEYWORDS = [
    "exam",
    "test",
    "quiz",
    "midterm",
    "final",
    "assessment",
    "evaluation",
]

CLASS_KEYWORDS = [
    "class",
    "lecture",
    "tutorial",
    "lab",
    "seminar",
    "workshop",
    "session",
]

# Date patterns
DATE_PATTERNS = [
    r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",  # MM/DD/YYYY or DD/MM/YYYY
    r"\d{4}[/-]\d{1,2}[/-]\d{1,2}",  # YYYY/MM/DD
    r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)day",  # Day of week
    r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)",
    r"next\s+\w+day",  # "next Monday"
    r"this\s+\w+day",  # "this Friday"
    r"tomorrow",
    r"today",
]

# Time patterns
TIME_PATTERNS = [
    r"\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)",  # 12-hour format
    r"\d{1,2}:\d{2}",  # 24-hour format
    r"\d{1,2}\s*(?:AM|PM|am|pm)",  # Hour only
]


class PatternMatcher:
    """Extract school-related information using pattern matching."""

    def __init__(self):
        """Initialize pattern matcher with compiled regex patterns."""
        self.assignment_pattern = re.compile(
            r"\b(" + "|".join(ASSIGNMENT_KEYWORDS) + r")\b", re.IGNORECASE
        )
        self.exam_pattern = re.compile(
            r"\b(" + "|".join(EXAM_KEYWORDS) + r")\b", re.IGNORECASE
        )
        self.class_pattern = re.compile(
            r"\b(" + "|".join(CLASS_KEYWORDS) + r")\b", re.IGNORECASE
        )
        self.date_patterns = [re.compile(p, re.IGNORECASE) for p in DATE_PATTERNS]
        self.time_patterns = [re.compile(p, re.IGNORECASE) for p in TIME_PATTERNS]

    def extract(self, text: str) -> Optional[SchoolEvent]:
        """
        Extract school event information from text using patterns.

        Args:
            text: Input text to extract from

        Returns:
            SchoolEvent if extraction successful, None otherwise
        """
        text = text.strip()
        if not text or len(text) < 10:
            return None

        # Determine event type
        event_type = self._detect_event_type(text)
        if not event_type:
            return None

        # Extract date/time
        date = self._extract_date(text)
        due_date = self._extract_due_date(text, event_type)

        # Extract title (simplified - take first sentence or key phrase)
        title = self._extract_title(text, event_type)

        # Calculate confidence based on matches
        confidence = self._calculate_confidence(text, event_type, date, due_date)

        if confidence < 0.3:
            return None

        return SchoolEvent(
            title=title,
            event_type=event_type,
            date=date,
            due_date=due_date,
            description=text[:200] if len(text) > 200 else text,
            confidence=confidence,
            source_text=text,
        )

    def _detect_event_type(self, text: str) -> Optional[EventType]:
        """Detect event type from keywords."""
        text_lower = text.lower()

        if self.assignment_pattern.search(text_lower):
            return EventType.ASSIGNMENT
        elif self.exam_pattern.search(text_lower):
            return EventType.EXAM
        elif self.class_pattern.search(text_lower):
            return EventType.CLASS
        else:
            return None

    def _extract_date(self, text: str) -> Optional[datetime]:
        """Extract date from text."""
        # Try all date patterns
        for pattern in self.date_patterns:
            match = pattern.search(text)
            if match:
                date_str = match.group(0)
                parsed = parse_date(date_str)
                if parsed:
                    return parsed

        # Try parsing the entire text
        parsed = parse_date(text)
        if parsed:
            return parsed

        return None

    def _extract_due_date(self, text: str, event_type: EventType) -> Optional[datetime]:
        """Extract due date specifically for assignments."""
        if event_type != EventType.ASSIGNMENT:
            return None

        # Look for "due" keyword followed by date
        due_pattern = re.compile(
            r"due\s*(?:on|by|:)?\s*([^\n,]+)", re.IGNORECASE
        )
        match = due_pattern.search(text)
        if match:
            date_str = match.group(1).strip()
            parsed = parse_date(date_str)
            if parsed:
                return parsed

        # If no explicit due date, use extracted date
        return self._extract_date(text)

    def _extract_title(self, text: str, event_type: EventType) -> str:
        """Extract or generate title from text."""
        # Try to find a title-like phrase
        sentences = text.split(".")
        if sentences:
            first_sentence = sentences[0].strip()
            if len(first_sentence) > 5 and len(first_sentence) < 100:
                return first_sentence

        # Generate title from event type
        type_name = event_type.value.title()
        return f"{type_name} - {text[:50]}"

    def _calculate_confidence(
        self,
        text: str,
        event_type: EventType,
        date: Optional[datetime],
        due_date: Optional[datetime],
    ) -> float:
        """Calculate confidence score for extraction."""
        confidence = 0.5  # Base confidence

        # Boost confidence if date found
        if date:
            confidence += 0.3
        if due_date:
            confidence += 0.2

        # Boost confidence if time found
        for pattern in self.time_patterns:
            if pattern.search(text):
                confidence += 0.1
                break

        # Boost confidence if multiple keywords found
        keyword_count = 0
        if event_type == EventType.ASSIGNMENT:
            keyword_count = len(self.assignment_pattern.findall(text.lower()))
        elif event_type == EventType.EXAM:
            keyword_count = len(self.exam_pattern.findall(text.lower()))
        elif event_type == EventType.CLASS:
            keyword_count = len(self.class_pattern.findall(text.lower()))

        if keyword_count > 1:
            confidence += 0.1

        return min(confidence, 1.0)

