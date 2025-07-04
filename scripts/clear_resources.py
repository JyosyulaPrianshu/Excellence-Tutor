#!/usr/bin/env python3
"""
Script to clear all resources from the Excellence Tutorial database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Resource

def clear_resources():
    """Clear all resources from the database"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Starting resources cleanup process...")
            
            # Count existing resources
            resource_count = Resource.query.count()
            
            if resource_count == 0:
                print("✅ No resources found in the database.")
                return True
            
            print(f"📚 Found {resource_count} resources in the database")
            
            # Confirm before deletion
            confirm = input(f"Are you sure you want to delete all {resource_count} resources? (yes/no): ").lower().strip()
            
            if confirm not in ['yes', 'y']:
                print("❌ Operation cancelled.")
                return False
            
            # Delete all resources
            deleted_count = Resource.query.delete()
            db.session.commit()
            
            print(f"✅ Successfully deleted {deleted_count} resources from the database!")
            print("🎉 Resources table has been cleared!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error clearing resources: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    print("🧹 Excellence Tutorial - Resources Cleanup Script")
    print("=" * 50)
    
    if clear_resources():
        print("\n🎯 Resources cleanup completed successfully!")
    else:
        print("\n💥 Resources cleanup failed!")
        sys.exit(1) 