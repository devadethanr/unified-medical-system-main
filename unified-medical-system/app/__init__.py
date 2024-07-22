from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
import random
from authlib.integrations.flask_client import OAuth
from flask_session import Session
from flask_mail import Mail

mongo = PyMongo()
login_manager = LoginManager()
oauth = OAuth()
mail = Mail()

GOOGLE_CLIENT_ID = '806603351387-asf74r67qn6101dtjmrdiqpbqq301vrm.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'

def create_app(config_class='config.DevelopmentConfig'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    try:
        mongo.init_app(app)
    except Exception as e:
        print(f"Error initializing Flask-PyMongo: {str(e)}")
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    #session management and storage
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'  # Directory for storing session files
    Session(app)
    
    #mail client configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USERNAME'] = 'devadethanr2025@mca.ajce.in'
    app.config['MAIL_PASSWORD'] = 'MUMUbubu@2024'
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    Mail(app)
    
    # Configure Google OAuth
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        access_token_url='https://accounts.google.com/o/oauth2/token',
        access_token_params=None,
        refresh_token_url=None,
        redirect_uri='http://127.0.0.1:5000/auth/google_authorized',
        client_kwargs={'scope': 'openid email profile'}
    )
    
    oauth.init_app(app)

    from app.routes import admin, patient, doctor, hospital, auth
    app.register_blueprint(auth.auth_bp, url_prefix='/auth')
    app.register_blueprint(admin.admin_bp, url_prefix='/admin')
    app.register_blueprint(patient.patient_bp, url_prefix='/patient')
    app.register_blueprint(doctor.doctor_bp, url_prefix='/doctor')
    app.register_blueprint(hospital.hospital_bp, url_prefix='/hospital')

    return app
