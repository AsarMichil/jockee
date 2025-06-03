import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import asyncio
from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.track import Track, FileSource
from app.models.job import AnalysisJob, JobStatus
from app.core.spotify import SpotifyClient
from app.services.audio_fetcher import AudioFetcher
from app.services.audio_analysis import AudioAnalyzer
from app.services.mix_generator import MixGenerator
from app.schemas.track import TrackCreate

logger = logging.getLogger(__name__)


def get_db_session():
    """Get database session for tasks."""
    return SessionLocal()


@celery_app.task(bind=True)
def analyze_playlist_task(self, job_id: str, spotify_access_token: str):
    """
    Celery task to analyze a playlist.

    Args:
        job_id: UUID of the analysis job
        spotify_access_token: Spotify access token for API calls
    """
    # Run the async function in the event loop
    return asyncio.run(_analyze_playlist_async(self, job_id, spotify_access_token))


async def _analyze_playlist_async(task, job_id: str, spotify_access_token: str):
    """Async implementation of playlist analysis."""
    db = get_db_session()

    try:
        # Get the job
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Update job status
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        db.commit()

        logger.info(f"Starting playlist analysis for job {job_id}")

        # Initialize services
        spotify_client = SpotifyClient(access_token=spotify_access_token)
        audio_fetcher = AudioFetcher()
        audio_analyzer = AudioAnalyzer()
        mix_generator = MixGenerator()

        # Extract playlist ID
        playlist_id = spotify_client.extract_playlist_id(job.playlist_url)
        if not playlist_id:
            raise ValueError(
                f"Could not extract playlist ID from URL: {job.playlist_url}"
            )

        # Get playlist info
        playlist_info = spotify_client.get_playlist_info(playlist_id)
        job.playlist_id = playlist_id
        job.playlist_name = playlist_info["name"]

        # Get playlist tracks
        spotify_tracks = spotify_client.get_playlist_tracks(playlist_id)

        # Apply max tracks limit if specified
        options = job.options or {}
        max_tracks = options.get("max_tracks", 50)
        if len(spotify_tracks) > max_tracks:
            spotify_tracks = spotify_tracks[:max_tracks]

        job.total_tracks = len(spotify_tracks)
        db.commit()

        logger.info(f"Found {len(spotify_tracks)} tracks in playlist")

        # Process each track
        processed_tracks = []

        for i, spotify_track in enumerate(spotify_tracks):
            try:
                # Update progress
                task.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": len(spotify_tracks),
                        "status": f"Processing {spotify_track['title']} by {spotify_track['artist']}",
                    },
                )

                # Check if track already exists
                existing_track = (
                    db.query(Track)
                    .filter(Track.spotify_id == spotify_track["spotify_id"])
                    .first()
                )

                if existing_track and options.get("skip_analysis_if_exists", False):
                    # Use existing track
                    track = existing_track
                    logger.info(f"Using existing track: {track.title}")
                else:
                    # Create or update track
                    track = await process_single_track(
                        db, spotify_track, audio_fetcher, audio_analyzer, options
                    )

                if track:
                    processed_tracks.append(track)
                    job.analyzed_tracks = len(processed_tracks)

                    # Count downloaded tracks
                    if track.file_source == FileSource.YOUTUBE:
                        job.downloaded_tracks += 1
                    elif track.file_source == FileSource.UNAVAILABLE:
                        job.failed_tracks += 1

                    db.commit()

            except Exception as e:
                logger.error(f"Error processing track {spotify_track['title']}: {e}")
                job.failed_tracks += 1
                db.commit()
                continue

        logger.info(f"Processed {len(processed_tracks)} tracks successfully")

        # Generate mix instructions
        if len(processed_tracks) >= 2:
            logger.info("Generating mix instructions")
            mix_result = mix_generator.generate_mix(processed_tracks, job.id)

            if "error" not in mix_result:
                # Save transitions to database
                for transition_data in mix_result["transitions"]:
                    db.add(transition_data)

                # Save mix result
                job.result = {
                    "total_duration": mix_result["total_duration"],
                    "total_tracks": mix_result["total_tracks"],
                    "metadata": mix_result["metadata"],
                    "playlist_info": playlist_info,
                }

                job.status = JobStatus.COMPLETED
                logger.info(f"Mix generation completed for job {job_id}")
            else:
                job.error_message = mix_result["error"]
                job.status = JobStatus.FAILED
                logger.error(f"Mix generation failed: {mix_result['error']}")
        else:
            job.error_message = "Not enough tracks with analysis data to generate mix"
            job.status = JobStatus.FAILED

        job.completed_at = datetime.utcnow()
        db.commit()

        return {
            "job_id": job_id,
            "status": job.status.value,
            "total_tracks": job.total_tracks,
            "analyzed_tracks": job.analyzed_tracks,
            "downloaded_tracks": job.downloaded_tracks,
            "failed_tracks": job.failed_tracks,
        }

    except Exception as e:
        logger.error(f"Error in playlist analysis task: {e}")

        # Update job with error
        if "job" in locals():
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()

        raise

    finally:
        db.close()


