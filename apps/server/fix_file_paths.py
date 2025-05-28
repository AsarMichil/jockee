#!/usr/bin/env python3
"""
Fix File Paths Script

This script finds existing audio files in the audio directory and updates
the database records to point to them. Useful when files exist but the
database records show them as unavailable.

Usage:
    python fix_file_paths.py [options]

Options:
    --dry-run: Show what would be fixed without actually doing it
    --force: Update even if track already has a file path
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path
import re

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.session import get_db
from app.models.track import Track, FileSource
from app.core.config import settings
from sqlalchemy.orm import Session


def sanitize_for_comparison(text: str) -> str:
    """Sanitize text for comparison (same logic as audio fetcher)."""
    # Remove or replace invalid characters
    text = re.sub(r'[<>:"/\\|?*]', "_", text)
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-").lower()


def find_matching_files(tracks: list, audio_dir: Path) -> dict:
    """Find audio files that match tracks."""
    matches = {}
    
    # Get all audio files
    audio_files = []
    for ext in ['*.mp3', '*.mp4', '*.wav', '*.m4a']:
        audio_files.extend(audio_dir.rglob(ext))
    
    print(f"Found {len(audio_files)} audio files in {audio_dir}")
    
    for track in tracks:
        # Generate expected file path using same logic as audio fetcher
        artist_clean = sanitize_for_comparison(track.artist)
        title_clean = sanitize_for_comparison(track.title)
        
        # Look for matching files
        possible_matches = []
        
        for audio_file in audio_files:
            file_artist = audio_file.parent.name.lower()
            file_title = audio_file.stem.lower()
            
            # Check if artist and title match
            if (artist_clean == file_artist or 
                artist_clean.replace("-", "") == file_artist.replace("-", "")):
                if (title_clean == file_title or 
                    title_clean.replace("-", "") == file_title.replace("-", "")):
                    possible_matches.append(audio_file)
        
        if possible_matches:
            # Use the first match (or could add logic to pick best match)
            best_match = possible_matches[0]
            matches[track.id] = {
                "track": track,
                "file_path": best_match,
                "file_size": best_match.stat().st_size,
                "all_matches": possible_matches
            }
            print(f"✓ Found match: {track.artist} - {track.title} → {best_match}")
        else:
            print(f"✗ No match found: {track.artist} - {track.title}")
            print(f"  Expected: {artist_clean}/{title_clean}.*")
    
    return matches


def update_track_file_info(
    db: Session, 
    matches: dict, 
    force: bool = False, 
    dry_run: bool = False
) -> dict:
    """Update track records with file information."""
    
    updated_tracks = []
    skipped_tracks = []
    
    for track_id, match_info in matches.items():
        track = match_info["track"]
        file_path = match_info["file_path"]
        file_size = match_info["file_size"]
        
        # Check if track already has a file path
        if track.file_path and not force:
            skipped_tracks.append({
                "track": track,
                "reason": "already has file path",
                "current_path": track.file_path
            })
            continue
        
        if not dry_run:
            # Update the track record
            track.file_path = str(file_path)
            track.file_source = FileSource.YOUTUBE  # Assume these were downloaded from YouTube
            track.file_size = file_size
            
            # Clear analysis data so it gets re-analyzed with the new file
            track.analyzed_at = None
            track.analysis_error = None
            # Keep analysis_version as 2.0.0 for librosa
        
        updated_tracks.append({
            "track": track,
            "file_path": str(file_path),
            "file_size": file_size
        })
    
    if not dry_run and updated_tracks:
        db.commit()
    
    return {
        "updated": updated_tracks,
        "skipped": skipped_tracks
    }


def get_tracks_needing_files(db: Session) -> list:
    """Get tracks that need file paths fixed."""
    
    # Get tracks that either have no file_path or have file_source as UNAVAILABLE
    tracks = db.query(Track).filter(
        (Track.file_path.is_(None)) | 
        (Track.file_source == FileSource.UNAVAILABLE)
    ).all()
    
    return tracks


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Fix file paths for existing audio files")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be fixed without doing it")
    parser.add_argument("--force", action="store_true",
                       help="Update even if track already has a file path")
    parser.add_argument("--status-only", action="store_true",
                       help="Only show current status, don't fix anything")
    
    args = parser.parse_args()
    
    print("🔧 Fix File Paths")
    print("=" * 60)
    print("This script finds existing audio files and updates database records")
    print("to point to them.")
    print("=" * 60)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get tracks that need fixing
        tracks = get_tracks_needing_files(db)
        
        print(f"\n📊 Current Status:")
        print(f"   Tracks needing file paths: {len(tracks)}")
        
        if not tracks:
            print("✅ No tracks need file path fixes!")
            return
        
        # Show tracks that need fixing
        print(f"\n📝 Tracks needing fixes:")
        for track in tracks:
            status = "❌" if track.file_source == FileSource.UNAVAILABLE else "?"
            print(f"   {status} {track.artist} - {track.title}")
        
        if args.status_only:
            return
        
        # Find matching files
        audio_dir = Path(settings.AUDIO_STORAGE_PATH)
        if not audio_dir.exists():
            print(f"❌ Audio directory not found: {audio_dir}")
            return
        
        print(f"\n🔍 Searching for matching files in {audio_dir}...")
        matches = find_matching_files(tracks, audio_dir)
        
        if not matches:
            print("❌ No matching files found!")
            return
        
        print(f"\n{'📋 Would fix' if args.dry_run else '🔧 Fixing'} {len(matches)} tracks...")
        
        # Update database records
        result = update_track_file_info(
            db=db,
            matches=matches,
            force=args.force,
            dry_run=args.dry_run
        )
        
        # Show results
        if result["updated"]:
            print(f"\n✅ {'Would update' if args.dry_run else 'Updated'} {len(result['updated'])} tracks:")
            for update in result["updated"]:
                track = update["track"]
                size_mb = update["file_size"] / 1024 / 1024
                print(f"   📁 {track.artist} - {track.title}")
                print(f"      File: {update['file_path']}")
                print(f"      Size: {size_mb:.1f} MB")
        
        if result["skipped"]:
            print(f"\n⏭️  Skipped {len(result['skipped'])} tracks:")
            for skip in result["skipped"]:
                track = skip["track"]
                print(f"   ⚠️  {track.artist} - {track.title} ({skip['reason']})")
        
        if args.dry_run:
            print(f"\n💡 Run without --dry-run to actually fix the file paths")
        else:
            print(f"\n✅ File paths fixed successfully!")
            print(f"   Tracks are now ready for analysis with librosa")
            print(f"   Run the playlist analysis again to analyze the tracks")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main()) 