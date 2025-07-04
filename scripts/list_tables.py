#!/usr/bin/env python3
"""
Script to list all table names and their columns in the database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

app = create_app()

with app.app_context():
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    print("Tables and their columns in the database:")
    for table in tables:
        print(f"\nTable: {table}")
        columns = inspector.get_columns(table)
        for col in columns:
            print(f"  - {col['name']} ({col['type']})") 