#!/usr/bin/env python3
"""
Clear Old Mix Data Script

This script clears old mix results and transitions while preserving:
- Downloaded audio files
- Track analysis data (BPM, key, energy, etc.)
- Track records in the database

This allows regenerating fresh mixes with updated algorithms or beat analysis data.

Usage:
    python clear_old_mixes.py [--dry-run] [--job-id JOB_ID]
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import SessionLocal
from app.models.job import AnalysisJob, MixTransition, JobStatus
from app.models.track import Track


def get_db_session():
    """Get database session."""
    return SessionLocal()


def clear_mix_data(
    db: Session,
    job_id: str = None,
    days_old: int = None,
    dry_run: bool = False
) -> dict:
    """Clear mix data while preserving tracks."""
    
    # Build query for jobs to clear
    jobs_query = db.query(AnalysisJob)
    
    if job_id:
        # Clear specific job
        jobs_query = jobs_query.filter(
            AnalysisJob.id == job_id,
            AnalysisJob.result.isnot(None)  # Only if it has results
        )
        description = f"job {job_id}"
    elif days_old:
        # Clear jobs older than specified days that have results
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        jobs_query = jobs_query.filter(
            AnalysisJob.created_at < cutoff_date,
            AnalysisJob.result.isnot(None)
        )
        description = f"jobs older than {days_old} days with mix results"
    else:
        # Clear all completed jobs that have mix results
        jobs_query = jobs_query.filter(
            AnalysisJob.status == JobStatus.COMPLETED,
            AnalysisJob.result.isnot(None)
        )
        description = "all completed jobs with mix results"
    
    jobs_to_clear = jobs_query.all()
    
    if not jobs_to_clear:
        return {
            "jobs_cleared": 0,
            "transitions_deleted": 0,
            "description": description,
            "jobs": []
        }
    
    job_info = []
    transitions_deleted = 0
    
    for job in jobs_to_clear:
        # Count transitions for this job
        transition_count = db.query(MixTransition).filter(
            MixTransition.job_id == job.id
        ).count()
        
        job_info.append({
            "id": job.id,
            "playlist_name": job.playlist_name,
            "status": job.status.value,
            "total_tracks": job.total_tracks,
            "analyzed_tracks": job.analyzed_tracks,
            "transitions": transition_count,
            "created_at": job.created_at,
            "has_mix_result": bool(job.result)
        })
        
        if not dry_run:
            # Delete mix transitions for this job
            deleted_transitions = db.query(MixTransition).filter(
                MixTransition.job_id == job.id
            ).delete()
            transitions_deleted += deleted_transitions
            
            # Properly clear mix result by setting it to None
            job.result = None
            job.status = JobStatus.COMPLETED  # Keep as completed but without mix
            
            # Update the job's updated_at timestamp
            job.updated_at = datetime.utcnow()
        else:
            transitions_deleted += transition_count
    
    if not dry_run:
        db.commit()
        print(f"✅ Cleared mix data for {len(jobs_to_clear)} jobs")
    else:
        print(f"🔍 Would clear mix data for {len(jobs_to_clear)} jobs")
    
    return {
        "jobs_cleared": len(jobs_to_clear),
        "transitions_deleted": transitions_deleted,
        "description": description,
        "jobs": job_info
    }


def get_mix_stats(db: Session) -> dict:
    """Get statistics about current mix data."""
    
    # Total jobs
    total_jobs = db.query(func.count(AnalysisJob.id)).scalar()
    
    # Jobs with mix results (check for non-null JSON)
    jobs_with_mixes = db.query(func.count(AnalysisJob.id)).filter(
        AnalysisJob.result.isnot(None)
    ).scalar()
    
    # Total transitions
    total_transitions = db.query(func.count(MixTransition.id)).scalar()
    
    # Jobs by status
    status_stats = db.query(
        AnalysisJob.status,
        func.count(AnalysisJob.id)
    ).group_by(AnalysisJob.status).all()
    
    # Total tracks (preserved)
    total_tracks = db.query(func.count(Track.id)).scalar()
    
    # Tracks with files
    tracks_with_files = db.query(func.count(Track.id)).filter(
        Track.file_path.isnot(None)
    ).scalar()
    
    # Tracks with analysis
    tracks_with_analysis = db.query(func.count(Track.id)).filter(
        Track.analyzed_at.isnot(None)
    ).scalar()
    
    return {
        "total_jobs": total_jobs,
        "jobs_with_mix_results": jobs_with_mixes,
        "total_transitions": total_transitions,
        "total_tracks": total_tracks,
        "tracks_with_files": tracks_with_files,
        "tracks_with_analysis": tracks_with_analysis,
        "status_breakdown": dict(status_stats)
    }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Clear old mix data while preserving tracks")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleared without actually doing it")
    parser.add_argument("--job-id", help="Clear mix data for specific job ID")
    parser.add_argument("--days-old", type=int, help="Clear mix data for jobs older than N days")
    parser.add_argument("--stats-only", action="store_true", help="Only show statistics")
    
    args = parser.parse_args()
    
    print("🎧 DJ Mix Data Cleaner")
    print("=" * 60)
    print("This script clears mix results and transitions while preserving:")
    print("  ✅ Downloaded audio files")
    print("  ✅ Track analysis data (BPM, key, energy, beat analysis)")
    print("  ✅ Track records in database")
    print("=" * 60)
    
    db = get_db_session()
    
    try:
        # Show current statistics
        print("\n📊 Current Mix Data Statistics:")
        stats = get_mix_stats(db)
        print(f"  Total jobs: {stats['total_jobs']}")
        print(f"  Jobs with mix results: {stats['jobs_with_mix_results']}")
        print(f"  Total transitions: {stats['total_transitions']}")
        print(f"  Total tracks: {stats['total_tracks']}")
        print(f"  Tracks with files: {stats['tracks_with_files']}")
        print(f"  Tracks with analysis: {stats['tracks_with_analysis']}")
        
        if stats['status_breakdown']:
            print(f"  Job status breakdown:")
            for status, count in stats['status_breakdown'].items():
                print(f"    {status}: {count}")
        
        if args.stats_only:
            return
        
        # Perform clearing operation
        print(f"\n🧹 Clearing Mix Data...")
        if args.dry_run:
            print("  (DRY RUN - No changes will be made)")
        
        result = clear_mix_data(
            db,
            job_id=args.job_id,
            days_old=args.days_old,
            dry_run=args.dry_run
        )
        
        print(f"\n📋 Results:")
        print(f"  Jobs affected: {result['jobs_cleared']}")
        print(f"  Transitions deleted: {result['transitions_deleted']}")
        print(f"  Scope: {result['description']}")
        
        if result['jobs']:
            print(f"\n📝 Affected Jobs:")
            for job in result['jobs']:
                print(f"  🎵 {job['playlist_name']} ({job['id']})")
                print(f"     Status: {job['status']}, Tracks: {job['analyzed_tracks']}/{job['total_tracks']}")
                print(f"     Transitions: {job['transitions']}, Created: {job['created_at']}")
        
        if not args.dry_run and result['jobs_cleared'] > 0:
            print(f"\n✅ Mix data cleared successfully!")
            print(f"   You can now re-run analysis jobs to generate fresh mixes")
            print(f"   with updated beat analysis and mixing algorithms.")
        elif args.dry_run:
            print(f"\n💡 Run without --dry-run to actually clear the data")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main() 