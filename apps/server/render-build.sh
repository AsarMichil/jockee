#!/usr/bin/env bash
# Render build script for Auto-DJ Backend
set -o errexit

echo "🚀 Starting Render build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# Run database migrations (only if DATABASE_URL is available)
echo "🗄️ Running database migrations..."
if [ -n "$DATABASE_URL" ]; then
    alembic upgrade head
    echo "✅ Database migrations completed"
else
    echo "⚠️  DATABASE_URL not set, skipping migrations"
fi

echo "✅ Build process completed successfully!" 