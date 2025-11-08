"""Message filtering logic for school-related content."""

import re
from typing import List

# Keywords that indicate school-related content
SCHOOL_KEYWORDS = [
    "assignment",
    "homework",
    "hw",
    "project",
    "exam",
    "test",
    "quiz",
    "class",
    "lecture",
    "due",
    "deadline",
    "submit",
    "midterm",
    "final",
    "lab",
    "tutorial",
    "seminar",
    "workshop",
    "course",
    "subject",
    "professor",
    "prof",
    "teacher",
    "instructor",
]


class MessageFilter:
    """Filter messages for school-related content."""

    def __init__(self):
        """Initialize message filter."""
        # Create regex pattern for keywords
        pattern = r"\b(" + "|".join(SCHOOL_KEYWORDS) + r")\b"
        self.keyword_pattern = re.compile(pattern, re.IGNORECASE)

    def is_school_related(self, text: str) -> bool:
        """
        Check if message contains school-related keywords.

        Args:
            text: Message text to check

        Returns:
            True if message appears school-related
        """
        if not text or len(text.strip()) < 5:
            return False

        text_lower = text.lower()

        # Check for keywords
        if self.keyword_pattern.search(text_lower):
            return True

        # Check for date patterns (often indicate deadlines/events)
        date_patterns = [
            r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
            r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)day",
            r"tomorrow",
            r"next\s+\w+day",
        ]

        for pattern in date_patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    def should_process(self, text: str, min_length: int = 10) -> bool:
        """
        Determine if message should be processed.

        Args:
            text: Message text
            min_length: Minimum text length

        Returns:
            True if message should be processed
        """
        if not text or len(text.strip()) < min_length:
            return False

        return self.is_school_related(text)

