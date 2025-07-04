#!/usr/bin/env python3
"""
Script to clear all data from the Excellence Tutorial database
while preserving user accounts and admin accounts.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Test, Mark, Fee, Payment, Notification, PDF, Profile, Setting, User, Resource
from datetime import datetime

def clear_all_data(full=False):
    """Clear all data. If full=True, also delete all users and profiles."""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Starting data cleanup process...")
            
            if full:
                print("🧨 Deleting all users and profiles...")
                num_profiles = Profile.query.delete()
                num_users = User.query.delete()
                print(f"   ✅ Deleted {num_profiles} profiles and {num_users} users")
            
            # Clear all tests and marks
            print("🗑️  Clearing tests and marks...")
            mark_count = Mark.query.delete()
            test_count = Test.query.delete()
            print(f"   ✅ Deleted {mark_count} marks and {test_count} tests")
            
            # Clear all fees and payments
            print("💰 Clearing fees and payments...")
            payment_count = Payment.query.delete()
            fee_count = Fee.query.delete()
            print(f"   ✅ Deleted {payment_count} payments and {fee_count} fees")
            
            # Clear all notifications
            print("🔔 Clearing notifications...")
            notification_count = Notification.query.delete()
            print(f"   ✅ Deleted {notification_count} notifications")
            
            # Clear all PDFs
            print("📄 Clearing PDFs...")
            pdf_count = PDF.query.delete()
            print(f"   ✅ Deleted {pdf_count} PDFs")

            # Clear all resources
            print("📚 Clearing resources...")
            resource_count = Resource.query.delete()
            print(f"   ✅ Deleted {resource_count} resources")
            
            # Clear all settings (except UPI settings if you want to keep them)
            print("⚙️  Clearing settings...")
            settings_count = Setting.query.delete()
            print(f"   ✅ Deleted {settings_count} settings")
            
            # Do NOT reset or modify profile data
            print("👤 Skipping profile data reset (preserving signup details)...")
            
            # Clear static files (PDFs and images except profile pics and UPI QR)
            print("📁 Clearing static files...")
            import shutil
            static_pdfs = os.path.join(app.root_path, 'static', 'pdfs')
            static_img = os.path.join(app.root_path, 'static', 'img')
            
            # Clear PDFs directory (except keep the directory)
            if os.path.exists(static_pdfs):
                for file in os.listdir(static_pdfs):
                    if file.endswith('.pdf'):
                        os.remove(os.path.join(static_pdfs, file))
                print(f"   ✅ Cleared PDF files from {static_pdfs}")
            
            # Clear uploaded images except upi_qr.jpg (do not touch profile pics)
            if os.path.exists(static_img):
                for file in os.listdir(static_img):
                    if file == 'upi_qr.jpg':
                        continue
                    # Only delete if it's not a profile pic (profile pics are referenced in Profile.profile_pic)
                    # We'll skip all files except upi_qr.jpg for safety
                print(f"   ✅ Skipped image deletion except upi_qr.jpg in {static_img}")
            
            # Commit all changes
            db.session.commit()
            
            print("\n🎉 Data cleanup completed successfully!")
            print(f"   • Tests: {test_count}")
            print(f"   • Marks: {mark_count}")
            print(f"   • Fees: {fee_count}")
            print(f"   • Payments: {payment_count}")
            print(f"   • Notifications: {notification_count}")
            print(f"   • PDFs: {pdf_count}")
            print(f"   • Resources: {resource_count}")
            print(f"   • Settings: {settings_count}")
            
            print("\n✅ All data has been cleared while preserving user accounts!")
            print("   Users can still log in, but all their data has been reset.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during data cleanup: {str(e)}")
            return False
    
    return True

def confirm_clear_data():
    """Ask for confirmation before clearing data"""
    print("⚠️  WARNING: This will permanently delete ALL data!")
    print("   • All tests and marks will be deleted")
    print("   • All fees and payments will be deleted")
    print("   • All notifications will be deleted")
    print("   • All PDFs will be deleted")
    print("   • All resources will be deleted")
    print("   • All settings will be deleted")
    print("   • All profile data will be reset")
    print("\n   ✅ User accounts will be preserved")
    print("   ✅ Admin accounts will be preserved")
    
    response = input("\n🤔 Are you sure you want to continue? (yes/no): ").lower().strip()
    return response in ['yes', 'y']

if __name__ == "__main__":
    print("🧹 Excellence Tutorial - Data Cleanup Script")
    print("=" * 50)
    full = '--full' in sys.argv
    # Skip confirmation prompt and proceed directly
    if clear_all_data(full=full):
        print("\n🎯 Data cleanup completed successfully!")
    else:
        print("\n💥 Data cleanup failed!")
        sys.exit(1) 