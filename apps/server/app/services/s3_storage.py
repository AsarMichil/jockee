import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from app.core.config import settings
import uuid
import os
import tempfile

logger = logging.getLogger(__name__)


class S3StorageService:
    """Service for handling S3 file uploads and CloudFront URL generation."""

    def __init__(self):
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.bucket_name = settings.S3_BUCKET_NAME
            self.cloudfront_domain = settings.CLOUDFRONT_DOMAIN
        except NoCredentialsError:
            logger.error("AWS credentials not configured")
            raise Exception("AWS credentials not configured")

    def generate_s3_key(self, artist: str, title: str, file_extension: str = "mp3") -> str:
        """Generate a unique S3 object key for the audio file."""
        # Sanitize artist and title for S3 key
        artist_clean = self._sanitize_for_s3_key(artist)
        title_clean = self._sanitize_for_s3_key(title)
        
        # Add a UUID to ensure uniqueness
        unique_id = str(uuid.uuid4())[:8]
        
        return f"audio/{artist_clean}/{title_clean}_{unique_id}.{file_extension}"

    def _sanitize_for_s3_key(self, text: str) -> str:
        """Sanitize text for use in S3 object keys."""
        # Replace spaces and special characters with underscores
        import re
        sanitized = re.sub(r'[^\w\-_.]', '_', text)
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        return sanitized.strip('_')

    async def upload_file(self, file_path: str, s3_key: str) -> Dict[str, Any]:
        """
        Upload a file to S3.
        
        Returns:
            Dict with keys: success, s3_key, file_size, error
        """
        result = {
            "success": False,
            "s3_key": None,
            "file_size": None,
            "error": None
        }

        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                result["error"] = f"File not found: {file_path}"
                return result

            file_size = file_path_obj.stat().st_size
            
            # Upload file to S3 with metadata
            extra_args = {
                'ContentType': 'audio/mpeg',
                'CacheControl': 'public, max-age=31536000',  # Cache for 1 year
                'Metadata': {
                    'uploaded-by': 'auto-dj-backend',
                    'file-type': 'audio'
                }
            }

            # Run the upload in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._upload_file_sync,
                file_path,
                s3_key,
                extra_args
            )

            result.update({
                "success": True,
                "s3_key": s3_key,
                "file_size": file_size
            })
            
            logger.info(f"Successfully uploaded file to S3: {s3_key}")

        except ClientError as e:
            error_msg = f"AWS S3 error uploading {s3_key}: {e}"
            logger.error(error_msg)
            result["error"] = error_msg
        except Exception as e:
            error_msg = f"Unexpected error uploading {s3_key}: {e}"
            logger.error(error_msg)
            result["error"] = error_msg

        return result

    def _upload_file_sync(self, file_path: str, s3_key: str, extra_args: Dict):
        """Synchronous S3 upload (to be run in executor)."""
        self.s3_client.upload_file(file_path, self.bucket_name, s3_key, ExtraArgs=extra_args)

    def generate_cloudfront_url(self, s3_key: str) -> str:
        """
        Generate a CloudFront URL for the given S3 object key.
        
        Args:
            s3_key: The S3 object key
            
        Returns:
            The CloudFront URL
        """
        return f"https://{self.cloudfront_domain}/{s3_key}"

    async def file_exists(self, s3_key: str) -> bool:
        """Check if a file exists in S3."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._file_exists_sync,
                s3_key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"Error checking if S3 file exists {s3_key}: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error checking S3 file {s3_key}: {e}")
            return False

    def _file_exists_sync(self, s3_key: str):
        """Synchronous S3 file existence check (to be run in executor)."""
        self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)

    async def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._delete_file_sync,
                s3_key
            )
            logger.info(f"Successfully deleted S3 file: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting S3 file {s3_key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting S3 file {s3_key}: {e}")
            return False

    def _delete_file_sync(self, s3_key: str):
        """Synchronous S3 file deletion (to be run in executor)."""
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)

    async def get_file_info(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Get metadata about a file in S3."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._get_file_info_sync,
                s3_key
            )
            
            return {
                "s3_key": s3_key,
                "file_size": response.get('ContentLength'),
                "last_modified": response.get('LastModified'),
                "content_type": response.get('ContentType'),
                "metadata": response.get('Metadata', {})
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            else:
                logger.error(f"Error getting S3 file info {s3_key}: {e}")
                return None
        except Exception as e:
            logger.error(f"Unexpected error getting S3 file info {s3_key}: {e}")
            return None

    def _get_file_info_sync(self, s3_key: str):
        """Synchronous S3 file info retrieval (to be run in executor)."""
        return self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key) 