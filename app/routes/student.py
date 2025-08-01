from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Profile, PDF, Notification, Test, Mark, Fee, Payment, Setting, Resource, DropoutRequest
from app.forms import StudentSignupForm, LoginForm, StudentTestUpdateForm, PasswordResetRequestForm, PasswordResetForm
from app import db, login_manager
from datetime import datetime, timedelta
from flask_wtf.csrf import generate_csrf
from app.utils import generate_password_reset_token, verify_password_reset_token, send_password_reset_email, get_leaderboard_for_class

student_bp = Blueprint('student', __name__)

@student_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = StudentSignupForm()
    if form.validate_on_submit():
        # Prevent students from selecting 'all' as their class
        if form.student_class.data == 'all':
            flash('You must select a specific class. "All Students" is not allowed.', 'danger')
            return render_template('shared/signup.html', form=form)
        # Check if email already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return render_template('shared/signup.html', form=form)
        # Create user
        hashed_pw = generate_password_hash(form.password.data)
        user = User(email=form.email.data, password=hashed_pw, is_admin=False)
        db.session.add(user)
        db.session.commit()
        # Assign roll_number as next available (max + 1)
        max_roll = db.session.query(db.func.max(Profile.roll_number)).scalar()
        next_roll = 1 if max_roll is None else max_roll + 1
        # Create profile
        profile = Profile(
            user_id=user.id,
            full_name=form.full_name.data,
            parent_name=form.parent_name.data,
            parent_phone=form.parent_phone.data,
            student_phone=form.student_phone.data,
            student_class=form.student_class.data,
            school_name=form.school_name.data,
            roll_number=next_roll
        )
        db.session.add(profile)
        db.session.commit()
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('student.login'))
    return render_template('shared/signup.html', form=form)

@student_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, is_admin=False).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('student.home'))
        flash('Invalid credentials.', 'danger')
    return render_template('shared/login.html', form=form, role='student')

@student_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('student.login'))

@student_bp.route('/home')
@login_required
def home():
    if current_user.is_admin:
        return redirect(url_for('admin.home1'))
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    # Show pending popup if set
    if profile and profile.pending_popup:
        flash(profile.pending_popup, 'warning')
        profile.pending_popup = None
        db.session.commit()
    
    # Build a queue of unseen notifications (class or personal)
    unseen_notifications = Notification.query.filter(
        ((Notification.user_id == None) & ((Notification.class_for == 'all') | (Notification.class_for == profile.student_class))) |
        (Notification.user_id == current_user.id),
        Notification.seen == False
    ).order_by(Notification.created_at.asc()).all()

    banner_notification = None
    if unseen_notifications:
        # Show the oldest unseen notification
        oldest_note = unseen_notifications[0]
        banner_notification = oldest_note.message
        oldest_note.seen = True
        db.session.commit()

    # Check for new learning resource notification
    resource_notification = Notification.query.filter(
        Notification.user_id == None,
        Notification.message == 'New learning resource is available now'
    ).order_by(Notification.created_at.desc()).first()
    
    return render_template('student/home.html', admin_notification=banner_notification, profile=profile, resource_notification=resource_notification)

@student_bp.route('/profile')
@login_required
def profile():
    try:
        profile = Profile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Profile not found.', 'danger')
            return redirect(url_for('student.home'))
        
        # Get all marks for this student
        marks = Mark.query.filter_by(user_id=current_user.id).join(Test).order_by(Test.date.desc()).all()
        
        # Get optimized leaderboard
        leaderboard = get_leaderboard_for_class(profile.student_class)

        # Popup logic for new PDFs (flash only, do not store in Notification table)
        latest_pdf = PDF.query.order_by(PDF.id.desc()).first()
        if latest_pdf and (not profile.last_seen_pdf_id or latest_pdf.id > profile.last_seen_pdf_id):
            flash(f'New PDF sent! <a href="{url_for("student.pdfs")}" class="underline">Open it</a>', 'info')
            profile.last_seen_pdf_id = latest_pdf.id
            db.session.commit()
        
        # Popup logic for new Tests (flash only, do not store in Notification table)
        latest_test = Test.query.order_by(Test.id.desc()).first()
        if latest_test and (not profile.last_seen_test_id or latest_test.id > profile.last_seen_test_id):
            flash(f'New test update required! <a href="{url_for("student.test_update")}" class="underline">Open it</a>', 'info')
            profile.last_seen_test_id = latest_test.id
            db.session.commit()
        
        # Only show admin/important notifications in the notification bar (from Notification table)
        # Do not flash them here; they will be shown in the notification bar/page
        if not profile.last_seen_notification_id:
            profile.last_seen_notification_id = 0
            db.session.commit()

        return render_template('student/profile.html', profile=profile, marks=marks, leaderboard=leaderboard)
        
    except Exception as e:
        db.session.rollback()
        flash('Error loading profile. Please try again.', 'danger')
        current_app.logger.error(f'Profile error: {str(e)}')
        return redirect(url_for('student.home'))

