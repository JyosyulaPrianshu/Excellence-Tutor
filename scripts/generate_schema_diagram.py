#!/usr/bin/env python3
"""
Script to generate a visual database schema diagram from the current models
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import MetaData

def generate_schema_info():
    """Generate detailed schema information"""
    print("🗄️ Excellence Tutorial - Database Schema Generator")
    print("=" * 60)
    
    app = create_app()
    with app.app_context():
        try:
            # Get database metadata
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"📊 Database: {db.engine.url.drivername}")
            print(f"📋 Total Tables: {len(tables)}")
            print()
            
            # Generate detailed table information
            for table_name in sorted(tables):
                if table_name == 'alembic_version':
                    continue
                    
                print(f"📄 Table: {table_name.upper()}")
                print("-" * 40)
                
                # Get columns
                columns = inspector.get_columns(table_name)
                for col in columns:
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    default = f" DEFAULT {col['default']}" if col['default'] else ""
                    print(f"  • {col['name']:<25} {col['type']:<15} {nullable}{default}")
                
                # Get foreign keys
                foreign_keys = inspector.get_foreign_keys(table_name)
                if foreign_keys:
                    print("  Foreign Keys:")
                    for fk in foreign_keys:
                        print(f"    → {fk['constrained_columns'][0]} → {fk['referred_table']}.{fk['referred_columns'][0]}")
                
                # Get indexes
                indexes = inspector.get_indexes(table_name)
                if indexes:
                    print("  Indexes:")
                    for idx in indexes:
                        unique = "UNIQUE " if idx['unique'] else ""
                        print(f"    • {unique}{idx['name']}: {', '.join(idx['column_names'])}")
                
                print()
            
            # Generate relationship summary
            print("🔗 RELATIONSHIPS SUMMARY")
            print("=" * 40)
            
            relationships = [
                ("users", "profiles", "1:1", "User authentication ↔ Student profile"),
                ("users", "marks", "1:N", "Student ↔ Test marks"),
                ("users", "fees", "1:N", "Student ↔ Monthly fees"),
                ("users", "payments", "1:N", "Student ↔ Payment records"),
                ("users", "notifications", "1:N", "Student ↔ Personal notifications"),
                ("users", "dropout_requests", "1:N", "Student ↔ Dropout requests"),
                ("tests", "marks", "1:N", "Test ↔ Student marks"),
                ("fees", "payments", "1:N", "Fee ↔ Payment attempts"),
            ]
            
            for table1, table2, rel_type, description in relationships:
                print(f"  {table1:<15} {rel_type:<5} {table2:<15} | {description}")
            
            # Generate class-based content summary
            print("\n📚 CLASS-BASED CONTENT SYSTEM")
            print("=" * 40)
            
            class_tables = ["pdfs", "tests", "notifications", "resources"]
            for table in class_tables:
                if table in tables:
                    print(f"  • {table:<15} | Supports class filtering via 'class_for' field")
            
            print("\n🎯 SUPPORTED CLASSES:")
            classes = [
                "6", "7", "8", "9", "10",
                "11_arts", "11_science", "12_arts", "12_science", "all"
            ]
            for cls in classes:
                print(f"    - {cls}")
            
        except Exception as e:
            print(f"❌ Error generating schema info: {e}")

def generate_migration_summary():
    """Generate a summary of all migrations"""
    print("\n📜 MIGRATION HISTORY SUMMARY")
    print("=" * 60)
    
    migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'migrations', 'versions')
    
    if not os.path.exists(migrations_dir):
        print("❌ Migrations directory not found")
        return
    
    migration_files = [f for f in os.listdir(migrations_dir) if f.endswith('.py')]
    migration_files.sort()
    
    print(f"📊 Total Migration Files: {len(migration_files)}")
    print()
    
    for i, migration_file in enumerate(migration_files, 1):
        # Extract migration info from filename
        parts = migration_file.replace('.py', '').split('_', 1)
        if len(parts) >= 2:
            revision = parts[0]
            description = parts[1].replace('_', ' ').title()
        else:
            revision = migration_file
            description = "Unknown"
        
        print(f"{i:2d}. {revision:<15} | {description}")

if __name__ == "__main__":
    generate_schema_info()
    generate_migration_summary()
    
    print("\n" + "=" * 60)
    print("🎉 Schema analysis complete!")
    print("\n💡 To visualize relationships, consider using:")
    print("   • DB Browser for SQLite (for local development)")
    print("   • pgAdmin (for PostgreSQL)")
    print("   • Online ERD tools like dbdiagram.io")