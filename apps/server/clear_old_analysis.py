#!/usr/bin/env python3
"""
Clear Old Analysis Data Script

This script clears analysis data from tracks that were analyzed with the old
Spotify audio features API (version 1.0.0) so they can be re-analyzed with
the new librosa-based system (version 2.0.0).

Usage:
    python clear_old_analysis.py [options]

Options:
    --dry-run: Show what would be cleared without actually doing it
    --all: Clear all analysis data regardless of version
    --version: Clear data for specific analysis version (default: 1.0.0)
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.session import get_db
from app.models.track import Track
from sqlalchemy.orm import Session
from sqlalchemy import func


def clear_analysis_data(
    db: Session, 
    analysis_version: str = None, 
    clear_all: bool = False, 
    dry_run: bool = False
) -> dict:
    """Clear analysis data from tracks."""
    
    # Build query
    query = db.query(Track)
    
    if clear_all:
        # Clear all analyzed tracks
        query = query.filter(Track.analyzed_at.isnot(None))
        description = "all analyzed tracks"
    elif analysis_version:
        # Clear tracks with specific analysis version
        query = query.filter(Track.analysis_version == analysis_version)
        description = f"tracks with analysis version {analysis_version}"
    else:
        # Default: clear old Spotify-based analysis (version 1.0.0)
        query = query.filter(Track.analysis_version == "1.0.0")
        description = "tracks with old Spotify-based analysis (v1.0.0)"
    
    # Get tracks to be updated
    tracks_to_update = query.all()
    
    if not tracks_to_update:
        return {
            "count": 0,
            "description": description,
            "tracks": []
        }
    
    # Show what will be cleared
    track_info = []
    for track in tracks_to_update:
        track_info.append({
            "id": track.id,
            "title": track.title,
            "artist": track.artist,
            "analysis_version": track.analysis_version,
            "analyzed_at": track.analyzed_at,
            "has_audio_features": any([
                track.bpm, track.key, track.energy, track.danceability,
                track.valence, track.acousticness, track.instrumentalness,
                track.liveness, track.speechiness, track.loudness
            ])
        })
    
    if not dry_run:
        # Actually clear the data
        for track in tracks_to_update:
            # Clear analysis results
            track.bpm = None
            track.key = None
            track.energy = None
            track.danceability = None
            track.valence = None
            track.acousticness = None
            track.instrumentalness = None
            track.liveness = None
            track.speechiness = None
            track.loudness = None
            
            # Clear analysis metadata
            track.analysis_version = None
            track.analyzed_at = None
            track.analysis_error = None
        
        # Commit changes
        db.commit()
    
    return {
        "count": len(tracks_to_update),
        "description": description,
        "tracks": track_info
    }


def get_analysis_stats(db: Session) -> dict:
    """Get statistics about current analysis data."""
    
    # Total tracks
    total_tracks = db.query(func.count(Track.id)).scalar()
    
    # Analyzed tracks
    analyzed_tracks = db.query(func.count(Track.id)).filter(
        Track.analyzed_at.isnot(None)
    ).scalar()
    
    # Tracks by analysis version
    version_stats = db.query(
        Track.analysis_version,
        func.count(Track.id)
    ).filter(
        Track.analysis_version.isnot(None)
    ).group_by(Track.analysis_version).all()
    
    # Tracks with audio features
    tracks_with_features = db.query(func.count(Track.id)).filter(
        Track.bpm.isnot(None)
    ).scalar()
    
    # Tracks with errors
    tracks_with_errors = db.query(func.count(Track.id)).filter(
        Track.analysis_error.isnot(None)
    ).scalar()
    
    return {
        "total_tracks": total_tracks,
        "analyzed_tracks": analyzed_tracks,
        "tracks_with_features": tracks_with_features,
        "tracks_with_errors": tracks_with_errors,
        "version_breakdown": dict(version_stats)
    }


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Clear old analysis data")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be cleared without doing it")
    parser.add_argument("--all", action="store_true",
                       help="Clear all analysis data regardless of version")
    parser.add_argument("--version", type=str, default="1.0.0",
                       help="Clear data for specific analysis version (default: 1.0.0)")
    parser.add_argument("--stats-only", action="store_true",
                       help="Only show statistics, don't clear anything")
    
    args = parser.parse_args()
    
    print("🧹 Clear Old Analysis Data")
    print("=" * 60)
    print("This script clears old analysis data so tracks can be re-analyzed")
    print("with the new librosa-based system.")
    print("=" * 60)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Show current statistics
        print("\n📊 Current Analysis Statistics:")
        stats = get_analysis_stats(db)
        print(f"   Total tracks: {stats['total_tracks']}")
        print(f"   Analyzed tracks: {stats['analyzed_tracks']}")
        print(f"   Tracks with features: {stats['tracks_with_features']}")
        print(f"   Tracks with errors: {stats['tracks_with_errors']}")
        
        if stats['version_breakdown']:
            print(f"   Analysis versions:")
            for version, count in stats['version_breakdown'].items():
                print(f"     - {version}: {count} tracks")
        
        if args.stats_only:
            return
        
        # Determine what to clear
        if args.all:
            clear_version = None
            clear_all = True
        else:
            clear_version = args.version
            clear_all = False
        
        # Clear analysis data
        print(f"\n🔍 {'[DRY RUN] ' if args.dry_run else ''}Clearing analysis data...")
        
        result = clear_analysis_data(
            db=db,
            analysis_version=clear_version,
            clear_all=clear_all,
            dry_run=args.dry_run
        )
        
        if result['count'] == 0:
            print(f"✅ No tracks found matching criteria: {result['description']}")
        else:
            print(f"{'📋 Would clear' if args.dry_run else '✅ Cleared'} {result['count']} {result['description']}")
            
            # Show sample of affected tracks
            if result['tracks']:
                print(f"\n📝 {'Tracks that would be affected:' if args.dry_run else 'Tracks that were cleared:'}")
                for i, track in enumerate(result['tracks'][:10]):  # Show first 10
                    status = "✓" if track['has_audio_features'] else "○"
                    print(f"   {status} {track['artist']} - {track['title']} (v{track['analysis_version']})")
                
                if len(result['tracks']) > 10:
                    print(f"   ... and {len(result['tracks']) - 10} more tracks")
        
        if args.dry_run:
            print(f"\n💡 Run without --dry-run to actually clear the data")
        else:
            print(f"\n✅ Analysis data cleared successfully!")
            print(f"   Tracks will be re-analyzed with librosa on next processing")
            
            # Show updated stats
            print(f"\n📊 Updated Statistics:")
            new_stats = get_analysis_stats(db)
            print(f"   Analyzed tracks: {new_stats['analyzed_tracks']} (was {stats['analyzed_tracks']})")
            print(f"   Tracks with features: {new_stats['tracks_with_features']} (was {stats['tracks_with_features']})")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main()) 