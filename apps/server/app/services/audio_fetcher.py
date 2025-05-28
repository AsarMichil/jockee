import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import yt_dlp
from app.core.config import settings
from app.models.track import FileSource
import re
import time

logger = logging.getLogger(__name__)


class AudioFetcher:
    """Service for downloading audio files using yt-dlp."""

    def __init__(self):
        self.download_count = 0
        self.last_download_time = 0
        self.rate_limit_delay = 60 / settings.YTDL_MAX_DOWNLOADS_PER_MINUTE

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
            Dict with keys: file_path, file_source, file_size, error
        """
        result = {
            "file_path": None,
            "file_source": FileSource.UNAVAILABLE,
            "file_size": None,
            "error": None,
        }

        try:
            # First check if file exists locally
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

            # Download from YouTube
            return await self._download_from_youtube(artist, title, spotify_id)

        except Exception as e:
            logger.error(f"Error fetching audio for {artist} - {title}: {e}")
            result["error"] = str(e)
            return result

    async def _download_from_youtube(
        self, artist: str, title: str, spotify_id: str
    ) -> Dict[str, Any]:
        """Download audio from YouTube using yt-dlp."""
        result = {
            "file_path": None,
            "file_source": FileSource.UNAVAILABLE,
            "file_size": None,
            "error": None,
        }

        try:
            # Rate limiting
            self._rate_limit()

            file_path = self._get_file_path(artist, title)
            
            # Ensure the directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Search query
            search_query = f"{artist} {title} audio"

            # yt-dlp options - simplified and fixed
            ydl_opts = {
                "format": "bestaudio/best",  # Get best audio quality available
                "outtmpl": str(file_path.parent / f"{file_path.stem}.%(ext)s"),  # Let yt-dlp handle extension
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
            mp3_path = file_path.with_suffix(".mp3")
            if mp3_path.exists() and mp3_path.stat().st_size > 0:
                file_size = mp3_path.stat().st_size
                result.update(
                    {
                        "file_path": str(mp3_path),
                        "file_source": FileSource.YOUTUBE,
                        "file_size": file_size,
                    }
                )
                logger.info(f"Successfully downloaded {artist} - {title} from YouTube")
            else:
                # Also check for other possible extensions that might have been created
                possible_files = list(file_path.parent.glob(f"{file_path.stem}.*"))
                if possible_files:
                    # Found a file, use the first one
                    actual_file = possible_files[0]
                    if actual_file.stat().st_size > 0:
                        file_size = actual_file.stat().st_size
                        result.update(
                            {
                                "file_path": str(actual_file),
                                "file_source": FileSource.YOUTUBE,
                                "file_size": file_size,
                            }
                        )
                        logger.info(f"Successfully downloaded {artist} - {title} from YouTube (as {actual_file.suffix})")
                    else:
                        result["error"] = "Download completed but file is empty"
                        logger.warning(f"Download failed for {artist} - {title}: file is empty")
                else:
                    result["error"] = "Download completed but file not found or empty"
                    logger.warning(f"Download failed for {artist} - {title}: file not found")

        except Exception as e:
            logger.error(f"Error downloading from YouTube for {artist} - {title}: {e}")
            result["error"] = str(e)

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
