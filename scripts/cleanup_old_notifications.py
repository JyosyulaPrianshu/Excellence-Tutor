#!/usr/bin/env python3
"""
Script to delete notifications older than 15 days (360 hours) from the database.
"""

import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Notification

def cleanup_old_notifications():
    """Delete notifications older than 15 days (360 hours)"""
    app = create_app()
    with app.app_context():
        try:
            cutoff = datetime.now() - timedelta(days=15)
            old_count = Notification.query.filter(Notification.created_at < cutoff).count()
            if old_count == 0:
                print("✅ No old notifications to delete.")
                return True
            print(f"🗑️  Found {old_count} notifications older than 15 days. Deleting...")
            Notification.query.filter(Notification.created_at < cutoff).delete(synchronize_session=False)
            db.session.commit()
            print(f"✅ Deleted {old_count} old notifications.")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during notification cleanup: {str(e)}")
            return False

if __name__ == "__main__":
    print("🧹 Excellence Tutorial - Old Notifications Cleanup Script")
    print("=" * 50)
    if cleanup_old_notifications():
        print("\n🎯 Old notifications cleanup completed successfully!")
    else:
        print("\n💥 Old notifications cleanup failed!")
        sys.exit(1) 