#!/usr/bin/env python3
"""
Check if all main tables are empty and print row counts.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Profile, Test, Mark, Fee, Payment, Notification, PDF, Resource, Setting

app = create_app()
with app.app_context():
    tables = [
        ("users", User),
        ("profiles", Profile),
        ("tests", Test),
        ("marks", Mark),
        ("fees", Fee),
        ("payments", Payment),
        ("notifications", Notification),
        ("pdfs", PDF),
        ("resources", Resource),
        ("settings", Setting),
    ]
    print("Table row counts:")
    for name, model in tables:
        count = model.query.count()
        print(f"{name}: {count}")
    print("\nDone.") 