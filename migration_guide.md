# Excellence Tutorial - Migration System Guide

## 🗄️ **Current Migration Status**

Your project has a comprehensive migration system with **15 migration files** tracking the evolution of your database schema.

### **Migration Timeline:**

1. **23dd92a121ee** - Initial migration (Base tables)
2. **23166b665816** - Added last_seen fields to Profile
3. **9c8198829c3a** - Added profile_pic column
4. **cf90f20ca95d** - Added reference field to Payment
5. **9f41621ce2a7** - Added pending_popup to Profile
6. **b6a453a2032e** - Added Setting model for configuration
7. **44a57895a877** - Increased password field length to 256
8. **add_performance_indexes** - PostgreSQL performance optimization
9. **237819d345d0** - Merge multiple heads
10. **c9122d5cd95a** - Added last_seen_personal_notification_id
11. **e149e87de828** - Added Resource model
12. **add_class_for_to_resources_pdfs_tests** - Added class filtering
13. **add_class_for_to_notifications** - Added class filtering to notifications
14. **add_seen_to_notifications** - Added seen status
15. **39d040298944** - Made roll_number unique per class
16. **4951720686c8** - Profiles table reset
17. **dba1dc2a20ee** - Added DropoutRequest model
18. **ae4394dbfc65** - Added reg_no to Profile
19. **36e378e0d78d** - Added UPISettingChangeLog (later removed)
20. **ac4625b082f6** - Added cloudinary_url to PDF model

## 🔧 **Migration Management Commands**

### **Check Current Migration Status:**
```bash
flask db current
```

### **View Migration History:**
```bash
flask db history
```

### **Show Pending Migrations:**
```bash
flask db show
```

### **Apply All Pending Migrations:**
```bash
flask db upgrade
```

### **Rollback to Previous Migration:**
```bash
flask db downgrade
```

### **Create New Migration:**
```bash
flask db migrate -m "Description of changes"
```

## 🚀 **Production Migration Strategy**

### **For Render Deployment:**

1. **Automatic Migration on Deploy:**
   ```yaml
   # In render.yaml
   startCommand: flask db upgrade && gunicorn -k eventlet --bind 0.0.0.0:$PORT run:app
   ```

2. **Manual Migration via Render Shell:**
   ```bash
   # Access Render shell and run:
   flask db upgrade
   ```

3. **Check Migration Status:**
   ```bash
   flask db current
   flask db history --verbose
   ```

## 📊 **Database Schema Evolution**

### **Core Tables (Initial Migration):**
- `users` - User authentication and roles
- `profiles` - Student profile information
- `tests` - Test definitions
- `marks` - Student test scores
- `fees` - Monthly fee records
- `payments` - Payment transactions
- `notifications` - System notifications
- `pdfs` - Study material files

### **Enhanced Features Added:**
- **Profile Management**: Profile pictures, popup messages, last seen tracking
- **Payment System**: UPI references, payment methods
- **Class-based Filtering**: Class-specific content delivery
- **Resource Management**: Learning resources with descriptions
- **Audit Trail**: Settings change logs
- **File Storage**: Cloudinary integration for persistent storage
- **Student Lifecycle**: Dropout request management

## 🔍 **Migration Best Practices**

### **1. Always Backup Before Migration:**
```bash
# For PostgreSQL
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

### **2. Test Migrations Locally First:**
```bash
# Create test migration
flask db migrate -m "Test migration"

# Review the generated migration file
# Apply to local database
flask db upgrade

# Test the application
# If issues, rollback
flask db downgrade
```

### **3. Review Generated Migrations:**
Always check the generated migration files in `migrations/versions/` before applying to production.

### **4. Handle Data Migrations:**
For complex data transformations, create custom migration scripts:

```python
# Example: migrations/versions/custom_data_migration.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Schema changes
    op.add_column('profiles', sa.Column('new_field', sa.String(50)))
    
    # Data migration
    connection = op.get_bind()
    connection.execute(
        "UPDATE profiles SET new_field = 'default_value' WHERE new_field IS NULL"
    )

