# Docker Deployment Guide

This guide explains how to run the Text Message Bot using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose installed (usually comes with Docker Desktop)
- Telegram Bot Token
- Google OAuth credentials (for Calendar and Tasks integration)

## Quick Start

### 1. Prepare Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
LOG_LEVEL=INFO
```

### 2. Prepare Google Credentials

Make sure you have:
- `credentials/credentials.json` - Google OAuth credentials
- The credentials directory should be accessible to Docker

### 3. Build and Run with Docker Compose

```bash
# Build and start the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

### 4. First Run - Google Authentication

On first run, the bot will need Google OAuth authentication. You have two options:

**Option A: Run once locally to authenticate**
```bash
# Run locally first to complete OAuth flow
python main.py
# This will create credentials/token.json
# Then run with Docker
docker-compose up -d
```

**Option B: Authenticate inside container**
```bash
# Run interactively
docker-compose run --rm bot python main.py
# Complete OAuth flow, then exit
# The token.json will be saved in ./data/credentials/ (if mounted)
```

## Docker Commands

### Build the image
```bash
docker-compose build
```

### Start the bot
```bash
docker-compose up -d
```

### Stop the bot
```bash
docker-compose down
```

### View logs
```bash
# All logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100 -f
```

### Restart the bot
```bash
docker-compose restart
```

### Execute commands in container
```bash
# Access shell
docker-compose exec bot bash

# Run Python script
docker-compose exec bot python -c "from database.db_manager import DatabaseManager; db = DatabaseManager(); print(db.get_statistics())"
```

## Volume Mounts

The docker-compose.yml mounts the following directories:

- `./credentials` → `/app/credentials` (read-only) - Google OAuth credentials
- `./data` → `/app/data` - Database and persistent data
- `./logs` → `/app/logs` - Log files

## Webhook Mode

To use webhook mode instead of polling:

1. Uncomment the ports section in `docker-compose.yml`:
```yaml
ports:
  - "8000:8000"
```

2. Set webhook environment variables in `.env`:
```env
WEBHOOK_URL=https://your-domain.com
WEBHOOK_PORT=8000
WEBHOOK_PATH=/webhook
```

3. Use `main_webhook.py` instead:
```yaml
# In docker-compose.yml, change CMD
command: python main_webhook.py
```

## Troubleshooting

### Bot not starting

Check logs:
```bash
docker-compose logs bot
```

### Google Authentication issues

Make sure `credentials/credentials.json` exists and is readable:
```bash
ls -la credentials/credentials.json
```

### Database issues

Check if data directory is writable:
```bash
ls -la data/
```

### Permission issues

On Linux, you may need to fix permissions:
```bash
sudo chown -R $USER:$USER data/ logs/
```

## Production Deployment

For production, consider:

1. **Use environment variables** instead of `.env` file
2. **Set up proper secrets management** (Docker secrets, Kubernetes secrets, etc.)
3. **Use webhook mode** instead of polling
4. **Set up reverse proxy** (nginx, traefik) for webhook
5. **Enable log rotation** (already configured)
6. **Set up monitoring** (Prometheus, Grafana)
7. **Use health checks** (already implemented)

## Health Checks

The bot includes health check endpoints accessible via commands:
- `/health` - Check service health
- `/status` - Check bot status
- `/metrics` - View metrics

## Updating the Bot

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose build
docker-compose up -d
```

## Clean Up

To remove everything (including data):

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker rmi text_message_bot_bot
```