async def process_single_track(
    db: Session,
    spotify_track: Dict[str, Any],
    audio_fetcher: AudioFetcher,
    audio_analyzer: AudioAnalyzer,
    options: Dict[str, Any],
) -> Track:
    """Process a single track: create/update, fetch audio, analyze."""

    # Check if track exists
    track = (
        db.query(Track).filter(Track.spotify_id == spotify_track["spotify_id"]).first()
    )

    if not track:
        # Create new track
        track_data = TrackCreate(
            spotify_id=spotify_track["spotify_id"],
            title=spotify_track["title"],
            artist=spotify_track["artist"],
            album=spotify_track.get("album"),
            duration=spotify_track.get("duration_ms", 0) / 1000
            if spotify_track.get("duration_ms")
            else None,
            duration_ms=spotify_track.get("duration_ms"),
            popularity=spotify_track.get("popularity"),
            preview_url=spotify_track.get("preview_url"),
        )

        track = Track(**track_data.dict())
        db.add(track)
        db.flush()  # Get the ID

    # Fetch audio file if not already available
    if not track.file_path or track.file_source == FileSource.UNAVAILABLE:
        logger.info(f"Fetching audio for {track.title} by {track.artist}")

        fetch_result = await audio_fetcher.fetch_audio(
            track.artist, track.title, track.spotify_id
        )

        if fetch_result["file_path"]:
            track.file_path = fetch_result["file_path"]
            track.file_source = fetch_result["file_source"]
            track.file_size = fetch_result["file_size"]
        else:
            track.file_source = FileSource.UNAVAILABLE
            if fetch_result.get("error"):
                logger.warning(f"Failed to fetch audio: {fetch_result['error']}")

    # Analyze audio if we have a file and no analysis yet
    skip_analysis_if_exists = options.get("skip_analysis_if_exists", False)
    should_analyze = track.file_path and (not track.analyzed_at or not skip_analysis_if_exists)
    
    if should_analyze:
        logger.info(f"Analyzing audio for {track.title}")

        analysis_result = await audio_analyzer.analyze_track(track.file_path)

        if not analysis_result.get("analysis_error"):
            # Update track with all analysis results from librosa
            track.bpm = analysis_result.get("bpm")
            track.key = analysis_result.get("key")
            track.energy = float(analysis_result.get("energy")) if analysis_result.get("energy") is not None else None
            track.danceability = float(analysis_result.get("danceability")) if analysis_result.get("danceability") is not None else None
            track.valence = float(analysis_result.get("valence")) if analysis_result.get("valence") is not None else None
            track.acousticness = float(analysis_result.get("acousticness")) if analysis_result.get("acousticness") is not None else None
            track.instrumentalness = float(analysis_result.get("instrumentalness")) if analysis_result.get("instrumentalness") is not None else None
            track.liveness = float(analysis_result.get("liveness")) if analysis_result.get("liveness") is not None else None
            track.speechiness = float(analysis_result.get("speechiness")) if analysis_result.get("speechiness") is not None else None
            track.loudness = float(analysis_result.get("loudness")) if analysis_result.get("loudness") is not None else None
            
            # Beat analysis results
            track.beat_timestamps = analysis_result.get("beat_timestamps")
            track.beat_intervals = analysis_result.get("beat_intervals")
            track.beat_confidence = float(analysis_result.get("beat_confidence")) if analysis_result.get("beat_confidence") is not None else None
            track.beat_confidence_scores = analysis_result.get("beat_confidence_scores")
            track.beat_regularity = float(analysis_result.get("beat_regularity")) if analysis_result.get("beat_regularity") is not None else None
            track.average_beat_interval = float(analysis_result.get("average_beat_interval")) if analysis_result.get("average_beat_interval") is not None else None
            
            track.analysis_version = analysis_result["analysis_version"]
            track.analyzed_at = analysis_result["analyzed_at"]
        else:
            track.analysis_error = analysis_result["analysis_error"]
            logger.warning(f"Analysis failed for {track.title}: {track.analysis_error}")
    elif track.analyzed_at and skip_analysis_if_exists:
        logger.info(f"Skipping analysis for {track.title} - already analyzed")

    db.commit()
    return track


@celery_app.task
def cleanup_old_files_task():
    """Periodic task to clean up old audio files."""
    try:
        audio_fetcher = AudioFetcher()
        deleted_count = audio_fetcher.cleanup_old_files(max_age_days=30)

        logger.info(f"Cleaned up {deleted_count} old audio files")

        # Get storage usage
        usage = audio_fetcher.get_storage_usage()
        logger.info(
            f"Current storage usage: {usage['usage_gb']:.2f} GB ({usage['file_count']} files)"
        )

        return {
            "deleted_files": deleted_count,
            "storage_usage_gb": usage["usage_gb"],
            "total_files": usage["file_count"],
        }

    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        raise


@celery_app.task
def health_check_task():
    """Health check task for monitoring."""
    try:
        # Test database connection
        db = get_db_session()
        db.execute("SELECT 1")
        db.close()

        # Test audio storage
        audio_fetcher = AudioFetcher()
        usage = audio_fetcher.get_storage_usage()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "storage_usage_gb": usage["usage_gb"],
            "storage_files": usage["file_count"],
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
