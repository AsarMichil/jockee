#!/usr/bin/env python3
"""
Check and Manage Analysis Jobs Script

This script helps check the status of analysis jobs and reset stuck ones.

Usage:
    python check_jobs.py [options]

Options:
    --reset-stuck: Reset jobs that are stuck in processing state
    --job-id: Check specific job by ID
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.session import get_db
from app.models.job import AnalysisJob, JobStatus
from app.models.track import Track  # Import Track model to resolve relationships
from sqlalchemy.orm import Session
from sqlalchemy import func


def get_job_status(db: Session, job_id: str = None) -> dict:
    """Get status of analysis jobs."""
    
    if job_id:
        # Get specific job
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            return {"error": f"Job {job_id} not found"}
        
        return {
            "jobs": [job],
            "total": 1
        }
    else:
        # Get all jobs
        jobs = db.query(AnalysisJob).order_by(AnalysisJob.created_at.desc()).limit(10).all()
        total = db.query(func.count(AnalysisJob.id)).scalar()
        
        return {
            "jobs": jobs,
            "total": total
        }


def reset_stuck_jobs(db: Session, max_age_minutes: int = 30) -> dict:
    """Reset jobs that are stuck in processing state."""
    
    # Find jobs that have been processing for too long
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
    
    stuck_jobs = db.query(AnalysisJob).filter(
        AnalysisJob.status == JobStatus.PROCESSING,
        AnalysisJob.started_at < cutoff_time
    ).all()
    
    reset_count = 0
    for job in stuck_jobs:
        job.status = JobStatus.FAILED
        job.error_message = f"Job reset - was stuck in processing for over {max_age_minutes} minutes"
        job.completed_at = datetime.now(timezone.utc)
        reset_count += 1
    
    if reset_count > 0:
        db.commit()
    
    return {
        "reset_count": reset_count,
        "jobs": stuck_jobs
    }


def format_job_info(job) -> str:
    """Format job information for display."""
    duration = ""
    if job.started_at and job.completed_at:
        delta = job.completed_at - job.started_at
        duration = f" ({delta.total_seconds():.1f}s)"
    elif job.started_at:
        # Make both datetimes timezone-aware for comparison
        now = datetime.now(timezone.utc)
        started_at = job.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        delta = now - started_at
        duration = f" (running {delta.total_seconds():.1f}s)"
    
    progress = ""
    if job.total_tracks and job.total_tracks > 0:
        progress = f" - {job.analyzed_tracks or 0}/{job.total_tracks} tracks"
    
    error = ""
    if job.error_message:
        error = f"\n      Error: {job.error_message}"
    
    return (
        f"   📋 {job.id}\n"
        f"      Status: {job.status.value}{duration}{progress}\n"
        f"      Playlist: {job.playlist_name or 'Unknown'}\n"
        f"      Created: {job.created_at}\n"
        f"      Downloads: {job.downloaded_tracks or 0}, Failed: {job.failed_tracks or 0}"
        f"{error}"
    )


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Check and manage analysis jobs")
    parser.add_argument("--reset-stuck", action="store_true",
                       help="Reset jobs stuck in processing state")
    parser.add_argument("--job-id", type=str,
                       help="Check specific job by ID")
    parser.add_argument("--max-age", type=int, default=30,
                       help="Max age in minutes for stuck jobs (default: 30)")
    
    args = parser.parse_args()
    
    print("📊 Analysis Jobs Manager")
    print("=" * 60)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Check for stuck jobs first
        if args.reset_stuck:
            print(f"🔍 Checking for jobs stuck in processing (older than {args.max_age} minutes)...")
            result = reset_stuck_jobs(db, args.max_age)
            
            if result["reset_count"] > 0:
                print(f"✅ Reset {result['reset_count']} stuck jobs:")
                for job in result["jobs"]:
                    print(f"   - {job.id} ({job.playlist_name or 'Unknown'})")
            else:
                print("✅ No stuck jobs found")
            print()
        
        # Get job status
        print("📋 Recent Jobs:")
        result = get_job_status(db, args.job_id)
        
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        
        if not result["jobs"]:
            print("   No jobs found")
        else:
            for job in result["jobs"]:
                print(format_job_info(job))
                print()
        
        if not args.job_id:
            print(f"📊 Total jobs in database: {result['total']}")
            
            # Show status breakdown
            status_counts = db.query(
                AnalysisJob.status,
                func.count(AnalysisJob.id)
            ).group_by(AnalysisJob.status).all()
            
            if status_counts:
                print("\n📈 Status Breakdown:")
                for status, count in status_counts:
                    print(f"   {status.value}: {count}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main()) 