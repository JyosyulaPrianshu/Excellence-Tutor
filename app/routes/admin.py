from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User, PDF, Notification, Profile, Test, Mark, Fee, Payment, Setting, Resource, DropoutRequest
from app.forms import LoginForm, AdminPDFUploadForm, AdminNotificationForm, AdminTestUploadForm, PasswordResetRequestForm, PasswordResetForm, AddAdminUserForm, UPISettingsForm, ResourceForm
from app import db, socketio
from app.utils import get_pending_approvals_count, generate_password_reset_token, verify_password_reset_token, send_password_reset_email, validate_pdf_file, generate_secure_filename, cleanup_old_files, get_leaderboard_for_class, assign_monthly_dues, get_fee_amount_for_class, get_current_time_ist
import os
from datetime import datetime, date, timedelta
from flask_wtf.csrf import validate_csrf, CSRFError
import pytz

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, is_admin=True).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('admin.home1'))
        flash('Invalid admin credentials.', 'danger')
    return render_template('shared/login.html', form=form, role='admin')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/home1')
@login_required
def home1():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    # Check for pending approvals and show popup
    pending_count = get_pending_approvals_count()
    pending_dropouts = DropoutRequest.query.filter_by(status='pending').all()
    seen_dropout_banners = session.get('seen_dropout_banners', [])
    unseen_dropouts = [d for d in pending_dropouts if d.id not in seen_dropout_banners]
    first_unseen = unseen_dropouts[0] if unseen_dropouts else None
    # Mark as seen after showing
    if first_unseen:
        seen_dropout_banners.append(first_unseen.id)
        session['seen_dropout_banners'] = seen_dropout_banners
    return render_template('admin/home1.html', pending_approvals=pending_count, pending_dropouts=pending_dropouts, first_unseen_dropout=first_unseen)

@admin_bp.route('/upload_pdfs', methods=['GET', 'POST'])
@login_required
def upload_pdfs():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    form = AdminPDFUploadForm()
    if form.validate_on_submit():
        try:
            title = form.title.data
            file = form.pdf_file.data
            class_for = form.class_for.data
            # Validate the file
            is_valid, result = validate_pdf_file(file)
            if not is_valid:
                flash(result, 'danger')
                return redirect(url_for('admin.upload_pdfs'))
            # Generate secure filename
            secure_filename = generate_secure_filename(file.filename)
            
            # Try to upload to Cloudinary first
            cloudinary_url = None
            try:
                from app.utils import upload_pdf_to_cloudinary
                current_app.logger.info(f'Attempting Cloudinary upload for file: {secure_filename}')
                cloudinary_url = upload_pdf_to_cloudinary(file, secure_filename)
                if cloudinary_url:
                    current_app.logger.info(f'Cloudinary upload successful: {cloudinary_url}')
                else:
                    current_app.logger.warning('Cloudinary upload returned None')
            except Exception as e:
                current_app.logger.error(f'Cloudinary upload failed: {e}')
                flash(f'Cloudinary upload failed: {str(e)}', 'warning')
            
            # Save file locally as backup
            pdf_folder = os.path.join(current_app.root_path, 'static', 'pdfs')
            os.makedirs(pdf_folder, exist_ok=True)
            file_path = os.path.join(pdf_folder, secure_filename)
            file.save(file_path)
            
            # Create database record
            pdf = PDF(title=title, file_path=secure_filename, cloudinary_url=cloudinary_url, class_for=class_for)
            db.session.add(pdf)
            db.session.commit()
            # Prepare class label for notification
            class_labels = {
                'all': 'All Students',
                '6': 'Class 6',
                '7': 'Class 7',
                '8': 'Class 8',
                '9': 'Class 9',
                '10': 'Class 10',
                '11_arts': 'Class 11 Arts',
                '11_science': 'Class 11 Science',
                '12_arts': 'Class 12 Arts',
                '12_science': 'Class 12 Science',
            }
            class_label = class_labels.get(class_for, class_for)
            # Store notification in DB (class-specific)
            note = Notification(
                user_id=None,
                message=f'📄 <b>{title}</b> is now available for <b>{class_label}</b>! <a href="{url_for("student.pdfs")}" class="underline">Download from Study Material</a>',
                class_for=class_for
            )
            db.session.add(note)
            db.session.commit()
            flash('PDF uploaded successfully!', 'success')
            socketio.emit('new_pdf', {'message': f'New PDF "{title}" uploaded for {class_label}.', 'url': url_for('student.pdfs'), 'button': 'Open it'})
        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading PDF: {str(e)}', 'danger')
            current_app.logger.error(f'PDF upload error: {str(e)}')
        return redirect(url_for('admin.upload_pdfs'))
    
    # Clean up old files periodically
    try:
        pdf_folder = os.path.join(current_app.root_path, 'static', 'pdfs')
        if os.path.exists(pdf_folder):
            cleanup_old_files(pdf_folder, max_age_days=90)  # Keep files for 90 days
    except Exception as e:
        current_app.logger.error(f'File cleanup error: {str(e)}')
    
    pdfs = PDF.query.order_by(PDF.uploaded_at.desc()).all()
    return render_template('admin/upload_pdfs.html', pdfs=pdfs, form=form)

