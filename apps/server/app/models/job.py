from sqlalchemy import Column, String, Integer, DateTime, Text, Enum, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.db.base import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    playlist_url = Column(String, nullable=False)
    playlist_id = Column(String)  # Extracted Spotify playlist ID
    playlist_name = Column(String)

    # Job status and progress
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, index=True)
    total_tracks = Column(Integer, default=0)
    analyzed_tracks = Column(Integer, default=0)
    downloaded_tracks = Column(Integer, default=0)
    failed_tracks = Column(Integer, default=0)

    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON)

    # Results
    result = Column(JSON)  # Mix instructions and metadata

    # Options
    options = Column(JSON)  # Job configuration options

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<AnalysisJob(id={self.id}, status='{self.status}', playlist_url='{self.playlist_url}')>"


class MixTransition(Base):
    __tablename__ = "mix_transitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("analysis_jobs.id"), nullable=False)
    position = Column(Integer, nullable=False)  # Order in the mix

    # Track references
    track_a_id = Column(UUID(as_uuid=True), ForeignKey("tracks.id"), nullable=False)
    track_b_id = Column(UUID(as_uuid=True), ForeignKey("tracks.id"), nullable=False)

    # Transition details
    transition_start = Column(Float, nullable=False)  # Seconds into track A
    transition_duration = Column(Float, nullable=False)  # Duration of crossfade
    technique = Column(String, default="crossfade")  # Mixing technique

    # BPM adjustment
    bpm_adjustment = Column(Float, default=0.0)  # Percentage adjustment needed

    # Compatibility scores
    bpm_compatibility = Column(Float)  # 0.0 to 1.0
    key_compatibility = Column(Float)  # 0.0 to 1.0
    energy_compatibility = Column(Float)  # 0.0 to 1.0
    overall_score = Column(Float)  # Combined compatibility score

    # Additional metadata
    mix_metadata = Column(JSON)

    # Relationships
    job = relationship("AnalysisJob", backref="transitions")
    track_a = relationship("Track", foreign_keys=[track_a_id])
    track_b = relationship("Track", foreign_keys=[track_b_id])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<MixTransition(id={self.id}, position={self.position}, job_id={self.job_id})>"
