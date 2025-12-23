from datetime import datetime, date
from app.models import Fee, Notification, Profile, User, Setting, Mark, PDF
from app import db, socketio
from flask import url_for
import pytz
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from flask_mail import Message
import os
import hashlib
from werkzeug.utils import secure_filename
import re

def get_current_time_ist():
    """Get current time in Indian Standard Time (IST)"""
    india_tz = pytz.timezone('Asia/Kolkata')
    return datetime.now(india_tz)

def get_fee_amount_for_class(student_class):
    """Return the monthly fee amount for the given class/stream key."""
    if student_class in ['6', '7']:
        return 400
    elif student_class in ['8', '9', '10']:
        return 500
    elif student_class in ['11_science', '12_science']:
        return 400
    elif student_class in ['11_arts', '12_arts']:
        return 700
    else:
        return 0  # fallback

def check_monthly_fee_notifications():
    """Check if it's the 1st of the month and send fee notifications"""
    # Use IST for date calculations
    india_tz = pytz.timezone('Asia/Kolkata')
    today = datetime.now(india_tz).date()
    
    # Check if it's the 1st of the month
    if today.day == 1:
        current_month = today.strftime('%B %Y')  # e.g., "July 2025"
        
        # Get all students
        students = Profile.query.all()
        
        for student in students:
            # Check if fee notification already sent for this month
            existing_notification = Notification.query.filter_by(
                user_id=student.user_id,
                message=f"Fee due for {current_month}"
            ).first()
            
            if not existing_notification:
                # Create fee notification
                notification = Notification(
                    user_id=student.user_id,
                    message=f"Fee due for {current_month}"
                )
                db.session.add(notification)
                
                # Send real-time popup notification
                socketio.emit('fee_notification', {
                    'message': f'Fee due for {current_month}',
                    'url': url_for('student.fee'),
                    'button': 'Pay Now'
                }, room=f'student_{student.user_id}')
        
        db.session.commit()

def get_fee_status_for_student(user_id):
    """Get fee status for a specific student"""
    fees = Fee.query.filter_by(user_id=user_id).order_by(Fee.month.desc()).all()
    
    outstanding_fees = [fee for fee in fees if not fee.is_paid]
    paid_fees = [fee for fee in fees if fee.is_paid]
    total_due = sum(fee.amount_due for fee in outstanding_fees)
    
    return {
        'outstanding_fees': outstanding_fees,
        'paid_fees': paid_fees,
        'total_due': total_due,
        'total_fees': len(fees)
    }

def get_pending_approvals_count():
    """Get count of pending payment approvals (both Cash and UPI)"""
    from app.models import Payment
    return Payment.query.filter_by(is_confirmed=False).count()

