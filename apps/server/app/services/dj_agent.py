import logging
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from app.schemas.job import JobResultResponse, MixInstructions, MixTransitionResponse
from app.schemas.track import TrackSummary

logger = logging.getLogger(__name__)


class DJEventType(Enum):
    """Types of DJ events that can be triggered."""
    TRACK_STARTED = "track_started"
    TRACK_ENDED = "track_ended"
    TRANSITION_STARTED = "transition_started"
    TRANSITION_ENDED = "transition_ended"
    MIX_STARTED = "mix_started"
    MIX_ENDED = "mix_ended"
    ERROR = "error"


@dataclass
class DJEvent:
    """Event emitted by the DJ Agent."""
    event_type: DJEventType
    timestamp: float
    data: Dict[str, Any]


class TransitionStrategy(ABC):
    """Abstract base class for transition techniques."""
    
    @abstractmethod
    async def apply_transition(
        self,
        track_a: TrackSummary,
        track_b: TrackSummary,
        transition_config: MixTransitionResponse,
        audio_controller: 'AudioController'
    ) -> bool:
        """Apply the transition between two tracks."""
        pass
    
    @abstractmethod
    def get_required_overlap_time(self, transition_config: MixTransitionResponse) -> float:
        """Get the required overlap time for this transition."""
        pass


class CrossfadeStrategy(TransitionStrategy):
    """Standard crossfade transition."""
    
    async def apply_transition(
        self,
        track_a: TrackSummary,
        track_b: TrackSummary,
        transition_config: MixTransitionResponse,
        audio_controller: 'AudioController'
    ) -> bool:
        """Apply crossfade transition."""
        try:
            duration = transition_config.transition_duration
            
            logger.info(f"Starting crossfade transition: {track_a.title} -> {track_b.title} ({duration}s)")
            
            # Start track B
            await audio_controller.start_track(track_b, fade_in_duration=duration)
            
            # Fade out track A over the transition duration
            await audio_controller.fade_out_track(track_a, fade_duration=duration)
            
            return True
            
        except Exception as e:
            logger.error(f"Crossfade transition failed: {e}")
            return False
    
    def get_required_overlap_time(self, transition_config: MixTransitionResponse) -> float:
        return transition_config.transition_duration


class SmoothBlendStrategy(TransitionStrategy):
    """Smooth blend transition with EQ matching."""
    
    async def apply_transition(
        self,
        track_a: TrackSummary,
        track_b: TrackSummary,
        transition_config: MixTransitionResponse,
        audio_controller: 'AudioController'
    ) -> bool:
        """Apply smooth blend transition."""
        try:
            duration = transition_config.transition_duration
            
            logger.info(f"Starting smooth blend: {track_a.title} -> {track_b.title} ({duration}s)")
            
            # Apply EQ matching if available
            if transition_config.metadata:
                eq_settings = transition_config.metadata.get("eq_settings")
                if eq_settings:
                    await audio_controller.apply_eq(track_b, eq_settings)
            
            # Start track B with slower fade
            await audio_controller.start_track(track_b, fade_in_duration=duration * 1.5)
            
            # Gradual fade out of track A
            await audio_controller.fade_out_track(track_a, fade_duration=duration * 1.2)
            
            return True
            
        except Exception as e:
            logger.error(f"Smooth blend transition failed: {e}")
            return False
    
    def get_required_overlap_time(self, transition_config: MixTransitionResponse) -> float:
        return transition_config.transition_duration * 1.5


class QuickCutStrategy(TransitionStrategy):
    """Quick cut transition."""
    
    async def apply_transition(
        self,
        track_a: TrackSummary,
        track_b: TrackSummary,
        transition_config: MixTransitionResponse,
        audio_controller: 'AudioController'
    ) -> bool:
        """Apply quick cut transition."""
        try:
            logger.info(f"Starting quick cut: {track_a.title} -> {track_b.title}")
            
            # Stop track A immediately
            await audio_controller.stop_track(track_a)
            
            # Start track B immediately
            await audio_controller.start_track(track_b, fade_in_duration=0.5)
            
            return True
            
        except Exception as e:
            logger.error(f"Quick cut transition failed: {e}")
            return False
    
    def get_required_overlap_time(self, transition_config: MixTransitionResponse) -> float:
        return 0.5  # Minimal overlap for sync


