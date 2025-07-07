#!/usr/bin/env python3
"""
Comprehensive diagnostic script to identify PDF download issues in production.
"""

import sys
import os
from dotenv import load_dotenv

# Load .env file first
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import PDF, Profile, User
from flask import url_for

app = create_app()

def check_pdf_download_issues():
    """Comprehensive check for PDF download issues"""
    
    print("🔍 PDF Download Issue Diagnosis")
    print("=" * 50)
    
    with app.app_context():
        # 1. Check database records
        print("\n1️⃣ Database Records:")
        pdfs = PDF.query.all()
        print(f"   Total PDF records: {len(pdfs)}")
        
        for pdf in pdfs:
            print(f"   - {pdf.title} (ID: {pdf.id})")
            print(f"     File path: {pdf.file_path}")
            print(f"     Class: {pdf.class_for}")
            print(f"     Uploaded: {pdf.uploaded_at}")
        
        # 2. Check file existence
        print("\n2️⃣ File System Check:")
        static_pdfs_dir = os.path.join(app.root_path, 'static', 'pdfs')
        print(f"   Static PDFs directory: {static_pdfs_dir}")
        
        if os.path.exists(static_pdfs_dir):
            files = os.listdir(static_pdfs_dir)
            print(f"   Files in directory: {files}")
            
            for pdf in pdfs:
                file_path = os.path.join(static_pdfs_dir, pdf.file_path)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"   ✅ {pdf.file_path} exists ({file_size} bytes)")
                else:
                    print(f"   ❌ {pdf.file_path} MISSING!")
        else:
            print("   ❌ Static PDFs directory does not exist!")
        
        # 3. Check URL generation
        print("\n3️⃣ URL Generation Test:")
        for pdf in pdfs:
            try:
                url = url_for('static', filename=f'pdfs/{pdf.file_path}')
                print(f"   Generated URL for {pdf.title}: {url}")
            except Exception as e:
                print(f"   ❌ Error generating URL for {pdf.title}: {e}")
        
        # 4. Check student access
        print("\n4️⃣ Student Access Check:")
        students = User.query.filter_by(is_admin=False).all()
        print(f"   Total students: {len(students)}")
        
        for student in students:
            profile = Profile.query.filter_by(user_id=student.id).first()
            if profile:
                accessible_pdfs = PDF.query.filter(
                    (PDF.class_for == 'all') | (PDF.class_for == profile.student_class)
                ).all()
                print(f"   Student {profile.full_name} (Class: {profile.student_class}): {len(accessible_pdfs)} PDFs accessible")
        
        # 5. Check Flask configuration
        print("\n5️⃣ Flask Configuration:")
        print(f"   Static folder: {app.static_folder}")
        print(f"   Static URL path: {app.static_url_path}")
        print(f"   Debug mode: {app.debug}")
        print(f"   Environment: {app.config.get('FLASK_ENV', 'Not set')}")
        
        # 6. Check for common issues
        print("\n6️⃣ Common Issues Check:")
        
        # Issue 1: Files missing from filesystem
        missing_files = []
        for pdf in pdfs:
            file_path = os.path.join(static_pdfs_dir, pdf.file_path)
            if not os.path.exists(file_path):
                missing_files.append(pdf.file_path)
        
        if missing_files:
            print(f"   ❌ Missing files: {missing_files}")
            print("   💡 Solution: Files were uploaded to production but lost during deployment")
        else:
            print("   ✅ All PDF files exist")
        
        # Issue 2: Static folder not configured
        if not app.static_folder:
            print("   ❌ Static folder not configured")
        else:
            print("   ✅ Static folder configured")
        
        # Issue 3: File permissions
        if os.path.exists(static_pdfs_dir):
            try:
                test_file = os.path.join(static_pdfs_dir, "test.txt")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                print("   ✅ Directory is writable")
            except Exception as e:
                print(f"   ❌ Directory permission issue: {e}")
        
        # Issue 4: URL routing
        try:
            test_url = url_for('static', filename='pdfs/test.pdf')
            print(f"   ✅ URL generation works: {test_url}")
        except Exception as e:
            print(f"   ❌ URL generation issue: {e}")

if __name__ == "__main__":
    check_pdf_download_issues() 