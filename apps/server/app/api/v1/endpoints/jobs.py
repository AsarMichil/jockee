from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.session import get_db
from app.api.v1.dependencies import get_spotify_client, get_spotify_access_token
from app.core.spotify import SpotifyClient
from app.models.job import AnalysisJob, JobStatus
from app.schemas.job import (
    PlaylistAnalysisRequest,
    JobStatusResponse,
    JobResultResponse,
    AnalysisJobCreate,
    AnalysisJob as AnalysisJobSchema,
)
from app.workers.analysis_tasks import analyze_playlist_task
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze", response_model=JobStatusResponse)
async def analyze_playlist(
    request_data: PlaylistAnalysisRequest,
    request: Request,
    db: Session = Depends(get_db),
    spotify_client: SpotifyClient = Depends(get_spotify_client),
    spotify_token: str = Depends(get_spotify_access_token),
):
    """
    Submit a playlist for analysis.

    This endpoint:
    1. Validates the Spotify playlist URL
    2. Creates an analysis job
    3. Starts background processing
    4. Returns job status for tracking
    """
    try:
        # Validate playlist URL and extract ID
        playlist_id = spotify_client.extract_playlist_id(
            request_data.spotify_playlist_url
        )
        if not playlist_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid Spotify playlist URL. Please provide a valid Spotify playlist link.",
            )

        # Check if playlist exists and is accessible
        try:
            playlist_info = spotify_client.get_playlist_info(playlist_id)
        except Exception as e:
            logger.error(f"Error accessing playlist {playlist_id}: {e}")
            raise HTTPException(
                status_code=400,
                detail="Unable to access playlist. Please check the URL and ensure the playlist is public or you have access.",
            )

        # Check if there's already a recent job for this playlist
        existing_job = (
            db.query(AnalysisJob)
            .filter(
                AnalysisJob.playlist_url == request_data.spotify_playlist_url,
                AnalysisJob.status.in_([JobStatus.PENDING, JobStatus.PROCESSING]),
            )
            .first()
        )

        if existing_job:
            logger.info(f"Found existing job {existing_job.id} for playlist")
            return JobStatusResponse(
                id=existing_job.id,
                status=existing_job.status,
                total_tracks=existing_job.total_tracks,
                analyzed_tracks=existing_job.analyzed_tracks,
                downloaded_tracks=existing_job.downloaded_tracks,
                failed_tracks=existing_job.failed_tracks,
                progress_percentage=_calculate_progress(existing_job),
                error_message=existing_job.error_message,
                created_at=existing_job.created_at,
                updated_at=existing_job.updated_at,
                started_at=existing_job.started_at,
                completed_at=existing_job.completed_at,
            )

        # Create new analysis job
        job_data = AnalysisJobCreate(
            playlist_url=request_data.spotify_playlist_url,
            playlist_id=playlist_id,
            playlist_name=playlist_info["name"],
            options=request_data.options.model_dump() if request_data.options else {},
        )

        job = AnalysisJob(**job_data.model_dump())
        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(
            f"Created analysis job {job.id} for playlist '{playlist_info['name']}'"
        )

        # Start background task
        task = analyze_playlist_task.delay(str(job.id), spotify_token)

        # Store task ID for potential cancellation
        job.options = job.options or {}
        job.options["celery_task_id"] = task.id
        db.commit()

        logger.info(f"Started background analysis task {task.id} for job {job.id}")

        return JobStatusResponse(
            id=job.id,
            status=job.status,
            total_tracks=job.total_tracks,
            analyzed_tracks=job.analyzed_tracks,
            downloaded_tracks=job.downloaded_tracks,
            failed_tracks=job.failed_tracks,
            progress_percentage=0.0,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating playlist analysis job: {e}")
        raise HTTPException(status_code=500, detail="Failed to start playlist analysis")


@router.get("/", response_model=List[AnalysisJobSchema])
async def get_user_jobs(
    request: Request,
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    db: Session = Depends(get_db),
):
    """
    Get user's analysis jobs.
    
    Since we're using session-based auth without user accounts,
    we'll return all jobs for now. In a future version with user accounts,
    this would filter by user_id.
    """
    try:
        query = db.query(AnalysisJob)
        
        # Filter by status if provided
        if status:
            query = query.filter(AnalysisJob.status == status)
        
        # Order by creation date (newest first)
        query = query.order_by(AnalysisJob.created_at.desc())
        
        # Apply pagination
        jobs = query.offset(offset).limit(limit).all()
        
        return jobs
        
    except Exception as e:
        logger.error(f"Error fetching user jobs: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch analysis jobs"
        )


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Get the status of an analysis job.
    """
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobStatusResponse(
            id=job.id,
            status=job.status,
            total_tracks=job.total_tracks,
            analyzed_tracks=job.analyzed_tracks,
            downloaded_tracks=job.downloaded_tracks,
            failed_tracks=job.failed_tracks,
            progress_percentage=_calculate_progress(job),
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job status")


@router.get("/{job_id}/results", response_model=JobResultResponse)
async def get_job_results(job_id: str, db: Session = Depends(get_db)):
    """
    Get the results of a completed analysis job.
    """
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status == JobStatus.PENDING:
            raise HTTPException(status_code=202, detail="Job is still pending")

        if job.status == JobStatus.PROCESSING:
            raise HTTPException(status_code=202, detail="Job is still processing")

        if job.status == JobStatus.FAILED:
            return JobResultResponse(
                id=job.id,
                status=job.status,
                playlist_url=job.playlist_url,
                playlist_name=job.playlist_name,
                total_tracks=job.total_tracks,
                analyzed_tracks=job.analyzed_tracks,
                downloaded_tracks=job.downloaded_tracks,
                failed_tracks=job.failed_tracks,
                tracks=[],  # Empty tracks array for failed jobs
                mix_instructions=None,
                error_message=job.error_message,
                created_at=job.created_at,
                completed_at=job.completed_at,
            )

        # Job completed successfully
        mix_instructions = None
        all_tracks = []
        
        if job.result and hasattr(job, 'transitions') and job.transitions:
            # Build mix instructions from stored data
            from app.schemas.job import MixInstructions, MixTransitionResponse
            from app.schemas.track import TrackSummary

            transitions = []
            # Keep track of unique tracks by ID to avoid duplicates
            track_ids_seen = set()
            
            for transition in job.transitions:
                track_a_summary = TrackSummary(
                    id=transition.track_a.id,
                    spotify_id=transition.track_a.spotify_id,
                    title=transition.track_a.title,
                    artist=transition.track_a.artist,
                    duration=transition.track_a.duration,
                    file_source=transition.track_a.file_source,
                    bpm=transition.track_a.bpm,
                    key=transition.track_a.key,
                    energy=transition.track_a.energy,
                    beat_timestamps=transition.track_a.beat_timestamps,
                    beat_intervals=transition.track_a.beat_intervals,
                    beat_confidence=transition.track_a.beat_confidence,
                    beat_confidence_scores=transition.track_a.beat_confidence_scores,
                    beat_regularity=transition.track_a.beat_regularity,
                    average_beat_interval=transition.track_a.average_beat_interval,
                    # Enhanced analysis fields
                    dominant_style=transition.track_a.dominant_style,
                    style_scores=transition.track_a.style_scores,
                    style_confidence=transition.track_a.style_confidence,
                    mix_in_point=transition.track_a.mix_in_point,
                    mix_out_point=transition.track_a.mix_out_point,
                    mixable_sections=transition.track_a.mixable_sections,
                    intro_end=transition.track_a.intro_end,
                    outro_start=transition.track_a.outro_start,
                    intro_energy=transition.track_a.intro_energy,
                    outro_energy=transition.track_a.outro_energy,
                    energy_profile=transition.track_a.energy_profile,
                    vocal_sections=transition.track_a.vocal_sections,
                    instrumental_sections=transition.track_a.instrumental_sections,
                )

                track_b_summary = TrackSummary(
                    id=transition.track_b.id,
                    spotify_id=transition.track_b.spotify_id,
                    title=transition.track_b.title,
                    artist=transition.track_b.artist,
                    duration=transition.track_b.duration,
                    file_source=transition.track_b.file_source,
                    bpm=transition.track_b.bpm,
                    key=transition.track_b.key,
                    energy=transition.track_b.energy,
                    beat_timestamps=transition.track_b.beat_timestamps,
                    beat_intervals=transition.track_b.beat_intervals,
                    beat_confidence=transition.track_b.beat_confidence,
                    beat_confidence_scores=transition.track_b.beat_confidence_scores,
                    beat_regularity=transition.track_b.beat_regularity,
                    average_beat_interval=transition.track_b.average_beat_interval,
                    # Enhanced analysis fields
                    dominant_style=transition.track_b.dominant_style,
                    style_scores=transition.track_b.style_scores,
                    style_confidence=transition.track_b.style_confidence,
                    mix_in_point=transition.track_b.mix_in_point,
                    mix_out_point=transition.track_b.mix_out_point,
                    mixable_sections=transition.track_b.mixable_sections,
                    intro_end=transition.track_b.intro_end,
                    outro_start=transition.track_b.outro_start,
                    intro_energy=transition.track_b.intro_energy,
                    outro_energy=transition.track_b.outro_energy,
                    energy_profile=transition.track_b.energy_profile,
                    vocal_sections=transition.track_b.vocal_sections,
                    instrumental_sections=transition.track_b.instrumental_sections,
                )

                # Add tracks to the unique tracks list
                if transition.track_a.id not in track_ids_seen:
                    all_tracks.append(track_a_summary)
                    track_ids_seen.add(transition.track_a.id)
                
                if transition.track_b.id not in track_ids_seen:
                    all_tracks.append(track_b_summary)
                    track_ids_seen.add(transition.track_b.id)

                transition_response = MixTransitionResponse(
                    id=transition.id,
                    position=transition.position,
                    track_a=track_a_summary,
                    track_b=track_b_summary,
                    transition_start=transition.transition_start,
                    transition_duration=transition.transition_duration,
                    technique=transition.technique,
                    bpm_adjustment=transition.bpm_adjustment,
                    bpm_compatibility=transition.bpm_compatibility,
                    key_compatibility=transition.key_compatibility,
                    energy_compatibility=transition.energy_compatibility,
                    overall_score=transition.overall_score,
                    metadata=transition.mix_metadata,
                )

                transitions.append(transition_response)

            mix_instructions = MixInstructions(
                total_duration=job.result.get("total_duration", 0),
                total_tracks=job.result.get("total_tracks", 0),
                transitions=transitions,
                metadata=job.result.get("metadata", {}),
            )

        return JobResultResponse(
            id=job.id,
            status=job.status,
            playlist_url=job.playlist_url,
            playlist_name=job.playlist_name,
            total_tracks=job.total_tracks,
            analyzed_tracks=job.analyzed_tracks,
            downloaded_tracks=job.downloaded_tracks,
            failed_tracks=job.failed_tracks,
            tracks=all_tracks,
            mix_instructions=mix_instructions,
            error_message=job.error_message,
            created_at=job.created_at,
            completed_at=job.completed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job results: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job results")


@router.delete("/{job_id}")
async def cancel_job(job_id: str, db: Session = Depends(get_db)):
    """
    Cancel a running analysis job.
    """
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
            raise HTTPException(status_code=400, detail="Job cannot be cancelled")

        # Try to revoke Celery task
        if job.options and job.options.get("celery_task_id"):
            try:
                from app.workers.celery_app import celery_app
                celery_app.control.revoke(job.options["celery_task_id"], terminate=True)
            except Exception as e:
                logger.warning(f"Failed to revoke Celery task: {e}")

        # Update job status
        job.status = JobStatus.FAILED
        job.error_message = "Job cancelled by user"
        job.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Cancelled job {job_id}")

        return {"message": "Job cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel job")


@router.get("/{job_id}/mix")
async def get_mix_instructions(job_id: str, db: Session = Depends(get_db)):
    """
    Get mix instructions for a completed job.
    This is an alias for the results endpoint that returns just the mix instructions.
    """
    try:
        job_result = await get_job_results(job_id, db)
        
        if not job_result.mix_instructions:
            raise HTTPException(
                status_code=404, 
                detail="Mix instructions not available for this job"
            )
        
        return job_result.mix_instructions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mix instructions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get mix instructions")


def _calculate_progress(job: AnalysisJob) -> float:
    """Calculate job progress percentage."""
    if job.total_tracks == 0:
        return 0.0

    if job.status == JobStatus.COMPLETED:
        return 100.0

    if job.status == JobStatus.FAILED:
        return 0.0

    # Calculate based on analyzed tracks
    progress = (job.analyzed_tracks / job.total_tracks) * 100
    return round(min(progress, 99.0), 1)  # Cap at 99% until fully complete 