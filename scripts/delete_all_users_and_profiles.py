#!/usr/bin/env python3
"""
Script to delete all users and profiles from the Excellence Tutorial database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Profile

def delete_all_users_and_profiles():
    app = create_app()
    with app.app_context():
        try:
            print("Deleting all profiles...")
            num_profiles = Profile.query.delete()
            print(f"   ✅ Deleted {num_profiles} profiles")
            print("Deleting all users...")
            num_users = User.query.delete()
            print(f"   ✅ Deleted {num_users} users")
            db.session.commit()
            print("\n🎯 All users and profiles have been deleted from the database!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during deletion: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    delete_all_users_and_profiles() 