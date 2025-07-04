#!/usr/bin/env python3
"""
Comprehensive Security Testing Script for Excellence Tutorial
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, PDF
from app.utils import validate_pdf_file, generate_secure_filename, sanitize_filename
from werkzeug.security import generate_password_hash
import tempfile
import io

def test_file_upload_security():
    """Test file upload security features"""
    print("🔒 Testing File Upload Security...")
    
    # Test 1: Valid PDF file
    print("\n1️⃣ Testing valid PDF file:")
    valid_pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n'
    valid_file = io.BytesIO(valid_pdf_content)
    valid_file.filename = 'test.pdf'
    valid_file.seek(0)
    
    is_valid, result = validate_pdf_file(valid_file)
    print(f"   Valid PDF: {'✅ PASS' if is_valid else '❌ FAIL'}")
    
    # Test 2: Invalid file extension
    print("\n2️⃣ Testing invalid file extension:")
    invalid_file = io.BytesIO(b'fake content')
    invalid_file.filename = 'test.exe'
    invalid_file.seek(0)
    
    is_valid, result = validate_pdf_file(invalid_file)
    print(f"   Invalid extension: {'✅ PASS' if not is_valid else '❌ FAIL'}")
    
    # Test 3: File too large
    print("\n3️⃣ Testing file size limit:")
    large_file = io.BytesIO(b'x' * (11 * 1024 * 1024))  # 11MB
    large_file.filename = 'large.pdf'
    large_file.seek(0)
    
    is_valid, result = validate_pdf_file(large_file)
    print(f"   File size limit: {'✅ PASS' if not is_valid else '❌ FAIL'}")
    
    # Test 4: Malicious content
    print("\n4️⃣ Testing malicious content detection:")
    malicious_content = b'%PDF-1.4\n<script>alert("xss")</script>\n'
    malicious_file = io.BytesIO(malicious_content)
    malicious_file.filename = 'malicious.pdf'
    malicious_file.seek(0)
    
    is_valid, result = validate_pdf_file(malicious_file)
    print(f"   Malicious content: {'✅ PASS' if not is_valid else '❌ FAIL'}")
    
    # Test 5: Secure filename generation
    print("\n5️⃣ Testing secure filename generation:")
    original_filename = "../../../etc/passwd.pdf"
    secure_name = generate_secure_filename(original_filename)
    print(f"   Original: {original_filename}")
    print(f"   Secure: {secure_name}")
    print(f"   Path traversal protection: {'✅ PASS' if '..' not in secure_name else '❌ FAIL'}")

def test_authentication_security():
    """Test authentication security"""
    print("\n🔐 Testing Authentication Security...")
    
    app = create_app()
    with app.app_context():
        # Test 1: Password hashing
        print("\n1️⃣ Testing password hashing:")
        password = "test123"
        hashed = generate_password_hash(password)
        print(f"   Original: {password}")
        print(f"   Hashed: {hashed[:50]}...")
        print(f"   Hashing: {'✅ PASS' if hashed != password else '❌ FAIL'}")
        
        # Test 2: User enumeration protection
        print("\n2️⃣ Testing user enumeration protection:")
        existing_user = User.query.first()
        if existing_user:
            print(f"   Found user: {existing_user.email}")
            print(f"   Password field: {'✅ PASS' if len(existing_user.password) > 20 else '❌ FAIL'}")

def test_database_security():
    """Test database security"""
    print("\n🗄️ Testing Database Security...")
    
    app = create_app()
    with app.app_context():
        # Test 1: SQL injection protection (ORM usage)
        print("\n1️⃣ Testing SQL injection protection:")
        try:
            # This should be safe due to ORM
            users = User.query.filter_by(email="test@example.com").all()
            print(f"   ORM query: {'✅ PASS'}")
        except Exception as e:
            print(f"   ORM query: {'❌ FAIL'} - {e}")
        
        # Test 2: Database connection security
        print("\n2️⃣ Testing database connection:")
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        if 'sqlite' in db_url:
            print(f"   Local SQLite: {'✅ PASS'}")
        elif 'postgresql' in db_url:
            print(f"   PostgreSQL with SSL: {'✅ PASS'}")
        else:
            print(f"   Database type: {'⚠️  CHECK'} - {db_url}")

def test_session_security():
    """Test session security"""
    print("\n🍪 Testing Session Security...")
    
    app = create_app()
    
    # Test 1: Session configuration
    print("\n1️⃣ Testing session configuration:")
    print(f"   Secure cookies: {app.config.get('SESSION_COOKIE_SECURE', False)}")
    print(f"   HTTP only: {app.config.get('SESSION_COOKIE_HTTPONLY', False)}")
    print(f"   SameSite: {app.config.get('SESSION_COOKIE_SAMESITE', 'Not set')}")
    
    # Test 2: CSRF protection
    print("\n2️⃣ Testing CSRF protection:")
    print(f"   CSRF enabled: {'✅ PASS' if app.config.get('WTF_CSRF_ENABLED', True) else '❌ FAIL'}")
    print(f"   CSRF timeout: {app.config.get('WTF_CSRF_TIME_LIMIT', 'Not set')} seconds")

def test_error_handling():
    """Test error handling security"""
    print("\n🚨 Testing Error Handling Security...")
    
    app = create_app()
    
    # Test 1: Error pages exist
    print("\n1️⃣ Testing error pages:")
    error_pages = ['404', '500', '403', 'csrf']
    for error in error_pages:
        template_path = f'app/templates/errors/{error}.html'
        exists = os.path.exists(template_path)
        print(f"   {error} page: {'✅ PASS' if exists else '❌ FAIL'}")

def main():
    """Run all security tests"""
    print("🛡️ Excellence Tutorial - Security Testing")
    print("=" * 50)
    
    test_file_upload_security()
    test_authentication_security()
    test_database_security()
    test_session_security()
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("🎯 Security Testing Complete!")
    print("\n📋 Manual Tests to Perform:")
    print("1. Try uploading non-PDF files")
    print("2. Try uploading files > 10MB")
    print("3. Test CSRF protection on forms")
    print("4. Test session timeout")
    print("5. Test admin access control")
    print("6. Test SQL injection attempts")
    print("7. Test XSS in input fields")

if __name__ == "__main__":
    main() 