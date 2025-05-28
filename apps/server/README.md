# Auto-DJ Backend - Phase 1 MVP

A FastAPI-based backend service for automatic DJ mixing that analyzes Spotify playlists and generates professional mixing instructions.

## 🎵 Features

### Phase 1 Core Functionality
- **Spotify Integration**: OAuth2 authentication and playlist fetching
- **Audio Analysis**: BPM detection, key analysis, and energy calculation using librosa
- **Audio Fetching**: Automatic MP3 downloading via yt-dlp when local files are missing
- **Mix Generation**: BPM-based track ordering with harmonic mixing compatibility
- **Background Processing**: Celery-based async analysis with progress tracking
- **RESTful API**: Comprehensive endpoints for playlist analysis and job management

### Technical Stack
- **FastAPI** with Python 3.12.8 (latest stable)
- **PostgreSQL** for persistent storage
- **Redis** for caching and job queues
- **Celery** for background task processing
- **SQLAlchemy** ORM with Alembic migrations
- **Docker** containerization with docker-compose

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose (or Docker with built-in compose)
- Python 3.12.8 (latest stable version)
- [Mise](https://mise.jdx.dev/) for Python version management (recommended)
- Spotify Developer Account (for API credentials)

### 1. Clone Repository
```bash
git clone <repository-url>
cd auto-dj-backend
```

### 2. Environment Setup
```bash
# Copy environment template
cp env.example .env

# Edit .env with your Spotify credentials
# Get these from: https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

### 3. Start Services
```bash
# Start all services (use 'docker compose' for newer Docker versions)
docker compose -f docker/docker-compose.yml up -d
# OR for older Docker versions:
# docker-compose -f docker/docker-compose.yml up -d

# Check service health
docker compose -f docker/docker-compose.yml ps
```

### 4. Initialize Database
```bash
# Run database migrations
docker exec autodj-api alembic upgrade head
```

### 5. Access API
- **API Documentation**: http://localhost:8000/api/v1/docs
- **Health Check**: http://localhost:8000/health
- **API Base**: http://localhost:8000/api/v1

## 📖 API Usage

### Authentication Flow
```bash
# 1. Get Spotify authorization URL
curl -X GET "http://localhost:8000/api/v1/auth/spotify"

# 2. Visit the returned auth_url in browser
# 3. After authorization, you'll be redirected with a code

# 4. Check authentication status
curl -X GET "http://localhost:8000/api/v1/auth/status"
```

### Playlist Analysis
```bash
# Submit playlist for analysis
curl -X POST "http://localhost:8000/api/v1/playlists/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "spotify_playlist_url": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
    "options": {
      "auto_fetch_missing": true,
      "max_tracks": 50
    }
  }'

# Check job status
curl -X GET "http://localhost:8000/api/v1/playlists/{job_id}/status"

# Get results when complete
curl -X GET "http://localhost:8000/api/v1/playlists/{job_id}/results"
```

### Track Information
```bash
# Get track details
curl -X GET "http://localhost:8000/api/v1/tracks/{track_id}"

# Search tracks
curl -X GET "http://localhost:8000/api/v1/tracks/search/?q=artist%20name"

# Get track statistics
curl -X GET "http://localhost:8000/api/v1/tracks/stats/"
```

## 🏗️ Architecture

### Project Structure
```
auto-dj-backend/
├── app/
│   ├── api/v1/endpoints/     # API route handlers
│   ├── core/                 # Core configuration and utilities
│   ├── models/               # SQLAlchemy database models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── services/             # Business logic services
│   ├── workers/              # Celery background tasks
│   └── main.py              # FastAPI application
├── alembic/                  # Database migrations
├── docker/                   # Docker configuration
├── tests/                    # Test suite
└── requirements.txt          # Python dependencies
```

### Data Flow
1. **Playlist Submission**: User submits Spotify playlist URL
2. **Validation**: System validates URL and checks playlist access
3. **Job Creation**: Analysis job created in database
4. **Background Processing**: Celery worker processes playlist:
   - Fetches track metadata from Spotify API
   - Downloads missing audio files via yt-dlp
   - Analyzes audio features using librosa
   - Generates mix transitions and compatibility scores
5. **Results**: Mix instructions stored and available via API

### Database Schema
- **tracks**: Audio track metadata and analysis results
- **analysis_jobs**: Playlist analysis job status and progress
- **mix_transitions**: Generated mixing instructions between tracks

## 🔧 Development

### Local Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env with your configuration

# Start external services
docker compose -f docker/docker-compose.yml up postgres redis -d

# Run database migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info

# Start Celery beat (separate terminal)
celery -A app.workers.celery_app beat --loglevel=info
```

### Code Quality and Formatting
```bash
# Format and lint code with Ruff (replaces Black, isort, flake8)
ruff format .  # Format code
ruff check .   # Lint code
ruff check . --fix  # Auto-fix issues

# Type checking with mypy
mypy app/

# Run all quality checks
ruff format . && ruff check . && mypy app/
```

