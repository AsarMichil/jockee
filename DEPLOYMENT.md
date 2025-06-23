# 🚀 Auto-DJ Server Deployment Guide

This guide covers both development and production deployment for the Auto-DJ Server.

## 📋 Overview

- **Development**: Local setup with Docker services
- **Production**: Render deployment with Blueprint (Infrastructure as Code)

## 🛠️ Development Setup

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Node.js/bun (for turbo workspace)

### Quick Start

1. **From the project root** (recommended):
   ```bash
   turbo run dev
   ```
   This starts all services: landing page, jockee frontend, and server.

2. **From the server directory only**:
   ```bash
   cd apps/server
   bun run dev
   ```

### What the dev script does:

1. ✅ Checks if Docker is available and running
2. 🚀 Starts PostgreSQL and Redis via Docker Compose (if needed)
3. ⏳ Waits for services to be healthy
4. 🎵 Starts the FastAPI server with hot reload

### Development URLs

- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/v1/docs
- **Health Check**: http://localhost:8000/health

### Additional Dev Commands

```bash
# Start only the API server (requires running services)
bun run dev:api

# Start Celery worker separately
bun run dev:worker

# Start Celery beat scheduler
bun run dev:beat

# Docker service management
bun run docker:up      # Start all Docker services
bun run docker:down    # Stop all Docker services
bun run docker:logs    # View service logs
```

## 🌐 Production Deployment (Render)

### Prerequisites

