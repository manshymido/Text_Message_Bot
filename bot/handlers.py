"""Telegram bot message handlers."""

from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from bot.filters import MessageFilter
from extractor.llm_extractor import LLMExtractor
from extractor.models import SchoolEvent
from extractor.pattern_matcher import PatternMatcher
from services.calendar_service import CalendarService
from services.task_service import TaskService
from utils.logger import logger


class MessageHandler:
    """Handle Telegram messages and extract school information."""

    def __init__(self):
        """Initialize message handler with extractors and services."""
        self.message_filter = MessageFilter()
        self.pattern_matcher = PatternMatcher()
        self.llm_extractor = LLMExtractor()
        self.calendar_service = CalendarService()
        self.task_service = TaskService()

    async def handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle incoming message from group chat.

        Args:
            update: Telegram update object
            context: Bot context
        """
        if not update.message or not update.message.text:
            return

        message_text = update.message.text
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id if update.message.from_user else None

        logger.info(
            f"Received message from chat {chat_id}, user {user_id}: {message_text[:100]}"
        )

        # Filter for school-related content
        if not self.message_filter.should_process(message_text):
            logger.debug("Message filtered out (not school-related)")
            return

        # Extract information
        event = await self._extract_event(message_text)

        if not event:
            logger.debug("Failed to extract event information")
            return

        logger.info(
            f"Extracted event: {event.title} ({event.event_type.value}) "
            f"with confidence {event.confidence:.2f}"
        )

        # Create calendar event
        calendar_event_id = None
        if event.date or event.due_date:
            try:
                calendar_event_id = self.calendar_service.create_event(event)
                if calendar_event_id:
                    logger.info(f"Created calendar event: {calendar_event_id}")
            except Exception as e:
                logger.error(f"Failed to create calendar event: {e}")

        # Create task (for assignments)
        task_id = None
        if event.event_type.value == "assignment":
            try:
                task_id = self.task_service.create_task(event)
                if task_id:
                    logger.info(f"Created task: {task_id}")
            except Exception as e:
                logger.error(f"Failed to create task: {e}")

        # Send confirmation if in group chat
        if update.message.chat.type in ["group", "supergroup"]:
            await self._send_confirmation(update, event, calendar_event_id, task_id)

    async def _extract_event(self, text: str) -> Optional[SchoolEvent]:
        """
        Extract event using hybrid approach (pattern matching + LLM).

        Args:
            text: Message text

        Returns:
            Extracted SchoolEvent or None
        """
        # Try pattern matching first (faster, cheaper)
        event = self.pattern_matcher.extract(text)

        # If pattern matching failed or low confidence, try LLM
        if not event or event.confidence < 0.6:
            llm_event = self.llm_extractor.extract(text)
            if llm_event:
                # Prefer LLM result if it has higher confidence
                if not event or llm_event.confidence > event.confidence:
                    event = llm_event
                    logger.debug("Used LLM extraction")

        return event

    async def _send_confirmation(
        self,
        update: Update,
        event: SchoolEvent,
        calendar_event_id: Optional[str],
        task_id: Optional[str],
    ) -> None:
        """Send confirmation message to chat."""
        try:
            confirmation_parts = [
                f"✓ Extracted: {event.title}",
                f"Type: {event.event_type.value.title()}",
            ]

            if event.date:
                confirmation_parts.append(
                    f"Date: {event.date.strftime('%Y-%m-%d %H:%M')}"
                )
            if event.due_date:
                confirmation_parts.append(
                    f"Due: {event.due_date.strftime('%Y-%m-%d %H:%M')}"
                )

            if calendar_event_id:
                confirmation_parts.append("📅 Calendar event created")
            if task_id:
                confirmation_parts.append("✅ Task created")

            confirmation = "\n".join(confirmation_parts)

            await update.message.reply_text(confirmation)

        except Exception as e:
            logger.error(f"Failed to send confirmation: {e}")

    async def handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command."""
        welcome_message = (
            "👋 Hello! I'm a school information extraction bot.\n\n"
            "I monitor group chats for school-related information like:\n"
            "• Assignments and homework\n"
            "• Exams and tests\n"
            "• Class schedules\n\n"
            "When I find relevant information, I automatically:\n"
            "• Create Google Calendar events\n"
            "• Create Google Tasks for assignments\n\n"
            "Just add me to your group chat and I'll start working!"
        )
        await update.message.reply_text(welcome_message)

    async def handle_status(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /status command."""
        status_parts = ["🤖 Bot Status:\n"]

        # Check services
        calendar_ok = self.calendar_service.service is not None
        task_ok = self.task_service.service is not None
        llm_ok = self.llm_extractor.client is not None

        status_parts.append(f"📅 Calendar: {'✓' if calendar_ok else '✗'}")
        status_parts.append(f"✅ Tasks: {'✓' if task_ok else '✗'}")
        status_parts.append(f"🤖 LLM: {'✓' if llm_ok else '✗'}")

        # List recent events
        if calendar_ok:
            events = self.calendar_service.list_upcoming_events(max_results=3)
            if events:
                status_parts.append(f"\n📅 Upcoming events: {len(events)}")

        # List recent tasks
        if task_ok:
            tasks = self.task_service.list_tasks(max_results=3)
            if tasks:
                status_parts.append(f"✅ Pending tasks: {len(tasks)}")

        status_message = "\n".join(status_parts)
        await update.message.reply_text(status_message)

