#!/bin/bash

# Notification Service Startup Script

set -e

echo "Starting Notification Service..."

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "Error: UV is not installed. Please install UV first."
    echo "Visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating from example..."
    cp env.example .env
    echo "Please edit .env file with your FCM credentials before running the service."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
uv sync

# Check if Valkey is running (optional)
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "Valkey/Redis is running"
    else
        echo "Warning: Valkey/Redis is not running. Starting with Docker..."
        docker-compose up -d valkey
        sleep 5
    fi
else
    echo "Warning: redis-cli not found. Make sure Valkey/Redis is running."
fi

# Start the service
echo "Starting the service..."
uv run python -m src.notification_service.main 