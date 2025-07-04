#!/usr/bin/env python3
"""
Script to print the total number of notifications, the number in the last 15 days, and the number that would be deleted by the cleanup logic.
"""

import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Notification

def notification_count():
    app = create_app()
    with app.app_context():
        total = Notification.query.count()
        cutoff = datetime.now() - timedelta(days=15)
        to_keep = Notification.query.filter(Notification.created_at >= cutoff).count()
        to_delete = Notification.query.filter(Notification.created_at < cutoff).count()
        print(f"Total notifications in database: {total}")
        print(f"Notifications in the last 15 days (will be kept): {to_keep}")
        print(f"Notifications older than 15 days (will be deleted): {to_delete}")
        return total, to_keep, to_delete

if __name__ == "__main__":
    print("🔔 Notification Count Script")
    print("=" * 40)
    notification_count() 