def assign_monthly_dues():
    """
    Assign monthly dues for all students for the current month.
    This function is called manually by the admin when they click the "Assign Monthly Dues" button.
    Dues are assigned based on the current date/time when the button is clicked.
    Also sends notifications to all students about the new dues.
    
    Month-based amount locking: Each month gets locked to the amount that was set when
    dues were first assigned for that month. New students joining that month get the same amount.
    """
    now = get_current_time_ist()
    current_month_label = now.strftime('%B %Y')
    
    # Check if dues already exist for this month to determine the locked amount
    existing_dues = Fee.query.filter_by(month=current_month_label).first()
    
    if existing_dues:
        # Month already has dues - use the locked amount from existing dues
        locked_amount = existing_dues.amount_due
        current_app.logger.info(f'Using locked amount for {current_month_label}: ₹{locked_amount}')
    else:
        # New month - get amount from UPI settings and lock it for this month
        monthly_due_setting = Setting.query.filter_by(key='monthly_due_amount').first()
        try:
            locked_amount = int(monthly_due_setting.value) if monthly_due_setting and monthly_due_setting.value.isdigit() else 1500
        except Exception:
            locked_amount = 1500
        current_app.logger.info(f'Setting locked amount for {current_month_label}: ₹{locked_amount}')
    
    # Get all non-admin users
    users = User.query.filter_by(is_admin=False).all()
    total_new_dues = 0
    
    for user in users:
        # Check if due already exists for this month
        existing_due = Fee.query.filter_by(user_id=user.id, month=current_month_label).first()
        
        if not existing_due:
            # Create due for current month with the locked amount
            fee = Fee(user_id=user.id, month=current_month_label, amount_due=locked_amount, is_paid=False)
            db.session.add(fee)
            total_new_dues += 1
    
    if total_new_dues > 0:
        # Send notifications to all students about the new dues
        notification_message = f"{current_month_label} month due added - ₹{locked_amount}. Please pay your dues on time."
        
        for user in users:
            # Create notification for each student
            notification = Notification(
                user_id=user.id,
                message=notification_message
            )
            db.session.add(notification)
            
            # Send real-time notification via SocketIO
            try:
                socketio.emit('fee_notification', {
                    'message': notification_message,
                    'url': url_for('student.fee'),
                    'button': 'View Dues'
                }, room=f'student_{user.id}')
            except Exception as e:
                current_app.logger.error(f'Error sending real-time notification to student {user.id}: {str(e)}')
        
        db.session.commit()
        current_app.logger.info(f'Assigned {total_new_dues} new monthly dues for {current_month_label} at locked amount ₹{locked_amount} and sent notifications to {len(users)} students')
    
    return total_new_dues

# Token helpers

def generate_password_reset_token(user_email, expires_sec=3600):
    s = URLSafeTimedSerializer(os.environ.get('SECRET_KEY', 'devkey'))
    return s.dumps(user_email, salt='password-reset-salt')

def verify_password_reset_token(token, max_age=3600):
    s = URLSafeTimedSerializer(os.environ.get('SECRET_KEY', 'devkey'))
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=max_age)
    except Exception:
        return None
    return email

# Email helper

