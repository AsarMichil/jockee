import librosa
import numpy as np
import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class AudioAnalyzer:
    """Service for analyzing audio files using librosa."""

    def __init__(self):
        self.sample_rate = 22050  # Standard sample rate for analysis
        self.analysis_version = "2.0.0"  # Updated version to reflect librosa-only analysis

    async def analyze_track(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze an audio track and extract features using librosa.

        Returns:
            Dict with analysis results or error information
        """
        result = {
            "bpm": None,
            "key": None,
            "energy": None,
            "danceability": None,
            "valence": None,
            "acousticness": None,
            "instrumentalness": None,
            "liveness": None,
            "speechiness": None,
            "loudness": None,
            "beat_timestamps": None,
            "beat_intervals": None,
            "beat_confidence": None,
            "analysis_version": self.analysis_version,
            "analyzed_at": datetime.utcnow(),
            "analysis_error": None,
        }

        try:
            if not Path(file_path).exists():
                result["analysis_error"] = f"File not found: {file_path}"
                return result

            # Run analysis in executor to avoid blocking
            loop = asyncio.get_event_loop()
            analysis_data = await loop.run_in_executor(
                None, self._analyze_audio_file, file_path
            )

            result.update(analysis_data)
            logger.info(f"Successfully analyzed audio file: {file_path}")

        except Exception as e:
            error_msg = f"Error analyzing audio file {file_path}: {str(e)}"
            logger.error(error_msg)
            result["analysis_error"] = error_msg

        return result

    def _analyze_audio_file(self, file_path: str) -> Dict[str, Any]:
        """Perform the actual audio analysis (blocking operation)."""
        try:
            # Load audio file
            y, sr = librosa.load(file_path, sr=self.sample_rate)

            # Ensure we have audio data
            if len(y) == 0:
                raise ValueError("Audio file appears to be empty")

            # Get duration for other analyses
            duration = librosa.get_duration(y=y, sr=sr)

            # Analyze different aspects
            bpm_data = self._analyze_tempo(y, sr)
            key_data = self._analyze_key(y, sr)
            energy_data = self._analyze_energy(y, sr)
            danceability_data = self._analyze_danceability(y, sr)
            valence_data = self._analyze_valence(y, sr)
            acoustic_data = self._analyze_acousticness(y, sr)
            instrumental_data = self._analyze_instrumentalness(y, sr)
            liveness_data = self._analyze_liveness(y, sr)
            speech_data = self._analyze_speechiness(y, sr)
            loudness_data = self._analyze_loudness(y, sr)
            
            # Enhanced analysis features
            style_data = self._analyze_track_style_internal(y, sr)
            mix_points_data = self._analyze_mix_points_internal(y, sr, duration, bpm_data)
            section_data = self._analyze_sections_internal(y, sr, duration)

            return {
                **bpm_data,
                **key_data,
                **energy_data,
                **danceability_data,
                **valence_data,
                **acoustic_data,
                **instrumental_data,
                **liveness_data,
                **speech_data,
                **loudness_data,
                **style_data,
                **mix_points_data,
                **section_data,
            }

        except Exception as e:
            raise Exception(f"Audio analysis failed: {str(e)}")

    def _analyze_tempo(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze tempo and beat information."""
        try:
            # Extract tempo and beats
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

            # Convert beat frames to timestamps (seconds)
            beat_timestamps = librosa.frames_to_time(beats, sr=sr) if beats is not None else []
            
            # Calculate beat intervals (time between consecutive beats)
            beat_intervals = []
            if len(beat_timestamps) > 1:
                beat_intervals = [beat_timestamps[i+1] - beat_timestamps[i] 
                                for i in range(len(beat_timestamps)-1)]
            
            # Calculate beat confidence using onset strength
            onset_envelope = librosa.onset.onset_strength(y=y, sr=sr)
            
            # Get beat confidence scores
            beat_confidence_scores = []
            if beats is not None and len(beats) > 0:
                # Sample onset strength at beat locations
                beat_frames = beats.astype(int)
                valid_frames = beat_frames[beat_frames < len(onset_envelope)]
                if len(valid_frames) > 0:
                    beat_confidence_scores = onset_envelope[valid_frames].tolist()
            
            # Calculate overall beat confidence (average strength at beat locations)
            overall_beat_confidence = float(np.mean(beat_confidence_scores)) if beat_confidence_scores else 0.0

            # Get more detailed tempo analysis using the new function location
            try:
                # Try the new location first (librosa >= 0.10.0)
                tempo_detailed = librosa.feature.rhythm.tempo(onset_envelope=onset_envelope, sr=sr)
            except AttributeError:
                # Fallback to old location for older versions
                tempo_detailed = librosa.beat.tempo(onset_envelope=onset_envelope, sr=sr)

            # Use the more detailed tempo if available
            if len(tempo_detailed) > 0:
                bpm = float(tempo_detailed[0])
            else:
                bpm = float(tempo)

            # Ensure BPM is in reasonable range
            if bpm < 60:
                bpm *= 2  # Double if too slow
            elif bpm > 200:
                bpm /= 2  # Halve if too fast

            # Calculate beat regularity (coefficient of variation of beat intervals)
            beat_regularity = 0.0
            if len(beat_intervals) > 1:
                mean_interval = np.mean(beat_intervals)
                std_interval = np.std(beat_intervals)
                if mean_interval > 0:
                    # Lower coefficient of variation = more regular beats
                    cv = std_interval / mean_interval
                    beat_regularity = max(0.0, 1.0 - cv)  # Convert to 0-1 scale

            return {
                "bpm": round(bpm, 2),
                "beat_count": len(beats) if beats is not None else 0,
                "beat_timestamps": [round(float(t), 4) for t in beat_timestamps],
                "beat_intervals": [round(float(interval), 4) for interval in beat_intervals],
                "beat_confidence": round(overall_beat_confidence, 3),
                "beat_confidence_scores": [round(float(score), 3) for score in beat_confidence_scores],
                "beat_regularity": round(beat_regularity, 3),
                "average_beat_interval": round(float(np.mean(beat_intervals)), 4) if beat_intervals else None,
            }

        except Exception as e:
            logger.warning(f"Tempo analysis failed: {e}")
            return {
                "bpm": None, 
                "beat_count": 0,
                "beat_timestamps": [],
                "beat_intervals": [],
                "beat_confidence": 0.0,
                "beat_confidence_scores": [],
                "beat_regularity": 0.0,
                "average_beat_interval": None,
            }

    def _analyze_key(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze musical key using chroma features."""
        try:
            # Extract chroma features
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)

            # Average chroma across time
            chroma_mean = np.mean(chroma, axis=1)

            # Find the dominant pitch class
            dominant_pitch = np.argmax(chroma_mean)

            # Map to key names (simplified)
            key_names = [
                "C",
                "C#",
                "D",
                "D#",
                "E",
                "F",
                "F#",
                "G",
                "G#",
                "A",
                "A#",
                "B",
            ]
            key = key_names[dominant_pitch]

            # Calculate confidence (how much stronger the dominant pitch is)
            confidence = float(chroma_mean[dominant_pitch] / np.sum(chroma_mean))

            # Simple major/minor detection based on chord patterns
            # This is a simplified approach - more sophisticated methods exist
            major_pattern = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])
            minor_pattern = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0])

            # Rotate patterns to match detected key
            major_rotated = np.roll(major_pattern, dominant_pitch)
            minor_rotated = np.roll(minor_pattern, dominant_pitch)

            # Calculate correlation with major and minor patterns
            major_corr = np.corrcoef(chroma_mean, major_rotated)[0, 1]
            minor_corr = np.corrcoef(chroma_mean, minor_rotated)[0, 1]

            # Determine if major or minor
            if not np.isnan(major_corr) and not np.isnan(minor_corr):
                if major_corr > minor_corr:
                    key_final = key
                else:
                    key_final = key + "m"
            else:
                key_final = key  # Default to major if correlation fails

            return {"key": key_final, "key_confidence": round(confidence, 3)}

        except Exception as e:
            logger.warning(f"Key analysis failed: {e}")
            return {"key": None, "key_confidence": 0.0}

    def _analyze_energy(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze energy and other audio characteristics."""
        try:
            # RMS energy
            rms = librosa.feature.rms(y=y)[0]
            energy = float(np.mean(rms))

            # Spectral centroid (brightness)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            brightness = float(np.mean(spectral_centroid))

            # Zero crossing rate (roughness indicator)
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            roughness = float(np.mean(zcr))

            # Spectral rolloff
            rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            rolloff_mean = float(np.mean(rolloff))

            # MFCC features for timbral analysis
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

            # Normalize energy to 0-1 scale (rough approximation)
            energy_normalized = min(energy * 10, 1.0)  # Scale factor may need adjustment

            return {
                "energy": round(float(energy_normalized), 3),
                "brightness": round(float(brightness), 2),
                "roughness": round(float(roughness), 3),
                "spectral_rolloff": round(float(rolloff_mean), 2),
                "mfcc_features": mfccs.tolist()
                if mfccs.size < 1000
                else None,  # Avoid huge arrays
            }

        except Exception as e:
            logger.warning(f"Energy analysis failed: {e}")
            return {
                "energy": None,
                "brightness": None,
                "roughness": None,
                "spectral_rolloff": None,
            }

    def _analyze_danceability(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze danceability based on rhythm and beat strength."""
        try:
            # Extract tempo and beat tracking
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # Beat strength and regularity
            onset_envelope = librosa.onset.onset_strength(y=y, sr=sr)
            
            # Calculate beat consistency (how regular the beats are)
            if len(beats) > 1:
                beat_intervals = np.diff(beats)
                beat_consistency = 1.0 - (np.std(beat_intervals) / np.mean(beat_intervals))
                beat_consistency = max(0.0, min(1.0, beat_consistency))
            else:
                beat_consistency = 0.0
            
            # Beat strength
            beat_strength = float(np.mean(onset_envelope))
            
            # Rhythm regularity using autocorrelation
            autocorr = np.correlate(onset_envelope, onset_envelope, mode='full')
            autocorr = autocorr[autocorr.size // 2:]
            
            # Find peaks in autocorrelation (indicates rhythmic patterns)
            if len(autocorr) > 1:
                rhythm_strength = float(np.max(autocorr[1:]) / autocorr[0])
            else:
                rhythm_strength = 0.0
            
            # Combine factors for danceability score
            danceability = (beat_consistency * 0.4 + 
                          min(beat_strength * 2, 1.0) * 0.4 + 
                          min(rhythm_strength, 1.0) * 0.2)
            
            return {"danceability": round(float(min(max(danceability, 0.0), 1.0)), 3)}
            
        except Exception as e:
            logger.warning(f"Danceability analysis failed: {e}")
            return {"danceability": None}

    def _analyze_valence(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze valence (musical positivity) based on harmonic and timbral features."""
        try:
            # Chroma features for harmonic content
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            
            # Major vs minor tendency (simplified)
            chroma_mean = np.mean(chroma, axis=1)
            
            # Major chord pattern (C, E, G positions in chroma)
            major_pattern = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])
            minor_pattern = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0])
            
            # Calculate correlation with major/minor patterns
            major_corr = np.corrcoef(chroma_mean, major_pattern)[0, 1] if not np.isnan(np.corrcoef(chroma_mean, major_pattern)[0, 1]) else 0
            minor_corr = np.corrcoef(chroma_mean, minor_pattern)[0, 1] if not np.isnan(np.corrcoef(chroma_mean, minor_pattern)[0, 1]) else 0
            
            # Spectral centroid (brightness correlates with positivity)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            brightness = np.mean(spectral_centroid)
            brightness_normalized = min(brightness / 4000, 1.0)  # Normalize to 0-1
            
            # Tempo factor (faster tempo often correlates with higher valence)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            tempo_factor = min(tempo / 140, 1.0)  # Normalize around 140 BPM
            
            # Combine factors
            harmonic_positivity = max(major_corr - minor_corr, 0.0)
            valence = (harmonic_positivity * 0.4 + 
                      brightness_normalized * 0.3 + 
                      tempo_factor * 0.3)
            
            # Ensure valence is a Python float before rounding
            valence_float = float(min(max(valence, 0.0), 1.0))
            
            return {"valence": round(valence_float, 3)}
            
        except Exception as e:
            logger.warning(f"Valence analysis failed: {e}")
            return {"valence": None}

    def _analyze_acousticness(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze acousticness based on spectral characteristics."""
        try:
            # Spectral features that indicate acoustic vs electric instruments
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            
            # Zero crossing rate (lower for acoustic instruments)
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            
            # MFCC features (acoustic instruments have different timbral characteristics)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_var = np.var(mfccs, axis=1)
            
            # Lower spectral centroid and bandwidth often indicate acoustic instruments
            centroid_score = 1.0 - min(np.mean(spectral_centroid) / 4000, 1.0)
            bandwidth_score = 1.0 - min(np.mean(spectral_bandwidth) / 2000, 1.0)
            zcr_score = 1.0 - min(np.mean(zcr) * 10, 1.0)
            
            # Combine factors
            acousticness = (centroid_score * 0.4 + 
                           bandwidth_score * 0.3 + 
                           zcr_score * 0.3)
            
            return {"acousticness": round(float(min(max(acousticness, 0.0), 1.0)), 3)}
            
        except Exception as e:
            logger.warning(f"Acousticness analysis failed: {e}")
            return {"acousticness": None}

    def _analyze_instrumentalness(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze instrumentalness based on vocal detection."""
        try:
            # MFCC features are good for detecting vocal content
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # Spectral centroid and rolloff
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            
            # Zero crossing rate (vocals have specific patterns)
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            
            # Chroma features (vocals often follow harmonic patterns)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_var = np.var(chroma, axis=1)
            
            # Vocal frequency range detection (roughly 80-1100 Hz for human voice)
            stft = librosa.stft(y)
            freqs = librosa.fft_frequencies(sr=sr)
            vocal_range_mask = (freqs >= 80) & (freqs <= 1100)
            vocal_energy = np.mean(np.abs(stft[vocal_range_mask, :]))
            total_energy = np.mean(np.abs(stft))
            vocal_ratio = vocal_energy / total_energy if total_energy > 0 else 0
            
            # Lower vocal ratio indicates higher instrumentalness
            instrumentalness = 1.0 - min(vocal_ratio * 3, 1.0)
            
            return {"instrumentalness": round(float(min(max(instrumentalness, 0.0), 1.0)), 3)}
            
        except Exception as e:
            logger.warning(f"Instrumentalness analysis failed: {e}")
            return {"instrumentalness": None}

    def _analyze_liveness(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze liveness based on audience detection and reverb."""
        try:
            # Spectral features that might indicate live recording
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            
            # RMS energy variation (live recordings often have more dynamic range)
            rms = librosa.feature.rms(y=y)[0]
            rms_var = np.var(rms)
            
            # Zero crossing rate variation
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            zcr_var = np.var(zcr)
            
            # Spectral contrast (live recordings might have different contrast patterns)
            spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
            contrast_var = np.var(spectral_contrast, axis=1)
            
            # Higher variation in spectral features might indicate live recording
            energy_variation = min(rms_var * 100, 1.0)
            spectral_variation = min(np.mean(contrast_var) * 10, 1.0)
            
            # Combine factors (this is a simplified approach)
            liveness = (energy_variation * 0.6 + spectral_variation * 0.4)
            
            # Ensure liveness is a Python float before rounding
            liveness_float = float(min(max(liveness, 0.0), 1.0))
            
            return {"liveness": round(liveness_float, 3)}
            
        except Exception as e:
            logger.warning(f"Liveness analysis failed: {e}")
            return {"liveness": None}

    def _analyze_speechiness(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze speechiness based on vocal and speech patterns."""
        try:
            # MFCC features are excellent for speech detection
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # Zero crossing rate (speech has characteristic patterns)
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            zcr_mean = np.mean(zcr)
            
            # Spectral centroid (speech has specific frequency characteristics)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            centroid_mean = np.mean(spectral_centroid)
            
            # Speech frequency range (roughly 300-3400 Hz for speech)
            stft = librosa.stft(y)
            freqs = librosa.fft_frequencies(sr=sr)
            speech_range_mask = (freqs >= 300) & (freqs <= 3400)
            speech_energy = np.mean(np.abs(stft[speech_range_mask, :]))
            total_energy = np.mean(np.abs(stft))
            speech_ratio = speech_energy / total_energy if total_energy > 0 else 0
            
            # Rhythm analysis (speech has different rhythm than music)
            onset_envelope = librosa.onset.onset_strength(y=y, sr=sr)
            onset_var = np.var(onset_envelope)
            
            # Combine factors for speechiness
            zcr_factor = min(zcr_mean * 20, 1.0)  # Speech typically has higher ZCR
            speech_freq_factor = min(speech_ratio * 2, 1.0)
            rhythm_factor = min(onset_var * 5, 1.0)  # Speech has more irregular rhythm
            
            speechiness = (speech_freq_factor * 0.5 + 
                          zcr_factor * 0.3 + 
                          rhythm_factor * 0.2)
            
            return {"speechiness": round(float(min(max(speechiness, 0.0), 1.0)), 3)}
            
        except Exception as e:
            logger.warning(f"Speechiness analysis failed: {e}")
            return {"speechiness": None}

    def _analyze_loudness(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze loudness in dB."""
        try:
            # RMS energy
            rms = librosa.feature.rms(y=y)[0]
            rms_mean = np.mean(rms)
            
            # Convert to dB (similar to Spotify's loudness measure)
            # Reference: 20 * log10(rms) but we need to handle the scale
            if rms_mean > 0:
                loudness_db = 20 * np.log10(rms_mean)
                # Spotify's loudness is typically between -60 and 0 dB
                # Adjust our scale to match approximately
                loudness_db = max(loudness_db, -60.0)  # Floor at -60 dB
            else:
                loudness_db = -60.0
            
            return {"loudness": round(float(loudness_db), 3)}
            
        except Exception as e:
            logger.warning(f"Loudness analysis failed: {e}")
            return {"loudness": None}

    def calculate_compatibility(
        self, track_a: Dict[str, Any], track_b: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate compatibility scores between two tracks."""
        compatibility = {
            "bpm_compatibility": 0.0,
            "key_compatibility": 0.0,
            "energy_compatibility": 0.0,
            "style_compatibility": 0.0,
            "vocal_compatibility": 0.0,
            "overall_score": 0.0,
        }

        try:
            # BPM compatibility (within 6% is considered compatible)
            if track_a.get("bpm") and track_b.get("bpm"):
                bpm_a, bpm_b = track_a["bpm"], track_b["bpm"]
                bpm_diff = abs(bpm_a - bpm_b) / max(bpm_a, bpm_b)
                compatibility["bpm_compatibility"] = max(0.0, 1.0 - (bpm_diff / 0.06))

            # Key compatibility (harmonic mixing)
            if track_a.get("key") and track_b.get("key"):
                key_score = self._calculate_key_compatibility(
                    track_a["key"], track_b["key"]
                )
                compatibility["key_compatibility"] = key_score

            # Energy compatibility - enhanced to consider intro/outro energy
            energy_a = track_a.get("energy", 0.5)
            energy_b = track_b.get("energy", 0.5)
            
            # If we have intro/outro energy data, use that for better transition matching
            outro_energy_a = track_a.get("outro_energy", energy_a)
            intro_energy_b = track_b.get("intro_energy", energy_b)
            
            energy_diff = abs(outro_energy_a - intro_energy_b)
            compatibility["energy_compatibility"] = max(0.0, 1.0 - energy_diff)

            # Style compatibility - check if both tracks have style data
            style_a = track_a.get("dominant_style")
            style_b = track_b.get("dominant_style")
            if style_a and style_b:
                if style_a == style_b:
                    compatibility["style_compatibility"] = 1.0
                elif self._are_compatible_styles(style_a, style_b):
                    compatibility["style_compatibility"] = 0.7
                else:
                    compatibility["style_compatibility"] = 0.3
            else:
                compatibility["style_compatibility"] = 0.5  # Neutral if no style data

            # Vocal compatibility - avoid vocal clashing
            vocal_a = track_a.get("vocal_centric", track_a.get("speechiness", 0.0))
            vocal_b = track_b.get("vocal_centric", track_b.get("speechiness", 0.0))
            
            # Strong vocals in both tracks can clash
            vocal_clash = vocal_a > 0.7 and vocal_b > 0.7
            if vocal_clash:
                compatibility["vocal_compatibility"] = 0.3
            else:
                # Smooth vocal transition
                vocal_diff = abs(vocal_a - vocal_b)
                compatibility["vocal_compatibility"] = max(0.3, 1.0 - vocal_diff)

            # Overall score with updated weights
            scores = [
                compatibility["bpm_compatibility"] * 0.25,    # BPM important but not everything
                compatibility["key_compatibility"] * 0.20,   # Key harmony
                compatibility["energy_compatibility"] * 0.30, # Energy flow most important  
                compatibility["style_compatibility"] * 0.15,  # Style consistency
                compatibility["vocal_compatibility"] * 0.10,  # Vocal considerations
            ]
            compatibility["overall_score"] = sum(scores)

        except Exception as e:
            logger.error(f"Error calculating compatibility: {e}")

        return compatibility

    def _calculate_key_compatibility(self, key_a: str, key_b: str) -> float:
        """Calculate harmonic compatibility between two keys."""
        # Simplified harmonic mixing rules
        # Perfect matches
        if key_a == key_b:
            return 1.0

        # Remove 'm' for minor keys to get root note
        root_a = key_a.replace("m", "")
        root_b = key_b.replace("m", "")
        is_minor_a = "m" in key_a
        is_minor_b = "m" in key_b

        # Key circle positions (Camelot wheel simplified)
        key_positions = {
            "C": 0,
            "G": 1,
            "D": 2,
            "A": 3,
            "E": 4,
            "B": 5,
            "F#": 6,
            "C#": 7,
            "G#": 8,
            "D#": 9,
            "A#": 10,
            "F": 11,
        }

        if root_a not in key_positions or root_b not in key_positions:
            return 0.5  # Unknown compatibility

        pos_a = key_positions[root_a]
        pos_b = key_positions[root_b]

        # Calculate distance on circle of fifths
        distance = min(abs(pos_a - pos_b), 12 - abs(pos_a - pos_b))

        # Compatible keys (distance 0, 1, or 7 on circle of fifths)
        if distance == 0:
            # Same root note
            if is_minor_a == is_minor_b:
                return 1.0  # Same key
            else:
                return 0.8  # Relative major/minor
        elif distance == 1:
            return 0.7  # Adjacent keys
        elif distance == 7:
            return 0.6  # Perfect fifth
        elif distance == 2:
            return 0.4  # Whole tone
        else:
            return 0.2  # Less compatible

    def find_mix_points(self, file_path: str, duration: float, analysis_data: Dict[str, Any] = None) -> Dict[str, float]:
        """Find optimal mix in/out points for a track using beat and energy analysis."""
        try:
            # If we don't have analysis data, load and analyze the file
            if analysis_data is None:
                y, sr = librosa.load(file_path, sr=self.sample_rate)
                if len(y) == 0:
                    raise ValueError("Audio file appears to be empty")
                
                # Get beat and energy data
                tempo_data = self._analyze_tempo(y, sr)
                energy_data = self._analyze_energy(y, sr)
                beat_timestamps = tempo_data.get("beat_timestamps", [])
                
                # Calculate RMS energy over time for section analysis
                rms = librosa.feature.rms(y=y, hop_length=512)[0]
                rms_times = librosa.frames_to_time(range(len(rms)), sr=sr, hop_length=512)
            else:
                # Use provided analysis data
                beat_timestamps = analysis_data.get("beat_timestamps", [])
                # For existing analysis, we'll need to reload audio for energy profile
                if beat_timestamps:
                    y, sr = librosa.load(file_path, sr=self.sample_rate)
                    rms = librosa.feature.rms(y=y, hop_length=512)[0]
                    rms_times = librosa.frames_to_time(range(len(rms)), sr=sr, hop_length=512)
                else:
                    rms = None
                    rms_times = None

            # Find optimal mix in point (intro analysis)
            mix_in_point = self._find_optimal_mix_in_point(beat_timestamps, rms, rms_times, duration)
            
            # Find optimal mix out point (outro analysis)  
            mix_out_point = self._find_optimal_mix_out_point(beat_timestamps, rms, rms_times, duration)

            # Ensure we have at least some playable content
            if mix_out_point <= mix_in_point:
                mix_in_point = duration * 0.1
                mix_out_point = duration * 0.9

            # Find additional mix-friendly sections
            mixable_sections = self._find_mixable_sections(beat_timestamps, rms, rms_times, duration)

            return {
                "mix_in_point": round(mix_in_point, 2),
                "mix_out_point": round(mix_out_point, 2),
                "playable_duration": round(mix_out_point - mix_in_point, 2),
                "mixable_sections": mixable_sections,
                "intro_energy": self._calculate_section_energy(rms, rms_times, 0, min(30, duration * 0.2)) if rms is not None else None,
                "outro_energy": self._calculate_section_energy(rms, rms_times, max(0, duration - 30), duration) if rms is not None else None,
            }

        except Exception as e:
            logger.error(f"Error finding mix points for {file_path}: {e}")
            return {
                "mix_in_point": 0.0,
                "mix_out_point": duration,
                "playable_duration": duration,
                "mixable_sections": [],
                "intro_energy": None,
                "outro_energy": None,
            }

    def _find_optimal_mix_in_point(self, beat_timestamps: List[float], rms: np.ndarray, rms_times: np.ndarray, duration: float) -> float:
        """Find optimal mix in point using beat alignment and energy analysis."""
        try:
            # Default fallback
            default_mix_in = min(16.0, duration * 0.15)
            
            if not beat_timestamps or rms is None:
                return default_mix_in
                
            # Look for energy buildup in intro (first 45 seconds)
            intro_end = min(45.0, duration * 0.3)
            intro_mask = rms_times <= intro_end
            intro_rms = rms[intro_mask]
            intro_times = rms_times[intro_mask]
            
            if len(intro_rms) < 2:
                return default_mix_in
                
            # Find where energy stabilizes or peaks
            # Look for the point where energy becomes consistent (good for mixing)
            window_size = min(20, len(intro_rms) // 4)  # 4 windows in intro
            energy_stability_scores = []
            
            for i in range(window_size, len(intro_rms) - window_size):
                window = intro_rms[i-window_size:i+window_size]
                stability = 1.0 - (np.std(window) / (np.mean(window) + 1e-8))
                energy_level = np.mean(window)
                # Prefer points with good energy and stability
                score = stability * 0.6 + energy_level * 0.4
                energy_stability_scores.append((intro_times[i], score))
            
            if not energy_stability_scores:
                return default_mix_in
                
            # Find the best energy-stable point
            best_time, _ = max(energy_stability_scores, key=lambda x: x[1])
            
            # Align to nearest beat if we have beat data
            if beat_timestamps:
                # Find beat closest to our energy-based point
                beat_diffs = [abs(beat - best_time) for beat in beat_timestamps if beat <= intro_end]
                if beat_diffs:
                    min_diff_idx = np.argmin(beat_diffs)
                    aligned_beats = [beat for beat in beat_timestamps if beat <= intro_end]
                    if min_diff_idx < len(aligned_beats):
                        best_time = aligned_beats[min_diff_idx]
            
            # Ensure reasonable bounds
            mix_in_point = max(8.0, min(best_time, intro_end))
            return mix_in_point
            
        except Exception as e:
            logger.warning(f"Error finding optimal mix in point: {e}")
            return min(16.0, duration * 0.15)

    def _find_optimal_mix_out_point(self, beat_timestamps: List[float], rms: np.ndarray, rms_times: np.ndarray, duration: float) -> float:
        """Find optimal mix out point using beat alignment and energy analysis."""
        try:
            # Default fallback  
            default_mix_out = max(duration - 16.0, duration * 0.85)
            
            if not beat_timestamps or rms is None:
                return default_mix_out
                
            # Look for energy fade or natural ending in outro (last 45 seconds)
            outro_start = max(0, duration - 45.0)
            outro_mask = rms_times >= outro_start
            outro_rms = rms[outro_mask]
            outro_times = rms_times[outro_mask]
            
            if len(outro_rms) < 2:
                return default_mix_out
                
            # Look for energy fade or stable low-energy section good for mixing out
            # Find where energy drops significantly or becomes stable at lower level
            window_size = min(20, len(outro_rms) // 4)
            fade_scores = []
            
            for i in range(window_size, len(outro_rms) - window_size):
                before_window = outro_rms[max(0, i-window_size*2):i]
                after_window = outro_rms[i:i+window_size]
                
                if len(before_window) > 0 and len(after_window) > 0:
                    # Score based on energy drop and stability in after window
                    energy_drop = np.mean(before_window) - np.mean(after_window)
                    after_stability = 1.0 - (np.std(after_window) / (np.mean(after_window) + 1e-8))
                    # Prefer points with significant energy drop and stable after section
                    score = max(0, energy_drop) * 0.7 + after_stability * 0.3
                    fade_scores.append((outro_times[i], score))
            
            if not fade_scores:
                return default_mix_out
                
            # Find the best fade point
            best_time, _ = max(fade_scores, key=lambda x: x[1])
            
            # Align to nearest beat if we have beat data
            if beat_timestamps:
                # Find beat closest to our energy-based point
                relevant_beats = [beat for beat in beat_timestamps if beat >= outro_start and beat <= duration - 4.0]
                if relevant_beats:
                    beat_diffs = [abs(beat - best_time) for beat in relevant_beats]
                    min_diff_idx = np.argmin(beat_diffs)
                    best_time = relevant_beats[min_diff_idx]
            
            # Ensure reasonable bounds (leave at least 4 seconds at end)
            mix_out_point = min(best_time, duration - 4.0)
            mix_out_point = max(mix_out_point, duration * 0.7)  # Don't go too early
            return mix_out_point
            
        except Exception as e:
            logger.warning(f"Error finding optimal mix out point: {e}")
            return max(duration - 16.0, duration * 0.85)

    def _find_mixable_sections(self, beat_timestamps: List[float], rms: np.ndarray, rms_times: np.ndarray, duration: float) -> List[Dict[str, Any]]:
        """Find additional sections suitable for mixing (breaks, buildups, etc.)."""
        sections = []
        
        if rms is None or len(rms) < 10:
            return sections
            
        try:
            # Find low-energy sections that could be good for mixing
            # These might be breakdowns, instrumental sections, etc.
            window_size = min(50, len(rms) // 10)  # ~2-3 second windows
            
            for i in range(0, len(rms) - window_size, window_size // 2):  # 50% overlap
                window = rms[i:i+window_size]
                window_times = rms_times[i:i+window_size]
                
                start_time = float(window_times[0])
                end_time = float(window_times[-1])
                
                # Skip if too close to intro/outro (already handled)
                if start_time < 20 or end_time > duration - 20:
                    continue
                    
                avg_energy = float(np.mean(window))
                energy_stability = float(1.0 - (np.std(window) / (np.mean(window) + 1e-8)))
                
                # Look for sections with low-medium energy and high stability
                if avg_energy < 0.3 and energy_stability > 0.7:  # Quiet, stable sections
                    # Check if there are beats in this section for better mixing
                    section_beats = [b for b in beat_timestamps if start_time <= b <= end_time]
                    has_beats = len(section_beats) > 0
                    
                    sections.append({
                        "type": "breakdown" if has_beats else "ambient",
                        "start": round(start_time, 2),
                        "end": round(end_time, 2),
                        "duration": round(end_time - start_time, 2),
                        "energy": round(avg_energy, 3),
                        "stability": round(energy_stability, 3),
                        "has_beats": has_beats,
                        "beat_count": len(section_beats)
                    })
            
            # Sort by suitability score (stability * (1-energy) for quiet stable sections)
            sections.sort(key=lambda s: s["stability"] * (1 - s["energy"]), reverse=True)
            
            # Return top 3 mixable sections
            return sections[:3]
            
        except Exception as e:
            logger.warning(f"Error finding mixable sections: {e}")
            return []

    def _calculate_section_energy(self, rms: np.ndarray, rms_times: np.ndarray, start_time: float, end_time: float) -> float:
        """Calculate average energy for a specific time section."""
        if rms is None or rms_times is None:
            return 0.0
            
        try:
            mask = (rms_times >= start_time) & (rms_times <= end_time)
            section_rms = rms[mask]
            return float(np.mean(section_rms)) if len(section_rms) > 0 else 0.0
        except Exception:
            return 0.0

    def analyze_track_style(self, file_path: str) -> Dict[str, Any]:
        """Analyze track style in a genre-agnostic way for better mixing compatibility."""
        try:
            y, sr = librosa.load(file_path, sr=self.sample_rate)
            
            # Analyze different style characteristics
            beat_driven_score = self._analyze_beat_driven(y, sr)
            melodic_focus_score = self._analyze_melodic_focus(y, sr)
            ambient_texture_score = self._analyze_ambient_texture(y, sr)
            vocal_centric_score = self._analyze_vocal_centric(y, sr)
            acoustic_score = self._analyze_acoustic_vs_electronic(y, sr)
            
            style_scores = {
                "beat_driven": beat_driven_score,
                "melodic_focus": melodic_focus_score,
                "ambient_texture": ambient_texture_score,
                "vocal_centric": vocal_centric_score,
                "acoustic": acoustic_score,
                "electronic": 1.0 - acoustic_score
            }
            
            # Determine dominant style
            dominant_style = max(style_scores.items(), key=lambda x: x[1])[0]
            
            return {
                "dominant_style": dominant_style,
                "style_scores": style_scores,
                "style_confidence": style_scores[dominant_style]
            }
            
        except Exception as e:
            logger.warning(f"Style analysis failed: {e}")
            return {
                "dominant_style": "unknown",
                "style_scores": {},
                "style_confidence": 0.0
            }

    def _analyze_beat_driven(self, y: np.ndarray, sr: int) -> float:
        """Analyze how beat-driven a track is."""
        try:
            # Strong, regular beats indicate beat-driven music
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            onset_envelope = librosa.onset.onset_strength(y=y, sr=sr)
            
            if len(beats) < 2:
                return 0.0
                
            # Beat regularity
            beat_intervals = np.diff(beats)
            regularity = 1.0 - (np.std(beat_intervals) / np.mean(beat_intervals)) if np.mean(beat_intervals) > 0 else 0.0
            regularity = max(0.0, min(1.0, regularity))
            
            # Beat strength
            beat_strength = np.mean(onset_envelope) if len(onset_envelope) > 0 else 0.0
            beat_strength = min(beat_strength * 2, 1.0)  # Normalize
            
            # Combine factors
            beat_driven = regularity * 0.6 + beat_strength * 0.4
            return float(beat_driven)
            
        except Exception:
            return 0.0

    def _analyze_melodic_focus(self, y: np.ndarray, sr: int) -> float:
        """Analyze melodic content strength."""
        try:
            # Pitch tracking and harmonic content
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            
            # Melodic content indicators
            chroma_var = np.var(chroma, axis=1)  # Pitch variation over time
            harmonic_strength = np.mean(chroma_var)
            
            # Spectral centroid variation (melodic movement)
            centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            centroid_var = np.var(centroid)
            melody_movement = min(centroid_var / 100000, 1.0)  # Normalize
            
            melodic_focus = harmonic_strength * 0.6 + melody_movement * 0.4
            return float(min(melodic_focus, 1.0))
            
        except Exception:
            return 0.0

    def _analyze_ambient_texture(self, y: np.ndarray, sr: int) -> float:
        """Analyze ambient/atmospheric texture."""
        try:
            # Low beat strength, high spectral complexity, reverb-like characteristics
            onset_envelope = librosa.onset.onset_strength(y=y, sr=sr)
            beat_strength = np.mean(onset_envelope)
            
            # Spectral characteristics of ambient music
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            
            # Low beat strength, spread spectrum = ambient
            low_beat_score = 1.0 - min(beat_strength * 3, 1.0)
            spectral_spread = np.mean(spectral_bandwidth) / 1000  # Normalize
            spectral_spread = min(spectral_spread, 1.0)
            
            ambient_score = low_beat_score * 0.6 + spectral_spread * 0.4
            return float(ambient_score)
            
        except Exception:
            return 0.0

    def _analyze_vocal_centric(self, y: np.ndarray, sr: int) -> float:
        """Analyze how vocal-centric a track is."""
        try:
            # Vocal frequency range and characteristics
            stft = librosa.stft(y)
            freqs = librosa.fft_frequencies(sr=sr)
            
            # Vocal range (roughly 80-1100 Hz)
            vocal_range_mask = (freqs >= 80) & (freqs <= 1100)
            vocal_energy = np.mean(np.abs(stft[vocal_range_mask, :]))
            total_energy = np.mean(np.abs(stft))
            vocal_ratio = vocal_energy / total_energy if total_energy > 0 else 0.0
            
            # MFCC characteristics (vocals have distinctive patterns)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            # Vocal-like MFCC variance patterns
            mfcc_vocal_score = np.mean(np.var(mfccs[1:4], axis=1)) / 10  # Normalize
            mfcc_vocal_score = min(mfcc_vocal_score, 1.0)
            
            vocal_centric = vocal_ratio * 0.7 + mfcc_vocal_score * 0.3
            return float(min(vocal_centric, 1.0))
            
        except Exception:
            return 0.0

    def _analyze_acoustic_vs_electronic(self, y: np.ndarray, sr: int) -> float:
        """Analyze acoustic vs electronic characteristics (returns acoustic score)."""
        try:
            # Spectral characteristics
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            
            # Acoustic instruments typically have:
            # - Lower spectral centroid 
            # - Lower bandwidth
            # - Lower zero crossing rate
            centroid_score = 1.0 - min(np.mean(spectral_centroid) / 4000, 1.0)
            bandwidth_score = 1.0 - min(np.mean(spectral_bandwidth) / 2000, 1.0)
            zcr_score = 1.0 - min(np.mean(zcr) * 10, 1.0)
            
            acoustic_score = (centroid_score * 0.4 + bandwidth_score * 0.3 + zcr_score * 0.3)
            return float(min(max(acoustic_score, 0.0), 1.0))
            
        except Exception:
            return 0.5  # Neutral if analysis fails

    def _are_compatible_styles(self, style_a: str, style_b: str) -> bool:
        """Check if two musical styles are compatible for mixing."""
        # Define style compatibility matrix
        compatible_pairs = {
            ("beat_driven", "electronic"),
            ("beat_driven", "melodic_focus"),
            ("melodic_focus", "acoustic"),
            ("ambient_texture", "melodic_focus"),
            ("acoustic", "melodic_focus"),
            ("electronic", "beat_driven"),
        }
        
        # Check both directions
        return (style_a, style_b) in compatible_pairs or (style_b, style_a) in compatible_pairs

    def calculate_enhanced_compatibility(
        self, track_a_path: str, track_b_path: str, track_a_data: Dict[str, Any] = None, track_b_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Calculate enhanced compatibility with full style analysis."""
        try:
            # Get style analysis for both tracks if not provided
            if not track_a_data or "dominant_style" not in track_a_data:
                style_a = self.analyze_track_style(track_a_path)
                track_a_data = {**(track_a_data or {}), **style_a}
                
            if not track_b_data or "dominant_style" not in track_b_data:
                style_b = self.analyze_track_style(track_b_path)
                track_b_data = {**(track_b_data or {}), **style_b}

            # Calculate base compatibility
            compatibility = self.calculate_compatibility(track_a_data, track_b_data)
            
            # Add enhanced metrics
            compatibility.update({
                "style_similarity": self._calculate_style_similarity(track_a_data, track_b_data),
                "genre_agnostic_match": self._calculate_genre_agnostic_match(track_a_data, track_b_data),
                "transition_difficulty": self._assess_transition_difficulty(track_a_data, track_b_data),
                "recommended_technique": self._recommend_transition_technique(compatibility),
            })
            
            return compatibility
            
        except Exception as e:
            logger.error(f"Error calculating enhanced compatibility: {e}")
            return {"error": str(e)}

    def _calculate_style_similarity(self, track_a: Dict[str, Any], track_b: Dict[str, Any]) -> float:
        """Calculate detailed style similarity score."""
        try:
            scores_a = track_a.get("style_scores", {})
            scores_b = track_b.get("style_scores", {})
            
            if not scores_a or not scores_b:
                return 0.5
                
            # Calculate cosine similarity between style vectors
            common_styles = set(scores_a.keys()) & set(scores_b.keys())
            if not common_styles:
                return 0.0
                
            dot_product = sum(scores_a[style] * scores_b[style] for style in common_styles)
            magnitude_a = sum(scores_a[style] ** 2 for style in common_styles) ** 0.5
            magnitude_b = sum(scores_b[style] ** 2 for style in common_styles) ** 0.5
            
            if magnitude_a * magnitude_b == 0:
                return 0.0
                
            similarity = dot_product / (magnitude_a * magnitude_b)
            return float(max(0.0, min(1.0, similarity)))
            
        except Exception:
            return 0.5

    def _calculate_genre_agnostic_match(self, track_a: Dict[str, Any], track_b: Dict[str, Any]) -> float:
        """Calculate how well tracks match regardless of specific genre."""
        try:
            # Focus on mixing-relevant characteristics
            factors = []
            
            # Rhythmic compatibility
            if track_a.get("beat_regularity") and track_b.get("beat_regularity"):
                rhythm_match = 1.0 - abs(track_a["beat_regularity"] - track_b["beat_regularity"])
                factors.append(("rhythm", rhythm_match, 0.3))
            
            # Dynamic range compatibility  
            if track_a.get("energy") and track_b.get("energy"):
                energy_match = 1.0 - abs(track_a["energy"] - track_b["energy"])
                factors.append(("energy", energy_match, 0.25))
                
            # Instrumental vs vocal balance
            if track_a.get("instrumentalness") and track_b.get("instrumentalness"):
                instrumental_match = 1.0 - abs(track_a["instrumentalness"] - track_b["instrumentalness"])
                factors.append(("instrumental", instrumental_match, 0.2))
                
            # Acoustic vs electronic balance
            acoustic_a = track_a.get("acousticness", 0.5)
            acoustic_b = track_b.get("acousticness", 0.5)
            acoustic_match = 1.0 - abs(acoustic_a - acoustic_b)
            factors.append(("acoustic", acoustic_match, 0.25))
            
            if not factors:
                return 0.5
                
            # Weighted average
            total_weight = sum(weight for _, _, weight in factors)
            weighted_sum = sum(score * weight for _, score, weight in factors)
            
            return float(weighted_sum / total_weight)
            
        except Exception:
            return 0.5

    def _assess_transition_difficulty(self, track_a: Dict[str, Any], track_b: Dict[str, Any]) -> str:
        """Assess how difficult the transition between tracks will be."""
        try:
            compatibility = self.calculate_compatibility(track_a, track_b)
            overall_score = compatibility["overall_score"]
            
            if overall_score >= 0.8:
                return "easy"
            elif overall_score >= 0.6:
                return "moderate"
            elif overall_score >= 0.4:
                return "challenging"
            else:
                return "difficult"
                
        except Exception:
            return "unknown"

    def _recommend_transition_technique(self, compatibility: Dict[str, float]) -> str:
        """Recommend transition technique based on compatibility scores."""
        overall_score = compatibility.get("overall_score", 0.0)
        bpm_compat = compatibility.get("bpm_compatibility", 0.0)
        energy_compat = compatibility.get("energy_compatibility", 0.0)
        
        if overall_score >= 0.8:
            return "smooth_blend"
        elif bpm_compat >= 0.7 and energy_compat >= 0.6:
            return "beatmatch_crossfade"
        elif overall_score >= 0.5:
            return "quick_cut"
        else:
            return "gap_transition"

    def _analyze_track_style_internal(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Internal method to analyze track style and return database fields."""
        try:
            # Calculate style scores
            beat_driven = self._analyze_beat_driven(y, sr)
            melodic_focus = self._analyze_melodic_focus(y, sr)
            ambient_texture = self._analyze_ambient_texture(y, sr)
            vocal_centric = self._analyze_vocal_centric(y, sr)
            acoustic_vs_electronic = self._analyze_acoustic_vs_electronic(y, sr)
            
            style_scores = {
                "beat_driven": round(beat_driven, 3),
                "melodic_focus": round(melodic_focus, 3),
                "ambient_texture": round(ambient_texture, 3),
                "vocal_centric": round(vocal_centric, 3),
                "acoustic_vs_electronic": round(acoustic_vs_electronic, 3),
            }
            
            # Determine dominant style
            max_score = max(style_scores.values())
            dominant_style = max(style_scores, key=style_scores.get)
            
            # Calculate confidence as the difference between highest and second highest
            sorted_scores = sorted(style_scores.values(), reverse=True)
            confidence = (sorted_scores[0] - sorted_scores[1]) if len(sorted_scores) > 1 else sorted_scores[0]
            
            return {
                "dominant_style": dominant_style,
                "style_scores": style_scores,
                "style_confidence": round(confidence, 3),
            }
            
        except Exception as e:
            logger.warning(f"Style analysis failed: {e}")
            return {
                "dominant_style": None,
                "style_scores": None,
                "style_confidence": 0.0,
            }

    def _analyze_mix_points_internal(self, y: np.ndarray, sr: int, duration: float, bpm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to analyze mix points and return database fields."""
        try:
            # Get RMS energy for analysis
            rms = librosa.feature.rms(y=y)[0]
            rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
            
            beat_timestamps = bpm_data.get("beat_timestamps", [])
            
            # Find optimal mix points
            mix_in_point = self._find_optimal_mix_in_point(beat_timestamps, rms, rms_times, duration)
            mix_out_point = self._find_optimal_mix_out_point(beat_timestamps, rms, rms_times, duration)
            mixable_sections = self._find_mixable_sections(beat_timestamps, rms, rms_times, duration)
            
            return {
                "mix_in_point": round(mix_in_point, 3),
                "mix_out_point": round(mix_out_point, 3),
                "mixable_sections": mixable_sections,
            }
            
        except Exception as e:
            logger.warning(f"Mix points analysis failed: {e}")
            return {
                "mix_in_point": None,
                "mix_out_point": None,
                "mixable_sections": None,
            }

    def _analyze_sections_internal(self, y: np.ndarray, sr: int, duration: float) -> Dict[str, Any]:
        """Internal method to analyze track sections and return database fields."""
        try:
            # Get RMS energy for section analysis
            rms = librosa.feature.rms(y=y)[0]
            rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
            
            # Analyze intro/outro sections
            intro_end = self._detect_intro_end(rms, rms_times, duration)
            outro_start = self._detect_outro_start(rms, rms_times, duration)
            
            # Calculate section energies
            intro_energy = self._calculate_section_energy(rms, rms_times, 0, intro_end)
            outro_energy = self._calculate_section_energy(rms, rms_times, outro_start, duration)
            
            # Create energy profile (simplified - just sample at regular intervals)
            energy_profile = self._create_energy_profile(rms, rms_times, duration)
            
            # Analyze vocal vs instrumental sections
            vocal_sections, instrumental_sections = self._analyze_vocal_sections(y, sr, duration)
            
            return {
                "intro_end": round(intro_end, 3),
                "outro_start": round(outro_start, 3),
                "intro_energy": round(intro_energy, 3),
                "outro_energy": round(outro_energy, 3),
                "energy_profile": energy_profile,
                "vocal_sections": vocal_sections,
                "instrumental_sections": instrumental_sections,
            }
            
        except Exception as e:
            logger.warning(f"Section analysis failed: {e}")
            return {
                "intro_end": None,
                "outro_start": None,
                "intro_energy": None,
                "outro_energy": None,
                "energy_profile": None,
                "vocal_sections": None,
                "instrumental_sections": None,
            }

    def _detect_intro_end(self, rms: np.ndarray, rms_times: np.ndarray, duration: float) -> float:
        """Detect when the intro section ends."""
        # Look for energy stabilization after initial buildup
        max_intro_duration = min(60.0, duration * 0.3)  # Max 60s or 30% of track
        intro_end_idx = min(len(rms) - 1, int(max_intro_duration / (rms_times[1] - rms_times[0])))
        
        # Find the point where energy becomes more stable
        window_size = max(1, len(rms) // 20)  # 5% of track
        energy_variance = []
        
        for i in range(window_size, intro_end_idx):
            window = rms[i-window_size:i+window_size]
            variance = np.var(window)
            energy_variance.append(variance)
        
        if energy_variance:
            # Find the point where variance stabilizes (becomes relatively low)
            stable_threshold = np.percentile(energy_variance, 25)  # Lower quartile
            for i, var in enumerate(energy_variance):
                if var <= stable_threshold:
                    return rms_times[i + window_size]
        
        # Fallback: 10% of track duration
        return min(max_intro_duration, duration * 0.1)

    def _detect_outro_start(self, rms: np.ndarray, rms_times: np.ndarray, duration: float) -> float:
        """Detect when the outro section starts."""
        # Look for energy decline in the last portion of the track
        min_outro_start = max(0.0, duration - 120.0)  # Start looking 2 minutes from end
        outro_start_idx = max(0, int(min_outro_start / (rms_times[1] - rms_times[0])))
        
        # Find sustained energy decline
        window_size = max(1, len(rms) // 20)  # 5% of track
        
        for i in range(len(rms) - window_size, outro_start_idx, -1):
            if i - window_size >= 0:
                recent_energy = np.mean(rms[i-window_size:i])
                earlier_energy = np.mean(rms[max(0, i-2*window_size):i-window_size])
                
                # If energy has dropped significantly, this might be outro start
                if recent_energy < earlier_energy * 0.8:  # 20% energy drop
                    return rms_times[i - window_size]
        
        # Fallback: 90% of track duration
        return max(min_outro_start, duration * 0.9)

    def _create_energy_profile(self, rms: np.ndarray, rms_times: np.ndarray, duration: float) -> List[Dict[str, float]]:
        """Create a simplified energy profile over time."""
        # Sample energy at 10-second intervals
        sample_interval = 10.0
        profile = []
        
        for t in np.arange(0, duration, sample_interval):
            # Find the closest RMS index
            idx = np.argmin(np.abs(rms_times - t))
            energy = float(rms[idx])
            
            profile.append({
                "time": round(t, 1),
                "energy": round(energy, 3)
            })
        
        return profile

    def _analyze_vocal_sections(self, y: np.ndarray, sr: int, duration: float) -> Tuple[List[Dict[str, float]], List[Dict[str, float]]]:
        """Analyze vocal vs instrumental sections using spectral features."""
        try:
            # Use spectral centroid and MFCC features to detect vocal sections
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # Vocal sections typically have higher spectral centroid and specific MFCC patterns
            # This is a simplified approach
            times = librosa.frames_to_time(np.arange(len(spectral_centroid)), sr=sr)
            
            # Simple threshold-based detection
            centroid_threshold = np.percentile(spectral_centroid, 70)  # Top 30% are likely vocal
            
            vocal_sections = []
            instrumental_sections = []
            
            in_vocal = False
            vocal_start = 0.0
            
            for i, (time, centroid) in enumerate(zip(times, spectral_centroid)):
                is_vocal = centroid > centroid_threshold
                
                if is_vocal and not in_vocal:
                    # Start of vocal section
                    vocal_start = time
                    in_vocal = True
                elif not is_vocal and in_vocal:
                    # End of vocal section
                    vocal_sections.append({
                        "start": round(vocal_start, 2),
                        "end": round(time, 2),
                        "confidence": 0.6  # Simple confidence score
                    })
                    in_vocal = False
            
            # Close any open vocal section
            if in_vocal:
                vocal_sections.append({
                    "start": round(vocal_start, 2),
                    "end": round(duration, 2),
                    "confidence": 0.6
                })
            
            # Fill gaps as instrumental sections
            last_end = 0.0
            for vocal in vocal_sections:
                if vocal["start"] > last_end:
                    instrumental_sections.append({
                        "start": round(last_end, 2),
                        "end": round(vocal["start"], 2),
                        "confidence": 0.6
                    })
                last_end = vocal["end"]
            
            # Add final instrumental section if needed
            if last_end < duration:
                instrumental_sections.append({
                    "start": round(last_end, 2),
                    "end": round(duration, 2),
                    "confidence": 0.6
                })
            
            return vocal_sections, instrumental_sections
            
        except Exception as e:
            logger.warning(f"Vocal section analysis failed: {e}")
            return [], []
