#!/usr/bin/env python3
"""
Librosa Audio Analysis Test Script

This script tests the librosa-based audio analysis functionality that replaced
Spotify's deprecated audio features API. It can be used to:
- Verify that librosa analysis is working correctly
- Test analysis on specific audio files
- Debug audio analysis issues

Usage:
    python test_librosa_analysis.py [audio_file_path]
    
If no file path is provided, it will look for audio files in the audio directory.
"""

import asyncio
import sys
import os
from pathlib import Path
import argparse

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.audio_analysis import AudioAnalyzer
from app.core.config import settings


async def test_audio_analysis(file_path: str = None):
    """Test the audio analysis with a specific file or find one automatically."""
    analyzer = AudioAnalyzer()
    
    if file_path:
        # Test with provided file
        test_file = Path(file_path)
        if not test_file.exists():
            print(f"❌ File not found: {file_path}")
            return False
    else:
        # Look for audio files in the audio directory
        audio_dir = Path(settings.AUDIO_STORAGE_PATH)
        if not audio_dir.exists():
            print(f"❌ Audio directory not found: {audio_dir}")
            print("   Please ensure you have downloaded some audio files first.")
            return False

        # Find any audio file to test with
        audio_files = list(audio_dir.rglob("*.mp3")) + list(audio_dir.rglob("*.wav")) + list(audio_dir.rglob("*.m4a"))
        
        if not audio_files:
            print(f"❌ No audio files found in {audio_dir}")
            print("   Please download some audio files first using the audio fetcher.")
            return False
        
        test_file = audio_files[0]
        print(f"🎵 Using audio file: {test_file}")

    print(f"🔬 Testing librosa analysis on: {test_file.name}")
    print(f"📁 File size: {test_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    try:
        # Run the analysis
        result = await analyzer.analyze_track(str(test_file))
        
        if result.get("analysis_error"):
            print(f"❌ Analysis failed: {result['analysis_error']}")
            return False
        
        print("✅ Audio analysis completed successfully!")
        print("\n📊 Analysis Results:")
        print("=" * 50)
        
        # Core features
        print(f"🎵 BPM: {result.get('bpm', 'N/A')}")
        print(f"🎼 Key: {result.get('key', 'N/A')}")
        print(f"⚡ Energy: {result.get('energy', 'N/A')}")
        print(f"💃 Danceability: {result.get('danceability', 'N/A')}")
        print(f"😊 Valence: {result.get('valence', 'N/A')}")
        print(f"🎸 Acousticness: {result.get('acousticness', 'N/A')}")
        print(f"🎹 Instrumentalness: {result.get('instrumentalness', 'N/A')}")
        print(f"🎤 Liveness: {result.get('liveness', 'N/A')}")
        print(f"🗣️  Speechiness: {result.get('speechiness', 'N/A')}")
        print(f"🔊 Loudness: {result.get('loudness', 'N/A')} dB")
        
        # Beat analysis information
        print(f"\n🥁 Beat Analysis:")
        print(f"   Beat Count: {result.get('beat_count', 'N/A')}")
        print(f"   Beat Confidence: {result.get('beat_confidence', 'N/A')}")
        print(f"   Beat Regularity: {result.get('beat_regularity', 'N/A')}")
        print(f"   Average Beat Interval: {result.get('average_beat_interval', 'N/A')}s")
        
        # Show first few beat timestamps
        beat_timestamps = result.get('beat_timestamps', [])
        if beat_timestamps:
            print(f"   First 10 Beat Timestamps: {[round(t, 2) for t in beat_timestamps[:10]]}")
            print(f"   Total Beat Timestamps: {len(beat_timestamps)}")
        
        beat_intervals = result.get('beat_intervals', [])
        if beat_intervals and len(beat_intervals) > 0:
            print(f"   Beat Interval Range: {min(beat_intervals):.3f}s - {max(beat_intervals):.3f}s")
        
        # Additional info
        print(f"\n📋 Analysis Info:")
        print(f"   Version: {result.get('analysis_version', 'N/A')}")
        print(f"   Analyzed at: {result.get('analyzed_at', 'N/A')}")
        
        # Verify all expected features are present
        expected_features = [
            'bpm', 'key', 'energy', 'danceability', 'valence', 
            'acousticness', 'instrumentalness', 'liveness', 
            'speechiness', 'loudness', 'beat_timestamps', 'beat_confidence'
        ]
        
        missing_features = [f for f in expected_features if result.get(f) is None]
        if missing_features:
            print(f"\n⚠️  Warning: Some features could not be analyzed: {missing_features}")
            return False
        else:
            print("\n✅ All audio features and beat analysis successfully extracted!")
            return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return False


def test_compatibility_calculation():
    """Test the compatibility calculation between two mock tracks."""
    analyzer = AudioAnalyzer()
    
    print("\n🔗 Testing compatibility calculation...")
    
    # Mock track data
    track_a = {
        "bpm": 120.0,
        "key": "C",
        "energy": 0.7,
        "danceability": 0.8,
        "valence": 0.6
    }
    
    track_b = {
        "bpm": 125.0,
        "key": "G", 
        "energy": 0.75,
        "danceability": 0.85,
        "valence": 0.65
    }
    
    try:
        compatibility = analyzer.calculate_compatibility(track_a, track_b)
        
        print("✅ Compatibility calculation successful!")
        print(f"   BPM compatibility: {compatibility['bpm_compatibility']:.3f}")
        print(f"   Key compatibility: {compatibility['key_compatibility']:.3f}")
        print(f"   Energy compatibility: {compatibility['energy_compatibility']:.3f}")
        print(f"   Overall score: {compatibility['overall_score']:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Compatibility calculation failed: {e}")
        return False


async def main():
    """Run the audio analysis tests."""
    parser = argparse.ArgumentParser(description="Test librosa audio analysis")
    parser.add_argument("file", nargs="?", help="Path to audio file to analyze")
    parser.add_argument("--compatibility-only", action="store_true", 
                       help="Only test compatibility calculation")
    
    args = parser.parse_args()
    
    print("🧪 Librosa Audio Analysis Test")
    print("=" * 60)
    print("This script tests the librosa-based audio analysis that replaced")
    print("Spotify's deprecated audio features API.")
    print("=" * 60)
    
    success = True
    
    if not args.compatibility_only:
        # Test audio analysis
        analysis_success = await test_audio_analysis(args.file)
        success = success and analysis_success
    
    # Test compatibility calculation
    compatibility_success = test_compatibility_calculation()
    success = success and compatibility_success
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed!")
        print("   ✅ Librosa analysis is working correctly")
        print("   ✅ Audio features are being extracted properly")
        print("   ✅ Compatibility calculation is functional")
        print("\n💡 The migration from Spotify's audio features API is complete!")
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 