@admin_bp.route('/notifystudents', methods=['GET', 'POST'])
@login_required
def notifystudents():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    form = AdminNotificationForm()
    if form.validate_on_submit():
        message = form.message.data
        class_for = form.class_for.data
        note = Notification(user_id=None, message=message, class_for=class_for)
        db.session.add(note)
        db.session.commit()
        flash('Notification sent!', 'success')
        socketio.emit('new_notification', {'message': message, 'url': url_for('student.notifications'), 'button': 'See it'})
        return redirect(url_for('admin.notifystudents'))

    # Delete old notifications (older than 15 days)
    cutoff = datetime.now() - timedelta(days=15)
    Notification.query.filter(Notification.created_at < cutoff).delete(synchronize_session=False)
    db.session.commit()

    # Fetch all notifications for display (no 10-message limit)
    notifications = Notification.query.filter(
        Notification.user_id == None,
        Notification.message != None,
        Notification.message != '',
        Notification.created_at >= cutoff
    ).order_by(Notification.created_at.desc()).all()
    return render_template('admin/notifystudents.html', notifications=notifications, form=form)

@admin_bp.route('/studentdetails')
@login_required
def studentdetails():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    # Get selected class from query parameters, default to 'all'
    selected_class = request.args.get('selected_class', 'all')
    
    # Filter students based on selected class
    if selected_class == 'all':
        students = Profile.query.order_by(Profile.roll_number).all()
    else:
        students = Profile.query.filter_by(student_class=selected_class).order_by(Profile.roll_number).all()
    
    return render_template('admin/studentdetails.html', students=students, selected_class=selected_class)

@admin_bp.route('/student/<int:student_id>')
@login_required
def student_profile(student_id):
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    try:
        student = Profile.query.get_or_404(student_id)
        marks = Mark.query.filter_by(user_id=student.user_id).join(Test).order_by(Test.date.desc()).all()
        # Get unpaid fees (dues)
        dues = Fee.query.filter_by(user_id=student.user_id, is_paid=False).all()
        # Get optimized leaderboard for the student's class
        leaderboard = get_leaderboard_for_class(student.student_class)
        return render_template('admin/student_profile.html', student=student, marks=marks, dues=dues, leaderboard=leaderboard)
    except Exception as e:
        flash('Error loading student profile. Please try again.', 'danger')
        current_app.logger.error(f'Student profile error: {str(e)}')
        return redirect(url_for('admin.studentdetails'))

@admin_bp.route('/test_upload', methods=['GET', 'POST'])
@login_required
def test_upload():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    form = AdminTestUploadForm()
    if form.validate_on_submit():
        try:
            date = form.date.data
            name = form.name.data
            total_marks = form.total_marks.data
            question_paper_file = form.question_paper.data
            class_for = form.class_for.data
            question_paper_filename = None
            if question_paper_file and question_paper_file.filename:
                # Validate the file
                is_valid, result = validate_pdf_file(question_paper_file)
                if not is_valid:
                    flash(result, 'danger')
                    return redirect(url_for('admin.test_upload'))
                # Generate secure filename
                question_paper_filename = generate_secure_filename(question_paper_file.filename)
                # Save file
                pdf_folder = os.path.join(current_app.root_path, 'static', 'pdfs')
                os.makedirs(pdf_folder, exist_ok=True)
                file_path = os.path.join(pdf_folder, question_paper_filename)
                question_paper_file.save(file_path)
            # Create test record
            test = Test(name=name, date=date, total_marks=total_marks, question_paper=question_paper_filename, class_for=class_for)
            db.session.add(test)
            db.session.commit()
            # Prepare class label for notification
            class_labels = {
                'all': 'All Students',
                '6': 'Class 6',
                '7': 'Class 7',
                '8': 'Class 8',
                '9': 'Class 9',
                '10': 'Class 10',
                '11_arts': 'Class 11 Arts',
                '11_science': 'Class 11 Science',
                '12_arts': 'Class 12 Arts',
                '12_science': 'Class 12 Science',
            }
            class_label = class_labels.get(class_for, class_for)
            # Store notification in DB (class-specific)
            note = Notification(
                message=f'📝 <b>{name}</b> test is now available for <b>{class_label}</b>! <a href="{url_for("student.test_update")}" class="underline">Update your marks</a>',
                class_for=class_for
            )
            db.session.add(note)
            db.session.commit()
            flash('Test created successfully!', 'success')
            socketio.emit('new_test', {'message': f'New test "{name}" uploaded for {class_label}.', 'url': url_for('student.test_update'), 'button': 'Update'})
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating test: {str(e)}', 'danger')
            current_app.logger.error(f'Test creation error: {str(e)}')
        return redirect(url_for('admin.test_upload'))
    
    tests = Test.query.order_by(Test.date.desc()).all()
    
    # Get current month and year for the date restriction notice
    current_date = datetime.now()
    current_month_name = current_date.strftime('%B')
    current_year = current_date.year
    
    return render_template('admin/test_upload.html', 
                         form=form, 
                         tests=tests,
                         current_month_name=current_month_name,
                         current_year=current_year)

