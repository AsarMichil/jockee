# S3 Storage Migration Guide

This guide outlines the migration from local file storage to AWS S3 + CloudFront for the Auto-DJ application.

## Overview

The application has been updated to store audio files in AWS S3 instead of local storage, with CloudFront providing fast global content delivery. This change improves scalability, reliability, and performance.

## Changes Made

### 1. Dependencies Added
- `boto3==1.35.75` - AWS SDK for Python
- `botocore==1.35.75` - Low-level AWS service access

### 2. Configuration Updates
New environment variables added to `env.example`:
```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name
CLOUDFRONT_DOMAIN=your-cloudfront-domain.cloudfront.net
```

### 3. Database Schema Changes
- Added `s3_object_key` column to `tracks` table
- Updated `FileSource` enum to include `S3` option
- Migration file: `a312ec46df43_add_s3_object_key_to_tracks.py`

### 4. New Services

#### S3StorageService (`app/services/s3_storage.py`)
- Handles file uploads to S3
- Generates CloudFront URLs
- Manages S3 file operations (check existence, delete, get info)
- Async operations with proper error handling

#### Updated AudioFetcher (`app/services/audio_fetcher.py`)
- Now uploads downloaded files to S3 after local processing
- Checks S3 first before downloading
- Maintains backward compatibility with local files
- Returns S3 object keys in addition to file paths

#### Updated AudioAnalyzer (`app/services/audio_analysis.py`)
- Added `analyze_track_s3()` method
- Downloads S3 files temporarily for analysis
- Cleans up temporary files after analysis
- Maintains backward compatibility with local files

### 5. API Endpoint Updates

#### Tracks API (`app/api/v1/endpoints/tracks.py`)
- Audio streaming endpoint now redirects to CloudFront for S3 files
- Audio URL endpoint returns CloudFront URLs directly for S3 files
- Maintains backward compatibility for local files
- Enhanced response format with source information

### 6. Background Task Updates

#### Analysis Tasks (`app/workers/analysis_tasks.py`)
- Updated to handle S3 object keys
- Proper counting of S3-stored files
- Uses appropriate analyzer method based on storage type

## Migration Steps

### 1. AWS Setup
1. Create an S3 bucket for audio storage
2. Set up CloudFront distribution pointing to the S3 bucket
3. Create IAM user with appropriate S3 permissions
4. Configure CORS on the S3 bucket if needed

### 2. Environment Configuration
Update your `.env` file with the new AWS configuration variables.

### 3. Database Migration
Run the database migration:
```bash
alembic upgrade head
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Test Integration
Run the test script to verify S3 integration:
```bash
python test_s3_integration.py
```

## Behavior Changes

### File Storage Priority
1. **New downloads**: Files are downloaded locally, then uploaded to S3
2. **Existing files**: S3 files are checked first, then local files (backward compatibility)
3. **Analysis**: S3 files are downloaded temporarily for analysis

### API Responses
- `GET /tracks/{id}/audio/url` now returns CloudFront URLs for S3 files
- Response includes `source` field indicating storage type (`s3` or `local`)
- Enhanced caching headers for better performance

### Background Processing
- Files are uploaded to S3 during the analysis pipeline
- Temporary local files are cleaned up after S3 upload
- Job counting properly handles S3-stored files

## Backward Compatibility

The system maintains full backward compatibility:
- Existing local files continue to work
- API endpoints handle both storage types
- Database supports both file paths and S3 keys
- Analysis works with both storage types

## Performance Benefits

1. **Global CDN**: CloudFront provides fast access worldwide
2. **Scalability**: No local storage limitations
3. **Reliability**: AWS infrastructure with built-in redundancy
4. **Caching**: Long-term caching for better performance

## Monitoring and Maintenance

### Key Metrics to Monitor
- S3 storage usage
- CloudFront cache hit ratio
- API response times
- Failed uploads/downloads

### Maintenance Tasks
- Monitor S3 costs
- Clean up old/unused files
- Update CloudFront cache policies as needed
- Review and rotate AWS credentials

## Troubleshooting

### Common Issues
1. **AWS Credentials**: Ensure credentials have proper S3 permissions
2. **CORS**: Configure S3 bucket CORS for web access if needed
3. **CloudFront**: Allow time for CloudFront distribution deployment
4. **Network**: Ensure outbound HTTPS access to AWS services

### Testing Commands
```bash
# Test S3 integration
python test_s3_integration.py

# Test API endpoints
curl http://localhost:8000/api/v1/tracks/{track_id}/audio/url

# Check database migration
alembic current
```

## Security Considerations

1. **IAM Permissions**: Use least-privilege access for S3
2. **Credentials**: Never commit AWS credentials to version control
3. **HTTPS**: Ensure all CloudFront distributions use HTTPS
4. **Access Logging**: Enable S3 and CloudFront access logging

## Cost Optimization

1. **S3 Storage Classes**: Consider using S3 Intelligent Tiering
2. **CloudFront**: Monitor and optimize cache behaviors
3. **Data Transfer**: Use CloudFront to reduce S3 data transfer costs
4. **Lifecycle Policies**: Set up S3 lifecycle policies for old files 