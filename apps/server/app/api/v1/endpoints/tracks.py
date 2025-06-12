from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse, FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import mimetypes
from pathlib import Path
from app.db.session import get_db
from app.models.track import Track, FileSource
from app.schemas.track import Track as TrackSchema, TrackSummary
from app.api.v1.dependencies import get_spotify_client
from app.core.spotify import SpotifyClient
from app.services.s3_storage import S3StorageService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
s3_storage = S3StorageService()


@router.get("/{track_id}/audio")
async def stream_track_audio(
    track_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Stream audio file for a track. For S3-stored files, redirects to CloudFront.
    For local files, provides direct streaming with range request support.
    Note: This endpoint doesn't require authentication for streaming,
    but getting the URL requires authentication via the /audio/url endpoint.
    """
    try:
        # Get track from database
        track = db.query(Track).filter(Track.id == track_id).first()
        
        if not track:
            raise HTTPException(status_code=404, detail="Track not found")
        
        # Handle S3-stored files
        if track.file_source == FileSource.S3 and track.s3_object_key:
            # Redirect to CloudFront URL for S3 files
            cloudfront_url = s3_storage.generate_cloudfront_url(track.s3_object_key)
            return RedirectResponse(url=cloudfront_url, status_code=302)
        
        # Handle local files (backward compatibility)
        if (track.file_source == FileSource.LOCAL or track.file_source == FileSource.YOUTUBE) and track.file_path:
            file_path = Path(track.file_path)
            if not file_path.exists():
                logger.error(f"Audio file not found on disk: {track.file_path}")
                raise HTTPException(status_code=404, detail="Audio file not found on disk")
            
            # Get file info
            file_size = file_path.stat().st_size
            content_type = mimetypes.guess_type(str(file_path))[0] or "audio/mpeg"
            
            # Handle range requests for streaming
            range_header = request.headers.get("range")
            
            if range_header:
                # Parse range header (e.g., "bytes=0-1023")
                try:
                    range_match = range_header.replace("bytes=", "").split("-")
                    start = int(range_match[0]) if range_match[0] else 0
                    end = int(range_match[1]) if range_match[1] else file_size - 1
                    
                    # Ensure valid range
                    start = max(0, start)
                    end = min(file_size - 1, end)
                    content_length = end - start + 1
                    
                    def generate_chunk():
                        with open(file_path, "rb") as f:
                            f.seek(start)
                            remaining = content_length
                            while remaining > 0:
                                chunk_size = min(8192, remaining)  # 8KB chunks
                                chunk = f.read(chunk_size)
                                if not chunk:
                                    break
                                remaining -= len(chunk)
                                yield chunk
                    
                    headers = {
                        "Content-Range": f"bytes {start}-{end}/{file_size}",
                        "Accept-Ranges": "bytes",
                        "Content-Length": str(content_length),
                        "Content-Type": content_type,
                        "Cache-Control": "public, max-age=3600",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                        "Access-Control-Allow-Headers": "Range, Content-Type",
                    }
                    
                    return StreamingResponse(
                        generate_chunk(),
                        status_code=206,  # Partial Content
                        headers=headers,
                        media_type=content_type
                    )
                    
                except (ValueError, IndexError) as e:
                    logger.error(f"Invalid range header: {range_header}, error: {e}")
                    # Fall through to serve full file
            
            # Serve full file if no range request or invalid range
            headers = {
                "Content-Length": str(file_size),
                "Content-Type": content_type,
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "Range, Content-Type",
            }
            
            return FileResponse(
                path=file_path,
                headers=headers,
                media_type=content_type,
                filename=f"{track.artist} - {track.title}.mp3"
            )
        
        # No valid file source
        raise HTTPException(status_code=404, detail="Audio file not available for this track")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming audio for track {track_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stream audio file")


@router.options("/{track_id}/audio")
async def audio_options(track_id: str):
    """
    Handle CORS preflight requests for audio streaming.
    """
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
        "Access-Control-Allow-Headers": "Range, Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
    }
    return StreamingResponse(iter([]), headers=headers)


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


@router.get("/{track_id}/audio/url")
async def get_track_audio_url(
    track_id: str,
    request: Request,
    db: Session = Depends(get_db),
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    """
    Get the streaming URL for a track's audio file.
    This endpoint returns the URL that can be used to stream the audio.
    For S3 files, returns the CloudFront URL directly.
    For local files, returns the streaming endpoint URL.
    """
    try:
        # Get track from database
        track = db.query(Track).filter(Track.id == track_id).first()
        
        if not track:
            raise HTTPException(status_code=404, detail="Track not found")
        
        # Handle S3-stored files
        if track.file_source == FileSource.S3 and track.s3_object_key:
            # Return CloudFront URL directly for S3 files
            cloudfront_url = s3_storage.generate_cloudfront_url(track.s3_object_key)
            return {
                "url": cloudfront_url,
                "source": "s3",
                "cache_control": "public, max-age=31536000"
            }
        
        # Handle local files (backward compatibility)
        if (track.file_source == FileSource.LOCAL or track.file_source == FileSource.YOUTUBE) and track.file_path:
            file_path = Path(track.file_path)
            if not file_path.exists():
                logger.error(f"Audio file not found on disk: {track.file_path}")
                raise HTTPException(status_code=404, detail="Audio file not found on disk")
            
            # Return the streaming URL for local files
            base_url = str(request.base_url).rstrip('/')
            audio_url = f"{base_url}/api/v1/tracks/{track_id}/audio"
            
            return {
                "url": audio_url,
                "source": "local",
                "cache_control": "public, max-age=3600"
            }
        
        # No valid file source
        raise HTTPException(status_code=404, detail="Audio file not available for this track")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audio URL for track {track_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audio URL")