@admin_bp.route('/studentleads', methods=['GET', 'POST'])
@login_required
def studentleads():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    try:
        if request.method == 'POST':
            selected_class = request.form.get('selected_class', '6')
        else:
            selected_class = request.args.get('selected_class', '6')
        leaderboard = get_leaderboard_for_class(selected_class)
        # Get information about which classes have leaderboard data
        classes_with_data = []
        class_options = ['6', '7', '8', '9', '10', '11_arts', '11_science', '12_arts', '12_science']
        for class_option in class_options:
            class_leaderboard = get_leaderboard_for_class(class_option)
            if class_leaderboard:  # If there are students with test marks
                classes_with_data.append({
                    'class': class_option,
                    'student_count': len(class_leaderboard)
                })
        return render_template('admin/studentleads.html', 
                             leaderboard=leaderboard, 
                             selected_class=selected_class,
                             classes_with_data=classes_with_data)
    except Exception as e:
        flash('Error loading leaderboard. Please try again.', 'danger')
        current_app.logger.error(f'Leaderboard error: {str(e)}')
        return render_template('admin/studentleads.html', 
                             leaderboard=[], 
                             selected_class='6',
                             classes_with_data=[])

@admin_bp.route("/test")
def test_admin():
    return "Admin blueprint is working!"

@admin_bp.route('/fee_management')
@login_required
def fee_management():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    # Get all students
    all_students = Profile.query.order_by(Profile.roll_number).all()
    
    # Get all fees with user and payment information
    all_fees = Fee.query.join(User).join(Profile).order_by(Fee.month.desc()).all()
    
    # Calculate summary statistics
    total_students = len(all_students)
    total_fees = sum(fee.amount_due for fee in all_fees)
    total_outstanding = sum(fee.amount_due for fee in all_fees if not fee.is_paid)
    
    # Get students with at least one unpaid fee (dues)
    students_with_dues_list = []
    for student in all_students:
        unpaid_fees = Fee.query.filter_by(user_id=student.user_id, is_paid=False).all()
        if unpaid_fees:
            students_with_dues_list.append({'profile': student})
    
    # Check current month dues status
    india_tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(india_tz)
    current_month_label = now.strftime('%B %Y')
    current_month_dues = Fee.query.filter_by(month=current_month_label).count()
    monthly_dues_completed = current_month_dues >= total_students
    
    # Get current monthly due amount from settings
    monthly_due_setting = Setting.query.filter_by(key='monthly_due_amount').first()
    current_monthly_amount = int(monthly_due_setting.value) if monthly_due_setting and monthly_due_setting.value.isdigit() else 1500
    
    # Show popup if there are pending approvals
    approval_count = Payment.query.filter_by(is_confirmed=False).count()
    if approval_count > 0:
        flash('Students waiting for approval. <a href="' + url_for('admin.approve') + '" class="underline">Open Approvals</a>', 'warning')
    
    return render_template('admin/fee_management.html',
                         all_students=all_students,
                         all_fees=all_fees,
                         total_students=total_students,
                         total_fees=total_fees,
                         total_outstanding=total_outstanding,
                         students_with_dues_list=students_with_dues_list,
                         students_with_dues=len(students_with_dues_list),
                         approval_count=approval_count,
                         current_month_label=current_month_label,
                         current_month_dues=current_month_dues,
                         monthly_dues_completed=monthly_dues_completed,
                         current_monthly_amount=current_monthly_amount)

@admin_bp.route('/add_fee', methods=['POST'])
@login_required
def add_fee():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    user_id = request.form.get('user_id')
    month = request.form.get('month')
    # amount = request.form.get('amount')  # Remove manual amount
    
    if user_id and month:
        # Get the student's class
        student_profile = Profile.query.filter_by(user_id=user_id).first()
        if not student_profile:
            flash('Student profile not found.', 'danger')
            return redirect(url_for('admin.fee_management'))
        fee_amount = get_fee_amount_for_class(student_profile.student_class)
        # Check if fee already exists for this user and month
        existing_fee = Fee.query.filter_by(user_id=user_id, month=month).first()
        if existing_fee:
            flash(f'Fee for {month} already exists for this student.', 'danger')
        else:
            fee = Fee(user_id=user_id, month=month, amount_due=fee_amount)
            db.session.add(fee)
            db.session.commit()
            flash(f'Fee added successfully for {month}.', 'success')
    else:
        flash('Please fill all fields.', 'danger')
    
    return redirect(url_for('admin.fee_management'))

@admin_bp.route('/confirm_payment/<int:payment_id>', methods=['POST'])
@login_required
def confirm_payment(payment_id):
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    payment = Payment.query.get_or_404(payment_id)
    if payment.method == 'Cash' and not payment.is_confirmed:
        payment.is_confirmed = True
        payment.confirmed_at = get_current_time_ist()
        payment.fee.is_paid = True
        db.session.commit()
        flash('Cash payment confirmed successfully!', 'success')
    else:
        flash('Invalid payment or already confirmed.', 'danger')
    
    return redirect(url_for('admin.fee_management'))

