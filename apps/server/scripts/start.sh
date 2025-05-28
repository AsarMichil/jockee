#!/bin/bash

# Auto-DJ Backend Startup Script
set -e

echo "🎵 Starting Auto-DJ Backend Development Environment"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from env.example..."
    cp env.example .env
    echo "📝 Please edit .env with your Spotify credentials before continuing."
    echo "   Get credentials from: https://developer.spotify.com/dashboard"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check for Mise and auto-install Python if available
if command -v mise > /dev/null 2>&1; then
    echo "✅ Mise detected"
    if [ -f .mise.toml ]; then
        echo "🐍 Installing Python via Mise..."
        mise install
        echo "✅ Python version set via Mise"
    fi
else
    echo "💡 Mise not found. Consider installing it for easier Python version management:"
    echo "   curl https://mise.jdx.dev/install.sh | sh"
fi

# Check if Python is available
if ! command -v python3 > /dev/null 2>&1 && ! command -v python > /dev/null 2>&1; then
    echo "❌ Python is not installed. Please install Python 3.12.8 first."
    echo "   With Mise: mise install"
    echo "   Or manually install Python 3.12.8"
    exit 1
fi

# Determine Python command (mise uses 'python', system typically uses 'python3')
PYTHON_CMD="python3"
if command -v mise > /dev/null 2>&1 && mise which python > /dev/null 2>&1; then
    PYTHON_CMD="python"
fi

# Check Python version compatibility
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ "$PYTHON_VERSION" < "3.12" ]]; then
    echo "⚠️  Warning: Python $PYTHON_VERSION detected."
    echo "   This project is optimized for Python 3.12.8 (latest stable)."
    echo "   While older versions may work, you may encounter compatibility issues."
    echo ""
    if command -v mise > /dev/null 2>&1; then
        echo "   Run 'mise install' to use the project's specified Python version (3.12.8)"
    else
        echo "   Consider installing Mise for easier version management:"
        echo "   curl https://mise.jdx.dev/install.sh | sh"
    fi
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Python $PYTHON_VERSION detected (compatible)"
fi

# Check if pip is available
if ! command -v pip > /dev/null 2>&1 && ! command -v pip3 > /dev/null 2>&1; then
    echo "❌ pip is not installed. Please install pip first."
    exit 1
fi

# Determine pip command
PIP_CMD="pip"
if command -v pip3 > /dev/null 2>&1; then
    PIP_CMD="pip3"
fi

# Install Python dependencies if not already installed
echo "📦 Checking Python dependencies..."
if ! $PYTHON_CMD -c "import fastapi" > /dev/null 2>&1; then
    echo "🔧 Installing Python dependencies..."
    $PIP_CMD install -r requirements.txt
else
    echo "✅ Python dependencies already installed"
fi

# Determine which docker compose command to use
DOCKER_COMPOSE_CMD=""
if command -v docker-compose > /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version > /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo "❌ Neither 'docker-compose' nor 'docker compose' is available."
    echo "   Please install Docker Compose or update Docker to a newer version."
    exit 1
fi

echo "🐳 Starting Docker services using: $DOCKER_COMPOSE_CMD"
$DOCKER_COMPOSE_CMD -f docker/docker-compose.dev.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if we need to run migrations
echo "🗄️  Setting up database..."
if [ ! -d "alembic/versions" ] || [ -z "$(ls -A alembic/versions 2>/dev/null)" ]; then
    echo "📦 Creating initial database migration..."
    alembic revision --autogenerate -m "Initial migration"
fi

echo "🔄 Running database migrations..."
alembic upgrade head

echo "✅ Database setup complete!"

echo ""
echo "🚀 Ready to start development!"
echo ""
echo "To start the API server:"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "To start Celery worker:"
echo "  celery -A app.workers.celery_app worker --loglevel=info"
echo ""
echo "To start Celery beat:"
echo "  celery -A app.workers.celery_app beat --loglevel=info"
echo ""
echo "API Documentation: http://localhost:8000/api/v1/docs"
echo "Health Check: http://localhost:8000/health"
echo ""
echo "🎉 Happy coding!" 