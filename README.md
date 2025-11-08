# Text Message Bot - School Information Extractor

A proof-of-concept Telegram bot that extracts school-related information from group chats and automatically creates Google Calendar events and Google Tasks.

## Features

- 🤖 **Intelligent Extraction**: Hybrid approach using pattern matching and LLM (OpenAI) for extracting school information
- 📅 **Calendar Integration**: Automatically creates Google Calendar events for exams, classes, and assignments
- ✅ **Task Management**: Creates Google Tasks for assignments with due dates
- 🔍 **Smart Filtering**: Only processes messages that contain school-related keywords
- 🛡️ **Error Handling**: Robust error handling with retry logic and logging

## Prerequisites

- Python 3.8 or higher
- Telegram account
- Google account with Calendar and Tasks access
- OpenAI API key (optional, for LLM extraction)

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
# Navigate to project directory
cd Text_Message_Bot

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Start a conversation and send `/newbot`
3. Follow the instructions to:
   - Choose a name for your bot
   - Choose a username (must end with 'bot')
4. BotFather will give you a **token** - save this for later
5. (Optional) Set bot description with `/setdescription`
6. (Optional) Set bot commands with `/setcommands`:
   ```
   start - Start the bot
   status - Check bot status
   ```

### 3. Set Up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - **Google Calendar API**
   - **Google Tasks API**
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Name it (e.g., "Text Message Bot")
   - Click "Create"
5. Download the credentials JSON file
6. Save it as `credentials/credentials.json` in the project directory

### 4. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your values:
   ```env
   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

   # OpenAI API Configuration (optional)
   OPENAI_API_KEY=your_openai_api_key_here

   # Google API Configuration
   GOOGLE_CREDENTIALS_FILE=credentials/credentials.json
   GOOGLE_TOKEN_FILE=credentials/token.json

   # Logging
   LOG_LEVEL=INFO

   # Bot Configuration
   DEFAULT_TIMEZONE=UTC
   ENABLE_LLM_EXTRACTION=true
   ```

### 5. Authenticate with Google

1. Run the bot for the first time:
   ```bash
   python main.py
   ```

2. On first run, it will open a browser window for Google OAuth authentication
3. Sign in with your Google account
4. Grant permissions for Calendar and Tasks
5. The token will be saved to `credentials/token.json` automatically

### 6. Add Bot to Group Chat

1. Create or open a Telegram group chat
2. Add your bot to the group (search for your bot's username)
3. Give the bot permission to read messages (admin rights may be required)
4. The bot will start monitoring messages automatically

## Usage

### Automatic Processing

The bot automatically processes messages in group chats that contain school-related keywords such as:
- Assignment, homework, project
- Exam, test, quiz
- Class, lecture, tutorial
- Due dates, deadlines

### Commands

- `/start` - Display welcome message and bot information
- `/status` - Check bot status and service availability

### Example Messages

The bot can extract information from messages like:

```
"Math assignment due next Monday at 11:59 PM"
"History exam on December 15th at 2:00 PM"
"CS101 lecture tomorrow at 10am in room 205"
"Submit your project by Friday"
```

## Project Structure

```
Text_Message_Bot/
├── main.py                 # Bot entry point
├── bot/
│   ├── handlers.py         # Message handlers
│   └── filters.py          # Message filtering
├── extractor/
│   ├── pattern_matcher.py # Pattern matching extraction
│   ├── llm_extractor.py    # LLM-based extraction
│   └── models.py           # Data models
├── services/
│   ├── calendar_service.py # Google Calendar integration
│   └── task_service.py     # Google Tasks integration
├── utils/
│   ├── config.py           # Configuration management
│   ├── logger.py           # Logging setup
│   └── auth.py             # Google OAuth2 helper
├── credentials/            # Google OAuth credentials (gitignored)
├── logs/                   # Log files (gitignored)
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Configuration

### Environment Variables

- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token (required)
- `OPENAI_API_KEY` - OpenAI API key for LLM extraction (optional)
- `GOOGLE_CREDENTIALS_FILE` - Path to Google OAuth credentials (default: `credentials/credentials.json`)
- `GOOGLE_TOKEN_FILE` - Path to save Google OAuth token (default: `credentials/token.json`)
- `LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `DEFAULT_TIMEZONE` - Timezone for calendar events (default: UTC)
- `ENABLE_LLM_EXTRACTION` - Enable/disable LLM extraction (default: true)

## How It Works

1. **Message Filtering**: Bot monitors group chat messages and filters for school-related keywords
2. **Information Extraction**: 
   - First tries pattern matching (fast, free)
   - Falls back to LLM extraction for complex text (if enabled)
3. **Event Creation**: 
   - Creates Google Calendar events for all extracted information
   - Creates Google Tasks for assignments with due dates
4. **Duplicate Detection**: Checks for existing events/tasks to avoid duplicates

## Troubleshooting

### Bot not responding

- Check that bot token is correct in `.env`
- Verify bot has permission to read messages in group
- Check logs in `logs/bot.log`

### Google Calendar/Tasks not working

- Verify `credentials/credentials.json` exists
- Run bot once to complete OAuth flow
- Check that APIs are enabled in Google Cloud Console
- Verify token file permissions

### LLM extraction not working

- Check OpenAI API key is set in `.env`
- Verify API key is valid and has credits
- Check `ENABLE_LLM_EXTRACTION` is set to `true`

### Low extraction accuracy

- Enable LLM extraction for better results
- Ensure messages contain clear keywords (assignment, exam, etc.)
- Include dates and times in messages for better extraction

## Logging

Logs are written to:
- Console (INFO level and above)
- `logs/bot.log` (all levels)

Set `LOG_LEVEL=DEBUG` in `.env` for detailed debugging information.

## Security Notes

- Never commit `.env` file or `credentials/` directory to version control
- Keep your bot token and API keys secure
- The `.gitignore` file is configured to exclude sensitive files

## Limitations

This is a proof-of-concept implementation. Known limitations:

- Pattern matching may miss complex natural language
- LLM extraction requires API credits
- Duplicate detection is basic (title similarity)
- No support for recurring events beyond single occurrences
- Limited timezone handling

## Future Enhancements

- Support for multiple calendars/task lists
- Better duplicate detection using fuzzy matching
- Support for recurring events
- Multi-language support
- Webhook support for production deployment
- Database for tracking processed messages

## License

This is a proof-of-concept project for educational purposes.

## Support

For issues or questions, check the logs in `logs/bot.log` for detailed error messages.

