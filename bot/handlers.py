"""Telegram bot message handlers."""

import uuid
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from bot.filters import MessageFilter
from database.db_manager import DatabaseManager
from extractor.llm_extractor import LLMExtractor
from extractor.models import SchoolEvent
from extractor.pattern_matcher import PatternMatcher
from security.rate_limiter import RateLimiter
from security.validator import InputValidator
from services.calendar_service import CalendarService
from services.task_service import TaskService
from monitoring.health_check import HealthChecker, HealthStatus
from monitoring.metrics import MetricsCollector
from utils.circuit_breaker import CircuitBreaker
from utils.dead_letter_queue import DeadLetterQueue
from utils.logger import logger


class BotMessageHandler:
    """Handle Telegram messages and extract school information."""

    def __init__(self):
        """Initialize message handler with extractors and services."""
        self.message_filter = MessageFilter()
        self.pattern_matcher = PatternMatcher()
        self.llm_extractor = LLMExtractor()
        self.calendar_service = CalendarService()
        self.task_service = TaskService()
        self.db_manager = DatabaseManager()
        self.rate_limiter = RateLimiter()
        self.input_validator = InputValidator()
        self.dlq = DeadLetterQueue()
        # Circuit breakers for external services
        self.calendar_circuit_breaker = CircuitBreaker(
            failure_threshold=5, recovery_timeout=60
        )
        self.task_circuit_breaker = CircuitBreaker(
            failure_threshold=5, recovery_timeout=60
        )
        # Metrics and health checks
        self.metrics = MetricsCollector()
        self.health_checker = HealthChecker()
        self._setup_health_checks()

    def _setup_health_checks(self):
        """Setup health checks for services."""
        # Calendar service health check
        self.health_checker.register_check(
            "calendar_service",
            lambda: (
                HealthStatus.HEALTHY if self.calendar_service.service else HealthStatus.UNHEALTHY,
                "Calendar service available" if self.calendar_service.service else "Calendar service unavailable",
            ),
            critical=True,
        )

        # Task service health check
        self.health_checker.register_check(
            "task_service",
            lambda: (
                HealthStatus.HEALTHY if self.task_service.service else HealthStatus.UNHEALTHY,
                "Task service available" if self.task_service.service else "Task service unavailable",
            ),
            critical=True,
        )

        # LLM service health check
        self.health_checker.register_check(
            "llm_service",
            lambda: (
                HealthStatus.HEALTHY if self.llm_extractor.model else HealthStatus.DEGRADED,
                "LLM service available" if self.llm_extractor.model else "LLM service unavailable (optional)",
            ),
            critical=False,
        )

        # Database health check
        self.health_checker.register_check(
            "database",
            lambda: (
                HealthStatus.HEALTHY if self.db_manager.db_path.exists() else HealthStatus.UNHEALTHY,
                "Database accessible" if self.db_manager.db_path.exists() else "Database not accessible",
            ),
            critical=True,
        )

        # Circuit breaker health checks
        self.health_checker.register_check(
            "calendar_circuit_breaker",
            lambda: (
                HealthStatus.HEALTHY if self.calendar_circuit_breaker.get_state().value == "closed" else HealthStatus.DEGRADED,
                f"Circuit breaker: {self.calendar_circuit_breaker.get_state().value}",
            ),
            critical=False,
        )

    async def handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle incoming message from group chat.

        Args:
            update: Telegram update object
            context: Bot context
        """
        if not update.message:
            logger.debug("Update has no message")
            return
            
        if not update.message.text:
            logger.debug("Message has no text content")
            return

        message_text = update.message.text
        chat_id = update.message.chat_id
        message_id = update.message.message_id
        chat_type = update.message.chat.type if update.message.chat else "unknown"
        user_id = update.message.from_user.id if update.message.from_user else None

        logger.info(
            f"Received message from chat {chat_id} (type: {chat_type}), user {user_id}: {message_text[:100]}"
        )

        # Validate input
        is_valid, error_msg = self.input_validator.validate_message(message_text)
        if not is_valid:
            logger.warning(f"Invalid message rejected: {error_msg}")
            return

        # Sanitize message
        message_text = self.input_validator.sanitize_message(message_text)

        # Rate limiting
        rate_limit_id = f"{chat_id}_{user_id}" if user_id else str(chat_id)
        is_allowed, rate_limit_reason = self.rate_limiter.is_allowed(rate_limit_id)
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {rate_limit_id}: {rate_limit_reason}")
            return

        # Check if message was already processed
        if self.db_manager.is_message_processed(message_id, chat_id):
            logger.debug(f"Message {message_id} from chat {chat_id} already processed, skipping")
            return

        # Filter for school-related content
        if not self.message_filter.should_process(message_text):
            logger.info(f"Message filtered out (not school-related): {message_text[:50]}...")
            # Record filtered message to avoid reprocessing
            self.db_manager.record_processed_message(
                message_id=message_id,
                chat_id=chat_id,
                user_id=user_id,
                message_text=message_text,
                extraction_success=False,
            )
            return
        
        logger.info(f"Message passed filter, processing: {message_text[:50]}...")

        # Track metrics
        self.metrics.increment("messages.processed")

        # Extract information
        with self.metrics.time_operation("extraction.duration"):
            event = await self._extract_event(message_text)

        if not event:
            logger.info("Failed to extract event information from message")
            self.metrics.increment("extraction.failed")
            # Record failed extraction
            self.db_manager.record_processed_message(
                message_id=message_id,
                chat_id=chat_id,
                user_id=user_id,
                message_text=message_text,
                extraction_success=False,
            )
            return

        self.metrics.increment("extraction.successful")

        event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
        logger.info(
            f"Extracted event: {event.title} ({event_type_str}) "
            f"with confidence {event.confidence:.2f}"
        )

        # Create calendar event with circuit breaker
        calendar_event_id = None
        if event.date or event.due_date:
            try:
                # Use async version if available, otherwise fallback to sync
                if hasattr(self.calendar_service, 'create_event_async'):
                    calendar_event_id = await self.calendar_service.create_event_async(event)
                else:
                    calendar_event_id = self.calendar_circuit_breaker.call(
                        self.calendar_service.create_event, event
                    )
                if calendar_event_id:
                    logger.info(f"Created calendar event: {calendar_event_id}")
                    self.metrics.increment("calendar.events.created")
                    # Record calendar event
                    self.db_manager.record_event(
                        event_id=str(uuid.uuid4()),
                        event_type="calendar",
                        title=event.title,
                        source_message_id=message_id,
                        source_chat_id=chat_id,
                        google_event_id=calendar_event_id,
                    )
            except Exception as e:
                logger.error(f"Failed to create calendar event: {e}")
                self.metrics.increment("calendar.events.failed")
                # Add to dead letter queue
                self.dlq.add_failed_message(
                    message_id=message_id,
                    chat_id=chat_id,
                    message_text=message_text,
                    error=str(e),
                    metadata={"operation": "create_calendar_event", "event_title": event.title},
                )

        # Create task (for assignments) with circuit breaker
        task_id = None
        event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
        if event_type_str == "assignment":
            try:
                # Use async version if available, otherwise fallback to sync
                if hasattr(self.task_service, 'create_task_async'):
                    task_id = await self.task_service.create_task_async(event)
                else:
                    task_id = self.task_circuit_breaker.call(
                        self.task_service.create_task, event
                    )
                if task_id:
                    logger.info(f"Created task: {task_id}")
                    self.metrics.increment("tasks.created")
                    # Record task event
                    self.db_manager.record_event(
                        event_id=str(uuid.uuid4()),
                        event_type="task",
                        title=event.title,
                        source_message_id=message_id,
                        source_chat_id=chat_id,
                        google_task_id=task_id,
                    )
            except Exception as e:
                logger.error(f"Failed to create task: {e}")
                self.metrics.increment("tasks.failed")
                # Add to dead letter queue
                self.dlq.add_failed_message(
                    message_id=message_id,
                    chat_id=chat_id,
                    message_text=message_text,
                    error=str(e),
                    metadata={"operation": "create_task", "event_title": event.title},
                )

        # Record successful processing
        self.db_manager.record_processed_message(
            message_id=message_id,
            chat_id=chat_id,
            user_id=user_id,
            message_text=message_text,
            extraction_success=True,
            event_id=calendar_event_id,
            task_id=task_id,
        )

        # Send confirmation message
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
            event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
            confirmation_parts = [
                f"✓ Extracted: {event.title}",
                f"Type: {event_type_str.title()}",
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
        llm_ok = self.llm_extractor.model is not None

        status_parts.append(f"📅 Calendar: {'✓' if calendar_ok else '✗'}")
        status_parts.append(f"✅ Tasks: {'✓' if task_ok else '✗'}")
        status_parts.append(f"🤖 LLM: {'✓' if llm_ok else '✗'}")

        # Health check status
        health_status = self.health_checker.get_overall_status()
        status_parts.append(f"\n🏥 Overall Health: {health_status.upper()}")

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

    async def handle_stats(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /stats command."""
        try:
            stats = self.db_manager.get_statistics()
            stats_parts = ["📊 Bot Statistics:\n"]

            stats_parts.append(f"📨 Total messages processed: {stats.get('total_messages', 0)}")
            stats_parts.append(
                f"✅ Successful extractions: {stats.get('successful_extractions', 0)}"
            )
            stats_parts.append(f"📅 Total events created: {stats.get('total_events', 0)}")

            events_by_type = stats.get("events_by_type", {})
            if events_by_type:
                stats_parts.append("\n📊 Events by type:")
                for event_type, count in events_by_type.items():
                    stats_parts.append(f"  • {event_type}: {count}")

            messages_by_chat = stats.get("messages_by_chat", {})
            if messages_by_chat:
                stats_parts.append(f"\n💬 Active chats: {len(messages_by_chat)}")

            stats_message = "\n".join(stats_parts)
            await update.message.reply_text(stats_message)

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            await update.message.reply_text("❌ Failed to retrieve statistics")

    async def handle_health(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /health command."""
        try:
            health_result = self.health_checker.run_all_checks()
            health_parts = [f"🏥 Health Check: {health_result['status'].upper()}\n"]

            for check_name, check_result in health_result["checks"].items():
                status_icon = "✓" if check_result["status"] == HealthStatus.HEALTHY else "✗"
                critical_mark = " [CRITICAL]" if check_result["critical"] else ""
                health_parts.append(
                    f"{status_icon} {check_name}: {check_result['status']}{critical_mark}"
                )
                if check_result["message"]:
                    health_parts.append(f"   {check_result['message']}")

            health_message = "\n".join(health_parts)
            await update.message.reply_text(health_message)

        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            await update.message.reply_text("❌ Failed to retrieve health status")

    async def handle_metrics(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /metrics command."""
        try:
            summary = self.metrics.get_summary()
            await update.message.reply_text(summary)
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            await update.message.reply_text("❌ Failed to retrieve metrics")

