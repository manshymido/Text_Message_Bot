"""Dead letter queue for failed messages."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from utils.logger import logger


class DeadLetterQueue:
    """Dead letter queue for storing failed message processing attempts."""

    def __init__(self, queue_dir: str = "data/dlq"):
        """
        Initialize dead letter queue.

        Args:
            queue_dir: Directory to store failed messages
        """
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)

    def add_failed_message(
        self,
        message_id: int,
        chat_id: int,
        message_text: str,
        error: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """
        Add a failed message to the queue.

        Args:
            message_id: Telegram message ID
            chat_id: Telegram chat ID
            message_text: Original message text
            error: Error message or exception
            metadata: Additional metadata
        """
        entry = {
            "message_id": message_id,
            "chat_id": chat_id,
            "message_text": message_text,
            "error": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        filename = f"{chat_id}_{message_id}_{datetime.utcnow().timestamp()}.json"
        filepath = self.queue_dir / filename

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
            logger.warning(f"Added failed message to DLQ: {filename}")
        except Exception as e:
            logger.error(f"Failed to write to DLQ: {e}")

    def get_failed_messages(
        self, chat_id: Optional[int] = None, limit: int = 10
    ) -> List[Dict]:
        """
        Get failed messages from the queue.

        Args:
            chat_id: Optional chat ID to filter by
            limit: Maximum number of messages to return

        Returns:
            List of failed message entries
        """
        entries = []

        for filepath in sorted(self.queue_dir.glob("*.json"), reverse=True):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    entry = json.load(f)

                if chat_id is None or entry.get("chat_id") == chat_id:
                    entries.append(entry)

                if len(entries) >= limit:
                    break
            except Exception as e:
                logger.error(f"Failed to read DLQ entry {filepath}: {e}")

        return entries

    def clear_failed_message(self, message_id: int, chat_id: int) -> bool:
        """
        Remove a specific failed message from the queue.

        Args:
            message_id: Telegram message ID
            chat_id: Telegram chat ID

        Returns:
            True if message was found and removed
        """
        for filepath in self.queue_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    entry = json.load(f)

                if (
                    entry.get("message_id") == message_id
                    and entry.get("chat_id") == chat_id
                ):
                    filepath.unlink()
                    logger.info(f"Removed DLQ entry: {filepath.name}")
                    return True
            except Exception as e:
                logger.error(f"Failed to process DLQ entry {filepath}: {e}")

        return False

    def get_queue_size(self) -> int:
        """
        Get the number of failed messages in the queue.

        Returns:
            Number of failed messages
        """
        return len(list(self.queue_dir.glob("*.json")))

    def clear_all(self) -> int:
        """
        Clear all failed messages from the queue.

        Returns:
            Number of messages cleared
        """
        count = 0
        for filepath in self.queue_dir.glob("*.json"):
            try:
                filepath.unlink()
                count += 1
            except Exception as e:
                logger.error(f"Failed to remove DLQ entry {filepath}: {e}")

        logger.info(f"Cleared {count} messages from DLQ")
        return count

