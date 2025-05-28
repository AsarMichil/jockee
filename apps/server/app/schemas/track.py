from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime
from app.models.track import FileSource


class TrackBase(BaseModel):
    spotify_id: str
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[float] = None
    duration_ms: Optional[float] = None
    popularity: Optional[float] = None
    preview_url: Optional[str] = None


class TrackCreate(TrackBase):
    pass


class TrackUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    file_path: Optional[str] = None
    file_source: Optional[FileSource] = None
    file_size: Optional[float] = None
    bpm: Optional[float] = None
    key: Optional[str] = None
    energy: Optional[float] = None
    danceability: Optional[float] = None
    valence: Optional[float] = None
    acousticness: Optional[float] = None
    instrumentalness: Optional[float] = None
    liveness: Optional[float] = None
    speechiness: Optional[float] = None
    loudness: Optional[float] = None
    analysis_version: Optional[str] = None
    analyzed_at: Optional[datetime] = None
    analysis_error: Optional[str] = None


class TrackAnalysis(BaseModel):
    bpm: Optional[float] = None
    key: Optional[str] = None
    energy: Optional[float] = None
    danceability: Optional[float] = None
    valence: Optional[float] = None
    acousticness: Optional[float] = None
    instrumentalness: Optional[float] = None
    liveness: Optional[float] = None
    speechiness: Optional[float] = None
    loudness: Optional[float] = None
    analysis_version: str
    analyzed_at: Optional[datetime] = None
    analysis_error: Optional[str] = None


class Track(TrackBase):
    id: UUID4
    file_path: Optional[str] = None
    file_source: FileSource
    file_size: Optional[float] = None

    # Audio analysis
    bpm: Optional[float] = None
    key: Optional[str] = None
    energy: Optional[float] = None
    danceability: Optional[float] = None
    valence: Optional[float] = None
    acousticness: Optional[float] = None
    instrumentalness: Optional[float] = None
    liveness: Optional[float] = None
    speechiness: Optional[float] = None
    loudness: Optional[float] = None

    # Analysis metadata
    analysis_version: Optional[str] = None
    analyzed_at: Optional[datetime] = None
    analysis_error: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrackSummary(BaseModel):
    id: UUID4
    spotify_id: str
    title: str
    artist: str
    duration: Optional[float] = None
    file_source: FileSource
    bpm: Optional[float] = None
    key: Optional[str] = None
    energy: Optional[float] = None

    class Config:
        from_attributes = True
