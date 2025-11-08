"""Google Tasks API integration."""

from datetime import datetime
from typing import List, Optional

from googleapiclient.errors import HttpError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from extractor.models import SchoolEvent
from utils.auth import get_tasks_service
from utils.logger import logger


class TaskService:
    """Service for managing Google Tasks."""

    def __init__(self):
        """Initialize task service."""
        self.service = get_tasks_service()
        self.task_list_id = None
        if not self.service:
            logger.warning("Tasks service not available")
        else:
            self._ensure_task_list()

    def _ensure_task_list(self):
        """Ensure default task list exists and get its ID."""
        try:
            task_lists = self.service.tasklists().list().execute()
            items = task_lists.get("items", [])

            # Use default "@default" list or first available
            for task_list in items:
                if task_list.get("id") == "@default":
                    self.task_list_id = "@default"
                    return

            if items:
                self.task_list_id = items[0]["id"]
            else:
                # Create a default list
                task_list = self.service.tasklists().insert(
                    body={"title": "School Tasks"}
                ).execute()
                self.task_list_id = task_list["id"]

            logger.info(f"Using task list: {self.task_list_id}")

        except Exception as e:
            logger.error(f"Failed to get task list: {e}")
            self.task_list_id = "@default"

    def create_task(self, event: SchoolEvent) -> Optional[str]:
        """
        Create a task from extracted school event.

        Args:
            event: SchoolEvent to create task for

        Returns:
            Task ID if successful, None otherwise
        """
        if not self.service or not self.task_list_id:
            logger.error("Task service not initialized")
            return None

        # Only create tasks for assignments
        if event.event_type.value != "assignment":
            return None

        # Use due_date if available, otherwise use date
        due_date = event.due_date if event.due_date else event.date
        if not due_date:
            logger.warning(f"No due date found for task: {event.title}")
            return None

        try:
            # Build task body
            task_body = self._build_task_body(event, due_date)

            # Check for duplicates
            if self._is_duplicate(event, due_date):
                logger.info(f"Duplicate task detected, skipping: {event.title}")
                return None

            # Create task
            created_task = self._create_task_with_retry(task_body)

            if created_task:
                task_id = created_task.get("id")
                logger.info(f"Created task: {event.title} (ID: {task_id})")
                return task_id
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return None

    def _build_task_body(self, event: SchoolEvent, due_date: datetime) -> dict:
        """Build Google Tasks task body."""
        # Format due date (Tasks API uses RFC 3339 format)
        due_date_str = due_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        # Build notes
        notes_parts = []
        if event.description:
            notes_parts.append(event.description)
        if event.location:
            notes_parts.append(f"Location: {event.location}")
        notes_parts.append(f"\nSource: {event.source_text[:200]}")
        notes = "\n".join(notes_parts)

        task_body = {
            "title": event.title,
            "notes": notes,
            "due": due_date_str,
            "status": "needsAction",
        }

        return task_body

    def _is_duplicate(self, event: SchoolEvent, due_date: datetime) -> bool:
        """Check if task already exists."""
        try:
            tasks_result = (
                self.service.tasks()
                .list(tasklist=self.task_list_id, showCompleted=False)
                .execute()
            )

            tasks = tasks_result.get("items", [])
            event_title_lower = event.title.lower()

            for existing_task in tasks:
                existing_title = existing_task.get("title", "").lower()
                # Simple similarity check
                if event_title_lower in existing_title or existing_title in event_title_lower:
                    # Check if due date is similar (same day)
                    existing_due = existing_task.get("due")
                    if existing_due:
                        try:
                            existing_due_dt = datetime.fromisoformat(
                                existing_due.replace("Z", "+00:00")
                            )
                            if existing_due_dt.date() == due_date.date():
                                return True
                        except Exception:
                            pass

            return False

        except Exception as e:
            logger.warning(f"Duplicate check failed: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((HttpError, ConnectionError)),
    )
    def _create_task_with_retry(self, task_body: dict) -> Optional[dict]:
        """Create task with retry logic."""
        try:
            created_task = (
                self.service.tasks()
                .insert(tasklist=self.task_list_id, body=task_body)
                .execute()
            )
            return created_task
        except HttpError as e:
            logger.error(f"HTTP error creating task: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating task: {e}")
            raise

    def list_tasks(self, max_results: int = 10) -> List[dict]:
        """
        List tasks from the default task list.

        Args:
            max_results: Maximum number of tasks to return

        Returns:
            List of task dictionaries
        """
        if not self.service or not self.task_list_id:
            return []

        try:
            tasks_result = (
                self.service.tasks()
                .list(
                    tasklist=self.task_list_id,
                    showCompleted=False,
                    maxResults=max_results,
                )
                .execute()
            )

            return tasks_result.get("items", [])

        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return []

