from sqlalchemy import Column, String, Float, DateTime, Text, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.db.base import Base


class FileSource(str, enum.Enum):
    LOCAL = "local"
    YOUTUBE = "youtube"
    UNAVAILABLE = "unavailable"


class Track(Base):
    __tablename__ = "tracks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    spotify_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    album = Column(String)
    duration = Column(Float)  # Duration in seconds
    duration_ms = Column(Float)  # Duration in milliseconds from Spotify
    popularity = Column(Float)
    preview_url = Column(String)

    # File information
    file_path = Column(String)
    file_source = Column(Enum(FileSource), default=FileSource.UNAVAILABLE)
    file_size = Column(Float)  # File size in bytes

    # Audio analysis results
    bpm = Column(Float)
    key = Column(String)  # Musical key (e.g., "C", "Am")
    energy = Column(Float)  # 0.0 to 1.0
    danceability = Column(Float)  # 0.0 to 1.0
    valence = Column(Float)  # 0.0 to 1.0
    acousticness = Column(Float)  # 0.0 to 1.0
    instrumentalness = Column(Float)  # 0.0 to 1.0
    liveness = Column(Float)  # 0.0 to 1.0
    speechiness = Column(Float)  # 0.0 to 1.0
    loudness = Column(Float)  # dB

    # Beat analysis results (for beat matching)
    beat_timestamps = Column(JSON)  # Array of beat timestamps in seconds
    beat_intervals = Column(JSON)  # Array of intervals between beats
    beat_confidence = Column(Float)  # Overall beat detection confidence (0.0 to 1.0)
    beat_confidence_scores = Column(JSON)  # Individual confidence scores for each beat
    beat_regularity = Column(Float)  # Beat timing consistency (0.0 to 1.0)
    average_beat_interval = Column(Float)  # Average time between beats in seconds

    # Enhanced analysis results
    # Style analysis
    dominant_style = Column(String)  # Dominant musical style
    style_scores = Column(JSON)  # Scores for different musical styles
    style_confidence = Column(Float)  # Confidence in style classification
    
    # Mix points analysis
    mix_in_point = Column(Float)  # Optimal mix-in point in seconds
    mix_out_point = Column(Float)  # Optimal mix-out point in seconds
    mixable_sections = Column(JSON)  # Array of mixable sections with timestamps
    
    # Section analysis
    intro_end = Column(Float)  # End of intro section in seconds
    outro_start = Column(Float)  # Start of outro section in seconds
    intro_energy = Column(Float)  # Average energy level during intro
    outro_energy = Column(Float)  # Average energy level during outro
    energy_profile = Column(JSON)  # Energy profile over time
    
    # Vocal analysis
    vocal_sections = Column(JSON)  # Sections with vocals
    instrumental_sections = Column(JSON)  # Instrumental sections

    # Analysis metadata
    analysis_version = Column(String, default="2.0.0")
    analyzed_at = Column(DateTime(timezone=True))
    analysis_error = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Track(id={self.id}, title='{self.title}', artist='{self.artist}')>"
