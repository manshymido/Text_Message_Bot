#!/bin/bash
# Quick start script for Docker

echo "🚀 Starting Text Message Bot with Docker..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file and add your credentials"
    echo "   Required: TELEGRAM_BOT_TOKEN"
    exit 1
fi

# Check if credentials directory exists
if [ ! -d "credentials" ]; then
    echo "⚠️  credentials/ directory not found. Creating..."
    mkdir -p credentials
    echo "📝 Please add credentials/credentials.json to the credentials/ directory"
fi

# Build and start
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting bot..."
docker-compose up -d

echo "✅ Bot started! View logs with: docker-compose logs -f"
echo "📊 Check status with: docker-compose ps"

