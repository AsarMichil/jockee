#!/usr/bin/env python3
"""
Reset Analysis Status Script

This script resets the analysis status for tracks so they can be re-analyzed.
Useful for tracks that failed analysis or need to be re-processed.

Usage:
    python reset_analysis.py [options]

Options:
    --dry-run: Show what would be reset without actually doing it
    --failed-only: Only reset tracks that have analysis errors
    --unanalyzed: Reset tracks that haven't been analyzed yet
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.session import get_db
from app.models.track import Track
from sqlalchemy.orm import Session
from sqlalchemy import func


def reset_analysis_status(
    db: Session, 
    failed_only: bool = False,
    unanalyzed: bool = False,
    dry_run: bool = False
) -> dict:
    """Reset analysis status for tracks."""
    
    # Build query
    query = db.query(Track)
    
    if failed_only:
        # Only tracks with analysis errors
        query = query.filter(Track.analysis_error.isnot(None))
        description = "tracks with analysis errors"
    elif unanalyzed:
        # Only tracks that haven't been analyzed
        query = query.filter(Track.analyzed_at.is_(None))
        description = "unanalyzed tracks"
    else:
        # All tracks with any analysis data
        query = query.filter(
            (Track.analyzed_at.isnot(None)) | 
            (Track.analysis_error.isnot(None))
        )
        description = "all tracks with analysis data"
    
    # Get tracks to be updated
    tracks_to_update = query.all()
    
    if not tracks_to_update:
        return {
            "count": 0,
            "description": description,
            "tracks": []
        }
    
    # Show what will be reset
    track_info = []
    for track in tracks_to_update:
        track_info.append({
            "id": track.id,
            "title": track.title,
            "artist": track.artist,
            "analysis_version": track.analysis_version,
            "analyzed_at": track.analyzed_at,
            "analysis_error": track.analysis_error,
            "has_file": track.file_path is not None,
            "file_source": track.file_source
        })
    
    if not dry_run:
        # Reset analysis status (but keep the version)
        for track in tracks_to_update:
            track.analyzed_at = None
            track.analysis_error = None
            # Keep analysis_version as 2.0.0 so it uses librosa
        
        # Commit changes
        db.commit()
    
    return {
        "count": len(tracks_to_update),
        "description": description,
        "tracks": track_info
    }


def get_track_status(db: Session) -> dict:
    """Get detailed status of tracks."""
    
    # Total tracks
    total_tracks = db.query(func.count(Track.id)).scalar()
    
    # Tracks with files
    tracks_with_files = db.query(func.count(Track.id)).filter(
        Track.file_path.isnot(None)
    ).scalar()
    
    # Analyzed tracks
    analyzed_tracks = db.query(func.count(Track.id)).filter(
        Track.analyzed_at.isnot(None)
    ).scalar()
    
    # Tracks with errors
    tracks_with_errors = db.query(func.count(Track.id)).filter(
        Track.analysis_error.isnot(None)
    ).scalar()
    
    # Tracks ready for analysis (have files but not analyzed)
    ready_for_analysis = db.query(func.count(Track.id)).filter(
        Track.file_path.isnot(None),
        Track.analyzed_at.is_(None),
        Track.analysis_error.is_(None)
    ).scalar()
    
    # File source breakdown
    file_sources = db.query(
        Track.file_source,
        func.count(Track.id)
    ).filter(
        Track.file_source.isnot(None)
    ).group_by(Track.file_source).all()
    
    return {
        "total_tracks": total_tracks,
        "tracks_with_files": tracks_with_files,
        "analyzed_tracks": analyzed_tracks,
        "tracks_with_errors": tracks_with_errors,
        "ready_for_analysis": ready_for_analysis,
        "file_source_breakdown": dict(file_sources)
    }


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Reset analysis status for tracks")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be reset without doing it")
    parser.add_argument("--failed-only", action="store_true",
                       help="Only reset tracks that have analysis errors")
    parser.add_argument("--unanalyzed", action="store_true",
                       help="Reset tracks that haven't been analyzed yet")
    parser.add_argument("--status-only", action="store_true",
                       help="Only show track status, don't reset anything")
    
    args = parser.parse_args()
    
    print("🔄 Reset Analysis Status")
    print("=" * 60)
    print("This script resets analysis status so tracks can be re-analyzed")
    print("with the librosa-based system.")
    print("=" * 60)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Show current status
        print("\n📊 Current Track Status:")
        status = get_track_status(db)
        print(f"   Total tracks: {status['total_tracks']}")
        print(f"   Tracks with files: {status['tracks_with_files']}")
        print(f"   Analyzed tracks: {status['analyzed_tracks']}")
        print(f"   Tracks with errors: {status['tracks_with_errors']}")
        print(f"   Ready for analysis: {status['ready_for_analysis']}")
        
        if status['file_source_breakdown']:
            print(f"   File sources:")
            for source, count in status['file_source_breakdown'].items():
                print(f"     - {source}: {count} tracks")
        
        if args.status_only:
            return
        
        # Reset analysis status
        print(f"\n🔍 {'[DRY RUN] ' if args.dry_run else ''}Resetting analysis status...")
        
        result = reset_analysis_status(
            db=db,
            failed_only=args.failed_only,
            unanalyzed=args.unanalyzed,
            dry_run=args.dry_run
        )
        
        if result['count'] == 0:
            print(f"✅ No tracks found matching criteria: {result['description']}")
        else:
            print(f"{'📋 Would reset' if args.dry_run else '✅ Reset'} {result['count']} {result['description']}")
            
            # Show sample of affected tracks
            if result['tracks']:
                print(f"\n📝 {'Tracks that would be affected:' if args.dry_run else 'Tracks that were reset:'}")
                for i, track in enumerate(result['tracks'][:10]):  # Show first 10
                    file_status = "📁" if track['has_file'] else "❌"
                    error_status = "⚠️" if track['analysis_error'] else "✓"
                    print(f"   {file_status}{error_status} {track['artist']} - {track['title']} ({track['file_source'] or 'no file'})")
                
                if len(result['tracks']) > 10:
                    print(f"   ... and {len(result['tracks']) - 10} more tracks")
        
        if args.dry_run:
            print(f"\n💡 Run without --dry-run to actually reset the status")
        else:
            print(f"\n✅ Analysis status reset successfully!")
            print(f"   Tracks are now ready for re-analysis with librosa")
            
            # Show updated status
            print(f"\n📊 Updated Status:")
            new_status = get_track_status(db)
            print(f"   Ready for analysis: {new_status['ready_for_analysis']} (was {status['ready_for_analysis']})")
            print(f"   Tracks with errors: {new_status['tracks_with_errors']} (was {status['tracks_with_errors']})")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main()) 