1. **Render Account**: [Sign up at render.com](https://render.com)
2. **Supabase Database**: Already set up ✅
3. **AWS S3 + CloudFront**: For audio file storage
4. **Spotify Developer App**: For Spotify integration

### Deployment Steps

#### 1. Prepare Environment Variables

Copy `apps/server/env.production` and update the values:

```bash
cd apps/server
cp env.production .env.production.local
# Edit .env.production.local with your actual values
```

#### 2. Run Deployment Check

```bash
cd apps/server
bun run deploy
```

This script will:
- ✅ Validate your `render.yaml` blueprint
- ✅ Check git status (uncommitted changes)
- 📋 Show deployment instructions
- 🔐 List required environment variables

#### 3. Deploy to Render

1. **Go to [Render Dashboard](https://dashboard.render.com)**
2. **Click "New" → "Blueprint"**
3. **Connect your repository** (if not already connected)
4. **Select your repository** - it will detect the `render.yaml` file
5. **Review the services** that will be created:
   - `autodj-redis` - Redis service for caching and Celery
   - `autodj-api` - FastAPI web service
   - `autodj-celery-worker` - Background worker for audio processing

#### 4. Set Environment Variables

In the Render Blueprint creation form, set these **required** variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret (64+ chars) | Generate with Python: `secrets.token_urlsafe(64)` |
| `DATABASE_URL` | Supabase connection string | `postgresql://postgres.xyz:[PASSWORD]@...` |
| `SPOTIFY_CLIENT_ID` | From Spotify Developer Dashboard | `abc123...` |
| `SPOTIFY_CLIENT_SECRET` | From Spotify Developer Dashboard | `def456...` |
| `SPOTIFY_REDIRECT_URI` | Your app's callback URL | `https://your-app.onrender.com/api/v1/auth/spotify/callback` |
| `AWS_ACCESS_KEY_ID` | AWS access key for S3 | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `abc123...` |
| `S3_BUCKET_NAME` | Your S3 bucket name | `autodj-audio-files` |
| `CLOUDFRONT_DOMAIN` | CloudFront distribution domain | `d123456abcdef8.cloudfront.net` |
| `CORS_ORIGINS` | Allowed frontend domains | `https://yourfrontend.com,https://your-app.onrender.com` |

#### 5. Deploy!

Click **"Apply"** to start the deployment. Render will:
1. Create the Redis service
2. Build and deploy the API service
3. Build and deploy the Celery worker
4. Run health checks

#### 6. Verify Deployment

After deployment completes:

1. **Check the API**: `https://your-app-name.onrender.com/health`
2. **View API docs**: `https://your-app-name.onrender.com/api/v1/docs`
3. **Monitor logs** in the Render Dashboard

## 🏗️ Architecture

### Development (Local)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI API   │    │  Celery Worker  │    │  Docker Services│
│  (Port 8000)    │    │  (Background)   │    │                 │
│                 │    │                 │    │  PostgreSQL     │
│                 │◄───┤                 │◄───┤  Redis          │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Production (Render)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Service   │    │ Background Work │    │  Redis Service  │
│   (autodj-api)  │    │(autodj-worker)  │    │(autodj-redis)   │
│                 │    │                 │    │                 │
│                 │◄───┤                 │◄───┤                 │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              
         ▼                                              
┌─────────────────┐                                     
│ Supabase (DB)   │                                     
│ AWS S3 Storage  │                                     
└─────────────────┘                                     
```

## 🔧 Configuration

### Environment-Specific Settings

The app automatically adjusts based on the `ENVIRONMENT` variable:

| Environment | Debug | Log Level | Features |
|-------------|-------|-----------|----------|
| `development` | `true` | `DEBUG` | Hot reload, verbose logging |
| `production` | `false` | `INFO` | Optimized for performance |

### Service Configuration

- **API**: Runs on port specified by `PORT` (Render sets this automatically)
- **Worker**: Configured for production with concurrency=1 (free tier optimization)
- **Redis**: Managed by Render with automatic connection strings

## 🛡️ Security Considerations

1. **Secret Key**: Use a strong, randomly generated secret key
2. **Database**: Use connection pooling (Supabase handles this)
3. **CORS**: Restrict to your actual frontend domains
4. **Rate Limiting**: Configure appropriate limits for yt-dlp

## 📊 Monitoring

### Health Checks

- **API Health**: `GET /health`
- **Render Dashboard**: Monitor all services
- **Logs**: Available in Render Dashboard

### Performance

- **Free Tier Limitations**: 
  - Services may sleep after inactivity
  - Limited resources (512MB RAM)
  - No persistent storage for audio files (use S3)

## 🚨 Troubleshooting

### Development Issues

**Docker services won't start:**
```bash
# Check Docker status
docker info

# Reset Docker services
bun run docker:down
bun run docker:up

# If you get "container name already in use" errors:
bun run docker:clean  # Nuclear option - removes everything
```

**Container naming conflicts:**
```bash
# Remove specific conflicting containers
docker rm -f autodj-postgres autodj-redis

# Or clean everything and start fresh
bun run docker:clean && bun run docker:up
```

**Port conflicts:**
```bash
# Check what's using port 8000
lsof -i :8000

# Use a different port
PORT=8001 bun run dev:api
```

### Production Issues

**Deployment fails:**
1. Check environment variables are set correctly
2. Verify `render.yaml` syntax
3. Check build logs in Render Dashboard

**Services unhealthy:**
1. Check environment variables
2. Verify database connection string
3. Monitor service logs

## 📚 Additional Resources

- [Render Blueprints Documentation](https://render.com/docs/infrastructure-as-code)
- [FastAPI Deployment Guide](https://render.com/docs/deploy-fastapi)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Supabase Connection Strings](https://supabase.com/docs/guides/database/connecting-to-postgres)

---

## 🎯 Quick Reference

### Development Commands
```bash
# Start everything
turbo run dev                    # From project root
bun run dev                      # From apps/server

# Individual services
bun run dev:api                  # FastAPI server only
bun run dev:worker              # Celery worker only
bun run dev:beat                # Celery beat scheduler
```

### Production Commands
```bash
bun run deploy                   # Check deployment readiness
# Then deploy via Render Dashboard
```

### Docker Commands
```bash
bun run docker:up               # Start services
bun run docker:down             # Stop services  
bun run docker:logs             # View logs
bun run docker:clean            # Clean everything (containers, images, volumes)
``` 