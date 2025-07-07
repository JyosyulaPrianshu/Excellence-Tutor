#!/usr/bin/env python3
"""
Comprehensive migration management script for Excellence Tutorial
"""

import sys
import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from flask_migrate import current, history, upgrade, downgrade, migrate

def run_command(command):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_migration_status():
    """Check current migration status"""
    print("🔍 Checking Migration Status...")
    print("=" * 50)
    
    app = create_app()
    with app.app_context():
        try:
            # Get current revision
            current_rev = current()
            print(f"Current Revision: {current_rev}")
            
            # Get migration history
            print("\n📜 Migration History:")
            success, stdout, stderr = run_command("flask db history --verbose")
            if success:
                print(stdout)
            else:
                print(f"Error getting history: {stderr}")
                
            # Check for pending migrations
            print("\n🔄 Checking for pending migrations...")
            success, stdout, stderr = run_command("flask db show")
            if success and stdout.strip():
                print("Pending migrations found:")
                print(stdout)
            else:
                print("✅ No pending migrations")
                
        except Exception as e:
            print(f"❌ Error checking migration status: {e}")

def apply_migrations():
    """Apply all pending migrations"""
    print("🚀 Applying Migrations...")
    print("=" * 50)
    
    # Create backup first
    backup_database()
    
    app = create_app()
    with app.app_context():
        try:
            print("Applying migrations...")
            upgrade()
            print("✅ Migrations applied successfully!")
            
            # Verify current status
            current_rev = current()
            print(f"New current revision: {current_rev}")
            
        except Exception as e:
            print(f"❌ Error applying migrations: {e}")
            print("Consider rolling back if needed")

def create_migration():
    """Create a new migration"""
    print("📝 Creating New Migration...")
    print("=" * 50)
    
    message = input("Enter migration message: ").strip()
    if not message:
        print("❌ Migration message is required")
        return
    
    try:
        success, stdout, stderr = run_command(f'flask db migrate -m "{message}"')
        if success:
            print("✅ Migration created successfully!")
            print(stdout)
        else:
            print(f"❌ Error creating migration: {stderr}")
    except Exception as e:
        print(f"❌ Error: {e}")

def rollback_migration():
    """Rollback to previous migration"""
    print("⏪ Rolling Back Migration...")
    print("=" * 50)
    
    print("⚠️  WARNING: This will rollback the database to the previous migration!")
    confirm = input("Are you sure? (yes/no): ").lower().strip()
    
    if confirm != 'yes':
        print("❌ Rollback cancelled")
        return
    
    # Create backup first
    backup_database()
    
    app = create_app()
    with app.app_context():
        try:
            print("Rolling back migration...")
            downgrade()
            print("✅ Migration rolled back successfully!")
            
            # Verify current status
            current_rev = current()
            print(f"Current revision after rollback: {current_rev}")
            
        except Exception as e:
            print(f"❌ Error rolling back migration: {e}")

def backup_database():
    """Create a database backup"""
    print("📦 Creating Database Backup...")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    if 'sqlite' in database_url:
        print("ℹ️  SQLite database - backup not implemented")
        return True
    
    if 'postgresql' in database_url:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"backup_{timestamp}.sql"
        
        try:
            success, stdout, stderr = run_command(f'pg_dump "{database_url}" > {backup_file}')
            if success:
                print(f"✅ Backup created: {backup_file}")
                return True
            else:
                print(f"❌ Backup failed: {stderr}")
                return False
        except Exception as e:
            print(f"❌ Backup error: {e}")
            return False
    
    print("❌ Unsupported database type for backup")
    return False

def reset_migrations():
    """Reset migration system (DEVELOPMENT ONLY)"""
    print("🚨 DANGER: Reset Migration System")
    print("=" * 50)
    
    print("⚠️  WARNING: This will DELETE ALL migration history!")
    print("⚠️  This should ONLY be used in development!")
    print("⚠️  NEVER use this in production!")
    
    confirm1 = input("Type 'RESET' to confirm: ").strip()
    if confirm1 != 'RESET':
        print("❌ Reset cancelled")
        return
    
    confirm2 = input("Are you absolutely sure? (yes/no): ").lower().strip()
    if confirm2 != 'yes':
        print("❌ Reset cancelled")
        return
    
    try:
        # Remove migrations directory
        import shutil
        migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'migrations')
        if os.path.exists(migrations_dir):
            shutil.rmtree(migrations_dir)
            print("🗑️  Removed migrations directory")
        
        # Reinitialize
        success, stdout, stderr = run_command("flask db init")
        if success:
            print("✅ Reinitialized migration system")
            
            # Create initial migration
            success, stdout, stderr = run_command('flask db migrate -m "Initial migration"')
            if success:
                print("✅ Created initial migration")
                
                # Apply migration
                success, stdout, stderr = run_command("flask db upgrade")
                if success:
                    print("✅ Applied initial migration")
                else:
                    print(f"❌ Error applying initial migration: {stderr}")
            else:
                print(f"❌ Error creating initial migration: {stderr}")
        else:
            print(f"❌ Error reinitializing: {stderr}")
            
    except Exception as e:
        print(f"❌ Reset error: {e}")

def fix_migration_conflicts():
    """Fix migration conflicts by merging heads"""
    print("🔧 Fixing Migration Conflicts...")
    print("=" * 50)
    
    try:
        # Check for multiple heads
        success, stdout, stderr = run_command("flask db heads")
        if success:
            heads = [line.strip() for line in stdout.split('\n') if line.strip()]
            if len(heads) > 1:
                print(f"Found {len(heads)} migration heads - merging...")
                
                # Merge heads
                success, stdout, stderr = run_command('flask db merge -m "Merge migration heads"')
                if success:
                    print("✅ Migration heads merged successfully!")
                    print("Now apply the merge migration:")
                    print("flask db upgrade")
                else:
                    print(f"❌ Error merging heads: {stderr}")
            else:
                print("✅ No migration conflicts found")
        else:
            print(f"❌ Error checking heads: {stderr}")
            
    except Exception as e:
        print(f"❌ Error fixing conflicts: {e}")

def show_migration_menu():
    """Show the main migration management menu"""
    while True:
        print("\n" + "=" * 60)
        print("🗄️  EXCELLENCE TUTORIAL - MIGRATION MANAGER")
        print("=" * 60)
        print("1. 🔍 Check Migration Status")
        print("2. 🚀 Apply Pending Migrations")
        print("3. 📝 Create New Migration")
        print("4. ⏪ Rollback Last Migration")
        print("5. 📦 Backup Database")
        print("6. 🔧 Fix Migration Conflicts")
        print("7. 🚨 Reset Migration System (DEV ONLY)")
        print("8. 🚪 Exit")
        print("=" * 60)
        
        choice = input("Select an option (1-8): ").strip()
        
        if choice == '1':
            check_migration_status()
        elif choice == '2':
            apply_migrations()
        elif choice == '3':
            create_migration()
        elif choice == '4':
            rollback_migration()
        elif choice == '5':
            backup_database()
        elif choice == '6':
            fix_migration_conflicts()
        elif choice == '7':
            reset_migrations()
        elif choice == '8':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    show_migration_menu()