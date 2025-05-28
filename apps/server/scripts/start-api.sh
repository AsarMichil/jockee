#!/bin/bash

# Start FastAPI server
echo "🚀 Starting Auto-DJ API Server..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please run ./scripts/start.sh first."
    exit 1
fi

# Check if services are running
if ! docker ps | grep -q "autodj-postgres.*Up" || ! docker ps | grep -q "autodj-redis.*Up"; then
    echo "❌ Database services not running. Please run ./scripts/start.sh first."
    exit 1
fi

# Determine Python command
PYTHON_CMD="python3"
if command -v mise > /dev/null 2>&1 && mise which python > /dev/null 2>&1; then
    PYTHON_CMD="python"
fi

echo "📡 API Server starting at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/api/v1/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server with reload for development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 