@student_bp.route('/notifications')
@login_required
def notifications():
    cutoff = datetime.now() - timedelta(days=15)
    # Delete old notifications
    Notification.query.filter(Notification.created_at < cutoff).delete(synchronize_session=False)
    db.session.commit()
    notif_type = request.args.get('type', 'class')
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if notif_type == 'my':
        notifications = Notification.query.filter(Notification.user_id == current_user.id, Notification.created_at >= cutoff).order_by(Notification.created_at.desc()).all()
    else:
        notifications = Notification.query.filter(
            Notification.user_id == None,
            (Notification.class_for == 'all') | (Notification.class_for == profile.student_class),
            Notification.created_at >= cutoff
        ).order_by(Notification.created_at.desc()).all()
    # Show all messages, seen and unseen, newest 10 as cards, rest as table
    return render_template('student/notifications.html', notifications=notifications, notif_type=notif_type)

@student_bp.route('/pdfs')
@login_required
def pdfs():
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    pdfs = PDF.query.filter((PDF.class_for == 'all') | (PDF.class_for == profile.student_class)).order_by(PDF.uploaded_at.desc()).all()
    return render_template('student/pdfs.html', pdfs=pdfs)

@student_bp.route('/fee', methods=['GET', 'POST'])
@login_required
def fee():
    # Get all fees for the student
    all_fees = Fee.query.filter_by(user_id=current_user.id).order_by(Fee.month.desc()).all()
    outstanding_fees = [fee for fee in all_fees if not fee.is_paid]
    paid_fees = [fee for fee in all_fees if fee.is_paid]
    
    # Calculate total due
    total_due = sum(fee.amount_due for fee in outstanding_fees)
    
    # Get payment history
    payments = Payment.query.filter_by(user_id=current_user.id).join(Fee).order_by(Payment.requested_at.desc()).all()
    
    return render_template('student/fee.html', 
                         all_fees=all_fees,
                         outstanding_fees=outstanding_fees,
                         paid_fees=paid_fees,
                         total_due=total_due,
                         payments=payments)

@student_bp.route('/cash_payment/<int:fee_id>', methods=['GET', 'POST'])
@login_required
def cash_payment(fee_id):
    fee = Fee.query.get_or_404(fee_id)
    
    # Ensure the fee belongs to the current user
    if fee.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('student.fee'))
    
    if request.method == 'POST':
        # Create cash payment request
        payment = Payment(
            user_id=current_user.id,
            fee_id=fee_id,
            method='Cash',
            is_confirmed=False
        )
        db.session.add(payment)
        db.session.commit()
        
        flash('Cash payment request submitted successfully! Please pay the amount to your teacher.', 'success')
        return redirect(url_for('student.fee'))
    
    # Get approved and pending cash payments for this student
    approved_cash_payments = Payment.query.filter_by(
        user_id=current_user.id, 
        method='Cash', 
        is_confirmed=True
    ).join(Fee).order_by(Payment.confirmed_at.desc()).all()
    
    pending_cash_payments = Payment.query.filter_by(
        user_id=current_user.id, 
        method='Cash', 
        is_confirmed=False
    ).join(Fee).order_by(Payment.requested_at.desc()).all()
    
    return render_template('student/cash.html',
                         fee=fee,
                         approved_cash_payments=approved_cash_payments,
                         pending_cash_payments=pending_cash_payments)

