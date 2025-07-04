#!/usr/bin/env python3
"""
Script to add 11 admin notifications for testing: oldest is long (89 chars, 10 days ago), 10 newer are normal (9 to 0 days ago).
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app, db
from app.models import Notification
from datetime import datetime, timedelta

def add_test_notifications():
    app = create_app()
    with app.app_context():
        # Delete all existing admin notifications for a clean test
        Notification.query.filter(Notification.user_id == None).delete(synchronize_session=False)
        db.session.commit()
        # Add oldest long message (10 days ago)
        long_msg = "This is a long notification message to test the tooltip. It should be exactly 89 chars!"
        n1 = Notification(user_id=None, message=long_msg, class_for='all', created_at=datetime.now() - timedelta(days=10))
        db.session.add(n1)
        # Add 10 normal messages, newer (9 to 0 days ago)
        for i in range(10, 0, -1):
            msg = f"Test notification {11-i}"  # short message
            n = Notification(user_id=None, message=msg, class_for='all', created_at=datetime.now() - timedelta(days=i-1))
            db.session.add(n)
        db.session.commit()
        print("✅ 11 test notifications added (oldest is long, 10 newer are normal).")

if __name__ == "__main__":
    add_test_notifications() 