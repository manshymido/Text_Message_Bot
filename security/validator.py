"""Input validation and sanitization."""

import re
from typing import Optional, Tuple


class InputValidator:
    """Validates and sanitizes user input."""

    # Maximum message length (Telegram limit is 4096)
    MAX_MESSAGE_LENGTH = 4096

    # Potentially dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
    ]

    def __init__(self):
        """Initialize validator with compiled regex patterns."""
        self.sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self.xss_patterns = [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS]

    def validate_message(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a message text.

        Args:
            text: Message text to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text:
            return False, "Message is empty"

        if not isinstance(text, str):
            return False, "Message must be a string"

        # Check length
        if len(text) > self.MAX_MESSAGE_LENGTH:
            return False, f"Message too long (max {self.MAX_MESSAGE_LENGTH} characters)"

        # Check for SQL injection patterns
        for pattern in self.sql_patterns:
            if pattern.search(text):
                return False, "Potentially dangerous content detected"

        # Check for XSS patterns
        for pattern in self.xss_patterns:
            if pattern.search(text):
                return False, "Potentially dangerous content detected"

        return True, None

    def sanitize_message(self, text: str) -> str:
        """
        Sanitize message text.

        Args:
            text: Message text to sanitize

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Remove null bytes
        text = text.replace("\x00", "")

        # Truncate if too long
        if len(text) > self.MAX_MESSAGE_LENGTH:
            text = text[:self.MAX_MESSAGE_LENGTH]

        # Remove control characters (except newlines and tabs)
        text = "".join(
            char if ord(char) >= 32 or char in "\n\t" else ""
            for char in text
        )

        return text.strip()

    def validate_chat_id(self, chat_id: int) -> bool:
        """
        Validate chat ID.

        Args:
            chat_id: Chat ID to validate

        Returns:
            True if valid
        """
        return isinstance(chat_id, int) and chat_id != 0

    def validate_user_id(self, user_id: Optional[int]) -> bool:
        """
        Validate user ID.

        Args:
            user_id: User ID to validate (can be None)

        Returns:
            True if valid
        """
        return user_id is None or (isinstance(user_id, int) and user_id > 0)