class BeatmatchStrategy(TransitionStrategy):
    """Beat-matched transition using beat timestamps."""
    
    async def apply_transition(
        self,
        track_a: TrackSummary,
        track_b: TrackSummary,
        transition_config: MixTransitionResponse,
        audio_controller: 'AudioController'
    ) -> bool:
        """Apply beatmatched transition."""
        try:
            duration = transition_config.transition_duration
            
            logger.info(f"Starting beatmatch: {track_a.title} -> {track_b.title} ({duration}s)")
            
            # Apply BPM adjustment if needed
            bpm_adjustment = transition_config.bpm_adjustment
            if abs(bpm_adjustment) > 1.0:  # Only adjust if significant difference
                await audio_controller.adjust_bpm(track_b, bpm_adjustment)
            
            # Sync to beat boundaries
            beat_sync_offset = self._calculate_beat_sync_offset(track_a, track_b)
            
            # Start track B synced to beat
            await audio_controller.start_track(
                track_b, 
                fade_in_duration=duration,
                sync_offset=beat_sync_offset
            )
            
            # Fade out track A on beat boundaries
            await audio_controller.fade_out_track(track_a, fade_duration=duration)
            
            return True
            
        except Exception as e:
            logger.error(f"Beatmatch transition failed: {e}")
            return False
    
    def _calculate_beat_sync_offset(self, track_a: TrackSummary, track_b: TrackSummary) -> float:
        """Calculate offset to sync beats between tracks."""
        if not track_a.beat_timestamps or not track_b.beat_timestamps:
            return 0.0
        
        # Simple beat sync - align to nearest beat boundary
        # In a real implementation, this would be more sophisticated
        a_beat_interval = track_a.average_beat_interval or 0.6
        return a_beat_interval / 2  # Half beat offset for smoother transition
    
    def get_required_overlap_time(self, transition_config: MixTransitionResponse) -> float:
        return transition_config.transition_duration


class CreativeStrategy(TransitionStrategy):
    """Creative transition with effects."""
    
    async def apply_transition(
        self,
        track_a: TrackSummary,
        track_b: TrackSummary,
        transition_config: MixTransitionResponse,
        audio_controller: 'AudioController'
    ) -> bool:
        """Apply creative transition with effects."""
        try:
            duration = transition_config.transition_duration
            
            logger.info(f"Starting creative transition: {track_a.title} -> {track_b.title} ({duration}s)")
            
            # Apply creative effects based on track characteristics
            effect = self._choose_creative_effect(track_a, track_b, transition_config)
            
            # Apply the chosen effect
            await audio_controller.apply_effect(track_a, effect, duration / 2)
            
            # Start track B with complementary effect
            await audio_controller.start_track(track_b, fade_in_duration=duration)
            
            # Fade out track A
            await audio_controller.fade_out_track(track_a, fade_duration=duration)
            
            return True
            
        except Exception as e:
            logger.error(f"Creative transition failed: {e}")
            return False
    
    def _choose_creative_effect(
        self, 
        track_a: TrackSummary, 
        track_b: TrackSummary, 
        transition_config: MixTransitionResponse
    ) -> str:
        """Choose appropriate creative effect based on track characteristics."""
        energy_diff = abs((track_a.energy or 0.5) - (track_b.energy or 0.5))
        
        if energy_diff > 0.3:
            return "echo_fade"  # For energy transitions
        elif transition_config.key_compatibility and transition_config.key_compatibility > 0.8:
            return "harmonic_filter"  # For harmonic matches
        else:
            return "reverb_tail"  # Default creative effect
    
    def get_required_overlap_time(self, transition_config: MixTransitionResponse) -> float:
        return transition_config.transition_duration


