#!/usr/bin/env python3
"""
Script to check PDF records in the database and verify file existence.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import PDF

app = create_app()

with app.app_context():
    # Get all PDF records from database
    pdfs = PDF.query.all()
    print(f"Total PDF records in database: {len(pdfs)}")
    
    for pdf in pdfs:
        print(f"\nPDF: {pdf.title}")
        print(f"  File path: {pdf.file_path}")
        print(f"  Class: {pdf.class_for}")
        print(f"  Uploaded: {pdf.uploaded_at}")
        
        # Check if file exists
        static_pdf_path = os.path.join(app.root_path, 'static', 'pdfs', pdf.file_path)
        if os.path.exists(static_pdf_path):
            file_size = os.path.getsize(static_pdf_path)
            print(f"  ✅ File exists ({file_size} bytes)")
        else:
            print(f"  ❌ File missing!")
    
    # Check static/pdfs directory
    static_pdfs_dir = os.path.join(app.root_path, 'static', 'pdfs')
    print(f"\nStatic PDFs directory: {static_pdfs_dir}")
    if os.path.exists(static_pdfs_dir):
        files = os.listdir(static_pdfs_dir)
        print(f"Files in directory: {files}")
    else:
        print("Static PDFs directory does not exist!") 