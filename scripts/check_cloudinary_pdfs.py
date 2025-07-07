#!/usr/bin/env python3
"""
Script to print all PDF records and their cloudinary_url values for debugging.
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
    pdfs = PDF.query.all()
    print(f"Total PDF records: {len(pdfs)}")
    for pdf in pdfs:
        print(f"ID: {pdf.id}")
        print(f"  Title: {pdf.title}")
        print(f"  File path: {pdf.file_path}")
        print(f"  Cloudinary URL: {pdf.cloudinary_url}")
        print(f"  Uploaded: {pdf.uploaded_at}")
        print(f"  Class: {pdf.class_for}")
        print("-") 