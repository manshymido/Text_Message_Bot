"""Tests for message filtering."""

import pytest

from bot.filters import MessageFilter


class TestMessageFilter:
    """Test cases for MessageFilter."""

    def test_school_related_keywords(self, message_filter):
        """Test that school-related keywords are detected."""
        test_cases = [
            ("Math assignment due Monday", True),
            ("History exam on Friday", True),
            ("CS101 lecture tomorrow", True),
            ("Homework submission deadline", True),
            ("Hello, how are you?", False),
            ("What's the weather like?", False),
        ]

        for message, expected in test_cases:
            assert message_filter.should_process(message) == expected

    def test_date_patterns(self, message_filter):
        """Test that messages with date patterns are detected."""
        test_cases = [
            ("Meeting on 12/25/2024", True),
            ("Event tomorrow", True),
            ("Deadline next Monday", True),
            ("Regular message", False),
        ]

        for message, expected in test_cases:
            assert message_filter.is_school_related(message) == expected

    def test_minimum_length(self, message_filter):
        """Test minimum length requirement."""
        assert message_filter.should_process("Hi") is False
        assert message_filter.should_process("Math assignment due Monday") is True

    def test_empty_message(self, message_filter):
        """Test empty message handling."""
        assert message_filter.should_process("") is False
        assert message_filter.should_process(None) is False

