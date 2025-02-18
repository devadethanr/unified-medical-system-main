import os
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for
from flask_pymongo import PyMongo
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from flask_session import Session
from flask_mail import Mail
from datetime import datetime
from config import Config
from pymongo.errors import ConnectionFailure
from app.routes.dbchat import check_gemini_api, init_dbchat

# Initialize Flask extensions
mongo = PyMongo()
login_manager = LoginManager()
oauth = OAuth()
mail = Mail()

def create_app(config_class='config.DevelopmentConfig'):
    app = Flask(__name__)

    # Load config
    if isinstance(config_class, str):
        app.config.from_object(config_class)
    else:
        app.config.update(config_class)

    # Initialize MongoDB
    try:
        mongo.init_app(app)
        # Test the connection
        mongo.db.command('ping')
        print("MongoDB connection successful!")
    except ConnectionFailure as e:
        print(f"MongoDB connection failed: {str(e)}")
        # You might want to handle this error more gracefully
    except Exception as e:
        print(f"Error initializing MongoDB: {str(e)}")

    # Check MongoDB connection
    try:
        mongo.db.command('ping')
        print("MongoDB connection successful!")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        
    # Check Gemini API connection
    if check_gemini_api():
        print("Gemini API connection successful!")
    else:
        print("Warning: Gemini API connection failed!")

    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Only initialize these services if not in testing mode
    if not app.config.get('TESTING'):
        # Session config
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
        Session(app)

        # Mail config
        app.config['MAIL_SERVER'] = 'smtp.gmail.com'
        app.config['MAIL_PORT'] = 587
        app.config['MAIL_USERNAME'] = os.getenv('MAIL_ID')
        app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
        app.config['MAIL_USE_TLS'] = True
        app.config['MAIL_USE_SSL'] = False
        mail.init_app(app)

        # OAuth config
        oauth.init_app(app)
        oauth.register(
            name='google',
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
            authorize_url='https://accounts.google.com/o/oauth2/auth',
            authorize_params=None,
            access_token_url='https://accounts.google.com/o/oauth2/token',
            access_token_params=None,
            refresh_token_url=None,
            redirect_uri='http://127.0.0.1:8000/auth/google_authorized',
            client_kwargs={'scope': 'openid email profile'}
        )

    # Register routes and error handlers
    @app.route('/')
    def index():
        return render_template('common/index.html')

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error/500.html'), 500

    # Register blueprints
    from app.routes import admin, patient, doctor, hospital, auth, meddata, dbchat
    app.register_blueprint(auth.auth_bp, url_prefix='/auth')
    app.register_blueprint(admin.admin_bp, url_prefix='/admin')
    app.register_blueprint(patient.patient_bp, url_prefix='/patient')
    app.register_blueprint(doctor.doctor_bp, url_prefix='/doctor')
    app.register_blueprint(hospital.hospital_bp, url_prefix='/hospital')
    app.register_blueprint(meddata.meddata_bp, url_prefix='/meddata')
    app.register_blueprint(dbchat.dbchat_bp, url_prefix='/dbchat')

    # Initialize dbchat system with mongo instance
    init_dbchat(mongo)

    # Template filters
    @app.template_filter('format_date')
    def format_date(value):
        if isinstance(value, dict) and '$date' in value:
            value = value['$date']
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.rstrip('Z'))
            except ValueError:
                return value
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return value

    return app
