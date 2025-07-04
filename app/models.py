from . import db
from flask_login import UserMixin
from datetime import datetime
import pytz

def get_current_time_ist():
    """Get current time in Indian Standard Time (IST)"""
    india_tz = pytz.timezone('Asia/Kolkata')
    return datetime.now(india_tz)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_current_time_ist)
    profile = db.relationship('Profile', backref='user', uselist=False)
    fees = db.relationship('Fee', backref='user', lazy=True)
    payments = db.relationship('Payment', backref='user', lazy=True)

class Profile(db.Model):
    __tablename__ = 'profiles'
    __table_args__ = (db.UniqueConstraint('student_class', 'roll_number', name='unique_roll_per_class'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    full_name = db.Column(db.String(120), nullable=False)
    parent_name = db.Column(db.String(120), nullable=False)
    parent_phone = db.Column(db.String(20), nullable=False)
    student_phone = db.Column(db.String(20), nullable=False)
    student_class = db.Column(db.String(20), nullable=False)
    school_name = db.Column(db.String(120), nullable=False)
    roll_number = db.Column(db.Integer)  # Unique per class
    last_seen_pdf_id = db.Column(db.Integer, default=0)
    last_seen_test_id = db.Column(db.Integer, default=0)
    last_seen_notification_id = db.Column(db.Integer, default=0)
    last_seen_personal_notification_id = db.Column(db.Integer, default=0)
    profile_pic = db.Column(db.String(256))
    pending_popup = db.Column(db.Text)  # One-time popup message for the student

class Test(db.Model):
    __tablename__ = 'tests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    total_marks = db.Column(db.Integer)
    question_paper = db.Column(db.String(256))
    marks = db.relationship('Mark', backref='test', lazy=True)
    class_for = db.Column(db.String(20), nullable=False, default='all')

class Mark(db.Model):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'))
    marks_obtained = db.Column(db.Integer)
    updated_at = db.Column(db.DateTime, default=get_current_time_ist)

class Fee(db.Model):
    __tablename__ = 'fees'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    month = db.Column(db.String(20), nullable=False)
    amount_due = db.Column(db.Integer, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    payments = db.relationship('Payment', backref='fee', lazy=True)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    fee_id = db.Column(db.Integer, db.ForeignKey('fees.id'))
    method = db.Column(db.String(20))  # UPI or Cash
    reference = db.Column(db.String(100))  # UPI reference number
    is_confirmed = db.Column(db.Boolean, default=False)
    requested_at = db.Column(db.DateTime, default=get_current_time_ist)
    confirmed_at = db.Column(db.DateTime)

class PDF(db.Model):
    __tablename__ = 'pdfs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    file_path = db.Column(db.String(256), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=get_current_time_ist)
    class_for = db.Column(db.String(20), nullable=False, default='all')

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # null for all students
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=get_current_time_ist)
    is_read = db.Column(db.Boolean, default=False)
    class_for = db.Column(db.String(20), nullable=True)  # null means all classes
    seen = db.Column(db.Boolean, default=False)  # 0 = not seen, 1 = seen

class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.String(256), nullable=False)
    # For scheduled monthly dues, use key 'monthly_dues_enabled' with value 'true' or 'false' 

class Resource(db.Model):
    __tablename__ = 'resources'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    link = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_current_time_ist)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    class_for = db.Column(db.String(20), nullable=False, default='all') 

class DropoutRequest(db.Model):
    __tablename__ = 'dropout_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    requested_at = db.Column(db.DateTime, default=get_current_time_ist)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    admin_response = db.Column(db.Text)
    processed_at = db.Column(db.DateTime)
    user = db.relationship('User', backref='dropout_requests') 