@admin_bp.route('/approve')
@login_required
def approve():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    # Get pending cash payments
    pending_cash_payments = Payment.query.filter_by(method='Cash', is_confirmed=False).join(Fee).join(User).join(Profile).order_by(Payment.requested_at.desc()).all()
    
    # Get pending UPI payments
    pending_upi_payments = Payment.query.filter_by(method='UPI', is_confirmed=False).join(Fee).join(User).join(Profile).order_by(Payment.requested_at.desc()).all()
    
    # Get recent approvals (only confirmed payments)
    recent_approvals = Payment.query.filter(
        Payment.is_confirmed == True
    ).join(Fee).join(User).join(Profile).order_by(Payment.confirmed_at.desc()).limit(10).all()
    
    # Calculate statistics
    pending_cash_count = len(pending_cash_payments)
    pending_upi_count = len(pending_upi_payments)
    total_pending = pending_cash_count + pending_upi_count
    
    approved_today = Payment.query.filter(
        Payment.is_confirmed == True,
        Payment.confirmed_at >= date.today()
    ).count()
    
    # For rejected payments, we need to track them differently since they're deleted
    # For now, we'll show 0 rejected today since rejected payments are deleted
    rejected_today = 0
    
    return render_template('admin/approve.html',
                         pending_cash_payments=pending_cash_payments,
                         pending_upi_payments=pending_upi_payments,
                         recent_approvals=recent_approvals,
                         pending_cash_count=pending_cash_count,
                         pending_upi_count=pending_upi_count,
                         total_pending=total_pending,
                         approved_today=approved_today,
                         rejected_today=rejected_today)

@admin_bp.route('/notify_student/<int:student_id>', methods=['POST'])
@login_required
def notify_student(student_id):
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    student = Profile.query.get_or_404(student_id)
    # Compose notification message (popup only, not stored)
    message = 'Please complete all your dues. <a href="' + url_for('student.fee') + '" class="underline">Open</a>'
    # Set pending_popup for the student
    student.pending_popup = message
    db.session.commit()
    flash('Student will see a popup about their dues next time they log in.', 'success')
    return redirect(url_for('admin.student_profile', student_id=student_id))

@admin_bp.route('/approve_payment/<int:payment_id>', methods=['POST'])
@login_required
def approve_payment(payment_id):
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.login'))
    
    payment = Payment.query.get_or_404(payment_id)
    payment.is_confirmed = True
    payment.confirmed_at = get_current_time_ist()
    
    # Update the associated fee as paid
    fee = Fee.query.get(payment.fee_id)
    if fee:
        fee.is_paid = True
    
    db.session.commit()
    flash('Payment approved successfully!', 'success')
    return redirect(url_for('admin.approve'))

@admin_bp.route('/reject_payment/<int:payment_id>', methods=['POST'])
@login_required
def reject_payment(payment_id):
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.login'))
    
    payment = Payment.query.get_or_404(payment_id)
    payment.is_confirmed = True  # Mark as processed
    payment.confirmed_at = get_current_time_ist()
    
    db.session.commit()
    flash('Payment rejected successfully!', 'success')
    return redirect(url_for('admin.approve'))

@admin_bp.route('/feedues')
@login_required
def feedues():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    # Get all students with their fee information
    all_students = Profile.query.all()
    
    students_with_dues_list = []
    students_paid_up_list = []
    total_outstanding = 0
    
    for student in all_students:
        # Get all fees for this student
        fees = Fee.query.filter_by(user_id=student.user_id).all()
        outstanding_fees = [fee for fee in fees if not fee.is_paid]
        paid_fees = [fee for fee in fees if fee.is_paid]
        
        total_due = sum(fee.amount_due for fee in outstanding_fees)
        total_paid = sum(fee.amount_due for fee in paid_fees)
        
        if outstanding_fees:
            # Student has dues
            students_with_dues_list.append({
                'profile': student,
                'outstanding_fees': outstanding_fees,
                'due_count': len(outstanding_fees),
                'total_due': total_due
            })
            total_outstanding += total_due
        else:
            # Student is paid up
            students_paid_up_list.append({
                'profile': student,
                'total_paid': total_paid
            })
    
    # Sort students with dues by due count (descending)
    students_with_dues_list.sort(key=lambda x: x['due_count'], reverse=True)
    
    return render_template('admin/feedues.html',
                         students_with_dues_list=students_with_dues_list,
                         students_paid_up_list=students_paid_up_list,
                         students_with_dues=len(students_with_dues_list),
                         students_paid_up=len(students_paid_up_list),
                         total_outstanding=total_outstanding,
                         total_students=len(all_students))

