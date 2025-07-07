#!/usr/bin/env python3
"""
Script to create admin users from environment variables.
This script is used during deployment to ensure admin users exist.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_admins():
    """Create admin users from environment variables"""
    admin1_email = os.getenv('ADMIN1_EMAIL')
    admin1_password = os.getenv('ADMIN1_PASSWORD')
    admin2_email = os.getenv('ADMIN2_EMAIL')
    admin2_password = os.getenv('ADMIN2_PASSWORD')

    admins = []
    if admin1_email and admin1_password:
        admins.append((admin1_email, admin1_password))
    if admin2_email and admin2_password:
        admins.append((admin2_email, admin2_password))

    if not admins:
        print('No valid admin credentials found in environment variables.')
        print('Please set ADMIN1_EMAIL/ADMIN1_PASSWORD and/or ADMIN2_EMAIL/ADMIN2_PASSWORD.')
        return False

    app = create_app()

    with app.app_context():
        try:
            for email, password in admins:
                existing = User.query.filter_by(email=email).first()
                if existing:
                    print(f"Admin with email {email} already exists.")
                    continue
                admin = User(email=email, password=generate_password_hash(password), is_admin=True)
                db.session.add(admin)
                print(f"Added admin: {email}")
            db.session.commit()
            print("Admin creation process completed successfully.")
            return True
        except Exception as e:
            print(f"Error creating admin users: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    if create_admins():
        print("Admin setup completed successfully.")
    else:
        print("Admin setup failed.")
        sys.exit(1) 