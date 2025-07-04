#!/usr/bin/env python3
"""
Script to list all users in the database, showing their email and admin status.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    users = User.query.all()
    print(f"Total users: {len(users)}")
    for user in users:
        print(f"Email: {user.email} | Admin: {user.is_admin}") 