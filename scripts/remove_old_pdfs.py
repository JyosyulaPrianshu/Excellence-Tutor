#!/usr/bin/env python3
"""
Script to remove all old PDF records from the database that do not have a Cloudinary URL set.
"""

import sys
import os
from dotenv import load_dotenv

# Load .env file first
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import PDF

app = create_app()

with app.app_context():
    old_pdfs = PDF.query.filter((PDF.cloudinary_url == None) | (PDF.cloudinary_url == '')).all()
    print(f"Found {len(old_pdfs)} old PDF(s) without Cloudinary URL.")
    for pdf in old_pdfs:
        print(f"Deleting: {pdf.title} (ID: {pdf.id}, file_path: {pdf.file_path})")
        db.session.delete(pdf)
    db.session.commit()
    print("✅ Old PDF records removed from the database.") 