@student_bp.route('/upi_payment/<int:fee_id>', methods=['GET', 'POST'])
@login_required
def upi_payment(fee_id):
    fee = Fee.query.get_or_404(fee_id)
    # Ensure the fee belongs to the current user
    if fee.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('student.fee'))
    # Fetch UPI ID and phone number from settings
    upi_setting = Setting.query.filter_by(key='upi_id').first()
    upi_id = upi_setting.value if upi_setting else 'excellence@paytm'
    phone_setting = Setting.query.filter_by(key='upi_phone').first()
    phone_number = phone_setting.value if phone_setting else ''
    if request.method == 'POST':
        # Get the UPI reference number from form
        upi_reference = request.form.get('upi_reference', '').strip()
        if not upi_reference:
            flash('Please provide the UPI reference number.', 'danger')
            return redirect(url_for('student.upi_payment', fee_id=fee_id))
        # Create UPI payment request (requires admin approval)
        payment = Payment(
            user_id=current_user.id,
            fee_id=fee_id,
            method='UPI',
            reference=upi_reference,
            is_confirmed=False
        )
        db.session.add(payment)
        db.session.commit()
        flash('UPI payment request submitted successfully! Admin will verify and approve your payment.', 'success')
        return redirect(url_for('student.fee'))
    # Get approved and pending UPI payments for this student
    approved_upi_payments = Payment.query.filter_by(
        user_id=current_user.id, 
        method='UPI', 
        is_confirmed=True
    ).join(Fee).order_by(Payment.confirmed_at.desc()).all()
    pending_upi_payments = Payment.query.filter_by(
        user_id=current_user.id, 
        method='UPI', 
        is_confirmed=False
    ).join(Fee).order_by(Payment.requested_at.desc()).all()
    return render_template('student/upi.html',
                         fee=fee,
                         upi_payments=approved_upi_payments,
                         pending_upi_payments=pending_upi_payments,
                         upi_id=upi_id,
                         phone_number=phone_number)

