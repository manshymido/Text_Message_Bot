"""Main entry point for Telegram bot."""

import sys

from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

from bot.handlers import BotMessageHandler
from utils.config import settings
from utils.logger import logger


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)


def main() -> None:
    """Start the Telegram bot."""
    try:
        # Validate configuration
        logger.info("Starting Text Message Bot...")
        logger.info(f"Log level: {settings.log_level}")
        logger.info(f"LLM extraction: {settings.enable_llm_extraction}")

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

        # Add error handler
        application.add_error_handler(error_handler)

        # Start bot
        logger.info("Bot is running. Press Ctrl+C to stop.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

