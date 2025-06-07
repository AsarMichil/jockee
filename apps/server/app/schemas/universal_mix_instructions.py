# schemas/universal_mix_instructions.py
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel

class TransitionStrategy(str, Enum):
    SMOOTH = "smooth"          # Gradual crossfade
    RADIO = "radio"            # Quick fade with small gap
    DJ_BLEND = "dj_blend"      # Beat-matched blend
    CREATIVE = "creative"      # Effect-based transition
    DIRECT = "direct"          # Hard cut

class TransitionMood(str, Enum):
    ENERGETIC = "energetic"    # Maintain/boost energy
    RELAXED = "relaxed"        # Smooth, chill transition
    DRAMATIC = "dramatic"      # Build tension/release
    NEUTRAL = "neutral"        # Natural flow

class UniversalTransition(BaseModel):
    id: str
    track_a_id: str
    track_b_id: str
    
    # Core timing
    start_time: float          # When to start transition in track A
    duration: float            # How long the transition takes
    overlap: float             # How much tracks overlap (0 = gap, 1 = full overlap)
    
    # Strategy selection
    strategy: TransitionStrategy
    mood: TransitionMood
    
    # Simple automation curves (0-1 normalized)
    fade_curve: str = "linear"  # linear, exponential, s-curve, equal-power
    
    # Compatibility metrics
    compatibility_score: float  # Overall how well these tracks mix
    genre_similarity: float     # 0 = completely different, 1 = same genre
    energy_match: float        # How well energy levels match
    tempo_match: float         # How well tempos align
    key_match: float           # Harmonic compatibility
    
    # User options
    user_selectable: bool = True
    recommended_rank: int = 1   # If multiple options, which to recommend
    description: str           # Human-readable description

class MixOption(BaseModel):
    """Present multiple transition options to user"""
    option_id: str
    name: str                  # "Smooth Blend", "Radio Style", "DJ Mix"
    description: str           # What this option will sound like
    preview_available: bool
    transitions: List[UniversalTransition]
    overall_flow: str          # Description of the entire mix flow

class SmartMixPlan(BaseModel):
    id: str
    options: List[MixOption]   # Multiple ways to mix the playlist
    default_option_id: str     # AI's recommendation
    metadata: Dict[str, Any]