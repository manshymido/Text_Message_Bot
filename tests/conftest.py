"""Pytest configuration and fixtures."""

import pytest
import tempfile
from pathlib import Path

from database.db_manager import DatabaseManager
from bot.filters import MessageFilter
from extractor.pattern_matcher import PatternMatcher
from extractor.llm_extractor import LLMExtractor


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    db_manager = DatabaseManager(db_path=db_path)
    yield db_manager
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def message_filter():
    """Create a message filter instance."""
    return MessageFilter()


@pytest.fixture
def pattern_matcher():
    """Create a pattern matcher instance."""
    return PatternMatcher()


@pytest.fixture
def llm_extractor():
    """Create an LLM extractor instance (may not have API key)."""
    return LLMExtractor()

