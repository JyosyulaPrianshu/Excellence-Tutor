#!/usr/bin/env python3
"""
Script to help upload a missing PDF file locally for testing.
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

def upload_missing_pdf():
    """Upload a sample PDF to test the download functionality"""
    
    print("📄 Upload Missing PDF for Testing")
    print("=" * 40)
    
    with app.app_context():
        # Check if we have the missing PDF record
        missing_pdf = PDF.query.filter_by(file_path='20250707094927_fab1f9ff_emp1.pdf').first()
        
        if missing_pdf:
            print(f"Found missing PDF record: {missing_pdf.title}")
            print(f"File path: {missing_pdf.file_path}")
            
            # Create a simple PDF file for testing
            static_pdfs_dir = os.path.join(app.root_path, 'static', 'pdfs')
            os.makedirs(static_pdfs_dir, exist_ok=True)
            
            file_path = os.path.join(static_pdfs_dir, missing_pdf.file_path)
            
            # Create a simple PDF content (this is a minimal PDF file)
            pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF for Download) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n364\n%%EOF\n'
            
            try:
                with open(file_path, 'wb') as f:
                    f.write(pdf_content)
                
                print(f"✅ Created test PDF file: {file_path}")
                print(f"   File size: {len(pdf_content)} bytes")
                print("\n💡 Now students should be able to download this PDF!")
                print("   The file contains a simple test message.")
                
            except Exception as e:
                print(f"❌ Error creating PDF file: {e}")
        else:
            print("❌ Missing PDF record not found in database")
            print("   This means the issue might be different.")

if __name__ == "__main__":
    upload_missing_pdf() 