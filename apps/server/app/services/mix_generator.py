import logging
from typing import List, Dict, Any, Optional
from app.models.track import Track
from app.models.job import MixTransition
from app.services.audio_analysis import AudioAnalyzer
import uuid

logger = logging.getLogger(__name__)


class MixGenerator:
    """Service for generating DJ mix instructions."""

    def __init__(self):
        self.analyzer = AudioAnalyzer()
        self.min_compatibility_score = 0.3  # Minimum score for a valid transition
        self.default_crossfade_duration = 16.0  # seconds

    def generate_mix(self, tracks: List[Track], job_id: uuid.UUID) -> Dict[str, Any]:
        """
        Generate mix instructions for a list of tracks.

        Args:
            tracks: List of Track objects with analysis data
            job_id: ID of the analysis job

        Returns:
            Dict containing mix instructions and metadata
        """
        try:
            if len(tracks) < 2:
                return {
                    "error": "Need at least 2 tracks to generate a mix",
                    "transitions": [],
                    "total_duration": 0,
                    "metadata": {},
                }

            # Filter tracks that have required analysis data
            analyzable_tracks = [
                track
                for track in tracks
                if track.bpm is not None and track.file_path is not None
            ]

            if len(analyzable_tracks) < 2:
                return {
                    "error": "Need at least 2 tracks with BPM analysis to generate a mix",
                    "transitions": [],
                    "total_duration": 0,
                    "metadata": {
                        "total_tracks": len(tracks),
                        "analyzable_tracks": len(analyzable_tracks),
                    },
                }

            # Sort tracks by BPM for smooth progression
            sorted_tracks = self._sort_tracks_by_bpm(analyzable_tracks)

            # Generate transitions between consecutive tracks
            transitions = []
            total_duration = 0

            for i in range(len(sorted_tracks) - 1):
                track_a = sorted_tracks[i]
                track_b = sorted_tracks[i + 1]

                transition = self._create_transition(track_a, track_b, i, job_id)

                if transition:
                    transitions.append(transition)
                    # Add track A duration (minus overlap) to total
                    if i == 0:
                        # First track plays fully until transition
                        total_duration += transition.transition_start

                    # Add transition duration
                    total_duration += transition.transition_duration

            # Add final track duration (after last transition)
            if transitions and len(sorted_tracks) > 0:
                last_track = sorted_tracks[-1]
                if last_track.duration:
                    # Assume we play from end of transition to end of track
                    remaining_duration = (
                        last_track.duration - self.default_crossfade_duration
                    )
                    total_duration += max(0, remaining_duration)

            # Generate metadata
            metadata = self._generate_metadata(sorted_tracks, transitions)

            return {
                "transitions": transitions,
                "total_duration": round(total_duration, 2),
                "total_tracks": len(sorted_tracks),
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Error generating mix: {e}")
            return {
                "error": str(e),
                "transitions": [],
                "total_duration": 0,
                "metadata": {},
            }

    def _sort_tracks_by_bpm(self, tracks: List[Track]) -> List[Track]:
        """Sort tracks by BPM for smooth progression."""
        return sorted(tracks, key=lambda t: t.bpm or 0)

    def _create_transition(
        self, track_a: Track, track_b: Track, position: int, job_id: uuid.UUID
    ) -> Optional[MixTransition]:
        """Create a transition between two tracks."""
        try:
            # Calculate compatibility scores
            track_a_data = self._track_to_dict(track_a)
            track_b_data = self._track_to_dict(track_b)

            compatibility = self.analyzer.calculate_compatibility(
                track_a_data, track_b_data
            )

            # Check if tracks are compatible enough
            if compatibility["overall_score"] < self.min_compatibility_score:
                logger.warning(
                    f"Low compatibility between {track_a.title} and {track_b.title}: "
                    f"{compatibility['overall_score']:.2f}"
                )
                # Still create transition but with shorter crossfade
                crossfade_duration = 4.0
            else:
                crossfade_duration = self.default_crossfade_duration

            # Calculate BPM adjustment needed
            bpm_adjustment = self._calculate_bpm_adjustment(track_a.bpm, track_b.bpm)

            # Find transition points
            transition_start = self._find_transition_start(track_a)

            # Create transition object
            transition = MixTransition(
                job_id=job_id,
                position=position,
                track_a_id=track_a.id,
                track_b_id=track_b.id,
                transition_start=transition_start,
                transition_duration=crossfade_duration,
                technique="crossfade",
                bpm_adjustment=bpm_adjustment,
                bpm_compatibility=compatibility["bpm_compatibility"],
                key_compatibility=compatibility["key_compatibility"],
                energy_compatibility=compatibility["energy_compatibility"],
                overall_score=compatibility["overall_score"],
                metadata={
                    "track_a_bpm": track_a.bpm,
                    "track_b_bpm": track_b.bpm,
                    "track_a_key": track_a.key,
                    "track_b_key": track_b.key,
                    "track_a_energy": track_a.energy,
                    "track_b_energy": track_b.energy,
                },
            )

            return transition

        except Exception as e:
            logger.error(
                f"Error creating transition between {track_a.title} and {track_b.title}: {e}"
            )
            return None

    def _track_to_dict(self, track: Track) -> Dict[str, Any]:
        """Convert Track object to dict for analysis."""
        return {
            "bpm": track.bpm,
            "key": track.key,
            "energy": track.energy,
            "danceability": track.danceability,
            "valence": track.valence,
            "loudness": track.loudness,
        }

    def _calculate_bpm_adjustment(self, bpm_a: float, bpm_b: float) -> float:
        """Calculate BPM adjustment percentage needed."""
        if not bpm_a or not bpm_b:
            return 0.0

        # Calculate percentage difference
        adjustment = ((bpm_b - bpm_a) / bpm_a) * 100
        return round(adjustment, 2)

    def _find_transition_start(self, track: Track) -> float:
        """Find optimal transition start point in track A."""
        if not track.duration:
            return 60.0  # Default fallback

        # For Phase 1, use simple approach:
        # Start transition in last 25% of track, but not too close to end
        track_duration = track.duration

        # Ensure we have at least 32 seconds to work with
        min_transition_start = max(track_duration - 64, track_duration * 0.75)
        max_transition_start = track_duration - self.default_crossfade_duration

        # Use the midpoint of this range
        transition_start = (min_transition_start + max_transition_start) / 2

        return round(max(0, transition_start), 2)

    def _generate_metadata(
        self, tracks: List[Track], transitions: List[MixTransition]
    ) -> Dict[str, Any]:
        """Generate metadata about the mix."""
        if not tracks:
            return {}

        # Calculate statistics
        bpms = [t.bpm for t in tracks if t.bpm]
        energies = [t.energy for t in tracks if t.energy]

        metadata = {
            "track_count": len(tracks),
            "transition_count": len(transitions),
            "avg_bpm": round(sum(bpms) / len(bpms), 2) if bpms else None,
            "bpm_range": {
                "min": min(bpms) if bpms else None,
                "max": max(bpms) if bpms else None,
            },
            "avg_energy": round(sum(energies) / len(energies), 3) if energies else None,
            "energy_range": {
                "min": min(energies) if energies else None,
                "max": max(energies) if energies else None,
            },
            "avg_compatibility": round(
                sum(t.overall_score for t in transitions if t.overall_score)
                / len(transitions),
                3,
            )
            if transitions
            else None,
            "keys_used": list(set(t.key for t in tracks if t.key)),
            "generation_algorithm": "bpm_sorted_crossfade_v1.0",
        }

        return metadata

    def optimize_track_order(self, tracks: List[Track]) -> List[Track]:
        """
        Optimize track order for better mixing flow.

        For Phase 1, this is a simple BPM-based sort.
        Future phases could implement more sophisticated algorithms.
        """
        # Filter tracks with BPM data
        tracks_with_bpm = [t for t in tracks if t.bpm is not None]
        tracks_without_bpm = [t for t in tracks if t.bpm is None]

        # Sort by BPM
        sorted_tracks = sorted(tracks_with_bpm, key=lambda t: t.bpm)

        # Add tracks without BPM at the end
        return sorted_tracks + tracks_without_bpm

    def validate_mix(self, transitions: List[MixTransition]) -> Dict[str, Any]:
        """Validate generated mix for potential issues."""
        issues = []
        warnings = []

        for i, transition in enumerate(transitions):
            # Check compatibility scores
            if transition.overall_score and transition.overall_score < 0.3:
                issues.append(
                    f"Transition {i+1}: Low compatibility score ({transition.overall_score:.2f})"
                )

            # Check BPM differences
            if abs(transition.bpm_adjustment) > 10:
                warnings.append(
                    f"Transition {i+1}: Large BPM difference ({transition.bpm_adjustment:.1f}%)"
                )

            # Check transition timing
            if transition.transition_duration > 32:
                warnings.append(
                    f"Transition {i+1}: Long crossfade ({transition.transition_duration}s)"
                )

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "total_transitions": len(transitions),
        }
