#!/usr/bin/env python3
"""
Delete all users and profiles, then add 2 new students for each class and a new admin.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Profile
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Delete all users and profiles
    Profile.query.delete()
    User.query.delete()
    db.session.commit()
    print("All users and profiles deleted.")

    # Add 2 students for each class
    student_classes = [
        ('6', 'Class 6'),
        ('7', 'Class 7'),
        ('8', 'Class 8'),
        ('9', 'Class 9'),
        ('10', 'Class 10'),
        ('11_arts', 'Class 11 Arts'),
        ('11_science', 'Class 11 Science'),
        ('12_arts', 'Class 12 Arts'),
        ('12_science', 'Class 12 Science'),
    ]
    student_password = "studentpass123"
    roll_counter = 1
    for class_key, class_label in student_classes:
        for i in range(2):
            email = f"freshstudent{i+1}_{class_key}@example.com"
            user = User(email=email, password=generate_password_hash(student_password), is_admin=False)
            db.session.add(user)
            db.session.commit()
            profile = Profile(
                user_id=user.id,
                full_name=f"Fresh Student {i+1} {class_label}",
                parent_name=f"Parent {i+1} {class_label}",
                parent_phone=f"90000000{roll_counter:02d}",
                student_phone=f"80000000{roll_counter:02d}",
                student_class=class_key,
                school_name="Fresh School",
                roll_number=roll_counter
            )
            db.session.add(profile)
            db.session.commit()
            print(f"Created student: {email} | roll_number: {roll_counter}")
            roll_counter += 1

    # Add a new admin
    admin_email = "freshadmin@example.com"
    admin_password = "adminpass123"
    admin = User(email=admin_email, password=generate_password_hash(admin_password), is_admin=True)
    db.session.add(admin)
    db.session.commit()
    print(f"Created admin: {admin_email} | password: {admin_password}")

    print("\nDone.") 