class AudioController:
    """Abstract audio controller interface for different audio backends."""
    
    async def start_track(self, track: TrackSummary, fade_in_duration: float = 0.0, sync_offset: float = 0.0):
        """Start playing a track."""
        logger.info(f"Starting track: {track.title} (fade: {fade_in_duration}s, offset: {sync_offset}s)")
        # Implementation depends on audio backend (Web Audio API, native audio, etc.)
        pass
    
    async def stop_track(self, track: TrackSummary):
        """Stop playing a track."""
        logger.info(f"Stopping track: {track.title}")
        pass
    
    async def fade_out_track(self, track: TrackSummary, fade_duration: float):
        """Fade out a track."""
        logger.info(f"Fading out track: {track.title} ({fade_duration}s)")
        pass
    
    async def adjust_bpm(self, track: TrackSummary, adjustment_percent: float):
        """Adjust track BPM."""
        logger.info(f"Adjusting BPM for {track.title}: {adjustment_percent:+.1f}%")
        pass
    
    async def apply_eq(self, track: TrackSummary, eq_settings: Dict[str, float]):
        """Apply EQ settings to track."""
        logger.info(f"Applying EQ to {track.title}: {eq_settings}")
        pass
    
    async def apply_effect(self, track: TrackSummary, effect: str, duration: float):
        """Apply audio effect to track."""
        logger.info(f"Applying {effect} to {track.title} for {duration}s")
        pass


