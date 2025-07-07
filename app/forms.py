from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from flask_wtf.file import FileField, FileAllowed
from wtforms import TextAreaField
from wtforms.fields import DateField, IntegerField, SelectField
from app.models import Test
from datetime import datetime
from calendar import month_name
from app.utils import get_current_time_ist

class_choices = [
    ('all', 'All Students'),
    ('6', 'Class 6'),
    ('7', 'Class 7'),
    ('8', 'Class 8'),
    ('9', 'Class 9'),
    ('10', 'Class 10'),
    ('11_arts', 'Class 11 Arts'),
    ('11_science', 'Class 11 Science'),
    ('12_arts', 'Class 12 Arts'),
    ('12_science', 'Class 12 Science'),
]

class StudentSignupForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    parent_name = StringField('Parent Name', validators=[DataRequired()])
    parent_phone = StringField('Parent Phone', validators=[DataRequired(), Length(min=10, max=15)])
    student_phone = StringField('Student Phone', validators=[DataRequired(), Length(min=10, max=15)])
    student_class = SelectField('Class', choices=class_choices, validators=[DataRequired()])
    school_name = StringField('School Name', validators=[DataRequired()])
    profile_pic = FileField('Profile Picture (optional)', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class AdminPDFUploadForm(FlaskForm):
    title = StringField('PDF Title', validators=[DataRequired(), Length(max=25)])
    pdf_file = FileField('PDF File', validators=[DataRequired(), FileAllowed(['pdf'], 'PDFs only!')])
    class_for = SelectField('Class', choices=class_choices, validators=[DataRequired()])
    pin = PasswordField('Upload PIN', validators=[DataRequired(), Length(min=4, max=32)])
    submit = SubmitField('Upload PDF')

class AdminNotificationForm(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=150)])
    class_for = SelectField('Class', choices=[
        ('all', 'All Students'),
        ('6', 'Class 6'),
        ('7', 'Class 7'),
        ('8', 'Class 8'),
        ('9', 'Class 9'),
        ('10', 'Class 10'),
        ('11_arts', 'Class 11 Arts'),
        ('11_science', 'Class 11 Science'),
        ('12_arts', 'Class 12 Arts'),
        ('12_science', 'Class 12 Science')
    ], default='all')
    submit = SubmitField('Send Notification')

class AdminTestUploadForm(FlaskForm):
    date = DateField('Test Date', format='%Y-%m-%d', validators=[DataRequired()])
    name = StringField('Test Name', validators=[DataRequired(), Length(max=25)])
    question_paper = FileField('Question Paper (PDF, optional)', validators=[FileAllowed(['pdf'], 'PDFs only!')])
    total_marks = IntegerField('Total Marks', validators=[DataRequired(), NumberRange(min=1, max=100, message='Total marks must be between 1 and 100')])
    class_for = SelectField('Class', choices=class_choices, validators=[DataRequired()])
    submit = SubmitField('Create Test')
    
    def validate_date(self, field):
        """Custom validator to ensure test date is in current or previous month (and not in the future)"""
        if field.data:
            current_date = datetime.now()
            test_date = field.data
            # Allow current month and previous month (same year or previous year if January)
            current_month = current_date.month
            current_year = current_date.year
            prev_month = current_month - 1 if current_month > 1 else 12
            prev_year = current_year if current_month > 1 else current_year - 1
            # Check if test date is in current or previous month
            if not ((test_date.year == current_year and test_date.month == current_month) or (test_date.year == prev_year and test_date.month == prev_month)):
                current_month_name = current_date.strftime('%B')
                prev_month_name = month_name[prev_month]
                raise ValidationError(f'Test date must be in {current_month_name} {current_year} or {prev_month_name} {prev_year}.')
            # Check if test date is not in the future
            if test_date > current_date.date():
                raise ValidationError('Test date cannot be in the future.')
            
            # Check if test date is not too far in the past (within last 30 days)
            from datetime import timedelta
            thirty_days_ago = current_date.date() - timedelta(days=30)
            if test_date < thirty_days_ago:
                raise ValidationError('Test date cannot be more than 30 days in the past.')

class StudentTestUpdateForm(FlaskForm):
    test_id = SelectField('Test', coerce=int, validators=[DataRequired()])
    marks_obtained = IntegerField('Marks Obtained', validators=[
        DataRequired(), 
        NumberRange(min=0, message='Marks cannot be negative')
    ])
    submit = SubmitField('Update Marks')
    
    def validate_marks_obtained(self, field):
        """Custom validator to ensure marks don't exceed test total"""
        if self.test_id.data:
            test = Test.query.get(self.test_id.data)
            if test and field.data > test.total_marks:
                raise ValidationError(f'Marks obtained cannot exceed the test total of {test.total_marks}')
            if field.data < 0:
                raise ValidationError('Marks cannot be negative')
            if field.data > 100:
                raise ValidationError('Marks cannot exceed 100')

class StudentFeeForm(FlaskForm):
    method = SelectField('Payment Method', choices=[('UPI', 'UPI'), ('Cash', 'Cash')], validators=[DataRequired()])
    submit = SubmitField('Pay/Request Approval')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class AddAdminUserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Add Admin User')

class UPISettingsForm(FlaskForm):
    upi_id = StringField('UPI ID', validators=[DataRequired()])
    phone_number = StringField('Phone Number (optional)')
    submit = SubmitField('Update UPI Settings')

class ResourceForm(FlaskForm):
    name = StringField('Resource Name', validators=[DataRequired(), Length(max=25)])
    link = StringField('Resource Link', validators=[DataRequired(), Length(max=500)])
    description = TextAreaField('Description (Optional)', validators=[Length(max=1000)])
    class_for = SelectField('Class', choices=class_choices, validators=[DataRequired()])
    submit = SubmitField('Add Resource') 