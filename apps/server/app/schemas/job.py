from pydantic import BaseModel, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.job import JobStatus
from app.schemas.track import TrackSummary


class PlaylistAnalysisOptions(BaseModel):
    auto_fetch_missing: bool = True
    max_tracks: int = 50
    skip_analysis_if_exists: bool = True
    download_timeout: int = 300  # seconds


class PlaylistAnalysisRequest(BaseModel):
    spotify_playlist_url: str
    options: Optional[PlaylistAnalysisOptions] = PlaylistAnalysisOptions()


class JobStatusResponse(BaseModel):
    id: UUID4
    status: JobStatus
    total_tracks: int
    analyzed_tracks: int
    downloaded_tracks: int
    failed_tracks: int
    progress_percentage: float
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MixTransitionResponse(BaseModel):
    id: UUID4
    position: int
    track_a: TrackSummary
    track_b: TrackSummary
    transition_start: float
    transition_duration: float
    technique: str
    bpm_adjustment: float
    bpm_compatibility: Optional[float] = None
    key_compatibility: Optional[float] = None
    energy_compatibility: Optional[float] = None
    overall_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class MixInstructions(BaseModel):
    total_duration: float  # Total mix duration in seconds
    total_tracks: int
    transitions: List[MixTransitionResponse]
    metadata: Dict[str, Any]


class JobResultResponse(BaseModel):
    id: UUID4
    status: JobStatus
    playlist_url: str
    playlist_name: Optional[str] = None
    total_tracks: int
    analyzed_tracks: int
    downloaded_tracks: int
    failed_tracks: int
    tracks: Optional[List[TrackSummary]] = None  # All tracks used in the job
    mix_instructions: Optional[MixInstructions] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisJobCreate(BaseModel):
    playlist_url: str
    playlist_id: Optional[str] = None
    playlist_name: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class AnalysisJobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    total_tracks: Optional[int] = None
    analyzed_tracks: Optional[int] = None
    downloaded_tracks: Optional[int] = None
    failed_tracks: Optional[int] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AnalysisJob(BaseModel):
    id: UUID4
    playlist_url: str
    playlist_id: Optional[str] = None
    playlist_name: Optional[str] = None
    status: JobStatus
    total_tracks: int
    analyzed_tracks: int
    downloaded_tracks: int
    failed_tracks: int
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