class DJAgent:
    """Main DJ Agent that orchestrates mix playback with transitions."""
    
    def __init__(self, audio_controller: AudioController):
        self.audio_controller = audio_controller
        self.transition_strategies = self._initialize_strategies()
        self.event_callbacks: List[Callable[[DJEvent], None]] = []
        self.current_mix: Optional[MixInstructions] = None
        self.current_position = 0
        self.is_playing = False
        self.start_time = 0.0
        
    def _initialize_strategies(self) -> Dict[str, TransitionStrategy]:
        """Initialize available transition strategies."""
        return {
            "crossfade": CrossfadeStrategy(),
            "smooth_blend": SmoothBlendStrategy(),
            "quick_cut": QuickCutStrategy(),
            "beatmatch": BeatmatchStrategy(),
            "creative": CreativeStrategy(),
        }
    
    def add_event_callback(self, callback: Callable[[DJEvent], None]):
        """Add event callback for DJ events."""
        self.event_callbacks.append(callback)
    
    def _emit_event(self, event_type: DJEventType, data: Dict[str, Any] = None):
        """Emit a DJ event to all callbacks."""
        event = DJEvent(
            event_type=event_type,
            timestamp=time.time(),
            data=data or {}
        )
        
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
    
    async def load_mix(self, job_result: JobResultResponse) -> bool:
        """Load mix instructions from job result."""
        try:
            if not job_result.mix_instructions:
                logger.error("No mix instructions found in job result")
                return False
            
            if not job_result.mix_instructions.transitions:
                logger.error("No transitions found in mix instructions")
                return False
            
            self.current_mix = job_result.mix_instructions
            self.current_position = 0
            
            logger.info(f"Loaded mix with {len(self.current_mix.transitions)} transitions")
            logger.info(f"Total duration: {self.current_mix.total_duration:.1f}s")
            
            self._emit_event(DJEventType.MIX_STARTED, {
                "total_tracks": self.current_mix.total_tracks,
                "total_duration": self.current_mix.total_duration,
                "transitions_count": len(self.current_mix.transitions)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load mix: {e}")
            self._emit_event(DJEventType.ERROR, {"error": str(e)})
            return False
    
    async def start_mix(self) -> bool:
        """Start playing the loaded mix."""
        try:
            if not self.current_mix or not self.current_mix.transitions:
                logger.error("No mix loaded")
                return False
            
            if self.is_playing:
                logger.warning("Mix is already playing")
                return False
            
            self.is_playing = True
            self.start_time = time.time()
            self.current_position = 0
            
            # Start the first track
            first_transition = self.current_mix.transitions[0]
            first_track = first_transition.track_a
            
            await self.audio_controller.start_track(first_track)
            
            self._emit_event(DJEventType.TRACK_STARTED, {
                "track": first_track.dict(),
                "position": 0
            })
            
            # Start the transition scheduler
            asyncio.create_task(self._run_transition_scheduler())
            
            logger.info(f"Started mix playback with track: {first_track.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start mix: {e}")
            self.is_playing = False
            self._emit_event(DJEventType.ERROR, {"error": str(e)})
            return False
    
    async def stop_mix(self):
        """Stop the current mix."""
        self.is_playing = False
        
        if self.current_mix and self.current_position < len(self.current_mix.transitions):
            current_transition = self.current_mix.transitions[self.current_position]
            await self.audio_controller.stop_track(current_transition.track_a)
            
            if self.current_position + 1 < len(self.current_mix.transitions):
                next_transition = self.current_mix.transitions[self.current_position + 1]
                await self.audio_controller.stop_track(next_transition.track_a)
        
        self._emit_event(DJEventType.MIX_ENDED, {
            "position": self.current_position,
            "completed": False
        })
        
        logger.info("Mix playback stopped")
    
    async def _run_transition_scheduler(self):
        """Run the transition scheduler loop."""
        try:
            while self.is_playing and self.current_position < len(self.current_mix.transitions):
                transition = self.current_mix.transitions[self.current_position]
                
                # Calculate when to start the transition
                elapsed_time = time.time() - self.start_time
                transition_time = transition.transition_start
                
                # Wait until it's time for the transition
                wait_time = transition_time - elapsed_time
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                
                if not self.is_playing:
                    break
                
                # Apply the transition
                success = await self._apply_transition(transition)
                
                if not success:
                    logger.error(f"Transition {self.current_position} failed")
                    self._emit_event(DJEventType.ERROR, {
                        "error": f"Transition {self.current_position} failed",
                        "transition": transition.dict()
                    })
                
                self.current_position += 1
            
            # Mix completed
            if self.is_playing:
                self.is_playing = False
                self._emit_event(DJEventType.MIX_ENDED, {
                    "position": self.current_position,
                    "completed": True
                })
                logger.info("Mix completed successfully")
                
        except Exception as e:
            logger.error(f"Error in transition scheduler: {e}")
            self.is_playing = False
            self._emit_event(DJEventType.ERROR, {"error": str(e)})
    
    async def _apply_transition(self, transition: MixTransitionResponse) -> bool:
        """Apply a specific transition."""
        try:
            strategy = self.transition_strategies.get(transition.technique)
            if not strategy:
                logger.warning(f"Unknown transition technique: {transition.technique}, using crossfade")
                strategy = self.transition_strategies["crossfade"]
            
            self._emit_event(DJEventType.TRANSITION_STARTED, {
                "transition": transition.dict(),
                "position": self.current_position
            })
            
            success = await strategy.apply_transition(
                transition.track_a,
                transition.track_b,
                transition,
                self.audio_controller
            )
            
            if success:
                self._emit_event(DJEventType.TRANSITION_ENDED, {
                    "transition": transition.dict(),
                    "position": self.current_position,
                    "success": True
                })
                
                self._emit_event(DJEventType.TRACK_STARTED, {
                    "track": transition.track_b.dict(),
                    "position": self.current_position + 1
                })
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to apply transition: {e}")
            return False
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current DJ status."""
        if not self.current_mix:
            return {"status": "no_mix_loaded"}
        
        elapsed_time = time.time() - self.start_time if self.is_playing else 0
        progress = elapsed_time / self.current_mix.total_duration if self.current_mix.total_duration > 0 else 0
        
        current_track = None
        if self.current_position < len(self.current_mix.transitions):
            current_track = self.current_mix.transitions[self.current_position].track_a.dict()
        
        return {
            "status": "playing" if self.is_playing else "paused",
            "current_position": self.current_position,
            "total_transitions": len(self.current_mix.transitions),
            "elapsed_time": elapsed_time,
            "total_duration": self.current_mix.total_duration,
            "progress": min(progress, 1.0),
            "current_track": current_track
        }


# Example usage and factory functions
def create_web_audio_controller() -> AudioController:
    """Create audio controller for web-based playback."""
    # This would integrate with Web Audio API
    return AudioController()


def create_native_audio_controller() -> AudioController:
    """Create audio controller for native audio playback."""
    # This would integrate with native audio libraries
    return AudioController()


async def main_example():
    """Example usage of the DJ Agent."""
    # Create DJ Agent
    audio_controller = create_web_audio_controller()
    dj = DJAgent(audio_controller)
    
    # Add event callback
    def on_dj_event(event: DJEvent):
        print(f"DJ Event: {event.event_type.value} at {event.timestamp}")
        if event.data:
            print(f"  Data: {event.data}")
    
    dj.add_event_callback(on_dj_event)
    
    # Load and play mix (job_result would come from API)
    # job_result = get_job_results_from_api(job_id)
    # success = await dj.load_mix(job_result)
    # if success:
    #     await dj.start_mix()


if __name__ == "__main__":
    asyncio.run(main_example()) 