@admin_bp.route('/dues', methods=['GET', 'POST'])
@login_required
def dues_management():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))

    # Handle add due form
    if request.method == 'POST' and 'add_due' in request.form:
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            flash('Invalid CSRF token.', 'danger')
            return redirect(url_for('admin.dues_management'))
        selected_students = request.form.getlist('selected_students')
        month = request.form.get('month')
        amount = request.form.get('amount')
        is_paid = request.form.get('is_paid') == 'on'
        if selected_students and month and amount:
            added_count = 0
            skipped_count = 0
            for user_id in selected_students:
                # Check if due already exists for this user and month
                existing_due = Fee.query.filter_by(user_id=user_id, month=month).first()
                if not existing_due:
                    fee = Fee(user_id=user_id, month=month, amount_due=int(amount), is_paid=is_paid)
                    db.session.add(fee)
                    added_count += 1
                else:
                    skipped_count += 1
            db.session.commit()
            if added_count > 0:
                flash(f'Due added for {added_count} students successfully.', 'success')
            if skipped_count > 0:
                flash(f'Skipped {skipped_count} students (dues already exist for this month).', 'warning')
        else:
            flash('Please select at least one student and fill all required fields.', 'danger')
        return redirect(url_for('admin.dues_management'))

    # Handle edit due form
    if request.method == 'POST' and 'edit_due' in request.form:
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            flash('Invalid CSRF token.', 'danger')
            return redirect(url_for('admin.dues_management'))
        fee_id = request.form.get('fee_id')
        amount = request.form.get('edit_amount')
        month = request.form.get('edit_month')
        is_paid = request.form.get('edit_is_paid') == 'on'
        fee = Fee.query.get(fee_id)
        if fee:
            fee.amount_due = int(amount)
            fee.month = month
            fee.is_paid = is_paid
            db.session.commit()
            flash('Due updated successfully.', 'success')
        else:
            flash('Due not found.', 'danger')
        return redirect(url_for('admin.dues_management'))

    # Handle delete due
    if request.method == 'POST' and 'delete_due' in request.form:
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            flash('Invalid CSRF token.', 'danger')
            return redirect(url_for('admin.dues_management'))
        fee_id = request.form.get('fee_id')
        fee = Fee.query.get(fee_id)
        if fee:
            db.session.delete(fee)
            db.session.commit()
            flash('Due deleted successfully.', 'success')
        else:
            flash('Due not found.', 'danger')
        return redirect(url_for('admin.dues_management'))

    # Handle mark as paid/unpaid
    if request.method == 'POST' and 'toggle_paid' in request.form:
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            flash('Invalid CSRF token.', 'danger')
            return redirect(url_for('admin.dues_management'))
        fee_id = request.form.get('fee_id')
        fee = Fee.query.get(fee_id)
        if fee:
            fee.is_paid = not fee.is_paid
            db.session.commit()
            flash('Due payment status updated.', 'success')
        else:
            flash('Due not found.', 'danger')
        return redirect(url_for('admin.dues_management'))

    # List all dues (reuse fee_management table data)
    dues = Fee.query.order_by(Fee.month.desc()).all()
    students = Profile.query.order_by(Profile.roll_number).all()
    
    # Pass current date for month options
    now = datetime.now()
    
    return render_template('admin/dues_management.html', dues=dues, students=students, now=now)

@admin_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, is_admin=True).first()
        if user:
            token = generate_password_reset_token(user.email)
            send_password_reset_email(user, token, is_admin=True)
        flash('If your email is registered as an admin, you will receive a password reset link.', 'info')
        return redirect(url_for('admin.login'))
    return render_template('student/forgot_password.html', form=form)

