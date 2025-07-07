#!/usr/bin/env python3
"""
Script to add a sample PDF record to the database for testing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import PDF
from datetime import datetime

app = create_app()

with app.app_context():
    try:
        # Create a sample PDF record
        sample_pdf = PDF(
            title="Sample Study Material",
            file_path="sample.pdf",
            class_for="all",
            uploaded_at=datetime.now()
        )
        
        db.session.add(sample_pdf)
        db.session.commit()
        
        print("✅ Sample PDF record added to database!")
        print(f"Title: {sample_pdf.title}")
        print(f"File path: {sample_pdf.file_path}")
        print(f"Class: {sample_pdf.class_for}")
        
        # Note: You'll need to manually add a PDF file to app/static/pdfs/sample.pdf
        # for the download to actually work
        print("\n⚠️  Note: You need to add a PDF file to app/static/pdfs/sample.pdf")
        print("   for the download to work properly.")
        
    except Exception as e:
        print(f"❌ Error adding sample PDF: {str(e)}")
        db.session.rollback() 