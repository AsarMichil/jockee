#!/bin/bash

# Start Celery worker
echo "👷 Starting Auto-DJ Celery Worker..."

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

echo "🔄 Worker will process background tasks (playlist analysis, audio processing)"
echo "📊 Monitor at: http://localhost:5555 (if Flower is installed)"
echo ""
echo "Press Ctrl+C to stop the worker"
echo ""

# Start Celery worker with appropriate concurrency for development
celery -A app.workers.celery_app worker --loglevel=info --concurrency=2 