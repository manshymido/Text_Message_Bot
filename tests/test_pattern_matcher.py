"""Tests for pattern matching extraction."""

import pytest
from datetime import datetime

from extractor.pattern_matcher import PatternMatcher
from extractor.models import EventType


class TestPatternMatcher:
    """Test cases for PatternMatcher."""

    def test_assignment_extraction(self, pattern_matcher):
        """Test assignment extraction."""
        text = "Math assignment due next Monday at 11:59 PM"
        event = pattern_matcher.extract(text)

        assert event is not None
        assert event.event_type == EventType.ASSIGNMENT
        assert "assignment" in event.title.lower() or "math" in event.title.lower()
        assert event.confidence > 0.3

    def test_exam_extraction(self, pattern_matcher):
        """Test exam extraction."""
        text = "History exam on Friday at 2pm"
        event = pattern_matcher.extract(text)

        assert event is not None
        assert event.event_type == EventType.EXAM
        assert event.confidence > 0.3

    def test_class_extraction(self, pattern_matcher):
        """Test class extraction."""
        text = "CS101 lecture tomorrow at 10am in room 205"
        event = pattern_matcher.extract(text)

        assert event is not None
        assert event.event_type == EventType.CLASS
        assert event.confidence > 0.3

    def test_no_match(self, pattern_matcher):
        """Test that non-school messages return None."""
        text = "Hello, how are you today?"
        event = pattern_matcher.extract(text)

        assert event is None

    def test_date_extraction(self, pattern_matcher):
        """Test date extraction."""
        text = "Assignment due 12/25/2024"
        event = pattern_matcher.extract(text)

        assert event is not None
        assert event.date is not None or event.due_date is not None

    def test_confidence_score(self, pattern_matcher):
        """Test confidence score calculation."""
        text = "Math assignment due next Monday at 11:59 PM"
        event = pattern_matcher.extract(text)

        assert event is not None
        assert 0.0 <= event.confidence <= 1.0

