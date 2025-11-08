"""Main entry point for Telegram bot with webhook support."""

import sys
from pathlib import Path

from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

from bot.handlers import BotMessageHandler
from utils.config import settings
from utils.logger import logger


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)


def main() -> None:
    """Start the Telegram bot with webhook."""
    try:
        # Validate configuration
        logger.info("Starting Text Message Bot (Webhook mode)...")
        logger.info(f"Log level: {settings.log_level}")
        logger.info(f"LLM extraction: {settings.enable_llm_extraction}")

        # Get webhook URL from environment
        import os
        webhook_url = os.getenv("WEBHOOK_URL")
        webhook_port = int(os.getenv("WEBHOOK_PORT", "8000"))
        webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")

        if not webhook_url:
            logger.error("WEBHOOK_URL environment variable is required for webhook mode")
            sys.exit(1)

        # Create application
        application = (
            Application.builder()
            .token(settings.telegram_bot_token)
            .build()
        )

        # Initialize handlers
        message_handler = BotMessageHandler()

        # Register handlers
        # Handle messages in groups (both group and supergroup)
        application.add_handler(
            MessageHandler(
                filters.TEXT & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
                message_handler.handle_message,
            )
        )
        
        # Also handle private messages for testing
        application.add_handler(
            MessageHandler(
                filters.TEXT & filters.ChatType.PRIVATE,
                message_handler.handle_message,
            )
        )

        # Handle commands
        application.add_handler(
            CommandHandler("start", message_handler.handle_start)
        )
        application.add_handler(
            CommandHandler("status", message_handler.handle_status)
        )
        application.add_handler(
            CommandHandler("stats", message_handler.handle_stats)
        )
        application.add_handler(
            CommandHandler("health", message_handler.handle_health)
        )
        application.add_handler(
            CommandHandler("metrics", message_handler.handle_metrics)
        )

        # Add error handler
        application.add_error_handler(error_handler)

        # Set webhook
        full_webhook_url = f"{webhook_url}{webhook_path}"
        logger.info(f"Setting webhook to: {full_webhook_url}")
        
        application.bot.set_webhook(
            url=full_webhook_url,
            allowed_updates=Update.ALL_TYPES,
        )

        # Start webhook server
        logger.info(f"Starting webhook server on port {webhook_port}")
        application.run_webhook(
            listen="0.0.0.0",
            port=webhook_port,
            webhook_url=full_webhook_url,
            allowed_updates=Update.ALL_TYPES,
        )

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

