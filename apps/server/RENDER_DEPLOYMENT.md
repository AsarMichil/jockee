# Render Deployment Guide for Auto-DJ Backend

This guide will help you deploy your Auto-DJ Backend to Render.com.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **Git Repository**: Your code must be in a GitHub/GitLab/Bitbucket repository
3. **External Services**:
   - AWS S3 bucket for audio file storage
   - Spotify Developer Account for API credentials

## Step 1: Create Required Services on Render

### 1.1 Create PostgreSQL Database
1. In Render Dashboard, click **New > PostgreSQL**
2. Name it: `auto-dj-database`
3. Choose a plan (Free tier available)
4. Create the database and note the connection details

### 1.2 Create Redis Instance
1. In Render Dashboard, click **New > Redis**
2. Name it: `auto-dj-redis`
3. Choose a plan (Free tier available)
4. Create the instance and note the connection details

## Step 2: Prepare External Services

### 2.1 AWS S3 Setup
1. Create an S3 bucket for audio file storage
2. Create an IAM user with S3 permissions
3. Optionally set up CloudFront for faster access
4. Note your AWS credentials and bucket details

### 2.2 Spotify API Setup
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Add redirect URI: `https://your-app-name.onrender.com/api/v1/auth/spotify/callback`
4. Note your Client ID and Client Secret

## Step 3: Deploy Web Service

### 3.1 Create Web Service
1. In Render Dashboard, click **New > Web Service**
2. Connect your GitHub/GitLab/Bitbucket repository
3. Configure the service:
   - **Name**: `auto-dj-backend` (or your preferred name)
   - **Language**: `Docker`
   - **Branch**: `main` (or your deployment branch)
   - **Root Directory**: `apps/server`
   - **Build Command**: `./render-build.sh`
   - **Start Command**: (leave empty - Docker will handle this)

### 3.2 Configure Environment Variables

Add these environment variables in the Render service settings:

#### Core Settings
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
```

#### Security
```bash
SECRET_KEY=generate-a-strong-random-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### Database (from your Render PostgreSQL)
```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

#### Redis (from your Render Redis)
```bash
REDIS_URL=redis://user:password@host:port
CELERY_BROKER_URL=redis://user:password@host:port
CELERY_RESULT_BACKEND=redis://user:password@host:port
```

#### Spotify API
```bash
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=https://your-app-name.onrender.com/api/v1/auth/spotify/callback
```

#### AWS S3
```bash
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name
CLOUDFRONT_DOMAIN=your-cloudfront-domain.cloudfront.net
```

#### Audio Processing
```bash
AUDIO_STORAGE_PATH=/tmp/audio
MAX_AUDIO_CACHE_GB=5
YTDL_RATE_LIMIT=1M
YTDL_MAX_DOWNLOADS_PER_MINUTE=30
```

#### CORS
```bash
CORS_ORIGINS=https://your-frontend-domain.com,https://your-app-name.onrender.com
```

### 3.3 Deploy
1. Click **Create Web Service**
2. Render will start building and deploying your application
3. Monitor the build logs for any issues

## Step 4: Background Workers (Celery)

Since Render doesn't natively support background workers with the Free tier, you have options:

### Option A: Background Worker Service (Paid Plans)
1. Create another web service for the Celery worker
2. Use the same repository and environment variables
3. Set the start command to: `celery -A app.workers.celery_app worker --loglevel=info`

### Option B: Combined Service (Free Tier)
The current setup runs everything in one container, which works for basic usage but may have limitations under heavy load.

## Step 5: Post-Deployment

### 5.1 Verify Deployment
1. Visit your service URL: `https://your-app-name.onrender.com`
2. Check health endpoint: `https://your-app-name.onrender.com/health`
3. Access API docs: `https://your-app-name.onrender.com/api/v1/docs`

### 5.2 Update Spotify Redirect URI
1. Go back to your Spotify app settings
2. Update the redirect URI with your actual Render URL
3. Save the changes

### 5.3 Test Functionality
1. Try the Spotify authentication flow
2. Submit a test playlist for analysis
3. Monitor the logs for any errors

## Important Considerations

### File Storage
- Render's filesystem is **ephemeral** - files are lost on restart/redeploy
- Your app is configured to use AWS S3 for persistent audio storage
- The `/tmp/audio` directory is only for temporary processing

### Database Migrations
- The build script automatically runs database migrations
- Make sure your DATABASE_URL is set before deployment

### Health Checks
- Your app includes a `/health` endpoint that checks database and Redis connectivity
- Render uses this for health monitoring

### Performance
- Free tier services sleep after 15 minutes of inactivity
- Consider upgrading to a paid plan for production use
- Monitor resource usage and scale as needed

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check that all environment variables are set
   - Verify the build script permissions: `chmod +x render-build.sh`
   - Review build logs for specific errors

2. **Database Connection Issues**
   - Verify DATABASE_URL format and credentials
   - Ensure the PostgreSQL service is running
   - Check network connectivity between services

3. **Redis Connection Issues**
   - Verify REDIS_URL format and credentials
   - Ensure the Redis service is running
   - Check that Celery environment variables match

4. **Spotify Authentication Fails**
   - Verify redirect URI exactly matches the one in Spotify settings
   - Check CLIENT_ID and CLIENT_SECRET are correct
   - Ensure the service URL is accessible

### Getting Help
- Check Render service logs in the dashboard
- Monitor the health endpoint for service status
- Review Render documentation for platform-specific issues

## Next Steps

1. Set up monitoring and alerts
2. Configure custom domain (if needed)
3. Set up CI/CD for automatic deployments
4. Consider implementing rate limiting for production
5. Set up backup strategies for your database 