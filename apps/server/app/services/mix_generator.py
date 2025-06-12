import logging
from typing import List, Dict, Any, Optional, Tuple
from app.models.track import Track, FileSource
from app.models.job import MixTransition
from app.services.audio_analysis import AudioAnalyzer
import uuid
from enum import Enum
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class MixStrategy(Enum):
    """Different mix ordering strategies."""
    BPM_PROGRESSION = "bpm_progression"
    ENERGY_FLOW = "energy_flow"
    KEY_HARMONY = "key_harmony"
    STYLE_CLUSTERS = "style_clusters"
    SMART_DJ = "smart_dj"


class TransitionTechnique(Enum):
    """Different transition techniques."""
    CROSSFADE = "crossfade"
    SMOOTH_BLEND = "smooth_blend"
    QUICK_CUT = "quick_cut"
    BEATMATCH = "beatmatch"
    CREATIVE = "creative"


class MixOption:
    """Represents a complete mix option with transitions."""
    def __init__(self, option_id: str, name: str, description: str, strategy: MixStrategy, 
                 transitions: List[MixTransition], total_duration: float, metadata: Dict[str, Any]):
        self.option_id = option_id
        self.name = name
        self.description = description
        self.strategy = strategy
        self.transitions = transitions
        self.total_duration = total_duration
        self.metadata = metadata


