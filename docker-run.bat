@echo off
REM Quick start script for Docker on Windows

echo 🚀 Starting Text Message Bot with Docker...

REM Check if .env exists
if not exist .env (
    echo ⚠️  .env file not found. Creating from .env.example...
    copy .env.example .env
    echo 📝 Please edit .env file and add your credentials
    echo    Required: TELEGRAM_BOT_TOKEN
    pause
    exit /b 1
)

REM Check if credentials directory exists
if not exist credentials (
    echo ⚠️  credentials/ directory not found. Creating...
    mkdir credentials
    echo 📝 Please add credentials/credentials.json to the credentials/ directory
)

REM Build and start
echo 🔨 Building Docker image...
docker-compose build

echo 🚀 Starting bot...
docker-compose up -d

echo ✅ Bot started! View logs with: docker-compose logs -f
echo 📊 Check status with: docker-compose ps
pause

