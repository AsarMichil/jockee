from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.track import Track
from app.schemas.track import Track as TrackSchema, TrackSummary
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{track_id}", response_model=TrackSchema)
async def get_track(track_id: str, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific track.
    """
    try:
        track = db.query(Track).filter(Track.id == track_id).first()

        if not track:
            raise HTTPException(status_code=404, detail="Track not found")

        return track

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting track {track_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get track")


@router.get("/spotify/{spotify_id}", response_model=TrackSchema)
async def get_track_by_spotify_id(spotify_id: str, db: Session = Depends(get_db)):
    """
    Get track information by Spotify ID.
    """
    try:
        track = db.query(Track).filter(Track.spotify_id == spotify_id).first()

        if not track:
            raise HTTPException(status_code=404, detail="Track not found")

        return track

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting track by Spotify ID {spotify_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get track")


@router.get("/", response_model=List[TrackSummary])
async def list_tracks(
    skip: int = 0,
    limit: int = 100,
    has_analysis: Optional[bool] = None,
    has_file: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """
    List tracks with optional filtering.

    Args:
        skip: Number of tracks to skip
        limit: Maximum number of tracks to return
        has_analysis: Filter by whether track has been analyzed
        has_file: Filter by whether track has an audio file
    """
    try:
        query = db.query(Track)

        # Apply filters
        if has_analysis is not None:
            if has_analysis:
                query = query.filter(Track.analyzed_at.isnot(None))
            else:
                query = query.filter(Track.analyzed_at.is_(None))

        if has_file is not None:
            if has_file:
                query = query.filter(Track.file_path.isnot(None))
            else:
                query = query.filter(Track.file_path.is_(None))

        # Order by creation date (newest first)
        query = query.order_by(Track.created_at.desc())

        # Apply pagination
        tracks = query.offset(skip).limit(limit).all()

        return tracks

    except Exception as e:
        logger.error(f"Error listing tracks: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tracks")


@router.get("/search/", response_model=List[TrackSummary])
async def search_tracks(q: str, limit: int = 20, db: Session = Depends(get_db)):
    """
    Search tracks by title or artist.
    """
    try:
        if len(q.strip()) < 2:
            raise HTTPException(
                status_code=400, detail="Search query must be at least 2 characters"
            )

        search_term = f"%{q.strip()}%"

        tracks = (
            db.query(Track)
            .filter(
                (Track.title.ilike(search_term)) | (Track.artist.ilike(search_term))
            )
            .order_by(Track.created_at.desc())
            .limit(limit)
            .all()
        )

        return tracks

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching tracks: {e}")
        raise HTTPException(status_code=500, detail="Failed to search tracks")


@router.get("/stats/", response_model=dict)
async def get_track_stats(db: Session = Depends(get_db)):
    """
    Get statistics about tracks in the database.
    """
    try:
        from sqlalchemy import func

        # Total tracks
        total_tracks = db.query(Track).count()

        # Tracks with analysis
        analyzed_tracks = db.query(Track).filter(Track.analyzed_at.isnot(None)).count()

        # Tracks by file source
        file_source_stats = (
            db.query(Track.file_source, func.count(Track.id))
            .group_by(Track.file_source)
            .all()
        )

        file_source_counts = {
            source.value if source else "unknown": count
            for source, count in file_source_stats
        }

        # BPM statistics
        bpm_stats = (
            db.query(func.min(Track.bpm), func.max(Track.bpm), func.avg(Track.bpm))
            .filter(Track.bpm.isnot(None))
            .first()
        )

        # Key distribution
        key_stats = (
            db.query(Track.key, func.count(Track.id))
            .filter(Track.key.isnot(None))
            .group_by(Track.key)
            .all()
        )

        key_distribution = {key: count for key, count in key_stats}

        return {
            "total_tracks": total_tracks,
            "analyzed_tracks": analyzed_tracks,
            "analysis_percentage": round((analyzed_tracks / total_tracks) * 100, 1)
            if total_tracks > 0
            else 0,
            "file_source_counts": file_source_counts,
            "bpm_stats": {
                "min": float(bpm_stats[0]) if bpm_stats[0] else None,
                "max": float(bpm_stats[1]) if bpm_stats[1] else None,
                "avg": round(float(bpm_stats[2]), 1) if bpm_stats[2] else None,
            },
            "key_distribution": key_distribution,
        }

    except Exception as e:
        logger.error(f"Error getting track stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get track statistics")
