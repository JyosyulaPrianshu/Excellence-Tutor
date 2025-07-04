#!/usr/bin/env python3
"""
Check user existence and create admin/student if none exist.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Profile
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    user_count = User.query.count()
    print(f"Total users: {user_count}")
    users = User.query.all()
    if users:
        print("\nAll users:")
        for user in users:
            print(f"ID: {user.id}, Email: {user.email}, Is Admin: {user.is_admin}")
    else:
        print("No users found. Creating admin and student...")
        # Always create a new admin
        admin_email = "admin@excellence.com"
        admin_password = "admin123"
        existing_admin = User.query.filter_by(email=admin_email).first()
        if existing_admin:
            Profile.query.filter_by(user_id=existing_admin.id).delete()
            db.session.delete(existing_admin)
            db.session.commit()
        admin = User(email=admin_email, password=generate_password_hash(admin_password), is_admin=True)
        db.session.add(admin)
        db.session.commit()
        print(f"Created admin: {admin_email} | password: {admin_password}")

    # Always create 9 students, one for each class/stream
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
    student_password = "student123"
    for idx, (class_key, class_label) in enumerate(student_classes, start=1):
        email = f"student{class_key}@excellence.com"
        existing_student = User.query.filter_by(email=email).first()
        if existing_student:
            Profile.query.filter_by(user_id=existing_student.id).delete()
            db.session.delete(existing_student)
            db.session.commit()
        student = User(email=email, password=generate_password_hash(student_password), is_admin=False)
        db.session.add(student)
        db.session.commit()
        # Assign roll_number as next available (max + 1) globally
        max_roll = db.session.query(db.func.max(Profile.roll_number)).scalar()
        next_roll = 1 if max_roll is None else max_roll + 1
        profile = Profile(
            user_id=student.id,
            full_name=f"Student {class_label}",
            parent_name=f"Parent {class_label}",
            parent_phone=f"90000000{idx:02d}",
            student_phone=f"80000000{idx:02d}",
            student_class=class_key,
            school_name="Excellence School",
            roll_number=next_roll
        )
        db.session.add(profile)
        db.session.commit()
        print(f"Created student: {email} | password: {student_password}")

    print("\nDone.") 