#!/usr/bin/env python3
"""Force clear mix results using raw SQL."""

from sqlalchemy import text
from app.db.session import SessionLocal

def main():
    db = SessionLocal()
    try:
        # Clear all mix results
        result = db.execute(text(
            "UPDATE analysis_jobs SET result = NULL WHERE status = 'COMPLETED' AND result IS NOT NULL"
        ))
        print(f"✅ Updated {result.rowcount} jobs - cleared their mix results")
        db.commit()
        
        # Verify
        check_result = db.execute(text(
            "SELECT COUNT(*) FROM analysis_jobs WHERE result IS NOT NULL"
        ))
        remaining = check_result.scalar()
        print(f"📊 Jobs with mix results remaining: {remaining}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main() 