import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import yt_dlp
from app.core.config import settings
from app.models.track import FileSource
from app.services.s3_storage import S3StorageService
import re
import time
import subprocess
import tempfile

logger = logging.getLogger(__name__)


class AudioFetcher:
    """Service for downloading audio files using yt-dlp."""

    def __init__(self):
        self.download_count = 0
        self.last_download_time = 0
        self.rate_limit_delay = 60 / settings.YTDL_MAX_DOWNLOADS_PER_MINUTE
        self.s3_storage = S3StorageService()

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        filename = re.sub(r"[^\w\s-]", "", filename)
        filename = re.sub(r"[-\s]+", "-", filename)
        return filename.strip("-")

    def _get_file_path(self, artist: str, title: str) -> Path:
        """Generate file path for audio file."""
        artist_clean = self._sanitize_filename(artist)
        title_clean = self._sanitize_filename(title)

        artist_dir = Path(settings.AUDIO_STORAGE_PATH) / artist_clean
        artist_dir.mkdir(parents=True, exist_ok=True)

        return artist_dir / f"{title_clean}.mp3"

    def _check_local_file(self, artist: str, title: str) -> Optional[str]:
        """Check if audio file exists locally."""
        file_path = self._get_file_path(artist, title)
        if file_path.exists() and file_path.stat().st_size > 0:
            return str(file_path)
        return None

    def _rate_limit(self):
        """Implement rate limiting for downloads."""
        current_time = time.time()
        time_since_last = current_time - self.last_download_time

        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)

        self.last_download_time = time.time()

    async def fetch_audio(
        self, artist: str, title: str, spotify_id: str
    ) -> Dict[str, Any]:
        """
        Fetch audio file for a track.

        Returns:
            Dict with keys: file_path, file_source, file_size, error, s3_object_key
        """
        result = {
            "file_path": None,
            "file_source": FileSource.UNAVAILABLE,
            "file_size": None,
            "s3_object_key": None,
            "error": None,
        }

        try:
            # First check if file exists in S3
            s3_key = self.s3_storage.generate_s3_key(artist, title)
            if await self.s3_storage.file_exists(s3_key):
                file_info = await self.s3_storage.get_file_info(s3_key)
                if file_info:
                    result.update(
                        {
                            "s3_object_key": s3_key,
                            "file_source": FileSource.S3,
                            "file_size": file_info["file_size"],
                        }
                    )
                    logger.info(f"Found S3 file for {artist} - {title}")
                    return result

            # Then check if file exists locally (for backward compatibility)
            local_path = self._check_local_file(artist, title)
            if local_path:
                file_size = Path(local_path).stat().st_size
                result.update(
                    {
                        "file_path": local_path,
                        "file_source": FileSource.LOCAL,
                        "file_size": file_size,
                    }
                )
                logger.info(f"Found local file for {artist} - {title}")
                return result

            # Download from YouTube and upload to S3
            return await self._download_and_upload_to_s3(artist, title, spotify_id)

        except Exception as e:
            logger.error(f"Error fetching audio for {artist} - {title}: {e}")
            result["error"] = str(e)
            return result

    async def _download_and_upload_to_s3(
        self, artist: str, title: str, spotify_id: str
    ) -> Dict[str, Any]:
        """Download audio from YouTube using yt-dlp and upload to S3."""
        result = {
            "file_path": None,
            "file_source": FileSource.UNAVAILABLE,
            "file_size": None,
            "s3_object_key": None,
            "error": None,
        }

        temp_file_path = None
        
        try:
            # Rate limiting
            self._rate_limit()

            # Use temp directory for download
            temp_dir = Path(tempfile.mkdtemp())
            temp_file_path = temp_dir / f"{self._sanitize_filename(artist)}_{self._sanitize_filename(title)}"
            
            # Ensure the directory exists
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Search query
            search_query = f"{artist} {title} audio"

            # yt-dlp options - simplified and fixed
            ydl_opts = {
                "format": "bestaudio/best",  # Get best audio quality available
                "outtmpl": str(temp_file_path.parent / f"{temp_file_path.stem}.%(ext)s"),  # Let yt-dlp handle extension
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }],
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "ratelimit": self._parse_rate_limit(settings.YTDL_RATE_LIMIT),
                "retries": 3,
                "fragment_retries": 3,
                "skip_unavailable_fragments": True,
                "writeinfojson": False,
                "writethumbnail": False,
                "writesubtitles": False,
                "writeautomaticsub": False,
                "ignoreerrors": True,
                "default_search": "ytsearch1:",  # Search YouTube and take first result
            }

            # Run yt-dlp in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, self._download_with_ytdlp, search_query, ydl_opts
            )

            # Check if download was successful
            mp3_path = temp_file_path.with_suffix(".mp3")
            downloaded_file = None
            
            if mp3_path.exists() and mp3_path.stat().st_size > 0:
                downloaded_file = mp3_path
            else:
                # Also check for other possible extensions that might have been created
                possible_files = list(temp_file_path.parent.glob(f"{temp_file_path.stem}.*"))
                if possible_files:
                    # Found a file, use the first one
                    actual_file = possible_files[0]
                    if actual_file.stat().st_size > 0:
                        downloaded_file = actual_file

            if downloaded_file:
                # Normalize the audio for consistent loudness
                normalization_success = self._normalize_audio(downloaded_file)
                if not normalization_success:
                    logger.warning(f"Audio normalization failed for {artist} - {title}, but keeping original file")
                
                # Generate S3 key and upload file
                s3_key = self.s3_storage.generate_s3_key(artist, title)
                upload_result = await self.s3_storage.upload_file(str(downloaded_file), s3_key)
                
                if upload_result["success"]:
                    result.update(
                        {
                            "s3_object_key": s3_key,
                            "file_source": FileSource.S3,
                            "file_size": upload_result["file_size"],
                        }
                    )
                    logger.info(f"Successfully downloaded {artist} - {title} from YouTube and uploaded to S3")
                else:
                    result["error"] = f"Upload to S3 failed: {upload_result['error']}"
                    logger.error(f"Upload to S3 failed for {artist} - {title}: {upload_result['error']}")
            else:
                result["error"] = "Download completed but file not found or empty"
                logger.warning(f"Download failed for {artist} - {title}: file not found")

        except Exception as e:
            logger.error(f"Error downloading from YouTube for {artist} - {title}: {e}")
            result["error"] = str(e)
        finally:
            # Clean up temporary files
            if temp_file_path and temp_file_path.parent.exists():
                try:
                    import shutil
                    shutil.rmtree(temp_file_path.parent)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory: {e}")

        return result

    def _download_with_ytdlp(self, search_query: str, ydl_opts: Dict[str, Any]):
        """Execute yt-dlp download (blocking operation)."""
        try:
            logger.info(f"Starting yt-dlp download for query: {search_query}")
            # logger.debug(f"yt-dlp options: {ydl_opts}")  # Temporarily disabled
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([search_query])
                
            logger.info(f"yt-dlp download completed for query: {search_query}")
            
            # List files in the output directory for debugging - temporarily disabled
            # output_template = ydl_opts.get("outtmpl", "")
            # if output_template:
            #     output_dir = Path(output_template).parent
            #     if output_dir.exists():
            #         files = list(output_dir.iterdir())
            #         logger.debug(f"Files in output directory {output_dir}: {[f.name for f in files]}")
            
        except Exception as e:
            logger.error(f"yt-dlp download failed for query {search_query}: {e}")
            raise

    def _parse_rate_limit(self, rate_limit_str: str) -> int:
        """Parse rate limit string to bytes per second."""
        rate_limit_str = rate_limit_str.upper()
        if rate_limit_str.endswith("K"):
            return int(rate_limit_str[:-1]) * 1024
        elif rate_limit_str.endswith("M"):
            return int(rate_limit_str[:-1]) * 1024 * 1024
        else:
            return int(rate_limit_str)

    def get_storage_usage(self) -> Dict[str, Any]:
        """Get current storage usage statistics."""
        storage_path = Path(settings.AUDIO_STORAGE_PATH)
        if not storage_path.exists():
            return {"total_size": 0, "file_count": 0, "usage_gb": 0.0}

        total_size = 0
        file_count = 0

        for file_path in storage_path.rglob("*.mp3"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1

        usage_gb = total_size / (1024**3)

        return {
            "total_size": total_size,
            "file_count": file_count,
            "usage_gb": round(usage_gb, 2),
            "max_gb": settings.MAX_AUDIO_CACHE_GB,
        }

    def cleanup_old_files(self, max_age_days: int = 30) -> int:
        """Clean up old audio files to manage storage."""
        storage_path = Path(settings.AUDIO_STORAGE_PATH)
        if not storage_path.exists():
            return 0

        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        deleted_count = 0

        for file_path in storage_path.rglob("*.mp3"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting file {file_path}: {e}")

        return deleted_count

    def _normalize_audio(self, file_path: Path) -> bool:
        """
        Normalize audio file to consistent loudness using FFmpeg's loudnorm filter.
        Uses EBU R128 standard with target of -16 LUFS.
        
        Args:
            file_path: Path to the audio file to normalize
            
        Returns:
            bool: True if normalization was successful, False otherwise
        """
        try:
            # Create temporary file for normalized audio
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            
            # FFmpeg command for loudness normalization
            # Target: -16 LUFS (good for music playback)
            # Range: 11 LU (dynamic range)  
            # Threshold: -1.5 dBTP (true peak threshold)
            cmd = [
                'ffmpeg',
                '-i', str(file_path),
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=summary',
                '-ar', '44100',  # Standard sample rate
                '-b:a', '320k',  # High quality bitrate
                '-y',  # Overwrite output file
                str(temp_path)
            ]
            
            logger.info(f"Normalizing audio: {file_path.name}")
            
            # Run FFmpeg normalization
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Check if normalized file was created and has content
                if temp_path.exists() and temp_path.stat().st_size > 0:
                    # Replace original file with normalized version
                    temp_path.replace(file_path)
                    logger.info(f"Successfully normalized audio: {file_path.name}")
                    return True
                else:
                    logger.warning(f"Normalization produced empty file for: {file_path.name}")
                    # Clean up empty temp file
                    if temp_path.exists():
                        temp_path.unlink()
                    return False
            else:
                logger.warning(f"FFmpeg normalization failed for {file_path.name}: {result.stderr}")
                # Clean up temp file
                if temp_path.exists():
                    temp_path.unlink()
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Normalization timeout for {file_path.name}")
            if temp_path.exists():
                temp_path.unlink()
            return False
        except Exception as e:
            logger.error(f"Error normalizing audio {file_path.name}: {e}")
            if 'temp_path' in locals() and temp_path.exists():
                temp_path.unlink()
            return False