@student_bp.route('/test_update', methods=['GET', 'POST'])
@login_required
def test_update():
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    # Get all tests for the student's class or all
    tests = Test.query.filter((Test.class_for == 'all') | (Test.class_for == profile.student_class)).order_by(Test.date.desc()).all()
    # Get test IDs for which this student already has marks
    marked_test_ids = [m.test_id for m in Mark.query.filter_by(user_id=current_user.id).all()]
    # Only allow updating marks for tests not already marked
    available_tests = [(t.id, f"{t.date.strftime('%d-%m-%Y')} - {t.name} (Total: {t.total_marks})") for t in tests if t.id not in marked_test_ids]
    form = StudentTestUpdateForm()
    form.test_id.choices = available_tests
    
    if form.validate_on_submit():
        try:
            # Server-side validation for additional security
            test = Test.query.get(form.test_id.data)
            if not test or (test.class_for != 'all' and test.class_for != profile.student_class):
                flash('Invalid test selected.', 'danger')
                return redirect(url_for('student.test_update'))
            
            marks_obtained = form.marks_obtained.data
            
            # Additional server-side validation
            if marks_obtained < 0:
                flash('Marks cannot be negative.', 'danger')
                return redirect(url_for('student.test_update'))
            
            if marks_obtained > test.total_marks:
                flash(f'Marks obtained ({marks_obtained}) cannot exceed test total ({test.total_marks}).', 'danger')
                # Log suspicious activity
                current_app.logger.warning(f'SUSPICIOUS ACTIVITY: Student {current_user.id} ({current_user.email}) attempted to submit marks {marks_obtained}/{test.total_marks} for test {test.id}')
                return redirect(url_for('student.test_update'))
            
            if marks_obtained > 100:
                flash('Marks cannot exceed 100.', 'danger')
                current_app.logger.warning(f'SUSPICIOUS ACTIVITY: Student {current_user.id} ({current_user.email}) attempted to submit marks {marks_obtained} (exceeds 100) for test {test.id}')
                return redirect(url_for('student.test_update'))
            
            # Check for suspicious patterns (e.g., perfect scores multiple times)
            student_marks = Mark.query.filter_by(user_id=current_user.id).all()
            perfect_scores = [m for m in student_marks if m.marks_obtained == m.test.total_marks]
            
            if marks_obtained == test.total_marks and len(perfect_scores) >= 3:
                current_app.logger.warning(f'SUSPICIOUS PATTERN: Student {current_user.id} ({current_user.email}) has {len(perfect_scores) + 1} perfect scores')
            
            # Create the mark record
            mark = Mark(
                user_id=current_user.id, 
                test_id=form.test_id.data, 
                marks_obtained=marks_obtained
            )
            db.session.add(mark)
            db.session.commit()
            
            # Log successful submission
            current_app.logger.info(f'Mark submitted: Student {current_user.id} ({current_user.email}) submitted {marks_obtained}/{test.total_marks} for test {test.id} ({test.name})')
            
            flash(f'Marks updated successfully! You scored {marks_obtained} out of {test.total_marks}.', 'success')
            return redirect(url_for('student.test_update'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error in test_update: {str(e)}')
            flash('An error occurred while updating marks. Please try again.', 'danger')
            return redirect(url_for('student.test_update'))
    
    # Show all marks for this student (only for their class/all)
    marks = Mark.query.filter_by(user_id=current_user.id).join(Test).filter((Test.class_for == 'all') | (Test.class_for == profile.student_class)).order_by(Test.date.desc()).all()
    return render_template('student/test_update.html', form=form, marks=marks)

@student_bp.route("/test")
def test_student():
    return "Student blueprint is working!"

@student_bp.route('/test_csrf', methods=['GET', 'POST'])
@login_required
def test_csrf():
    """Test route to verify CSRF token generation"""
    if request.method == 'POST':
        test_input = request.form.get('test_input', 'No input')
        return f"CSRF Test Successful! Input: {test_input}"
    else:
        return render_template('student/test_form.html')

@student_bp.route('/class_notifications')
@login_required
def class_notifications():
    notifications = Notification.query.filter(Notification.user_id == None).order_by(Notification.created_at.desc()).all()
    return render_template('student/classnotific.html', notifications=notifications)

@student_bp.route('/my_notifications')
@login_required
def my_notifications():
    notifications = Notification.query.filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('student/mynotifications.html', notifications=notifications)

@student_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, is_admin=False).first()
        if user:
            token = generate_password_reset_token(user.email)
            send_password_reset_email(user, token)
        flash('If your email is registered, you will receive a password reset link.', 'info')
        return redirect(url_for('student.login'))
    return render_template('student/forgot_password.html', form=form)

@student_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_password_reset_token(token)
    if not email:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('student.forgot_password'))
    user = User.query.filter_by(email=email, is_admin=False).first()
    if not user:
        flash('Invalid user.', 'danger')
        return redirect(url_for('student.forgot_password'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        from werkzeug.security import generate_password_hash
        user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('student.login'))
    return render_template('student/reset_password.html', form=form)

@student_bp.route('/qr')
def qr():
    from app.models import Setting
    qr_setting = Setting.query.filter_by(key='upi_qr').first()
    qr_url = url_for('static', filename=qr_setting.value) if qr_setting else None
    return render_template('student/qr.html', qr_url=qr_url)

@student_bp.route('/resources')
@login_required
def resources():
    try:
        profile = Profile.query.filter_by(user_id=current_user.id).first()
        resources = Resource.query.filter((Resource.class_for == 'all') | (Resource.class_for == profile.student_class)).order_by(Resource.created_at.desc()).all()
        return render_template('student/resourcestudent.html', resources=resources)
    except Exception as e:
        flash('Error loading resources. Please try again.', 'danger')
        current_app.logger.error(f'Resources error: {str(e)}')
        return render_template('student/resourcestudent.html', resources=[]) 

@student_bp.route('/drop_request', methods=['GET', 'POST'])
@login_required
def drop_request():
    if current_user.is_admin:
        return redirect(url_for('admin.home1'))
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    dues = Fee.query.filter_by(user_id=current_user.id, is_paid=False).all()
    total_due = sum(fee.amount_due for fee in dues)
    existing_request = DropoutRequest.query.filter_by(user_id=current_user.id, status='pending').first()
    if request.method == 'POST':
        if total_due > 0:
            flash('You must clear all dues before requesting to quit.', 'danger')
            return redirect(url_for('student.drop_request'))
        if existing_request:
            flash('You have already submitted a dropout request. Please wait for admin approval.', 'warning')
            return redirect(url_for('student.drop_request'))
        # Create dropout request
        dropout = DropoutRequest(user_id=current_user.id)
        db.session.add(dropout)
        db.session.commit()
        flash('Your dropout request has been submitted for admin approval.', 'success')
        return redirect(url_for('student.home'))
    return render_template('student/drop_page.html', profile=profile, dues=dues, total_due=total_due, existing_request=existing_request) 