def send_password_reset_email(user, token, is_admin=False):
    from flask import current_app, url_for
    from flask_mail import Message
    from app import mail
    
    try:
        # Ensure we have an application context
        with current_app.app_context():
            if is_admin:
                reset_url = url_for('admin.reset_password', token=token, _external=True)
            else:
                reset_url = url_for('student.reset_password', token=token, _external=True)
            
            # Debug log the email configuration
            current_app.logger.debug('Sending password reset email...')
            current_app.logger.debug(f'MAIL_SERVER: {current_app.config.get("MAIL_SERVER")}')
            current_app.logger.debug(f'MAIL_PORT: {current_app.config.get("MAIL_PORT")}')
            current_app.logger.debug(f'MAIL_USE_TLS: {current_app.config.get("MAIL_USE_TLS")}')
            current_app.logger.debug(f'MAIL_USERNAME: {current_app.config.get("MAIL_USERNAME")}')
            current_app.logger.debug(f'MAIL_DEFAULT_SENDER: {current_app.config.get("MAIL_DEFAULT_SENDER")}')
            
            # Use the configured email from app.config
            sender_email = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
            if not sender_email:
                current_app.logger.error('Neither MAIL_DEFAULT_SENDER nor MAIL_USERNAME is configured in app.config')
                return False
                
            msg = Message(
                'Password Reset Request',
                sender=sender_email,
                recipients=[user.email]
            )
            msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, simply ignore this email.'''
            
            mail.send(msg)
            current_app.logger.info(f'Password reset email sent to {user.email}')
            return True
            
    except Exception as e:
        current_app.logger.error(f'Error sending password reset email to {user.email if user else "unknown"}: {str(e)}', exc_info=True)
        return False

def validate_pdf_file(file):
    """
    Validate PDF file for security and content
    """
    if not file:
        return False, "No file provided"
    
    # Check file size (max 10MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > 10 * 1024 * 1024:  # 10MB limit
        return False, "File size too large. Maximum size is 10MB."
    
    # Check file extension
    filename = secure_filename(file.filename)
    if not filename.lower().endswith('.pdf'):
        return False, "Only PDF files are allowed."
    
    # Check file content for PDF magic number
    try:
        file_content = file.read(2048)  # Read first 2KB for magic number detection
        file.seek(0)  # Reset file pointer
        
        # Check if it's actually a PDF by magic number
        if not file_content.startswith(b'%PDF'):
            return False, "Invalid PDF file. File content does not match PDF format."
        
        # Additional security: check for suspicious content
        if b'javascript:' in file_content.lower() or b'<script' in file_content.lower():
            return False, "File contains potentially malicious content."
            
    except Exception as e:
        return False, f"Error reading file: {str(e)}"
    
    return True, filename

def generate_secure_filename(original_filename):
    """
    Generate a secure filename with timestamp in IST
    """
    timestamp = get_current_time_ist().strftime('%Y%m%d%H%M%S')
    # Create a hash of the original filename for uniqueness
    filename_hash = hashlib.md5(original_filename.encode()).hexdigest()[:8]
    safe_filename = secure_filename(original_filename)
    name, ext = os.path.splitext(safe_filename)
    return f"{timestamp}_{filename_hash}_{name}{ext}"

def cleanup_old_files(folder_path, max_age_days=30):
    """
    Clean up old files from a folder
    """
    try:
        current_time = datetime.utcnow()
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                age_days = (current_time - file_time).days
                if age_days > max_age_days:
                    os.remove(file_path)
                    print(f"Cleaned up old file: {filename}")
    except Exception as e:
        print(f"Error during file cleanup: {e}")

def sanitize_filename(filename):
    """
    Sanitize filename to prevent path traversal attacks
    """
    # Remove any path separators
    filename = os.path.basename(filename)
    # Remove any non-alphanumeric characters except dots and hyphens
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    # Ensure it doesn't start with a dot
    if filename.startswith('.'):
        filename = 'file_' + filename
    return filename

def get_leaderboard_for_class(student_class):
    """
    Get optimized leaderboard for a specific class
    """
    try:
        # Use a single query with joins and aggregation
        leaderboard_data = db.session.query(
            Profile.full_name,
            Profile.roll_number,
            db.func.coalesce(db.func.sum(Mark.marks_obtained), 0).label('total'),
            db.func.count(Mark.id).label('total_tests')
        ).filter(
            Profile.student_class == student_class
        ).outerjoin(
            Mark, Profile.user_id == Mark.user_id
        ).group_by(
            Profile.id, Profile.full_name, Profile.roll_number
        ).order_by(
            db.func.coalesce(db.func.sum(Mark.marks_obtained), 0).desc()
        ).all()
        
        return [
            {
                'name': row.full_name,
                'roll_number': row.roll_number,
                'total': row.total,
                'total_tests': row.total_tests
            }
            for row in leaderboard_data
        ]
    except Exception as e:
        current_app.logger.error(f'Error calculating leaderboard: {str(e)}')
        return []

def get_student_leaderboard_position(student_class, student_roll_number):
    """
    Get a student's position in the class leaderboard
    """
    try:
        leaderboard = get_leaderboard_for_class(student_class)
        for i, entry in enumerate(leaderboard, 1):
            if entry['roll_number'] == student_roll_number:
                return i, len(leaderboard)
        return None, len(leaderboard)
    except Exception as e:
        current_app.logger.error(f'Error getting student position: {str(e)}')
        return None, 0

def search_students_by_name(search_term, limit=10):
    """
    PostgreSQL full-text search for students by name
    """
    try:
        from sqlalchemy import text
        
        # Use PostgreSQL full-text search
        query = text("""
            SELECT id, full_name, roll_number, student_class 
            FROM profile 
            WHERE to_tsvector('english', full_name) @@ plainto_tsquery('english', :search_term)
            ORDER BY ts_rank(to_tsvector('english', full_name), plainto_tsquery('english', :search_term)) DESC
            LIMIT :limit
        """)
        
        result = db.session.execute(query, {
            'search_term': search_term,
            'limit': limit
        })
        
        return [
            {
                'id': row.id,
                'full_name': row.full_name,
                'roll_number': row.roll_number,
                'student_class': row.student_class
            }
            for row in result
        ]
    except Exception as e:
        current_app.logger.error(f'Search error: {str(e)}')
        # Fallback to simple LIKE search
        return Profile.query.filter(
            Profile.full_name.ilike(f'%{search_term}%')
        ).limit(limit).all()

def search_pdfs_by_title(search_term, limit=10):
    """
    PostgreSQL full-text search for PDFs by title
    """
    try:
        from sqlalchemy import text
        
        # Use PostgreSQL full-text search
        query = text("""
            SELECT id, title, file_path, uploaded_at 
            FROM pdf 
            WHERE to_tsvector('english', title) @@ plainto_tsquery('english', :search_term)
            ORDER BY ts_rank(to_tsvector('english', title), plainto_tsquery('english', :search_term)) DESC, uploaded_at DESC
            LIMIT :limit
        """)
        
        result = db.session.execute(query, {
            'search_term': search_term,
            'limit': limit
        })
        
        return [
            {
                'id': row.id,
                'title': row.title,
                'file_path': row.file_path,
                'uploaded_at': row.uploaded_at
            }
            for row in result
        ]
    except Exception as e:
        current_app.logger.error(f'PDF search error: {str(e)}')
        # Fallback to simple LIKE search
        return PDF.query.filter(
            PDF.title.ilike(f'%{search_term}%')
        ).order_by(PDF.uploaded_at.desc()).limit(limit).all()

def get_database_stats():
    """
    Get PostgreSQL database statistics for monitoring
    """
    try:
        from sqlalchemy import text
        
        stats_query = text("""
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats 
            WHERE schemaname = 'public'
            ORDER BY tablename, attname
        """)
        
        result = db.session.execute(stats_query)
        return [dict(row) for row in result]
    except Exception as e:
        current_app.logger.error(f'Database stats error: {str(e)}')
        return []

def optimize_database():
    """
    Run PostgreSQL maintenance tasks
    """
    try:
        from sqlalchemy import text
        
        # Analyze tables for better query planning
        db.session.execute(text('ANALYZE'))
        db.session.commit()
        
        current_app.logger.info('Database optimization completed')
        return True
    except Exception as e:
        current_app.logger.error(f'Database optimization error: {str(e)}')
        db.session.rollback()
        return False

def upload_pdf_to_cloudinary(file, filename):
    """
    Upload PDF to Cloudinary and return the URL
    """
    try:
        import cloudinary
        import cloudinary.uploader
        
        # Configure Cloudinary
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
        api_key = os.environ.get('CLOUDINARY_API_KEY')
        api_secret = os.environ.get('CLOUDINARY_API_SECRET')
        
        if not all([cloud_name, api_key, api_secret]):
            print("Cloudinary credentials not found in environment variables")
            return None
        
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Reset file pointer to beginning
        file.seek(0)
        
        # Upload file to Cloudinary
        result = cloudinary.uploader.upload(
            file,
            public_id=f"pdfs/{filename}",
            resource_type="raw",
            format="pdf"
        )
        
        print(f"Cloudinary upload successful: {result['secure_url']}")
        return result['secure_url']
        
    except ImportError:
        print("Cloudinary not installed. Install with: pip install cloudinary")
        return None
    except Exception as e:
        print(f"Error uploading to Cloudinary: {e}")
        return None

def get_pdf_download_url(pdf_record):
    """
    Get the download URL for a PDF record
    """
    if hasattr(pdf_record, 'cloudinary_url') and pdf_record.cloudinary_url:
        # Use Cloudinary URL if available
        return pdf_record.cloudinary_url
    else:
        # Fallback to static file URL
        from flask import url_for
        return url_for('static', filename=f'pdfs/{pdf_record.file_path}') 