@admin_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_password_reset_token(token)
    if not email:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('admin.forgot_password'))
    user = User.query.filter_by(email=email, is_admin=True).first()
    if not user:
        flash('Invalid admin user.', 'danger')
        return redirect(url_for('admin.forgot_password'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Your password has been updated! You can now log in as admin.', 'success')
        return redirect(url_for('admin.login'))
    return render_template('student/reset_password.html', form=form)

@admin_bp.route('/adduser', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        return redirect(url_for('admin.login'))
    form = AddAdminUserForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Admin with this email already exists.', 'danger')
        else:
            new_admin = User(email=form.email.data, password=generate_password_hash(form.password.data), is_admin=True)
            db.session.add(new_admin)
            db.session.commit()
            flash('New admin user added successfully!', 'success')
            return redirect(url_for('main.landing'))
    return render_template('admin/add_user.html', form=form)

@admin_bp.route('/upi_settings', methods=['GET', 'POST'])
@login_required
def upi_settings():
    if not current_user.is_admin:
        return redirect(url_for('admin.login'))
    upi_setting = Setting.query.filter_by(key='upi_id').first()
    phone_setting = Setting.query.filter_by(key='upi_phone').first()
    form = UPISettingsForm(
        upi_id=upi_setting.value if upi_setting else '',
        phone_number=phone_setting.value if phone_setting else ''
    )
    if form.validate_on_submit():
        # Update UPI ID
        if upi_setting:
            upi_setting.value = form.upi_id.data
        else:
            upi_setting = Setting(key='upi_id', value=form.upi_id.data)
            db.session.add(upi_setting)
        # Update phone number
        if phone_setting:
            phone_setting.value = form.phone_number.data
        else:
            phone_setting = Setting(key='upi_phone', value=form.phone_number.data)
            db.session.add(phone_setting)
        db.session.commit()
        flash('UPI settings updated successfully!', 'success')
        return redirect(url_for('admin.upi_settings'))
    return render_template('admin/upi_settings.html', form=form)

@admin_bp.route('/test_marks_management')
@login_required
def test_marks_management():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    try:
        # Get month and year from query parameters, default to current month
        from datetime import datetime, date
        current_date = datetime.now()
        
        # Get selected month, year, and class from query parameters
        selected_month = request.args.get('month', current_date.month, type=int)
        selected_year = request.args.get('year', current_date.year, type=int)
        selected_class = request.args.get('class', 'all')
        
        # Validate month and year
        if selected_month < 1 or selected_month > 12:
            selected_month = current_date.month
        if selected_year < 2025 or selected_year > current_date.year:
            selected_year = current_date.year
        
        # Calculate navigation months
        current_month = current_date.month
        current_year = current_date.year
        
        # Previous month
        if selected_month == 1:
            previous_month = 12
            previous_year = selected_year - 1
        else:
            previous_month = selected_month - 1
            previous_year = selected_year
        
        # Next month
        if selected_month == 12:
            next_month = 1
            next_year = selected_year + 1
        else:
            next_month = selected_month + 1
            next_year = selected_year
        
        # Get tests for the selected month, filtered by class if specified
        test_query = Test.query.filter(
            db.extract('month', Test.date) == selected_month,
            db.extract('year', Test.date) == selected_year
        )
        
        # Filter tests by class if a specific class is selected
        if selected_class != 'all':
            # Show tests for 'all' students AND tests for the specific class
            test_query = test_query.filter(
                db.or_(
                    Test.class_for == 'all',
                    Test.class_for == selected_class
                )
            )
        
        tests_in_month = test_query.order_by(Test.date.desc()).all()
        
        # Get all marks for tests in the selected month, filtered by class if specified
        test_ids = [test.id for test in tests_in_month]
        marks_in_month = []
        
        if test_ids:
            query = db.session.query(Mark, User, Profile, Test).join(
                User, Mark.user_id == User.id
            ).join(
                Profile, User.id == Profile.user_id
            ).join(
                Test, Mark.test_id == Test.id
            ).filter(
                Mark.test_id.in_(test_ids)
            )
            
            # Add class filter if a specific class is selected
            if selected_class != 'all':
                query = query.filter(Profile.student_class == selected_class)
            
            marks_in_month = query.order_by(Test.date.desc(), Profile.full_name).all()
        
        # Calculate statistics for the selected month
        total_marks = len(marks_in_month)
        perfect_scores = len([m for m in marks_in_month if m[0].marks_obtained == m[3].total_marks])
        high_scores = len([m for m in marks_in_month if m[0].marks_obtained > m[3].total_marks * 0.9])  # 90%+ scores
        
        # Group marks by test for the toggle functionality
        marks_by_test = {}
        for mark, user, profile, test in marks_in_month:
            if test.id not in marks_by_test:
                marks_by_test[test.id] = {
                    'test': test,
                    'marks': []
                }
            marks_by_test[test.id]['marks'].append({
                'mark': mark,
                'user': user,
                'profile': profile
            })
        
        # Create month names dictionary
        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        
        # Create year options (from 2025 to current year)
        year_options = list(range(2025, current_date.year + 1))
        
        return render_template('admin/test_marks_management.html', 
                             tests_in_month=tests_in_month,
                             marks_by_test=marks_by_test,
                             total_marks=total_marks,
                             perfect_scores=perfect_scores,
                             high_scores=high_scores,
                             selected_month=selected_month,
                             selected_year=selected_year,
                             selected_class=selected_class,
                             month_names=month_names,
                             year_options=year_options,
                             current_month=current_month,
                             current_year=current_year,
                             previous_month=previous_month,
                             previous_year=previous_year,
                             next_month=next_month,
                             next_year=next_year)
        
    except Exception as e:
        flash('Error loading test marks. Please try again.', 'danger')
        current_app.logger.error(f'Test marks management error: {str(e)}')
        return redirect(url_for('admin.home1'))

@admin_bp.route('/edit_mark/<int:mark_id>', methods=['GET', 'POST'])
@login_required
def edit_mark(mark_id):
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.login'))
    
    mark = Mark.query.get_or_404(mark_id)
    test = Test.query.get(mark.test_id)
    user = User.query.get(mark.user_id)
    profile = Profile.query.filter_by(user_id=mark.user_id).first()
    
    if request.method == 'POST':
        new_marks = request.form.get('marks_obtained')
        if new_marks and new_marks.isdigit():
            mark.marks_obtained = int(new_marks)
            mark.updated_at = get_current_time_ist()
            db.session.commit()
            flash('Mark updated successfully!', 'success')
            return redirect(url_for('admin.test_marks_management'))
        else:
            flash('Please enter a valid mark.', 'error')
    
    return render_template('admin/edit_mark.html', mark=mark, test=test, user=user, profile=profile)

@admin_bp.route('/delete_mark/<int:mark_id>', methods=['POST'])
@login_required
def delete_mark(mark_id):
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    mark = Mark.query.get_or_404(mark_id)
    test = Test.query.get(mark.test_id)
    user = User.query.get(mark.user_id)
    
    try:
        # Log the deletion
        current_app.logger.warning(f'Admin {current_user.id} ({current_user.email}) deleted mark {mark.marks_obtained}/{test.total_marks} for student {user.id} ({user.email}) for test {test.id}')
        
        db.session.delete(mark)
        db.session.commit()
        
        flash('Mark deleted successfully.', 'success')
        return redirect(url_for('admin.test_marks_management'))
        
    except Exception as e:
        db.session.rollback()
        flash('Error deleting mark. Please try again.', 'danger')
        current_app.logger.error(f'Delete mark error: {str(e)}')
        return redirect(url_for('admin.test_marks_management'))

@admin_bp.route('/suspicious_activity')
@login_required
def suspicious_activity():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    try:
        # Find suspicious patterns
        suspicious_marks = []
        
        # Get all marks with student info
        all_marks = db.session.query(Mark, User, Profile, Test).join(
            User, Mark.user_id == User.id
        ).join(
            Profile, User.id == Profile.user_id
        ).join(
            Test, Mark.test_id == Test.id
        ).all()
        
        # Check for perfect scores (multiple)
        student_perfect_scores = {}
        for mark, user, profile, test in all_marks:
            if mark.marks_obtained == test.total_marks:
                if user.id not in student_perfect_scores:
                    student_perfect_scores[user.id] = []
                student_perfect_scores[user.id].append((mark, test))
        
        # Flag students with 3+ perfect scores
        for user_id, perfect_marks in student_perfect_scores.items():
            if len(perfect_marks) >= 3:
                user = User.query.get(user_id)
                profile = Profile.query.filter_by(user_id=user_id).first()
                suspicious_marks.append({
                    'type': 'Multiple Perfect Scores',
                    'student': user,
                    'profile': profile,
                    'marks': perfect_marks,
                    'count': len(perfect_marks)
                })
        
        # Check for marks exceeding test total (shouldn't happen with new validation)
        for mark, user, profile, test in all_marks:
            if mark.marks_obtained > test.total_marks:
                suspicious_marks.append({
                    'type': 'Marks Exceed Total',
                    'student': user,
                    'profile': profile,
                    'mark': mark,
                    'test': test
                })
        
        return render_template('admin/suspicious_activity.html', suspicious_marks=suspicious_marks)
        
    except Exception as e:
        flash('Error loading suspicious activity. Please try again.', 'danger')
        current_app.logger.error(f'Suspicious activity error: {str(e)}')
        return redirect(url_for('admin.home1'))

@admin_bp.route('/trigger_monthly_dues', methods=['POST'])
@login_required
def trigger_monthly_dues():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    from app.utils import get_fee_amount_for_class
    india_tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(india_tz)
    current_month_label = now.strftime('%B %Y')
    all_students = Profile.query.order_by(Profile.roll_number).all()
    added_count = 0
    skipped_count = 0
    for student in all_students:
        # Check if fee already exists for this user and month
        existing_fee = Fee.query.filter_by(user_id=student.user_id, month=current_month_label).first()
        if not existing_fee:
            fee_amount = get_fee_amount_for_class(student.student_class)
            fee = Fee(user_id=student.user_id, month=current_month_label, amount_due=fee_amount)
            db.session.add(fee)
            added_count += 1
            # Create notification for the student
            notification_message = f"{current_month_label} month due added. Please complete the due"
            existing_notification = Notification.query.filter_by(user_id=student.user_id, message=notification_message).first()
            if not existing_notification:
                notification = Notification(user_id=student.user_id, message=notification_message)
                db.session.add(notification)
                db.session.commit()
        else:
            skipped_count += 1
    db.session.commit()
    flash(f'Monthly dues assigned: {added_count} students, skipped {skipped_count} (already assigned).', 'success')
    return redirect(url_for('admin.fee_management'))

@admin_bp.route('/resource', methods=['GET', 'POST'])
@login_required
def resource():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    
    form = ResourceForm()
    
    if form.validate_on_submit():
        try:
            from app.models import Resource
            class_for = form.class_for.data
            # Create new resource
            resource = Resource(
                name=form.name.data,
                link=form.link.data,
                description=form.description.data,
                created_by=current_user.id,
                class_for=class_for
            )
            db.session.add(resource)
            db.session.commit()
            # Prepare class label for notification
            class_labels = {
                'all': 'All Students',
                '6': 'Class 6',
                '7': 'Class 7',
                '8': 'Class 8',
                '9': 'Class 9',
                '10': 'Class 10',
                '11_arts': 'Class 11 Arts',
                '11_science': 'Class 11 Science',
                '12_arts': 'Class 12 Arts',
                '12_science': 'Class 12 Science',
            }
            class_label = class_labels.get(class_for, class_for)
            # Store notification in DB (class-specific)
            message = f'📚 <b>{form.name.data}</b> resource is now available for <b>{class_label}</b>! <a href="{url_for("student.resources")}" class="underline">Open Resource</a>'
            notification = Notification(message=message, class_for=class_for)
            db.session.add(notification)
            db.session.commit()
            # Send real-time notification via SocketIO
            socketio.emit('new_notification', {
                'message': message,
                'url': url_for('student.resources'),
                'button': 'View Resources'
            })
            flash('Resource added successfully! Students will be notified.', 'success')
            return redirect(url_for('admin.resource'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding resource: {str(e)}', 'danger')
            current_app.logger.error(f'Resource error: {str(e)}')
    
    # Get recent resources
    try:
        from app.models import Resource
        resources = Resource.query.order_by(Resource.created_at.desc()).limit(10).all()
    except Exception as e:
        resources = []
        current_app.logger.error(f'Error fetching resources: {str(e)}')
    
    return render_template('admin/resource.html', form=form, resources=resources) 

@admin_bp.route('/dropouts')
@login_required
def dropouts():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    status = request.args.get('status', 'pending')
    requests = DropoutRequest.query.filter_by(status=status).order_by(DropoutRequest.requested_at.desc()).all()
    return render_template('admin/dropouts.html', requests=requests, status=status)

@admin_bp.route('/dropout/<int:request_id>', methods=['GET', 'POST'])
@login_required
def dropout_request_detail(request_id):
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    dropout = DropoutRequest.query.get_or_404(request_id)
    student = Profile.query.filter_by(user_id=dropout.user_id).first()
    dues = Fee.query.filter_by(user_id=dropout.user_id, is_paid=False).all()
    total_due = sum(fee.amount_due for fee in dues)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'approve' and total_due == 0:
            # Approve and commit the dropout request
            dropout.status = 'approved'
            dropout.processed_at = get_current_time_ist()
            db.session.commit()
            # Delete the dropout request
            db.session.delete(dropout)
            db.session.commit()
            # Now delete all related data and the user
            user = User.query.get(dropout.user_id)
            if user:
                # Delete related Profile
                profile = Profile.query.filter_by(user_id=user.id).first()
                if profile:
                    db.session.delete(profile)
                # Delete related Notifications
                Notification.query.filter_by(user_id=user.id).delete()
                # Delete related Fees
                Fee.query.filter_by(user_id=user.id).delete()
                # Delete related Payments
                Payment.query.filter_by(user_id=user.id).delete()
                # Delete related Marks
                Mark.query.filter_by(user_id=user.id).delete()
                # Delete related DropoutRequests
                DropoutRequest.query.filter_by(user_id=user.id).delete()
                # Delete related Resources (if created_by)
                Resource.query.filter_by(created_by=user.id).delete()
                # (Add other related deletions as needed)
                db.session.delete(user)
                db.session.commit()
            resequence_roll_numbers(student.student_class)
            # Log out the student if they are logged in
            try:
                from flask_login import current_user as flask_current_user
                if flask_current_user.is_authenticated and flask_current_user.id == user.id:
                    logout_user()
            except Exception:
                pass
            # TODO: Send email to user.email about approval
            flash('Dropout approved and student removed.', 'success')
        elif action == 'reject':
            dropout.status = 'rejected'
            dropout.admin_response = request.form.get('admin_response', '')
            dropout.processed_at = get_current_time_ist()
            db.session.commit()
            user = User.query.get(dropout.user_id)
            # TODO: Send email to user.email about rejection with reason
            flash('Dropout request rejected.', 'info')
        return redirect(url_for('admin.dropouts'))
    return render_template('admin/dropout_detail.html', dropout=dropout, student=student, dues=dues, total_due=total_due)

@admin_bp.route('/remove_students', methods=['GET', 'POST'])
@login_required
def remove_students():
    if not current_user.is_admin:
        return redirect(url_for('student.home'))
    selected_class = request.args.get('class_for', 'all')
    search = request.args.get('search', '').lower()
    if selected_class == 'all':
        students = Profile.query.order_by(Profile.student_class, Profile.roll_number).all()
    else:
        students = Profile.query.filter_by(student_class=selected_class).order_by(Profile.roll_number).all()
    if search:
        students = [s for s in students if search in s.full_name.lower() or search in str(s.roll_number)]
    if request.method == 'POST':
        student_id = int(request.form.get('student_id'))
        student = Profile.query.get(student_id)
        if not student:
            flash('Student not found.', 'danger')
            return redirect(url_for('admin.remove_students', class_for=selected_class))
        user = User.query.get(student.user_id)
        if not user:
            flash('User record not found for this student.', 'danger')
            return redirect(url_for('admin.remove_students', class_for=selected_class))
        student_class = student.student_class
        student_name = student.full_name  # Save name before deletion
        # Delete related Profile
        db.session.delete(student)
        # Delete related Notifications
        Notification.query.filter_by(user_id=user.id).delete()
        # Delete related Fees
        Fee.query.filter_by(user_id=user.id).delete()
        # Delete related Payments
        Payment.query.filter_by(user_id=user.id).delete()
        # Delete related Marks
        Mark.query.filter_by(user_id=user.id).delete()
        # Delete related DropoutRequests
        DropoutRequest.query.filter_by(user_id=user.id).delete()
        # Delete related Resources (if created_by)
        Resource.query.filter_by(created_by=user.id).delete()
        # (Add other related deletions as needed)
        db.session.delete(user)
        db.session.commit()
        resequence_roll_numbers(student_class)
        flash(f'{student_name} successfully removed and roll numbers resequenced.', 'success')
        return redirect(url_for('admin.remove_students', class_for=selected_class))
    # Attach dues info
    students_with_dues = []
    for s in students:
        dues = Fee.query.filter_by(user_id=s.user_id, is_paid=False).all()
        students_with_dues.append({'student': s, 'dues_count': len(dues), 'dues_total': sum(f.amount_due for f in dues)})
    return render_template('admin/remove_students.html', students=students_with_dues, selected_class=selected_class, search=search)

def resequence_roll_numbers(student_class):
    # Get all students in class, order by roll_number
    students = Profile.query.filter_by(student_class=student_class).order_by(Profile.roll_number).all()
    # Step 1: Assign temporary roll numbers to avoid unique constraint collision
    for idx, student in enumerate(students, start=1):
        student.roll_number = -idx  # Use negative numbers as temporary
    db.session.commit()
    # Step 2: Assign correct sequential roll numbers
    for idx, student in enumerate(students, start=1):
        student.roll_number = idx
    db.session.commit()

# CSRF error handler
@admin_bp.app_errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('errors/csrf.html', reason=e.description), 400 