#!/usr/bin/env python3
"""
Script to clear all dues from the database
"""

import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Fee, Payment, Notification

def clear_all_dues():
    """Remove all dues, payments, and related notifications from the database"""
    app = create_app()
    
    with app.app_context():
        try:
            # Count existing records
            fee_count = Fee.query.count()
            payment_count = Payment.query.count()
            
            # Find notifications related to dues
            due_notifications = Notification.query.filter(
                Notification.message.like('%month due added%')
            ).count()
            
            print(f"Found {fee_count} dues, {payment_count} payments, and {due_notifications} due-related notifications")
            
            if fee_count == 0:
                print("No dues found to remove.")
                return
            
            # Confirm before deletion
            confirm = input(f"Are you sure you want to delete {fee_count} dues, {payment_count} payments, and {due_notifications} notifications? (yes/no): ")
            
            if confirm.lower() != 'yes':
                print("Operation cancelled.")
                return
            
            # Delete all payments first (due to foreign key constraints)
            Payment.query.delete()
            print(f"Deleted {payment_count} payments")
            
            # Delete all fees
            Fee.query.delete()
            print(f"Deleted {fee_count} dues")
            
            # Delete due-related notifications
            deleted_notifications = Notification.query.filter(
                Notification.message.like('%month due added%')
            ).delete(synchronize_session=False)
            print(f"Deleted {deleted_notifications} due-related notifications")
            
            # Commit the changes
            db.session.commit()
            
            print("✅ All dues, payments, and related notifications have been successfully removed!")
            print("The database is now clean and ready for fresh dues assignment.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error clearing dues: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    print("🗑️  Due Clearing Script")
    print("=" * 50)
    clear_all_dues() 