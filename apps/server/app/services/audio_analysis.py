import librosa
import numpy as np
import logging
from typing import Dict, Any
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

            # Energy compatibility
            if track_a.get("energy") and track_b.get("energy"):
                energy_diff = abs(track_a["energy"] - track_b["energy"])
                compatibility["energy_compatibility"] = max(0.0, 1.0 - energy_diff)

            # Overall score (weighted average)
            scores = [
                compatibility["bpm_compatibility"] * 0.4,  # BPM is most important
                compatibility["key_compatibility"] * 0.3,  # Key is important
                compatibility["energy_compatibility"] * 0.3,  # Energy matters too
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

    def find_mix_points(self, file_path: str, duration: float) -> Dict[str, float]:
        """Find optimal mix in/out points for a track."""
        try:
            # For Phase 1, use simple time-based approach
            # In future phases, this could use beat detection and energy analysis

            # Typical intro/outro lengths in seconds
            intro_length = min(32.0, duration * 0.15)  # 15% of track or 32 seconds
            outro_length = min(32.0, duration * 0.15)

            # Mix points
            mix_in_point = intro_length
            mix_out_point = duration - outro_length

            # Ensure we have at least some playable content
            if mix_out_point <= mix_in_point:
                mix_in_point = duration * 0.1
                mix_out_point = duration * 0.9

            return {
                "mix_in_point": round(mix_in_point, 2),
                "mix_out_point": round(mix_out_point, 2),
                "playable_duration": round(mix_out_point - mix_in_point, 2),
            }

        except Exception as e:
            logger.error(f"Error finding mix points for {file_path}: {e}")
            return {
                "mix_in_point": 0.0,
                "mix_out_point": duration,
                "playable_duration": duration,
            }
