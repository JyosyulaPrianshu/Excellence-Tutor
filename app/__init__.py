from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from config import Config
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_mail import Mail
import os
import time
import logging
import pytz
from datetime import datetime

# Initialize extensions
login_manager = LoginManager()
db = SQLAlchemy()
csrf = CSRFProtect()
migrate = Migrate()
socketio = SocketIO(cors_allowed_origins="*")
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        # Use a simple file handler instead of rotating file handler to avoid Windows issues
        file_handler = logging.FileHandler('logs/excellence_tutorial.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Excellence Tutorial startup')

    # Add static_bust filter for cache-busting
    @app.template_filter('static_bust')
    def static_bust(filename):
        """Add a timestamp to static files for cache-busting"""
        if not filename:
            return filename
        
        # Get the file path
        file_path = os.path.join(app.static_folder, filename)
        
        # Check if file exists and get its modification time
        if os.path.exists(file_path):
            timestamp = int(os.path.getmtime(file_path))
        else:
            # If file doesn't exist, use current time
            timestamp = int(time.time())
        
        # Add timestamp as query parameter
        return f"{filename}?v={timestamp}"

    # Add IST time filter for converting UTC to IST
    @app.template_filter('ist_time')
    def ist_time(dt, format='%d-%m-%Y %H:%M'):
        """Convert UTC datetime to IST and format it"""
        if not dt:
            return '-'
        
        # If datetime is naive (no timezone), assume it's already in IST
        # since we're now storing all times in IST
        if dt.tzinfo is None:
            return dt.strftime(format)
        
        # If datetime has timezone info, convert to IST
        ist_tz = pytz.timezone('Asia/Kolkata')
        ist_time = dt.astimezone(ist_tz)
        
        return ist_time.strftime(format)

    # Add IST date filter for converting UTC to IST date only
    @app.template_filter('ist_date')
    def ist_date(dt, format='%d-%m-%Y'):
        """Convert UTC datetime to IST and format as date only"""
        if not dt:
            return '-'
        
        # If datetime is naive (no timezone), assume it's already in IST
        # since we're now storing all times in IST
        if dt.tzinfo is None:
            return dt.strftime(format)
        
        # If datetime has timezone info, convert to IST
        ist_tz = pytz.timezone('Asia/Kolkata')
        ist_time = dt.astimezone(ist_tz)
        
        return ist_time.strftime(format)

    # Global error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Server Error: {error}')
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        app.logger.warning(f'CSRF Error: {e}')
        return render_template('errors/csrf.html'), 400

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    mail.init_app(app)

    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes.student import student_bp
    from app.routes.admin import admin_bp
    from app.routes.main import main_bp
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(main_bp)

    return app 