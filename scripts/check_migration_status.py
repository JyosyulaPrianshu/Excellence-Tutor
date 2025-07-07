#!/usr/bin/env python3
"""
Quick script to check migration status and database health
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from flask_migrate import current
from sqlalchemy import text

def check_migration_status():
    """Check current migration status and database health"""
    print("🔍 Excellence Tutorial - Migration Status Check")
    print("=" * 50)
    
    app = create_app()
    with app.app_context():
        try:
            # Check current migration
            current_rev = current()
            print(f"📍 Current Migration: {current_rev}")
            
            # Check database connection
            try:
                db.session.execute(text('SELECT 1'))
                print("✅ Database Connection: OK")
            except Exception as e:
                print(f"❌ Database Connection: FAILED - {e}")
                return
            
            # Check if all tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            expected_tables = [
                'users', 'profiles', 'tests', 'marks', 'fees', 'payments',
                'notifications', 'pdfs', 'settings', 'resources', 'dropout_requests'
            ]
            
            print(f"\n📊 Database Tables ({len(tables)} total):")
            for table in expected_tables:
                if table in tables:
                    print(f"  ✅ {table}")
                else:
                    print(f"  ❌ {table} (MISSING)")
            
            # Check for extra tables
            extra_tables = set(tables) - set(expected_tables) - {'alembic_version'}
            if extra_tables:
                print(f"\n🔍 Additional Tables: {', '.join(extra_tables)}")
            
            # Check table row counts
            print(f"\n📈 Table Row Counts:")
            from app.models import User, Profile, Test, Mark, Fee, Payment, Notification, PDF, Setting, Resource
            
            models = [
                ('Users', User),
                ('Profiles', Profile),
                ('Tests', Test),
                ('Marks', Mark),
                ('Fees', Fee),
                ('Payments', Payment),
                ('Notifications', Notification),
                ('PDFs', PDF),
                ('Settings', Setting),
                ('Resources', Resource),
            ]
            
            for name, model in models:
                try:
                    count = model.query.count()
                    print(f"  📋 {name}: {count}")
                except Exception as e:
                    print(f"  ❌ {name}: ERROR - {e}")
            
            # Check for migration issues
            print(f"\n🔧 Migration Health Check:")
            
            # Check alembic_version table
            try:
                result = db.session.execute(text('SELECT version_num FROM alembic_version'))
                version = result.scalar()
                if version == current_rev:
                    print("  ✅ Migration version consistency: OK")
                else:
                    print(f"  ⚠️  Version mismatch: DB={version}, Flask-Migrate={current_rev}")
            except Exception as e:
                print(f"  ❌ Alembic version check: FAILED - {e}")
            
            # Check for pending migrations
            try:
                import subprocess
                result = subprocess.run(['flask', 'db', 'show'], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    print("  ⚠️  Pending migrations detected")
                    print(f"     {result.stdout.strip()}")
                else:
                    print("  ✅ No pending migrations")
            except Exception as e:
                print(f"  ❌ Pending migration check: FAILED - {e}")
            
            print(f"\n🎯 Summary:")
            print(f"  • Database: Connected and accessible")
            print(f"  • Tables: {len([t for t in expected_tables if t in tables])}/{len(expected_tables)} expected tables present")
            print(f"  • Migration: {current_rev}")
            
        except Exception as e:
            print(f"❌ Error during status check: {e}")

if __name__ == "__main__":
    check_migration_status()