class MixGenerator:
    """Service for generating DJ mix instructions with multiple options."""

    def __init__(self):
        self.analyzer = AudioAnalyzer()
        self.min_compatibility_score = 0.3  # Minimum score for a valid transition
        self.default_crossfade_duration = 16.0  # seconds

    async def generate_mix_options(self, tracks: List[Track], job_id: uuid.UUID) -> Dict[str, Any]:
        """
        Generate multiple mix options for a list of tracks.

        Args:
            tracks: List of Track objects with analysis data
            job_id: ID of the analysis job

        Returns:
            Dict containing multiple mix options and metadata
        """
        try:
            if len(tracks) < 2:
                return {
                    "error": "Need at least 2 tracks to generate a mix",
                    "options": [],
                    "default_option_id": None,
                    "metadata": {},
                }

            # Filter tracks that have required analysis data
            analyzable_tracks = [
                track
                for track in tracks
                if track.bpm is not None
            ]

            if len(analyzable_tracks) < 2:
                return {
                    "error": "Need at least 2 tracks with BPM analysis to generate a mix",
                    "options": [],
                    "default_option_id": None,
                    "metadata": {
                        "total_tracks": len(tracks),
                        "analyzable_tracks": len(analyzable_tracks),
                    },
                }

            # Enhance track data with style analysis if file paths are available
            enhanced_tracks = await self._enhance_tracks_with_style_analysis(analyzable_tracks)

            # Generate different ordering strategies
            mix_options = []
            
            # BPM progression (original method)
            bpm_ordered = self._order_by_strategy(enhanced_tracks, MixStrategy.BPM_PROGRESSION)
            bpm_option = self._create_mix_option(
                bpm_ordered, job_id, MixStrategy.BPM_PROGRESSION,
                "BPM Progression", "Smooth BPM progression from slow to fast"
            )
            mix_options.append(bpm_option)

            # Energy flow ordering
            energy_ordered = self._order_by_strategy(enhanced_tracks, MixStrategy.ENERGY_FLOW)
            energy_option = self._create_mix_option(
                energy_ordered, job_id, MixStrategy.ENERGY_FLOW,
                "Energy Journey", "Dynamic energy flow with peaks and valleys"
            )
            mix_options.append(energy_option)

            # Key harmony ordering (if keys are available)
            if any(track.key for track in enhanced_tracks):
                key_ordered = self._order_by_strategy(enhanced_tracks, MixStrategy.KEY_HARMONY)
                key_option = self._create_mix_option(
                    key_ordered, job_id, MixStrategy.KEY_HARMONY,
                    "Harmonic Flow", "Transitions following musical key relationships"
                )
                mix_options.append(key_option)

            # Style clusters (if style data is available)
            style_ordered = self._order_by_strategy(enhanced_tracks, MixStrategy.STYLE_CLUSTERS)
            style_option = self._create_mix_option(
                style_ordered, job_id, MixStrategy.STYLE_CLUSTERS,
                "Style Journey", "Groups similar styles together with smooth transitions"
            )
            mix_options.append(style_option)

            # Smart DJ ordering (compatibility-based)
            smart_ordered = self._order_by_strategy(enhanced_tracks, MixStrategy.SMART_DJ)
            smart_option = self._create_mix_option(
                smart_ordered, job_id, MixStrategy.SMART_DJ,
                "DJ Style", "Optimized for maximum mixing compatibility"
            )
            mix_options.append(smart_option)

            # Determine best default option
            default_option = self._select_default_option(mix_options)

            # Generate overall metadata
            overall_metadata = self._generate_overall_metadata(enhanced_tracks, mix_options)

            return {
                "options": [self._mix_option_to_dict(option) for option in mix_options],
                "default_option_id": default_option.option_id,
                "total_tracks": len(enhanced_tracks),
                "metadata": overall_metadata,
            }

        except Exception as e:
            logger.error(f"Error generating mix options: {e}")
            return {
                "error": str(e),
                "options": [],
                "default_option_id": None,
                "metadata": {},
            }

    async def generate_mix(self, tracks: List[Track], job_id: uuid.UUID) -> Dict[str, Any]:
        """
        Generate a single mix (backward compatibility).
        Returns the best mix option.
        """
        try:
            mix_options = await self.generate_mix_options(tracks, job_id)
            
            if mix_options.get("error"):
                return {
                    "error": mix_options["error"],
                    "transitions": [],
                    "total_duration": 0,
                    "metadata": {},
                }
            
            # Find the best mix option object (not dict) for database saving
            options = mix_options.get("options", [])
            default_id = mix_options.get("default_option_id")
            
            if not options:
                return {
                    "error": "No mix options generated",
                    "transitions": [],
                    "total_duration": 0,
                    "metadata": {},
                }
            
            # Get the actual MixOption object (not the dict version)
            # We need to regenerate the default option to get the MixTransition objects
            # Filter tracks that have audio files (S3, local, or YouTube) and BPM data
            usable_tracks = [
                track for track in tracks
                if track.bpm is not None and (
                    (track.file_source == FileSource.S3 and track.s3_object_key) or
                    (track.file_path and Path(track.file_path).exists()) or
                    (track.file_source == FileSource.YOUTUBE and track.spotify_id)
                )
            ]
            
            if not usable_tracks:
                return {
                    "error": "No tracks with required data for mix generation",
                    "transitions": [],
                    "total_duration": 0,
                    "metadata": {},
                }
            
            # Enhance tracks with style analysis
            enhanced_tracks = await self._enhance_tracks_with_style_analysis(usable_tracks)
            
            # Generate the BPM progression option (default/most reliable)
            bpm_ordered = self._order_by_strategy(enhanced_tracks, MixStrategy.BPM_PROGRESSION)
            default_mix_option = self._create_mix_option(
                bpm_ordered, job_id, MixStrategy.BPM_PROGRESSION,
                "BPM Progression", "Smooth BPM progression from slow to fast"
            )
            
            if not default_mix_option:
                return {
                    "error": "Failed to create mix option",
                    "transitions": [],
                    "total_duration": 0,
                    "metadata": {},
                }
            
            return {
                "transitions": default_mix_option.transitions,  # These are MixTransition objects
                "total_duration": default_mix_option.total_duration,
                "total_tracks": len(tracks),
                "metadata": default_mix_option.metadata,
            }
            
        except Exception as e:
            logger.error(f"Error generating mix: {e}")
            return {
                "error": str(e),
                "transitions": [],
                "total_duration": 0,
                "metadata": {},
            }

    async def _enhance_tracks_with_style_analysis(self, tracks: List[Track]) -> List[Track]:
        """Enhance tracks with style analysis data."""
        enhanced_tracks = []
        
        for track in tracks:
            # Check if track has audio file (S3, local, or YouTube)
            has_s3_file = track.file_source == FileSource.S3 and track.s3_object_key
            has_local_file = track.file_path and Path(track.file_path).exists()
            has_youtube_file = track.file_source == FileSource.YOUTUBE and track.spotify_id
            
            if has_s3_file or has_local_file or has_youtube_file:
                try:
                    if has_s3_file:
                        # Use S3 methods for CloudFront files
                        style_data = await self.analyzer.analyze_track_style_s3(track.s3_object_key)
                        mix_points = await self.analyzer.find_mix_points_s3(
                            track.s3_object_key,
                            track.duration or 180.0  # Use track duration or default
                        )
                    elif has_local_file:
                        # Use existing local file methods
                        style_data = self.analyzer.analyze_track_style(track.file_path)
                        mix_points = self.analyzer.find_mix_points(
                            track.file_path,
                            track.duration or 180.0  # Use track duration or default
                        )
                    else:  # YouTube file
                        # For YouTube tracks, skip additional analysis if already done
                        # The track should already have the necessary analysis data
                        style_data = {
                            "dominant_style": track.dominant_style,
                            "style_scores": track.style_scores or {},
                            "style_confidence": track.style_confidence or 0.0
                        }
                        mix_points = {
                            "mix_in_point": track.mix_in_point,
                            "mix_out_point": track.mix_out_point,
                            "mixable_sections": track.mixable_sections or [],
                        }
                    
                    # Update track with enhanced data if we got new analysis
                    if style_data and style_data.get("dominant_style"):
                        track.dominant_style = style_data["dominant_style"]
                        track.style_scores = style_data.get("style_scores")
                        track.style_confidence = style_data.get("style_confidence")
                    
                    if mix_points and mix_points.get("mix_in_point") is not None:
                        track.mix_in_point = mix_points["mix_in_point"]
                        track.mix_out_point = mix_points["mix_out_point"]
                        track.mixable_sections = mix_points.get("mixable_sections")
                    
                    enhanced_tracks.append(track)
                    
                except Exception as e:
                    logger.warning(f"Failed to enhance track {track.title} with style analysis: {e}")
                    # Still add the track even if enhancement fails
                    enhanced_tracks.append(track)
            else:
                logger.info(f"Skipping track {track.title} - no accessible audio file")
        
        logger.info(f"Enhanced {len(enhanced_tracks)} out of {len(tracks)} tracks with style analysis")
        return enhanced_tracks

    def _order_by_strategy(self, tracks: List[Track], strategy: MixStrategy) -> List[Track]:
        """Order tracks according to the specified strategy."""
        try:
            if strategy == MixStrategy.BPM_PROGRESSION:
                return sorted(tracks, key=lambda t: t.bpm or 0)
                
            elif strategy == MixStrategy.ENERGY_FLOW:
                return self._order_by_energy_flow(tracks)
                
            elif strategy == MixStrategy.KEY_HARMONY:
                return self._order_by_key_harmony(tracks)
                
            elif strategy == MixStrategy.STYLE_CLUSTERS:
                return self._order_by_style_clusters(tracks)
                
            elif strategy == MixStrategy.SMART_DJ:
                return self._order_by_compatibility(tracks)
                
            else:
                # Default to BPM ordering
                return sorted(tracks, key=lambda t: t.bpm or 0)
                
        except Exception as e:
            logger.error(f"Error ordering tracks by {strategy}: {e}")
            return tracks

    def _order_by_energy_flow(self, tracks: List[Track]) -> List[Track]:
        """Order tracks to create a dynamic energy journey."""
        try:
            # Create energy journey: low -> high -> low -> high (peaks and valleys)
            sorted_by_energy = sorted(tracks, key=lambda t: t.energy or 0.5)
            
            if len(sorted_by_energy) <= 3:
                return sorted_by_energy
                
            # Create wave pattern
            journey = []
            low_energy = sorted_by_energy[:len(sorted_by_energy)//2]
            high_energy = sorted_by_energy[len(sorted_by_energy)//2:]
            
            # Interleave low and high energy tracks
            for i in range(max(len(low_energy), len(high_energy))):
                if i < len(low_energy):
                    journey.append(low_energy[i])
                if i < len(high_energy):
                    journey.append(high_energy[i])
                    
            return journey
            
        except Exception:
            return sorted(tracks, key=lambda t: t.energy or 0.5)

    def _order_by_key_harmony(self, tracks: List[Track]) -> List[Track]:
        """Order tracks following harmonic relationships."""
        try:
            tracks_with_keys = [t for t in tracks if t.key]
            tracks_without_keys = [t for t in tracks if not t.key]
            
            if len(tracks_with_keys) < 2:
                return tracks
                
            # Start with first track
            ordered = [tracks_with_keys[0]]
            remaining = tracks_with_keys[1:]
            
            # Build chain of harmonically compatible tracks
            while remaining:
                last_track = ordered[-1]
                
                # Find most compatible next track
                best_next = None
                best_score = -1
                
                for track in remaining:
                    score = self.analyzer._calculate_key_compatibility(last_track.key, track.key)
                    if score > best_score:
                        best_score = score
                        best_next = track
                
                if best_next:
                    ordered.append(best_next)
                    remaining.remove(best_next)
                else:
                    # Add remaining track anyway
                    ordered.append(remaining.pop(0))
            
            # Add tracks without keys at the end
            return ordered + tracks_without_keys
            
        except Exception:
            return tracks

    def _order_by_style_clusters(self, tracks: List[Track]) -> List[Track]:
        """Group tracks by similar styles."""
        try:
            # Group by dominant style
            style_groups = {}
            
            for track in tracks:
                style_data = getattr(track, '_style_data', None)
                if style_data:
                    dominant_style = style_data.get('dominant_style', 'unknown')
                else:
                    dominant_style = 'unknown'
                    
                if dominant_style not in style_groups:
                    style_groups[dominant_style] = []
                style_groups[dominant_style].append(track)
            
            # Order groups by typical energy progression
            style_order = ['ambient_texture', 'acoustic', 'melodic_focus', 'beat_driven', 'electronic', 'unknown']
            
            ordered = []
            for style in style_order:
                if style in style_groups:
                    # Sort within group by BPM
                    group_tracks = sorted(style_groups[style], key=lambda t: t.bpm or 0)
                    ordered.extend(group_tracks)
                    
            return ordered
            
        except Exception:
            return tracks

    def _order_by_compatibility(self, tracks: List[Track]) -> List[Track]:
        """Order tracks to maximize transition compatibility."""
        try:
            if len(tracks) < 2:
                return tracks
                
            # Start with a random track (could be optimized)
            ordered = [tracks[0]]
            remaining = tracks[1:]
            
            # Greedily add most compatible tracks
            while remaining:
                last_track = ordered[-1]
                best_track = None
                best_score = -1
                
                for track in remaining:
                    last_data = self._track_to_dict_enhanced(last_track)
                    track_data = self._track_to_dict_enhanced(track)
                    
                    compatibility = self.analyzer.calculate_compatibility(last_data, track_data)
                    score = compatibility.get("overall_score", 0)
                    
                    if score > best_score:
                        best_score = score
                        best_track = track
                
                if best_track:
                    ordered.append(best_track)
                    remaining.remove(best_track)
                else:
                    # Add remaining track anyway
                    ordered.append(remaining.pop(0))
                    
            return ordered
            
        except Exception:
            return tracks

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

    def _track_to_dict_enhanced(self, track: Track) -> Dict[str, Any]:
        """Convert Track object to dict for enhanced analysis."""
        return {
            "bpm": track.bpm,
            "key": track.key,
            "energy": track.energy,
            "danceability": track.danceability,
            "valence": track.valence,
            "loudness": track.loudness,
            "style_data": getattr(track, '_style_data', None),
            "mix_points": getattr(track, '_mix_points', None),
        }

    def _create_mix_option(self, tracks: List[Track], job_id: uuid.UUID, strategy: MixStrategy, name: str, description: str) -> MixOption:
        """Create a mix option from a list of tracks."""
        try:
            # Generate transitions between consecutive tracks
            transitions = []
            total_duration = 0

            for i in range(len(tracks) - 1):
                track_a = tracks[i]
                track_b = tracks[i + 1]

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
            if transitions and len(tracks) > 0:
                last_track = tracks[-1]
                if last_track.duration:
                    # Assume we play from end of transition to end of track
                    remaining_duration = (
                        last_track.duration - self.default_crossfade_duration
                    )
                    total_duration += max(0, remaining_duration)

            # Generate metadata
            metadata = self._generate_metadata(tracks, transitions)

            return MixOption(
                option_id=uuid.uuid4().hex,
                name=name,
                description=description,
                strategy=strategy,
                transitions=transitions,
                total_duration=round(total_duration, 2),
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error creating mix option: {e}")
            return None

    def _select_default_option(self, options: List[MixOption]) -> MixOption:
        """Select the best default mix option based on criteria."""
        if not options:
            return None
            
        # Score options based on various criteria
        scored_options = []
        
        for option in options:
            score = 0.0
            
            # Prefer options with higher average compatibility
            if option.transitions:
                avg_compatibility = sum(t.overall_score for t in option.transitions if t.overall_score) / len(option.transitions)
                score += avg_compatibility * 0.4
            
            # Prefer certain strategies
            strategy_scores = {
                MixStrategy.SMART_DJ: 0.3,
                MixStrategy.BPM_PROGRESSION: 0.25, 
                MixStrategy.ENERGY_FLOW: 0.2,
                MixStrategy.KEY_HARMONY: 0.15,
                MixStrategy.STYLE_CLUSTERS: 0.1,
            }
            score += strategy_scores.get(option.strategy, 0.0)
            
            # Prefer shorter total duration (more efficient mixes)
            if option.total_duration > 0:
                duration_score = max(0, 1.0 - (option.total_duration / 3600))  # Normalize to 1 hour
                score += duration_score * 0.1
            
            scored_options.append((option, score))
        
        # Return highest scoring option
        return max(scored_options, key=lambda x: x[1])[0]

    def _generate_overall_metadata(self, tracks: List[Track], options: List[MixOption]) -> Dict[str, Any]:
        """Generate overall metadata about all mix options."""
        if not tracks:
            return {}

        # Calculate statistics
        bpms = [t.bpm for t in tracks if t.bpm]
        energies = [t.energy for t in tracks if t.energy]
        
        # Analyze style diversity if available
        styles = []
        for track in tracks:
            style_data = getattr(track, '_style_data', None)
            if style_data:
                styles.append(style_data.get('dominant_style', 'unknown'))

        style_diversity = len(set(styles)) / len(styles) if styles else 0.0

        metadata = {
            "track_count": len(tracks),
            "option_count": len(options),
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
            "style_diversity": round(style_diversity, 3),
            "keys_used": list(set(t.key for t in tracks if t.key)),
            "generation_algorithm": "multiple_mix_options_v1.0",
        }

        return metadata

    def _mix_option_to_dict(self, option: MixOption) -> Dict[str, Any]:
        """Convert MixOption object to dict for serialization."""
        return {
            "option_id": option.option_id,
            "name": option.name,
            "description": option.description,
            "strategy": option.strategy.value,
            "transitions": [self._transition_to_dict(t) for t in option.transitions],
            "total_duration": option.total_duration,
            "metadata": option.metadata,
        }

    def _transition_to_dict(self, transition: MixTransition) -> Dict[str, Any]:
        """Convert MixTransition object to dict for serialization."""
        return {
            "job_id": str(transition.job_id),
            "position": transition.position,
            "track_a_id": str(transition.track_a_id),
            "track_b_id": str(transition.track_b_id),
            "transition_start": transition.transition_start,
            "transition_duration": transition.transition_duration,
            "technique": transition.technique,
            "bpm_adjustment": transition.bpm_adjustment,
            "bpm_compatibility": transition.bpm_compatibility,
            "key_compatibility": transition.key_compatibility,
            "energy_compatibility": transition.energy_compatibility,
            "overall_score": transition.overall_score,
            "metadata": transition.metadata,
        }

    def _create_transition(
        self, track_a: Track, track_b: Track, position: int, job_id: uuid.UUID
    ) -> Optional[MixTransition]:
        """Create a transition between two tracks with enhanced analysis."""
        try:
            # Calculate compatibility scores using enhanced data
            track_a_data = self._track_to_dict_enhanced(track_a)
            track_b_data = self._track_to_dict_enhanced(track_b)

            compatibility = self.analyzer.calculate_compatibility(
                track_a_data, track_b_data
            )

            # Determine transition technique based on compatibility
            technique = self._select_transition_technique(compatibility, track_a_data, track_b_data)
            
            # Adjust transition duration based on technique and compatibility
            if compatibility["overall_score"] < self.min_compatibility_score:
                logger.warning(
                    f"Low compatibility between {track_a.title} and {track_b.title}: "
                    f"{compatibility['overall_score']:.2f}"
                )
                crossfade_duration = 4.0  # Shorter for difficult transitions
            elif technique == TransitionTechnique.SMOOTH_BLEND:
                crossfade_duration = self.default_crossfade_duration * 1.5  # Longer smooth blends
            elif technique == TransitionTechnique.QUICK_CUT:
                crossfade_duration = 2.0  # Very short cut
            else:
                crossfade_duration = self.default_crossfade_duration

            # Calculate BPM adjustment needed
            bpm_adjustment = self._calculate_bpm_adjustment(track_a.bpm, track_b.bpm)

            # Find transition points using enhanced mix point analysis
            transition_start = self._find_enhanced_transition_start(track_a, track_b, compatibility)

            # Create transition object
            transition = MixTransition(
                job_id=job_id,
                position=position,
                track_a_id=track_a.id,
                track_b_id=track_b.id,
                transition_start=transition_start,
                transition_duration=crossfade_duration,
                technique=technique.value,
                bpm_adjustment=bpm_adjustment,
                bpm_compatibility=compatibility.get("bpm_compatibility", 0.0),
                key_compatibility=compatibility.get("key_compatibility", 0.0),
                energy_compatibility=compatibility.get("energy_compatibility", 0.0),
                overall_score=compatibility.get("overall_score", 0.0),
                metadata={
                    "track_a_bpm": track_a.bpm,
                    "track_b_bpm": track_b.bpm,
                    "track_a_key": track_a.key,
                    "track_b_key": track_b.key,
                    "track_a_energy": track_a.energy,
                    "track_b_energy": track_b.energy,
                    "style_compatibility": compatibility.get("style_compatibility", 0.0),
                    "vocal_compatibility": compatibility.get("vocal_compatibility", 0.0),
                },
            )

            return transition

        except Exception as e:
            logger.error(
                f"Error creating transition between {track_a.title} and {track_b.title}: {e}"
            )
            return None

    def _select_transition_technique(self, compatibility: Dict[str, float], track_a_data: Dict[str, Any], track_b_data: Dict[str, Any]) -> TransitionTechnique:
        """Select the best transition technique based on compatibility and track characteristics."""
        overall_score = compatibility.get("overall_score", 0.0)
        bpm_compatibility = compatibility.get("bpm_compatibility", 0.0)
        energy_compatibility = compatibility.get("energy_compatibility", 0.0)
        
        # High compatibility tracks can use smooth blends
        if overall_score >= 0.8 and bpm_compatibility >= 0.7:
            return TransitionTechnique.SMOOTH_BLEND
            
        # Good BPM matching suggests beatmatching
        elif bpm_compatibility >= 0.8:
            return TransitionTechnique.BEATMATCH
            
        # Very different energy levels need cuts
        elif energy_compatibility < 0.3:
            return TransitionTechnique.QUICK_CUT
            
        # Low overall compatibility suggests creative transitions
        elif overall_score < 0.4:
            return TransitionTechnique.CREATIVE
            
        # Default to crossfade
        else:
            return TransitionTechnique.CROSSFADE

    def _find_enhanced_transition_start(self, track_a: Track, track_b: Track, compatibility: Dict[str, float]) -> float:
        """Find optimal transition start point using enhanced mix point analysis."""
        try:
            # Use enhanced mix points if available
            mix_points = getattr(track_a, '_mix_points', None)
            
            if mix_points and mix_points.get('mix_out_point'):
                # Use the calculated optimal mix out point
                return float(mix_points['mix_out_point'])
            
            # Fall back to basic calculation
            return self._find_transition_start(track_a)
            
        except Exception as e:
            logger.warning(f"Error finding enhanced transition start: {e}")
            return self._find_transition_start(track_a)

    def _find_transition_start(self, track: Track) -> float:
        """Find optimal transition start point in track A (basic method)."""
        if not track.duration:
            return 60.0  # Default fallback

        # Use simple approach: Start transition in last 25% of track, but not too close to end
        track_duration = track.duration

        # Ensure we have at least 32 seconds to work with
        min_transition_start = max(track_duration - 64, track_duration * 0.75)
        max_transition_start = track_duration - self.default_crossfade_duration

        # Use the midpoint of this range
        transition_start = (min_transition_start + max_transition_start) / 2

        return round(max(0, transition_start), 2)

    def _calculate_bpm_adjustment(self, bpm_a: float, bpm_b: float) -> float:
        """Calculate BPM adjustment percentage needed."""
        if not bpm_a or not bpm_b:
            return 0.0

        # Calculate percentage difference
        adjustment = ((bpm_b - bpm_a) / bpm_a) * 100
        return round(adjustment, 2)

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
