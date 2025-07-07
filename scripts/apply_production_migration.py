#!/usr/bin/env python3
"""
Script to apply the cloudinary_url migration to production database.
"""

import sys
import os
from dotenv import load_dotenv

# Load .env file first
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

app = create_app()

def apply_production_migration():
    """Apply the cloudinary_url migration to production database"""
    
    print("🔄 Applying cloudinary_url migration to production database...")
    
    with app.app_context():
        try:
            # Run the migration
            from flask_migrate import upgrade
            upgrade()
            print("✅ Migration applied successfully!")
            
            # Verify the column exists
            from sqlalchemy import text
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'pdfs' AND column_name = 'cloudinary_url'
            """))
            
            if result.fetchone():
                print("✅ cloudinary_url column exists in production database!")
            else:
                print("❌ cloudinary_url column not found!")
                
        except Exception as e:
            print(f"❌ Error applying migration: {e}")

if __name__ == "__main__":
    apply_production_migration() 