def downgrade():
    op.drop_column('profiles', 'new_field')
```

## 🛠️ **Common Migration Scenarios**

### **1. Adding a New Column:**
```bash
# 1. Modify your model
# 2. Generate migration
flask db migrate -m "Add new column to table"
# 3. Review and apply
flask db upgrade
```

### **2. Modifying Existing Column:**
```bash
# Be careful with data loss!
flask db migrate -m "Modify column type"
# Review the migration carefully
flask db upgrade
```

### **3. Adding Indexes for Performance:**
```python
# In migration file
def upgrade():
    op.create_index('idx_user_email', 'users', ['email'])
    op.create_index('idx_profile_class', 'profiles', ['student_class'])

def downgrade():
    op.drop_index('idx_user_email', 'users')
    op.drop_index('idx_profile_class', 'profiles')
```

## 🚨 **Migration Troubleshooting**

### **1. Migration Conflicts:**
```bash
# If you have conflicting migrations
flask db merge -m "Merge conflicting migrations"
```

### **2. Reset Migration History (DANGEROUS):**
```bash
# Only for development - NEVER in production
rm -rf migrations/
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### **3. Manual Migration Fixes:**
```bash
# Mark migration as applied without running it
flask db stamp head

# Apply specific migration
flask db upgrade <revision_id>
```

## 📋 **Migration Checklist for Production**

### **Before Deployment:**
- [ ] Test migration on local copy of production data
- [ ] Review all migration files for correctness
- [ ] Ensure backup strategy is in place
- [ ] Check for any breaking changes
- [ ] Verify rollback procedures

### **During Deployment:**
- [ ] Put application in maintenance mode (if needed)
- [ ] Create database backup
- [ ] Apply migrations
- [ ] Verify application functionality
- [ ] Monitor for errors

### **After Deployment:**
- [ ] Verify all features work correctly
- [ ] Check database integrity
- [ ] Monitor application logs
- [ ] Confirm rollback plan if needed

## 🔄 **Automated Migration Scripts**

### **Production Migration Script:**
```bash
#!/bin/bash
# production_migrate.sh

echo "🔄 Starting production migration..."

# Backup database
echo "📦 Creating backup..."
pg_dump $DATABASE_URL > "backup_$(date +%Y%m%d_%H%M%S).sql"

# Apply migrations
echo "🚀 Applying migrations..."
flask db upgrade

# Verify
echo "✅ Checking migration status..."
flask db current

echo "🎉 Migration completed!"
```

### **Development Reset Script:**
```bash
#!/bin/bash
# dev_reset.sh

echo "🧹 Resetting development database..."

# Drop and recreate
flask db downgrade base
flask db upgrade

# Seed with test data
python scripts/check_and_create_users.py

echo "✅ Development database reset complete!"
```

## 📈 **Migration Monitoring**

### **Track Migration Performance:**
```python
# Add to migration file for timing
import time

def upgrade():
    start_time = time.time()
    
    # Your migration code here
    op.add_column('table', sa.Column('new_col', sa.String(50)))
    
    end_time = time.time()
    print(f"Migration completed in {end_time - start_time:.2f} seconds")
```

### **Log Migration Events:**
```python
# In your application
import logging

@app.before_first_request
def check_migrations():
    from flask_migrate import current
    revision = current()
    logging.info(f"Current database revision: {revision}")
```

## 🎯 **Next Steps**

1. **Review Current State:**
   ```bash
   flask db current
   flask db history
   ```

2. **Apply Any Pending Migrations:**
   ```bash
   flask db upgrade
   ```

3. **Set Up Automated Backups:**
   - Configure regular database backups
   - Test restore procedures

4. **Monitor Migration Performance:**
   - Track migration execution times
   - Monitor for any issues post-migration

Your migration system is well-structured and production-ready! The comprehensive history shows thoughtful database evolution with proper version control.