### Running Tests
```bash
# Install test dependencies (included in requirements.txt)
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 📊 Monitoring

### Health Checks
- **API Health**: `GET /health`
- **Database**: Connection test included in health check
- **Redis**: Connection test included in health check
- **Celery**: Use `celery -A app.workers.celery_app inspect active`

### Logs
```bash
# API logs
docker logs autodj-api

# Worker logs
docker logs autodj-celery-worker

# Database logs
docker logs autodj-postgres
```

### Storage Management
```bash
# Check audio storage usage
curl -X GET "http://localhost:8000/api/v1/tracks/stats/"

# Manual cleanup (removes files older than 30 days)
docker exec autodj-celery-worker python -c "
from app.services.audio_fetcher import AudioFetcher
fetcher = AudioFetcher()
deleted = fetcher.cleanup_old_files(30)
print(f'Deleted {deleted} files')
"
```

## 🔒 Security Considerations

### Phase 1 Security Features
- **CORS Configuration**: Configurable allowed origins
- **Session Management**: Secure session cookies for Spotify tokens
- **Input Validation**: Pydantic schemas for all API inputs
- **Rate Limiting**: Built into yt-dlp for download protection
- **Error Handling**: Sanitized error messages in API responses

### Production Recommendations
- Use strong `SECRET_KEY` in production
- Configure proper CORS origins
- Set up HTTPS with SSL certificates
- Implement API rate limiting
- Use environment-specific database credentials
- Regular security updates for dependencies

## 🚀 Deployment

### Docker Production Deployment
```bash
# Build and deploy
docker compose -f docker/docker-compose.yml up -d

# Scale workers
docker compose -f docker/docker-compose.yml up -d --scale celery_worker=3

# Update application
docker compose -f docker/docker-compose.yml pull
docker compose -f docker/docker-compose.yml up -d
```

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `SPOTIFY_CLIENT_ID` | Spotify API client ID | Required |
| `SPOTIFY_CLIENT_SECRET` | Spotify API client secret | Required |
| `SECRET_KEY` | Application secret key | Required |
| `AUDIO_STORAGE_PATH` | Audio files storage path | `/app/audio` |
| `MAX_AUDIO_CACHE_GB` | Maximum audio cache size | `50` |
| `YTDL_RATE_LIMIT` | yt-dlp download rate limit | `50K` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 🔮 Phase 2 Roadmap

### Planned Features
- **Advanced Mixing Algorithms**: Beat-matched transitions, energy curve optimization
- **Real-time Audio Processing**: Live mixing capabilities
- **User Accounts**: Persistent user sessions and preferences
- **WebSocket Support**: Real-time progress updates
- **Advanced Audio Analysis**: Harmonic content, vocal detection
- **Multiple Audio Sources**: SoundCloud, local file uploads
- **Mix Export**: Generate actual mixed audio files
- **Machine Learning**: AI-powered track compatibility prediction

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Run test suite: `pytest`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open Pull Request

### Code Standards
- **Python**: Follow PEP 8, use Ruff for formatting and linting
- **Type Hints**: Required for all functions
- **Documentation**: Docstrings for all public functions
- **Testing**: Minimum 80% test coverage
- **API**: OpenAPI/Swagger documentation

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues

**Python Version Compatibility**
- This project uses Python 3.12.8 (latest stable version)
- All dependencies are compatible with Python 3.12
- This project includes a `.mise.toml` file that automatically sets Python 3.12.8
- If you have Mise installed, simply run:
  ```bash
  # Install Mise (if not already installed)
  curl https://mise.jdx.dev/install.sh | sh
  
  # Install the specified Python version
  mise install
  
  # Verify version
  python --version
  ```
- Alternative: Use pyenv if you prefer:
  ```bash
  # Install pyenv (macOS)
  brew install pyenv
  
  # Install Python 3.12.8
  pyenv install 3.12.8
  pyenv local 3.12.8
  
  # Verify version
  python --version
  ```

**Docker Compose Command Not Found**
- For newer Docker versions, use `docker compose` (without hyphen)
- For older versions, install `docker-compose` separately
- The startup script automatically detects which command to use

**Spotify Authentication Fails**
- Verify `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`
- Check redirect URI matches Spotify app settings
- Ensure playlist is public or you have access

**Audio Download Fails**
- Check internet connection
- Verify yt-dlp rate limits
- Some tracks may not be available on YouTube

**Database Connection Issues**
- Verify PostgreSQL is running
- Check `DATABASE_URL` format
- Ensure database exists and user has permissions

### Getting Help
- **Documentation**: Check API docs at `/api/v1/docs`
- **Logs**: Check application and worker logs
- **Issues**: Open GitHub issue with error details
- **Health Check**: Use `/health` endpoint for system status

## 📈 Performance

### Expected Performance (Phase 1)
- **Playlist Analysis**: 50 tracks in ~5 minutes
- **Download Success Rate**: 80%+ for popular tracks
- **Concurrent Jobs**: 2-3 simultaneous analyses
- **Storage Efficiency**: ~5MB per track average
- **API Response Time**: <200ms for most endpoints

### Optimization Tips
- Use SSD storage for audio files
- Increase Celery worker concurrency for faster processing
- Configure Redis memory limits appropriately
- Monitor disk space for audio storage
- Regular cleanup of old audio files 