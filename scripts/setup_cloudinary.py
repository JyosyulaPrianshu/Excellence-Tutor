#!/usr/bin/env python3
"""
Script to set up Cloudinary for PDF storage.
This will solve the file persistence issue on Render.
"""

import sys
import os
from dotenv import load_dotenv

# Load .env file first
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_cloudinary():
    """Set up Cloudinary configuration"""
    
    print("☁️ Setting up Cloudinary for PDF Storage")
    print("=" * 50)
    
    print("\n📋 Steps to set up Cloudinary:")
    print("1. Go to https://cloudinary.com/ and create a free account")
    print("2. Get your credentials from the dashboard")
    print("3. Add these environment variables to your .env file:")
    print()
    print("CLOUDINARY_CLOUD_NAME=your_cloud_name")
    print("CLOUDINARY_API_KEY=your_api_key")
    print("CLOUDINARY_API_SECRET=your_api_secret")
    print()
    print("4. Add these to your Render environment variables:")
    print("   - Go to your Render dashboard")
    print("   - Click on your web service")
    print("   - Go to Environment tab")
    print("   - Add the three CLOUDINARY_ variables")
    print()
    print("5. Install cloudinary package:")
    print("   pip install cloudinary")
    print()
    print("6. Update requirements.txt to include cloudinary")
    
    # Check if cloudinary is already installed
    try:
        import cloudinary
        print("\n✅ Cloudinary is already installed!")
    except ImportError:
        print("\n❌ Cloudinary not installed. Run: pip install cloudinary")
    
    # Check if environment variables are set
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
    api_key = os.getenv('CLOUDINARY_API_KEY')
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
    
    if cloud_name and api_key and api_secret:
        print("✅ Cloudinary environment variables are set!")
    else:
        print("❌ Cloudinary environment variables are missing!")
        print("   Please add them to your .env file and Render environment.")

if __name__ == "__main__":
    setup_cloudinary() 