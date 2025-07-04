#!/usr/bin/env python3
"""
Script to print all notifications in the database.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app, db
from app.models import Notification

def list_notifications():
    app = create_app()
    with app.app_context():
        notifications = Notification.query.order_by(Notification.created_at.desc()).all()
        for n in notifications:
            print(f"ID: {n.id} | User: {n.user_id} | Class: {n.class_for} | Created: {n.created_at} | Seen: {n.seen} | Message: {n.message[:60]}...")

if __name__ == "__main__":
    print("🔔 All Notifications in Database:")
    print("=" * 60)
    list_notifications() 