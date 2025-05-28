#!/usr/bin/env python3
"""
Test script for audio fetcher functionality.
This script tests the audio downloading functionality to ensure yt-dlp is working correctly.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.audio_fetcher import AudioFetcher
from app.core.config import settings


async def test_audio_fetcher():
    """Test the audio fetcher with a simple track."""
    fetcher = AudioFetcher()
    
    # Test with a simple, well-known track
    test_artist = "Rick Astley"
    test_title = "Never Gonna Give You Up"
    test_spotify_id = "test_id"
    
    print(f"🎵 Testing audio fetcher with: {test_artist} - {test_title}")
    print(f"📁 Audio storage path: {settings.AUDIO_STORAGE_PATH}")
    
    # Ensure audio directory exists
    audio_dir = Path(settings.AUDIO_STORAGE_PATH)
    audio_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Audio directory created/verified: {audio_dir}")
    
    try:
        # Run the fetch
        result = await fetcher.fetch_audio(test_artist, test_title, test_spotify_id)
        
        if result.get("error"):
            print(f"❌ Fetch failed: {result['error']}")
            return False
        
        if result.get("file_path"):
            print("✅ Audio fetch completed successfully!")
            print(f"   File path: {result['file_path']}")
            print(f"   File source: {result['file_source']}")
            print(f"   File size: {result.get('file_size', 0)} bytes")
            
            # Verify file exists
            file_path = Path(result['file_path'])
            if file_path.exists():
                print(f"✅ File verified to exist: {file_path}")
                print(f"   Actual file size: {file_path.stat().st_size} bytes")
                return True
            else:
                print(f"❌ File does not exist: {file_path}")
                return False
        else:
            print("❌ No file path returned")
            return False
        
    except Exception as e:
        print(f"❌ Error during fetch: {e}")
        return False


def test_storage_usage():
    """Test storage usage functionality."""
    fetcher = AudioFetcher()
    
    try:
        usage = fetcher.get_storage_usage()
        print("\n📊 Storage Usage:")
        print(f"   Total files: {usage['file_count']}")
        print(f"   Total size: {usage['usage_gb']:.2f} GB")
        print(f"   Max allowed: {usage['max_gb']} GB")
        return True
        
    except Exception as e:
        print(f"❌ Error getting storage usage: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 Testing Audio Fetcher")
    print("=" * 50)
    
    # Test storage usage first
    storage_success = test_storage_usage()
    
    # Test audio fetching
    fetch_success = await test_audio_fetcher()
    
    print("\n" + "=" * 50)
    if fetch_success and storage_success:
        print("🎉 All tests passed! Audio fetcher is working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 